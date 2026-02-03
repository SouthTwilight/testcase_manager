from datetime import datetime
from flask import Blueprint, request, jsonify
from sqlalchemy import func, case
from extra.extensions import db
from models import TestCase

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
