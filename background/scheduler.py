from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, time, timedelta
import atexit
import json
from models import db, TestPlan, DistributedLock
from config import Config
from executor import TestCaseExecutor
from distributed import DistributedManager


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

            # 优雅关闭
            atexit.register(lambda: self.scheduler.shutdown())

    def _run_daily_schedule(self):
        """执行每日定时任务"""
        with self.app.app_context():
            # 使用分布式锁确保只有一个机器执行定时任务
            with self.distributed_manager.distributed_lock('daily_schedule_lock', 600) as acquired:
                if not acquired:
                    print("Another machine is executing daily schedule")
                    return

            # 检查是否有正在执行的计划
            running_plans = TestPlan.query.filter_by(status='running').first()
            if running_plans:
                print("有测试计划正在执行，跳过本次定时任务")
                return

            # 检查是否在允许的时间范围内
            current_time = datetime.now().time()
            schedule_start = Config.SCHEDULE_START_TIME
            schedule_end = Config.SCHEDULE_END_TIME

            # 处理跨天的时间范围
            if schedule_start > schedule_end:
                # 时间范围跨天，如23:00-08:00
                if current_time < schedule_start and current_time > schedule_end:
                    print("当前时间不在允许的执行时间范围内")
                    return
            else:
                # 时间范围不跨天
                if current_time < schedule_start or current_time > schedule_end:
                    print("当前时间不在允许的执行时间范围内")
                    return

            # 创建每日定时计划
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

            # 执行计划
            try:
                self.is_running = True
                result = self.executor.execute_test_plan(daily_plan.id)
                print(f"Daily schedule completed: {result}")
            except Exception as e:
                print(f"Daily schedule failed: {e}")
                daily_plan.status = 'failed'
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
                print(f"Scanned cases: {result}")

    def _check_running_plans(self):
        """检查是否有运行超时的计划"""
        with self.app.app_context():
            running_plans = TestPlan.query.filter_by(status='running').all()
            for plan in running_plans:
                # 如果计划开始执行超过6小时，标记为失败
                if plan.last_execution_time and (datetime.now() - plan.last_execution_time).seconds > 21600:
                    plan.status = 'failed'
                    db.session.commit()
                    print(f"Plan {plan.id} marked as failed due to timeout")

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
            print(f"执行计划失败: {str(e)}")

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
            print("No available machines for distributed execution")
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
        # 这里实现具体的测试用例执行逻辑
        # 包括根据priorities过滤用例、重试机制、超时控制等
        pass
