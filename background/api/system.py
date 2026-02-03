from flask import Blueprint, jsonify
from watchdog.observers import Observer
from extra.extensions import db
from models import MachineStatus
from scanner import TestCaseScanner, FileChangeHandler

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
