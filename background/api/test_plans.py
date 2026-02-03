import json
from datetime import datetime
from flask import Blueprint, request, jsonify
from app import db
from models import TestPlan

test_plans_bp = Blueprint('test_plans', __name__, url_prefix='/api/test-plans')


@test_plans_bp.route('', methods=['POST'])
def create_test_plan():
    """创建测试计划"""
    data = request.get_json()

    # 验证必填字段
    if not data.get('name'):
        return jsonify({
            'success': False,
            'message': '计划名称不能为空'
        }), 400

    try:
        # 创建测试计划
        plan = TestPlan(
            name=data.get('name'),
            description=data.get('description', ''),
            plan_type=data.get('plan_type', 'manual'),
            distributed=data.get('distributed', False),
            case_ids=json.dumps(data.get('case_ids', [])),
            priorities=json.dumps(data.get('priorities', [])),
            retry_count=data.get('retry_count', 0),
            timeout_minutes=data.get('timeout_minutes', 0),
            include_paths=json.dumps(data.get('include_paths', [])),
            exclude_paths=json.dumps(data.get('exclude_paths', [])),
            assigned_machines=json.dumps(data.get('assigned_machines', [])),
            total_cases=len(data.get('case_ids', [])),
            created_by=data.get('created_by', 'system')
        )

        db.session.add(plan)
        db.session.commit()

        return jsonify({
            'success': True,
            'plan_id': plan.id,
            'message': '测试计划创建成功'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'创建测试计划失败: {str(e)}'
        }), 500


@test_plans_bp.route('', methods=['GET'])
def get_test_plans():
    """获取测试计划列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    plan_type = request.args.get('plan_type')
    status = request.args.get('status')

    query = TestPlan.query

    if plan_type:
        query = query.filter(TestPlan.plan_type == plan_type)
    if status:
        query = query.filter(TestPlan.status == status)

    plans = query.order_by(TestPlan.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'success': True,
        'plans': [plan.to_dict() for plan in plans.items],
        'total': plans.total,
        'page': plans.page,
        'pages': plans.pages,
        'per_page': plans.per_page
    })


@test_plans_bp.route('/<int:plan_id>', methods=['GET'])
def get_test_plan(plan_id):
    """获取单个测试计划详情"""
    plan = TestPlan.query.get(plan_id)

    if not plan:
        return jsonify({
            'success': False,
            'message': '测试计划不存在'
        }), 404

    return jsonify({
        'success': True,
        'data': plan.to_dict()
    })


@test_plans_bp.route('/<int:plan_id>/execute', methods=['POST'])
def execute_test_plan(plan_id):
    """执行指定的测试计划"""
    plan = TestPlan.query.get(plan_id)

    if not plan:
        return jsonify({
            'success': False,
            'message': '测试计划不存在'
        }), 404

    # 更新计划状态为运行中
    plan.status = 'running'
    plan.last_execution_time = datetime.now()
    db.session.commit()

    # 异步执行测试计划
    from app import scheduler
    import threading

    thread = threading.Thread(
        target=execute_plan_async,
        args=(plan.id,)
    )
    thread.daemon = True
    thread.start()

    return jsonify({
        'success': True,
        'message': '测试计划开始执行',
        'plan_id': plan.id
    })


def execute_plan_async(plan_id):
    """异步执行测试计划"""
    from app import app, scheduler
    with app.app_context():
        try:
            plan = TestPlan.query.get(plan_id)
            if not plan:
                return

            # 获取计划配置
            case_ids = json.loads(plan.case_ids) if plan.case_ids else []
            priorities = json.loads(plan.priorities) if plan.priorities else []

            # 调用scheduler执行计划
            scheduler.execute_test_cases(
                plan_id=plan.id,
                case_ids=case_ids,
                priorities=priorities,
                retry_count=plan.retry_count,
                timeout_minutes=plan.timeout_minutes,
                distributed=plan.distributed
            )

        except Exception as e:
            plan = TestPlan.query.get(plan_id)
            if plan:
                plan.status = 'failed'
                db.session.commit()
            print(f"执行计划失败: {str(e)}")
