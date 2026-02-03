import json
from datetime import datetime
from flask import Blueprint, request, jsonify
import threading
import concurrent.futures

from extra.extensions import db
from models import TestExecution, TestPlan, BatchExecution
from run import app, scheduler

test_execution_bp = Blueprint('test_execution', __name__, url_prefix='/api')


@test_execution_bp.route('/execute-plan', methods=['POST'])
def execute_test_plan_direct():
    """执行测试计划（兼容旧接口）"""
    data = request.get_json()

    # 创建测试计划
    plan_data = {
        'name': data.get('name', f'Manual Plan - {datetime.now()}'),
        'plan_type': data.get('plan_type', 'manual'),
        'distributed': data.get('distributed', False),
        'case_ids': data.get('case_ids', []),
        'priorities': data.get('priorities', []),
        'retry_count': data.get('retry_count', 0),
        'timeout_minutes': data.get('timeout_minutes', 0),
        'include_paths': data.get('include_paths', []),
        'exclude_paths': data.get('exclude_paths', []),
        'created_by': data.get('created_by', 'system')
    }

    # 调用创建接口
    from .test_plans import create_test_plan
    plan_response = create_test_plan()
    if plan_response.status_code != 200:
        return plan_response

    plan_id = plan_response.get_json()['plan_id']

    # 执行测试计划
    from .test_plans import execute_test_plan
    return execute_test_plan(plan_id)


@test_execution_bp.route('/execution-history')
def get_execution_history():
    """获取执行历史"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    case_hash = request.args.get('case_hash')
    plan_id = request.args.get('plan_id')

    query = TestExecution.query

    if case_hash:
        query = query.filter_by(case_hash=case_hash)
    if plan_id:
        query = query.filter_by(plan_id=plan_id)

    query = query.order_by(TestExecution.execution_time.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    history = []
    for execution in pagination.items:
        history.append({
            'id': execution.id,
            'case_hash': execution.case_hash,
            'execution_time': execution.execution_time.isoformat() if execution.execution_time else None,
            'status': execution.status,
            'duration': execution.duration,
            'executed_by': execution.executed_by,
            'machine_id': execution.machine_id,
            'plan_id': execution.plan_id
        })

    return jsonify({
        'success': True,
        'history': history,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })


@test_execution_bp.route('/batch-execute-plans', methods=['POST'])
def batch_execute_plans():
    """批量执行测试计划"""
    data = request.get_json()

    plan_ids = data.get('plan_ids', [])
    execution_config = data.get('execution_config', {})
    description = data.get('description', f'批量执行 {len(plan_ids)} 个计划')

    if not plan_ids:
        return jsonify({
            'success': False,
            'message': '请选择要执行的计划'
        })

    # 获取所有选中的计划
    plans = TestPlan.query.filter(TestPlan.id.in_(plan_ids)).all()

    # 检查计划状态
    running_plans = [p for p in plans if p.status == 'running']
    if running_plans and not execution_config.get('force_execute', False):
        return jsonify({
            'success': False,
            'message': f'有 {len(running_plans)} 个计划正在执行中，请等待完成或选择强制执行'
        })

    # 创建批量执行记录
    batch_execution = BatchExecution(
        name=description,
        plan_ids=','.join(map(str, plan_ids)),
        execution_config=json.dumps(execution_config),
        status='running',
        created_by="admin"
    )
    db.session.add(batch_execution)
    db.session.commit()

    # 异步执行批量任务
    thread = threading.Thread(
        target=execute_batch_plans_async,
        args=(batch_execution.id, plan_ids, execution_config)
    )
    thread.daemon = True
    thread.start()

    return jsonify({
        'success': True,
        'batch_id': batch_execution.id,
        'message': '批量执行已开始'
    })


def execute_batch_plans_async(batch_id, plan_ids, execution_config):
    """异步执行批量计划"""

    with app.app_context():
        from models import BatchExecution, TestPlan

        batch_execution = BatchExecution.query.get(batch_id)
        if not batch_execution:
            return

        try:
            execution_mode = execution_config.get('execution_mode', 'sequential')
            concurrency = execution_config.get('concurrency', 1)
            failure_handling = execution_config.get('failure_handling', 'continue')

            plans = TestPlan.query.filter(TestPlan.id.in_(plan_ids)).all()

            # 根据执行模式执行
            if execution_mode == 'sequential':
                # 顺序执行
                for plan in plans:
                    try:
                        execute_plan_sync(plan.id, execution_config)
                    except Exception as e:
                        if failure_handling == 'stop':
                            break
                        elif failure_handling == 'retry':
                            # 重试逻辑
                            pass
                        continue  # continue模式继续执行下一个

            elif execution_mode == 'parallel':
                # 并行执行
                with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
                    future_to_plan = {
                        executor.submit(execute_plan_sync, plan.id, execution_config): plan
                        for plan in plans
                    }

                    for future in concurrent.futures.as_completed(future_to_plan):
                        plan = future_to_plan[future]
                        try:
                            future.result()
                        except Exception as e:
                            # 错误处理
                            pass

            # 更新批量执行状态
            batch_execution.status = 'completed'
            batch_execution.completed_at = datetime.now()

        except Exception as e:
            batch_execution.status = 'failed'
            batch_execution.error_message = str(e)

        finally:
            db.session.commit()


def execute_plan_sync(plan_id, execution_config):
    """同步执行单个计划"""
    plan = TestPlan.query.get(plan_id)
    if not plan:
        return

    # 更新计划状态
    plan.status = 'running'
    plan.last_execution_time = datetime.now()

    # 执行计划
    scheduler.execute_plan_immediately(plan_id)

    db.session.commit()


@test_execution_bp.route('/batch-executions')
def get_batch_executions():
    """获取批量执行记录"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = BatchExecution.query.order_by(BatchExecution.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    executions = []
    for execution in pagination.items:
        executions.append({
            'id': execution.id,
            'name': execution.name,
            'plan_ids': execution.plan_ids.split(',') if execution.plan_ids else [],
            'status': execution.status,
            'execution_config': json.loads(execution.execution_config) if execution.execution_config else {},
            'created_by': execution.created_by,
            'created_at': execution.created_at.isoformat() if execution.created_at else None,
            'started_at': execution.started_at.isoformat() if execution.started_at else None,
            'completed_at': execution.completed_at.isoformat() if execution.completed_at else None,
            'error_message': execution.error_message
        })

    return jsonify({
        'success': True,
        'executions': executions,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })
