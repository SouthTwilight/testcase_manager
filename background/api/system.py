from flask import Blueprint, request, jsonify
from watchdog.observers import Observer
from extra.extensions import db
from models import MachineStatus
from scanner import TestCaseScanner, FileChangeHandler
from config import Config
import json

system_bp = Blueprint('system', __name__, url_prefix='/api')


@system_bp.route('/scan-cases')
def scan_test_cases():
    """扫描用例"""
    scanner = TestCaseScanner()
    count = scanner.scan_all_cases(update_status=True)

    return jsonify({
        'success': True,
        'count': count,
        'message': f'Scanned {count} test cases'
    })


@system_bp.route('/machines')
def get_machines():
    """获取机器状态"""
    machines = MachineStatus.query.order_by(MachineStatus.last_heartbeat.desc()).all()

    machine_list = []
    for machine in machines:
        machine_list.append({
            'id': machine.id,
            'machine_id': machine.machine_id,
            'machine_ip': machine.machine_ip,
            'machine_name': machine.machine_name,
            'status': machine.status,
            'last_heartbeat': machine.last_heartbeat.isoformat() if machine.last_heartbeat else None,
            'cpu_usage': machine.cpu_usage,
            'memory_usage': machine.memory_usage,
            'disk_usage': machine.disk_usage,
            'current_tasks': machine.current_tasks,
            'max_tasks': machine.max_tasks
        })

    return jsonify({
        'success': True,
        'machines': machine_list
    })


@system_bp.route('/settings', methods=['GET'])
def get_settings():
    """获取系统配置"""
    settings = {
        # 基本设置
        'system_name': '测试用例管理系统',
        'system_version': '1.0.0',
        'test_case_root': Config.TEST_CASE_ROOT,
        'watchdog_enabled': Config.WATCHDOG_ENABLED,
        'auto_scan_interval': Config.WATCHDOG_INTERVAL,

        # 数据保留设置
        'max_history_days': 90,
        'enable_audit_log': False,

        # 国际化设置
        'default_language': 'zh-CN',
        'timezone': 'Asia/Shanghai',

        # 调度器设置
        'scheduler_enabled': True,
        'schedule_time': '23:00',
        'schedule_days': ['1', '2', '3', '4', '5'],
        'max_parallel_plans': 3,
        'auto_retry_failed': True,
        'retry_count': 3,
        'timeout_hours': 8,
        'notify_on_complete': True,

        # 执行器设置
        'executor_type': 'local',
        'max_workers': Config.MAX_CONCURRENT_TESTS,
        'task_timeout': Config.TEST_TIMEOUT,
        'enable_cache': True,
        'cache_ttl': 3600,
        'log_level': 'INFO',

        # 优先级设置
        'priorities': {
            'new_cases': True,
            'failed_cases': True,
            'long_not_executed': True,
            'priority_paths': True
        },
        'priority_paths': Config.HIGH_PRIORITY_DIRS
    }

    return jsonify({
        'success': True,
        'settings': settings
    })


@system_bp.route('/settings', methods=['PUT'])
def update_settings():
    """更新系统配置"""
    data = request.get_json()

    # 这里可以更新配置文件或数据库
    # 简化处理：返回成功，实际应用中需要持久化配置

    return jsonify({
        'success': True,
        'message': '配置更新成功'
    })


@system_bp.route('/settings/reset', methods=['POST'])
def reset_settings():
    """重置配置为默认值"""
    # 重置为默认配置
    return jsonify({
        'success': True,
        'message': '配置已重置为默认值',
        'settings': get_settings().get_json()['settings']
    })


@system_bp.route('/scheduler/status', methods=['GET'])
def get_scheduler_status():
    """获取调度器状态"""
    from run import app
    with app.app_context():
        scheduler = app.scheduler if hasattr(app, 'scheduler') else None

        if not scheduler:
            return jsonify({
                'success': True,
                'running': False,
                'jobs': []
            })

        jobs = []
        if hasattr(scheduler, 'scheduler') and scheduler.scheduler:
            for job in scheduler.scheduler.get_jobs():
                jobs.append({
                    'id': job.id,
                    'name': job.name,
                    'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None
                })

        return jsonify({
            'success': True,
            'running': scheduler.scheduler.running if scheduler.scheduler else False,
            'jobs': jobs
        })


@system_bp.route('/system/info', methods=['GET'])
def get_system_info():
    """获取系统信息"""
    from models import TestCase, TestExecution, TestPlan
    import platform
    import psutil

    # 获取系统资源使用情况
    cpu_usage = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    # 获取数据库统计
    total_cases = TestCase.query.filter_by(is_active=True).count()
    total_plans = TestPlan.query.count()
    total_executions = TestExecution.query.count()

    return jsonify({
        'success': True,
        'system': {
            'hostname': platform.node(),
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'cpu_usage': cpu_usage,
            'memory_usage': memory.percent,
            'memory_total': memory.total,
            'memory_available': memory.available,
            'disk_usage': disk.percent,
            'disk_total': disk.total,
            'disk_free': disk.free
        },
        'database': {
            'total_cases': total_cases,
            'total_plans': total_plans,
            'total_executions': total_executions
        }
    })
