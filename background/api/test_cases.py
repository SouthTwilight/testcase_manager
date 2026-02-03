from datetime import datetime
from flask import Blueprint, request, jsonify
from sqlalchemy import func, case
from extra.extensions import db
from models import TestCase
import threading

test_cases_bp = Blueprint('test_cases', __name__, url_prefix='/api/test-cases')


@test_cases_bp.route('')
def get_test_cases():
    """获取测试用例列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    path = request.args.get('path')
    search = request.args.get('search')

    query = TestCase.query.filter_by(is_active=True)

    if status:
        query = query.filter_by(status=status)
    if path:
        query = query.filter(TestCase.relative_path.like(f'{path}%'))
    if search:
        query = query.filter(
            db.or_(
                TestCase.name.like(f'%{search}%'),
                TestCase.relative_path.like(f'%{search}%')
            )
        )

    # 排序：优先显示未执行和失败的用例
    from sqlalchemy import case
    status_order = case(
        (TestCase.status == 'not_executed', 1),
        (TestCase.status == 'failed', 2),
        (TestCase.status == 'executing', 3),
        (TestCase.status == 'passed', 4),
        else_=5
    )

    query = query.order_by(status_order, TestCase.last_execution_time.desc())
    not_executed = query.filter(TestCase.status == 'not_executed').count()
    failed = query.filter(TestCase.status == 'failed').count()
    passed = query.filter(TestCase.status == 'passed').count()
    executing = query.filter(TestCase.status == 'executing').count()
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    cases = []
    for case in pagination.items:
        cases.append({
            'id': case.id,
            'case_hash': case.case_hash,
            'name': case.name,
            'relative_path': case.relative_path,
            'status': case.status,
            'last_execution_time': case.last_execution_time.isoformat() if case.last_execution_time else None,
            'last_modify_time': case.verified_at.isoformat() if case.verified_at else None,
            'execution_duration': case.execution_duration,
            'avg_duration': case.avg_duration,
            'total_executions': case.total_executions,
            'file_mtime': case.file_mtime.isoformat() if case.file_mtime else None,
            'verified_by': case.verified_by,
            'is_manually_modified': case.is_manually_modified
        })

    return jsonify({
        'success': True,
        'cases': cases,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'not_executed': not_executed,
        'passed': passed,
        'failed': failed,
        'executing': executing
    })


@test_cases_bp.route('/stats')
def get_test_cases_stats():
    """获取测试用例统计信息（按路径分类）"""
    # 按一级目录统计
    stats = db.session.query(
        func.substring_index(TestCase.relative_path, '/', 1).label('category'),
        func.count('*').label('total'),
        func.sum(func.if_(TestCase.status == 'passed', 1, 0)).label('passed'),
        func.sum(func.if_(TestCase.status == 'failed', 1, 0)).label('failed'),
        func.sum(func.if_(TestCase.status == 'not_executed', 1, 0)).label('not_executed'),
        func.sum(func.if_(TestCase.status == 'executing', 1, 0)).label('executing')
    ).filter_by(is_active=True).group_by('category').all()

    return jsonify({
        'success': True,
        'stats': [{
            'category': stat.category,
            'total': stat.total,
            'passed': stat.passed,
            'failed': stat.failed,
            'not_executed': stat.not_executed,
            'executing': stat.executing,
            'pass_rate': round((stat.passed / stat.total * 100), 2) if stat.total > 0 else 0
        } for stat in stats]
    })


@test_cases_bp.route('/<string:case_hash>', methods=['PUT'])
def update_test_case(case_hash):
    """更新测试用例（人工校验）"""
    case = TestCase.query.filter_by(case_hash=case_hash).first_or_404()

    data = request.get_json()

    # 允许人工修改的字段
    if 'status' in data:
        case.status = data['status']
        case.is_manually_modified = True

    if 'verification_notes' in data:
        case.verification_notes = data['verification_notes']
        case.verified_by = data.get("user", "unknown")
        case.verified_at = datetime.now()

    if 'result_details' in data:
        case.result_details = data['result_details']

    db.session.commit()

    return jsonify({'success': True})


@test_cases_bp.route('/<string:case_hash>', methods=['GET'])
def get_test_case(case_hash):
    """获取单个测试用例详情"""
    case = TestCase.query.filter_by(case_hash=case_hash).first()

    if not case:
        return jsonify({
            'success': False,
            'message': '测试用例不存在'
        }), 404

    return jsonify({
        'success': True,
        'case': {
            'id': case.id,
            'case_hash': case.case_hash,
            'name': case.name,
            'full_path': case.full_path,
            'relative_path': case.relative_path,
            'status': case.status,
            'last_execution_time': case.last_execution_time.isoformat() if case.last_execution_time else None,
            'execution_duration': case.execution_duration,
            'avg_duration': case.avg_duration,
            'total_executions': case.total_executions,
            'result_details': case.result_details,
            'error_message': case.error_message,
            'stack_trace': case.stack_trace,
            'file_size': case.file_size,
            'file_mtime': case.file_mtime.isoformat() if case.file_mtime else None,
            'content_hash': case.content_hash,
            'verified_by': case.verified_by,
            'verified_at': case.verified_at.isoformat() if case.verified_at else None,
            'verification_notes': case.verification_notes,
            'is_manually_modified': case.is_manually_modified,
            'created_at': case.created_at.isoformat() if case.created_at else None,
            'updated_at': case.updated_at.isoformat() if case.updated_at else None,
            'is_active': case.is_active
        }
    })


@test_cases_bp.route('/<string:case_hash>', methods=['DELETE'])
def delete_test_case(case_hash):
    """删除测试用例（软删除）"""
    case = TestCase.query.filter_by(case_hash=case_hash).first()

    if not case:
        return jsonify({
            'success': False,
            'message': '测试用例不存在'
        }), 404

    # 软删除：只标记为不活跃
    case.is_active = False
    case.updated_at = datetime.now()
    db.session.commit()

    return jsonify({
        'success': True,
        'message': '测试用例已删除'
    })


@test_cases_bp.route('/scan', methods=['POST'])
def scan_cases():
    """手动触发用例扫描"""
    from scanner import TestCaseScanner

    data = request.get_json()
    scan_type = data.get('scan_type', 'incremental')  # 'full' or 'incremental'

    def scan_async():
        from app import app
        with app.app_context():
            scanner = TestCaseScanner()
            if scan_type == 'full':
                scanner.scan_all_cases(update_status=True)
            else:
                scanner.scan_new_and_changed_cases()

    # 异步执行扫描
    thread = threading.Thread(target=scan_async)
    thread.daemon = True
    thread.start()

    return jsonify({
        'success': True,
        'message': f'{"全量" if scan_type == "full" else "增量"}扫描已开始',
        'scan_type': scan_type
    })


@test_cases_bp.route('/batch', methods=['PUT'])
def batch_update_cases():
    """批量更新测试用例状态"""
    data = request.get_json()

    case_hashes = data.get('case_hashes', [])
    if not case_hashes:
        return jsonify({
            'success': False,
            'message': '请选择要更新的用例'
        }), 400

    updates = data.get('updates', {})

    # 查询要更新的用例
    cases = TestCase.query.filter(
        TestCase.case_hash.in_(case_hashes),
        TestCase.is_active == True
    ).all()

    if not cases:
        return jsonify({
            'success': False,
            'message': '未找到可更新的用例'
        }), 404

    updated_count = 0
    for case in cases:
        if 'status' in updates:
            case.status = updates['status']
            case.is_manually_modified = True

        if 'verification_notes' in updates:
            case.verification_notes = updates['verification_notes']
            case.verified_by = updates.get('user', 'batch_user')
            case.verified_at = datetime.now()

        updated_count += 1

    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'已更新 {updated_count} 个用例',
        'updated_count': updated_count
    })


@test_cases_bp.route('/batch', methods=['DELETE'])
def batch_delete_cases():
    """批量删除测试用例（软删除）"""
    data = request.get_json()

    case_hashes = data.get('case_hashes', [])
    if not case_hashes:
        return jsonify({
            'success': False,
            'message': '请选择要删除的用例'
        }), 400

    # 查询要删除的用例
    cases = TestCase.query.filter(
        TestCase.case_hash.in_(case_hashes),
        TestCase.is_active == True
    ).all()

    if not cases:
        return jsonify({
            'success': False,
            'message': '未找到可删除的用例'
        }), 404

    deleted_count = 0
    for case in cases:
        case.is_active = False
        case.updated_at = datetime.now()
        deleted_count += 1

    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'已删除 {deleted_count} 个用例',
        'deleted_count': deleted_count
    })


@test_cases_bp.route('/paths', methods=['GET'])
def get_case_paths():
    """获取用例路径列表（用于筛选器）"""
    query = TestCase.query.filter_by(is_active=True)

    # 获取一级目录
    paths = db.session.query(
        func.substring_index(TestCase.relative_path, '/', 1).label('path')
    ).filter_by(is_active=True).distinct().all()

    path_list = [p[0] for p in paths if p[0]]
    path_list.sort()

    return jsonify({
        'success': True,
        'paths': path_list
    })
