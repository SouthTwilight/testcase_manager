from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, time, timedelta
import atexit
import json
from models import db, TestPlan, DistributedLock
from config import Config
from executor import TestCaseExecutor
from distributed import DistributedManager
from utils.logger import logger


class TestScheduler:
    def __init__(self, app):
        self.app = app
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        self.executor = TestCaseExecutor()
        self.distributed_manager = DistributedManager(app)
        self.is_running = False

    def start(self):
        """启动调度器"""
        if not self.scheduler.running:
            self.scheduler.start()

            # 添加每日定时任务
            self.scheduler.add_job(
                func=self._run_daily_schedule,
                trigger=CronTrigger(hour=23, minute=0),  # 每天23:00执行
                id='daily_test_schedule'
            )

            # 每5分钟检查一次用例变更
            self.scheduler.add_job(
                func=self._scan_changed_cases,
                trigger='interval',
                minutes=5,
                id='scan_cases_job'
            )

            # 每10分钟检查一次运行中的计划
            self.scheduler.add_job(
                func=self._check_running_plans,
                trigger='interval',
                minutes=10,
                id='check_plans_job'
            )

            print("Test scheduler started")
            logger.info("Test scheduler started")

            # 优雅关闭
            atexit.register(lambda: self.scheduler.shutdown())

    def _run_daily_schedule(self):
        """执行每日定时任务"""
        with self.app.app_context():
            # 使用分布式锁确保只有一个机器执行定时任务
            with self.distributed_manager.distributed_lock('daily_schedule_lock', 600) as acquired:
                if not acquired:
                    logger.warning("Another machine is executing daily schedule")
                    return

            # 检查是否有正在执行的计划
            running_plans = TestPlan.query.filter_by(status='running').first()
            if running_plans:
                logger.info(f"有测试计划正在执行（ID: {running_plans.id}），跳过本次定时任务")
                return

            # 检查是否在允许的时间范围内
            current_time = datetime.now().time()
            schedule_start = Config.SCHEDULE_START_TIME
            schedule_end = Config.SCHEDULE_END_TIME

            # 处理跨天的时间范围
            if schedule_start > schedule_end:
                # 时间范围跨天，如23:00-08:00
                if current_time < schedule_start and current_time > schedule_end:
                    logger.info("当前时间不在允许的执行时间范围内")
                    return
            else:
                # 时间范围不跨天
                if current_time < schedule_start or current_time > schedule_end:
                    logger.info("当前时间不在允许的执行时间范围内")
                    return

            # 查询所有待执行的定时计划
            pending_scheduled_plans = TestPlan.query.filter_by(
                plan_type='scheduled',
                status='pending'
            ).all()

            # 如果有待执行的定时计划，选择最优先的一个执行
            if pending_scheduled_plans:
                selected_plan = self._select_plan_to_execute(pending_scheduled_plans)
                logger.info(f"从 {len(pending_scheduled_plans)} 个待执行计划中选择执行计划: {selected_plan.name} (ID: {selected_plan.id})")

                # 执行选中的计划
                self._execute_plan_and_handle_result(selected_plan)
            else:
                # 没有待执行的定时计划，创建默认的每日定时计划
                logger.info("没有待执行的定时计划，创建默认每日计划")
                daily_plan = TestPlan(
                    name=f"Daily Schedule - {datetime.now().strftime('%Y-%m-%d')}",
                    description="Automated daily test execution",
                    plan_type='scheduled',
                    status='pending',
                    created_by='system',
                    created_at=datetime.now()
                )

                db.session.add(daily_plan)
                db.session.commit()

                # 执行默认计划
                self._execute_plan_and_handle_result(daily_plan)

    def _select_plan_to_execute(self, plans):
        """从多个计划中选择一个执行

        规则：
        1. 计划时长更短的优先
        2. 如果时长相同，最新创建的优先

        Args:
            plans: 待执行的测试计划列表

        Returns:
            选中的测试计划
        """
        if len(plans) == 1:
            return plans[0]

        # 计算每个计划的优先级分数
        # 规则：计划时长越短分数越高，创建时间越新分数越高
        scored_plans = []
        current_time = datetime.now()

        for plan in plans:
            # 估算计划时长（timeout_minutes，默认为60分钟）
            estimated_duration = plan.timeout_minutes if plan.timeout_minutes and plan.timeout_minutes > 0 else 60

            # 计算创建时间差（秒数）
            created_age = (current_time - plan.created_at).total_seconds() if plan.created_at else 0

            # 计算分数：时长越短分数越高，创建时间越新分数越高
            # 使用负数是因为我们要排序，分数越高越优先
            score = (
                -estimated_duration * 1000  # 时长权重（主要）
                -created_age * 0.001  # 创建时间权重（次要）
            )

            scored_plans.append((score, plan))

        # 按分数排序，选择最高分的计划
        scored_plans.sort(key=lambda x: x[0])
        selected_score, selected_plan = scored_plans[0]

        logger.info(f"计划选择详情 - 选中的计划: {selected_plan.name}, "
                   f"时长: {selected_plan.timeout_minutes or 60}分钟, "
                   f"创建时间: {selected_plan.created_at}")

        # 记录被跳过的计划
        for score, plan in scored_plans[1:]:
            logger.info(f"跳过计划: {plan.name}, "
                       f"时长: {plan.timeout_minutes or 60}分钟, "
                       f"创建时间: {plan.created_at}")

        return selected_plan

    def _execute_plan_and_handle_result(self, plan):
        """执行计划并处理结果

        Args:
            plan: 要执行的测试计划
        """
        # 执行计划
        try:
            self.is_running = True
            result = self.executor.execute_test_plan(plan.id)
            logger.info(f"计划执行完成: {result}")
        except Exception as e:
            logger.error(f"计划执行失败: {str(e)}")
            plan.status = 'failed'
            db.session.commit()
        finally:
            self.is_running = False

    def _scan_changed_cases(self):
        """扫描变更的用例"""
        with self.app.app_context():
            from scanner import TestCaseScanner
            scanner = TestCaseScanner()
            result = scanner.scan_new_and_changed_cases()

            if result['new_count'] > 0 or result['changed_count'] > 0:
                logger.info(f"Scanned cases: {result}")

    def _check_running_plans(self):
        """检查是否有运行超时的计划"""
        with self.app.app_context():
            running_plans = TestPlan.query.filter_by(status='running').all()
            for plan in running_plans:
                # 如果计划开始执行超过6小时，标记为失败
                if plan.last_execution_time and (datetime.now() - plan.last_execution_time).seconds > 21600:
                    plan.status = 'failed'
                    db.session.commit()
                    logger.warning(f"Plan {plan.id} marked as failed due to timeout")

    def create_custom_plan(self, plan_name, include_paths=None, exclude_paths=None,
                           distributed=False, case_ids=None, priorities=None,
                           retry_count=0, timeout_minutes=0):
        """创建自定义计划"""
        from app import db
        from models import TestPlan

        plan = TestPlan(
            name=plan_name,
            plan_type='custom',
            distributed=distributed,
            include_paths=json.dumps(include_paths or []),
            exclude_paths=json.dumps(exclude_paths or []),
            case_ids=json.dumps(case_ids or []),
            priorities=json.dumps(priorities or []),
            retry_count=retry_count,
            timeout_minutes=timeout_minutes,
            total_cases=len(case_ids or []),
            created_by='scheduler'
        )

        db.session.add(plan)
        db.session.commit()

        return plan.id

    def create_scheduled_plan(self, plan_name, cron_expression, **kwargs):
        """创建定时计划"""
        from app import db
        from models import TestPlan

        plan = TestPlan(
            name=plan_name,
            plan_type='scheduled',
            schedule_cron=cron_expression,
            distributed=kwargs.get('distributed', False),
            include_paths=json.dumps(kwargs.get('include_paths', [])),
            exclude_paths=json.dumps(kwargs.get('exclude_paths', [])),
            case_ids=json.dumps(kwargs.get('case_ids', [])),
            priorities=json.dumps(kwargs.get('priorities', [])),
            retry_count=kwargs.get('retry_count', 0),
            timeout_minutes=kwargs.get('timeout_minutes', 0),
            total_cases=len(kwargs.get('case_ids', [])),
            created_by='scheduler'
        )

        db.session.add(plan)
        db.session.commit()

        # 添加定时任务
        self.scheduler.add_job(
            func=self.execute_plan_immediately,
            trigger=CronTrigger.from_crontab(cron_expression),
            args=(plan.id,),
            id=f'test_plan_{plan.id}',
            name=plan_name
        )

        return plan.id

    def execute_plan_immediately(self, plan_id):
        """立即执行计划"""
        from app import db
        from models import TestPlan

        plan = TestPlan.query.get(plan_id)
        if not plan:
            return

        # 更新状态
        plan.status = 'running'
        plan.last_execution_time = datetime.now()
        db.session.commit()

        try:
            # 执行测试用例
            case_ids = json.loads(plan.case_ids) if plan.case_ids else []
            priorities = json.loads(plan.priorities) if plan.priorities else []

            # 这里实现具体的测试用例执行逻辑
            self.execute_test_cases(
                plan_id=plan.id,
                case_ids=case_ids,
                priorities=priorities,
                retry_count=plan.retry_count,
                timeout_minutes=plan.timeout_minutes,
                distributed=plan.distributed
            )

        except Exception as e:
            plan.status = 'failed'
            db.session.commit()
            logger.error(f"执行计划失败: {str(e)}")

    def _execute_plan_thread(self, plan_id):
        """执行计划的线程函数"""
        with self.app.app_context():
            plan = TestPlan.query.get(plan_id)
            if plan:
                if plan.distributed:
                    self._execute_distributed_plan(plan)
                else:
                    self.executor.execute_test_plan(plan_id)

    def _execute_distributed_plan(self, plan):
        """分布式执行测试计划"""
        # 获取可用机器
        machines = self.distributed_manager.get_available_machines()

        if not machines:
            logger.warning("No available machines for distributed execution")
            plan.status = 'failed'
            db.session.commit()
            return

        # 选择用例并分配给各机器
        include_paths = json.loads(plan.include_paths) if plan.include_paths else None
        exclude_paths = json.loads(plan.exclude_paths) if plan.exclude_paths else None

        from .executor import TestCaseExecutor
        executor = TestCaseExecutor()
        cases = executor.select_cases_for_execution(
            limit=1000,
            include_paths=include_paths,
            exclude_paths=exclude_paths
        )

        # 分配用例给各机器
        cases_per_machine = len(cases) // len(machines) + 1

        for i, machine in enumerate(machines):
            start_idx = i * cases_per_machine
            end_idx = min((i + 1) * cases_per_machine, len(cases))
            machine_cases = cases[start_idx:end_idx]

            # 准备任务数据
            task_data = {
                'plan_id': plan.id,
                'case_hashes': [case.case_hash for case in machine_cases],
                'machine_id': machine.machine_id
            }

            # 分配任务
            self.distributed_manager.assign_task_to_machine(task_data)

    ''' 测试任务执行器 '''
    def execute_test_cases(self, plan_id, case_ids, priorities, retry_count, timeout_minutes, distributed):
        """执行测试用例的具体实现"""
        from models import TestPlan, TestCase

        plan = TestPlan.query.get(plan_id)
        if not plan:
            logger.warning(f"Plan {plan_id} not found")
            return

        try:
            # 获取要执行的用例
            cases_to_execute = []

            if case_ids:
                # 如果指定了case_ids，直接使用
                cases = TestCase.query.filter(
                    TestCase.case_hash.in_(case_ids),
                    TestCase.is_active == True
                ).all()
                cases_to_execute = cases
            else:
                # 否则根据路径选择用例
                include_paths = json.loads(plan.include_paths) if plan.include_paths else None
                exclude_paths = json.loads(plan.exclude_paths) if plan.exclude_paths else None
                cases_to_execute = self.executor.select_cases_for_execution(
                    limit=1000,
                    include_paths=include_paths,
                    exclude_paths=exclude_paths
                )

            if not cases_to_execute:
                logger.warning("No cases to execute")
                plan.status = 'completed'
                db.session.commit()
                return

            # 更新计划统计
            plan.total_cases = len(cases_to_execute)
            plan.executed_cases = 0
            plan.passed_cases = 0
            plan.failed_cases = 0

            # 执行用例
            results = []
            completed_count = 0

            for case in cases_to_execute:
                for attempt in range(retry_count + 1):
                    try:
                        status, duration, details = self.executor.execute_single_case(case, plan_id)

                        # 更新统计
                        completed_count += 1
                        if status == 'passed':
                            plan.passed_cases += 1
                        elif status == 'failed':
                            plan.failed_cases += 1

                        plan.executed_cases = completed_count

                        # 如果成功或已到最大重试次数，跳出重试循环
                        if status == 'passed' or attempt == retry_count:
                            results.append({
                                'case_hash': case.case_hash,
                                'name': case.name,
                                'status': status,
                                'duration': duration
                            })
                            break

                    except Exception as e:
                        logger.error(f"Error executing case {case.case_hash}: {str(e)}")
                        if attempt == retry_count:
                            # 最后一次重试也失败
                            plan.failed_cases += 1
                            plan.executed_cases += 1
                            results.append({
                                'case_hash': case.case_hash,
                                'name': case.name,
                                'status': 'failed',
                                'error': str(e)
                            })

            # 更新计划状态
            plan.status = 'completed'
            db.session.commit()

            logger.info(f"Plan {plan_id} execution completed: {completed_count} cases executed")

        except Exception as e:
            plan.status = 'failed'
            db.session.commit()
            logger.error(f"Plan {plan_id} execution failed: {str(e)}")
