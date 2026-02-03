import json
from datetime import datetime
from flask import Blueprint, request, jsonify
from extra.extensions import db
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


@test_plans_bp.route('/<int:plan_id>/pause', methods=['POST'])
def pause_test_plan(plan_id):
    """暂停测试计划"""
    plan = TestPlan.query.get(plan_id)

    if not plan:
        return jsonify({
            'success': False,
            'message': '测试计划不存在'
        }), 404

    if plan.status != 'running':
        return jsonify({
            'success': False,
            'message': f'无法暂停状态为 {plan.status} 的计划'
        }), 400

    # 更新计划状态为暂停
    plan.status = 'paused'
    db.session.commit()

    return jsonify({
        'success': True,
        'message': '测试计划已暂停'
    })


@test_plans_bp.route('/<int:plan_id>/resume', methods=['POST'])
def resume_test_plan(plan_id):
    """继续执行测试计划"""
    plan = TestPlan.query.get(plan_id)

    if not plan:
        return jsonify({
            'success': False,
            'message': '测试计划不存在'
        }), 404

    if plan.status != 'paused':
        return jsonify({
            'success': False,
            'message': f'无法继续状态为 {plan.status} 的计划'
        }), 400

    # 更新计划状态为运行中
    plan.status = 'running'
    db.session.commit()

    return jsonify({
        'success': True,
        'message': '测试计划已继续执行'
    })


@test_plans_bp.route('/<int:plan_id>', methods=['PUT'])
def update_test_plan(plan_id):
    """更新测试计划"""
    plan = TestPlan.query.get(plan_id)

    if not plan:
        return jsonify({
            'success': False,
            'message': '测试计划不存在'
        }), 404

    data = request.get_json()

    # 允许更新的字段
    if 'name' in data:
        plan.name = data['name']
    if 'description' in data:
        plan.description = data['description']
    if 'case_ids' in data:
        plan.case_ids = json.dumps(data['case_ids'])
        plan.total_cases = len(data['case_ids'])
    if 'priorities' in data:
        plan.priorities = json.dumps(data['priorities'])
    if 'retry_count' in data:
        plan.retry_count = data['retry_count']
    if 'timeout_minutes' in data:
        plan.timeout_minutes = data['timeout_minutes']

    db.session.commit()

    return jsonify({
        'success': True,
        'message': '测试计划更新成功',
        'plan': plan.to_dict()
    })


@test_plans_bp.route('/<int:plan_id>', methods=['DELETE'])
def delete_test_plan(plan_id):
    """删除测试计划"""
    plan = TestPlan.query.get(plan_id)

    if not plan:
        return jsonify({
            'success': False,
            'message': '测试计划不存在'
        }), 404

    # 检查计划是否正在运行
    if plan.status == 'running':
        return jsonify({
            'success': False,
            'message': '无法删除正在运行的计划，请先暂停执行'
        }), 400

    plan_id_val = plan.id
    plan_name = plan.name

    db.session.delete(plan)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'测试计划 "{plan_name}" 已删除',
        'plan_id': plan_id_val
    })


@test_plans_bp.route('/<int:plan_id>/tasks', methods=['GET'])
def get_plan_tasks(plan_id):
    """获取测试计划的执行任务列表"""
    from models import ExecutionTask

    plan = TestPlan.query.get(plan_id)

    if not plan:
        return jsonify({
            'success': False,
            'message': '测试计划不存在'
        }), 404

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    status = request.args.get('status')

    query = ExecutionTask.query.filter_by(plan_id=plan_id)

    if status:
        query = query.filter_by(status=status)

    query = query.order_by(ExecutionTask.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    tasks = []
    for task in pagination.items:
        tasks.append({
            'id': task.id,
            'task_id': task.task_id,
            'case_hash': task.case_hash,
            'status': task.status,
            'machine_id': task.machine_id,
            'created_at': task.created_at.isoformat() if task.created_at else None,
            'started_at': task.started_at.isoformat() if task.started_at else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
            'result': task.result
        })

    return jsonify({
        'success': True,
        'tasks': tasks,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })
