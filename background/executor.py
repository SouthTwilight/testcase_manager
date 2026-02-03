import subprocess
import json
import time
import threading
from datetime import datetime, timedelta
from models import db, TestCase, TestExecution, ExecutionTask, TestPlan
from config import Config
from distributed import DistributedManager
from utils.logger import logger


class TestCaseExecutor:
    def __init__(self, max_workers=None, result_parser=None):
        """
        初始化测试用例执行器

        Args:
            max_workers: 最大并发数（由于依赖唯一硬件资源，固定为1）
            result_parser: 自定义结果解析函数，签名为:
                         func(result: subprocess.CompletedProcess, test_case: TestCase) -> tuple[str, str]
                         返回 (status, details_json)
                         其中 status 为 'passed'/'failed'/'skipped'等
        """
        # 强制串行执行，因为依赖唯一的硬件资源（测试机）
        self.max_workers = 1
        self.timeout = Config.TEST_TIMEOUT
        self.executing_cases = set()  # 正在执行的用例哈希集合
        self.lock = threading.Lock()
        self.distributed_manager = DistributedManager()
        self.result_parser = result_parser  # 自定义结果解析器

        # 硬件资源锁：确保同一时间只有一个用例在执行
        self.hardware_lock = threading.Lock()
        self.current_hardware_owner = None

    def calculate_priority_score(self, test_case):
        """计算用例执行优先级分数"""
        score = 0
        now = datetime.now()

        # 1. 新增用例（未执行过的）
        if test_case.status == 'not_executed':
            score += Config.PRIORITY_WEIGHTS['new_case']

        # 2. 正在执行的用例不重复执行
        if test_case.status == 'executing':
            return -1  # 负分表示跳过

        # 3. 上次执行失败的用例
        if test_case.status == 'failed':
            score += Config.PRIORITY_WEIGHTS['failed_case']

        # 4. 长时间未执行的用例
        if test_case.last_execution_time:
            days_since_last = (now - test_case.last_execution_time).days
            interval_score = min(days_since_last / 30, 1.0)  # 最大30天
            score += interval_score * Config.PRIORITY_WEIGHTS['long_interval']

        # 5. 优先目录中的用例
        for priority_dir in Config.HIGH_PRIORITY_DIRS:
            if test_case.relative_path.startswith(priority_dir):
                score += Config.PRIORITY_WEIGHTS['high_priority_dir']
                break

        # 6. 执行时间短的用例优先
        if test_case.avg_duration > 0:
            duration_score = 1.0 / (1.0 + test_case.avg_duration / 60)  # 归一化
            score += duration_score * Config.PRIORITY_WEIGHTS['short_duration']

        return score

    def select_cases_for_execution(self, limit=100, include_paths=None, exclude_paths=None):
        """选择要执行的用例"""
        query = TestCase.query.filter_by(is_active=True)

        # 路径过滤
        if include_paths:
            import json
            include_list = json.loads(include_paths) if isinstance(include_paths, str) else include_paths
            # 构建路径过滤条件
            from sqlalchemy import or_
            conditions = []
            for path in include_list:
                conditions.append(TestCase.relative_path.like(f"{path}%"))
            if conditions:
                query = query.filter(or_(*conditions))

        if exclude_paths:
            exclude_list = json.loads(exclude_paths) if isinstance(exclude_paths, str) else exclude_paths
            for path in exclude_list:
                query = query.filter(~TestCase.relative_path.like(f"{path}%"))

        # 获取所有符合条件的用例并计算优先级
        all_cases = query.all()
        prioritized_cases = []

        for case in all_cases:
            score = self.calculate_priority_score(case)
            if score >= 0:  # 排除正在执行的用例
                prioritized_cases.append((score, case))

        # 按优先级排序
        prioritized_cases.sort(key=lambda x: x[0], reverse=True)

        # 返回前limit个用例
        return [case for _, case in prioritized_cases[:limit]]

    def execute_single_case(self, test_case, plan_id=None):
        """执行单个测试用例（串行执行，独占硬件资源）"""
        case_hash = test_case.case_hash

        # 获取硬件资源锁（测试机）
        acquired = self.hardware_lock.acquire(blocking=True, timeout=60)
        if not acquired:
            return 'skipped', 0, '无法获取硬件资源（测试机）'

        try:
            self.current_hardware_owner = case_hash

            # 检查用例是否正在执行
            with self.lock:
                if case_hash in self.executing_cases:
                    return 'skipped', 0, 'Case is already executing'

                # 标记为执行中
                self.executing_cases.add(case_hash)

                # 更新数据库状态
                test_case.status = 'executing'
                test_case.updated_at = datetime.now()
                db.session.commit()

            start_time = datetime.now()

            try:
                # 根据文件类型选择执行命令
                if test_case.full_path.endswith('.py'):
                    # 执行Python测试用例（直接执行文件）
                    cmd = ['python', test_case.full_path]
                elif test_case.full_path.endswith('.java'):
                    # 执行Java测试用例
                    cmd = ['java', '-jar', 'test-runner.jar', test_case.full_path]
                else:
                    # 其他语言可以根据需要扩展
                    raise NotImplementedError(f"Unsupported file type: {test_case.full_path}")

                # 执行测试
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    cwd=Config.TEST_CASE_ROOT
                )

                # 解析执行结果 - 支持自定义解析器
                if self.result_parser:
                    # 使用自定义结果解析器
                    status, details = self.result_parser(result, test_case)
                else:
                    # 使用默认结果解析器
                    status, details = self._parse_execution_result(result)
                duration = (datetime.now() - start_time).total_seconds()

            except subprocess.TimeoutExpired:
                status = 'failed'
                details = json.dumps({'error': 'Test execution timeout'})
                duration = self.timeout
            except Exception as e:
                status = 'failed'
                details = json.dumps({'error': str(e), 'type': type(e).__name__})
                duration = (datetime.now() - start_time).total_seconds()
            finally:
                # 移除执行中标记
                with self.lock:
                    self.executing_cases.discard(case_hash)
                    self.current_hardware_owner = None

            # 保存执行结果
            self._save_execution_result(test_case, status, duration, details, plan_id)

            return status, duration, details

        finally:
            # 释放硬件资源锁
            self.hardware_lock.release()

    def execute_test_plan(self, plan_id):
        """执行测试计划（串行执行，因为依赖唯一硬件资源）"""
        plan = TestPlan.query.get(plan_id)
        if not plan or plan.status == 'running':
            return {'error': 'Plan not found or already running'}

        # 获取计划配置
        include_paths = plan.include_paths
        exclude_paths = plan.exclude_paths

        # 选择用例
        cases = self.select_cases_for_execution(
            limit=plan.total_cases if plan.total_cases else 1000,
            include_paths=include_paths,
            exclude_paths=exclude_paths
        )

        # 更新计划状态
        plan.status = 'running'
        plan.last_execution_time = datetime.now()
        plan.total_cases = len(cases)
        plan.executed_cases = 0
        plan.passed_cases = 0
        plan.failed_cases = 0
        db.session.commit()

        # 串行执行（因为依赖唯一硬件资源：测试机）
        results = []
        completed_count = 0
        failed_cases = []

        logger.info(f"开始执行测试计划 {plan_id}，共 {len(cases)} 个用例，将串行执行")

        for index, case in enumerate(cases, 1):
            try:
                logger.info(f"正在执行第 {index}/{len(cases)} 个用例: {case.name}")

                # 执行单个用例
                status, duration, details = self.execute_single_case(case, plan.id)

                # 更新计划统计
                completed_count += 1
                if status == 'passed':
                    plan.passed_cases += 1
                    logger.info(f"用例 {case.name} 执行成功")
                elif status == 'failed':
                    plan.failed_cases += 1
                    failed_cases.append(case.name)
                    logger.warning(f"用例 {case.name} 执行失败")
                else:
                    logger.info(f"用例 {case.name} 执行状态: {status}")

                plan.executed_cases = completed_count

                # 每执行完一个用例就提交数据库更新
                db.session.commit()

                results.append({
                    'case_hash': case.case_hash,
                    'name': case.name,
                    'status': status,
                    'duration': duration
                })

            except Exception as e:
                logger.error(f"执行用例 {case.case_hash} 时发生错误: {str(e)}")
                completed_count += 1
                plan.failed_cases += 1
                plan.executed_cases = completed_count
                failed_cases.append(case.name)
                db.session.commit()

                results.append({
                    'case_hash': case.case_hash,
                    'name': case.name,
                    'status': 'failed',
                    'error': str(e)
                })

        # 更新计划状态
        plan.status = 'completed'
        db.session.commit()

        logger.info(f"测试计划 {plan_id} 执行完成！总计: {len(cases)}, 成功: {plan.passed_cases}, 失败: {plan.failed_cases}")
        if failed_cases:
            logger.warning(f"失败的用例: {', '.join(failed_cases)}")

        return {
            'plan_id': plan.id,
            'total_cases': len(cases),
            'executed_cases': completed_count,
            'passed_cases': plan.passed_cases,
            'failed_cases': plan.failed_cases,
            'results': results
        }

    def _parse_execution_result(self, result):
        """解析测试执行结果"""
        if result.returncode == 0:
            status = 'passed'
        else:
            status = 'failed'

        details = {
            'stdout': result.stdout[-5000:],  # 限制输出大小
            'stderr': result.stderr[-5000:],
            'return_code': result.returncode,
            'command': ' '.join(result.args)
        }

        return status, json.dumps(details, ensure_ascii=False)

    def _save_execution_result(self, test_case, status, duration, details, plan_id=None):
        """保存执行结果到数据库"""
        # 更新用例状态
        test_case.status = status
        test_case.last_execution_time = datetime.now()

        # 更新执行时长统计
        test_case.total_executions += 1
        if test_case.avg_duration == 0:
            test_case.avg_duration = duration
        else:
            # 加权平均
            test_case.avg_duration = (test_case.avg_duration * (
                        test_case.total_executions - 1) + duration) / test_case.total_executions

        test_case.execution_duration = duration
        test_case.result_details = details
        test_case.updated_at = datetime.now()

        # 记录执行历史
        execution = TestExecution(
            case_hash=test_case.case_hash,
            status=status,
            duration=duration,
            details=details,
            executed_by='scheduler',
            machine_id=Config.MACHINE_ID,
            plan_id=plan_id
        )

        db.session.add(execution)
        db.session.commit()
