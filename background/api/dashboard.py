from datetime import datetime, timedelta
from sqlalchemy import func

from flask import Blueprint, jsonify
from extra.extensions import db
from models import TestCase, TestExecution, TestPlan

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api')


@dashboard_bp.route('/dashboard-stats')
def dashboard_stats():
    """获取仪表板统计数据"""
    total_cases = TestCase.query.filter_by(is_active=True).count()
    passed_cases = TestCase.query.filter_by(status='passed').count()
    failed_cases = TestCase.query.filter_by(status='failed').count()
    not_executed_cases = TestCase.query.filter_by(status='not_executed').count()
    executing_cases = TestCase.query.filter_by(status='executing').count()

    # 最近24小时执行统计
    since_time = datetime.now() - timedelta(days=1)
    recent_executions = TestExecution.query.filter(
        TestExecution.execution_time >= since_time
    ).count()

    # 成功率
    executed_cases = total_cases - not_executed_cases
    success_rate = (passed_cases / executed_cases * 100) if executed_cases > 0 else 0

    # 今日新增用例
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_cases = TestCase.query.filter(
        TestCase.created_at >= today_start
    ).count()

    return jsonify({
        'success': True,
        'total_cases': total_cases,
        'passed_cases': passed_cases,
        'failed_cases': failed_cases,
        'not_executed_cases': not_executed_cases,
        'executing_cases': executing_cases,
        'today_cases': today_cases,
        'recent_executions': recent_executions,
        'success_rate': round(success_rate, 2)
    })


@dashboard_bp.route('/test-plan-stats')
def test_plan_stats():
    """获取测试计划统计"""
    total_plans = TestPlan.query.count()

    # 按状态统计
    plan_stats = db.session.query(
        TestPlan.status,
        func.count('*').label('count')
    ).group_by(TestPlan.status).all()

    status_breakdown = {stat[0]: stat[1] for stat in plan_stats}

    # 最近7天创建的计划数
    week_ago = datetime.now() - timedelta(days=7)
    recent_plans = TestPlan.query.filter(
        TestPlan.created_at >= week_ago
    ).count()

    # 正在运行的计划
    running_plans = TestPlan.query.filter_by(status='running').count()

    return jsonify({
        'success': True,
        'total_plans': total_plans,
        'status_breakdown': status_breakdown,
        'recent_plans': recent_plans,
        'running_plans': running_plans
    })


@dashboard_bp.route('/execution-trend')
def execution_trend():
    """获取执行趋势数据（最近7天）"""
    week_ago = datetime.now() - timedelta(days=7)

    # 按日期和状态统计
    trend = db.session.query(
        func.date(TestExecution.execution_time).label('date'),
        TestExecution.status,
        func.count('*').label('count')
    ).filter(
        TestExecution.execution_time >= week_ago
    ).group_by(
        func.date(TestExecution.execution_time),
        TestExecution.status
    ).order_by('date').all()

    # 整理数据
    dates = set()
    status_data = {}

    for date, status, count in trend:
        date_str = date.isoformat() if hasattr(date, 'isoformat') else str(date)
        dates.add(date_str)

        if status not in status_data:
            status_data[status] = {}

        status_data[status][date_str] = count

    # 补全缺失的日期
    trend_data = []
    for date in sorted(dates):
        day_data = {'date': date}
        for status in ['passed', 'failed', 'skipped', 'blocked']:
            day_data[status] = status_data.get(status, {}).get(date, 0)
        trend_data.append(day_data)

    return jsonify({
        'success': True,
        'trend': trend_data
    })


@dashboard_bp.route('/system-health')
def system_health():
    """获取系统健康状态"""
    # 用例执行状态
    executing_count = TestCase.query.filter_by(status='executing').count()

    # 长时间未执行的用例（超过7天）
    week_ago = datetime.now() - timedelta(days=7)
    long_no_exec = TestCase.query.filter(
        TestCase.last_execution_time < week_ago,
        TestCase.status != 'not_executed'
    ).count()

    # 计划状态
    running_plans = TestPlan.query.filter_by(status='running').all()
    failed_plans = TestPlan.query.filter_by(status='failed').count()

    # 最近执行失败率（最近100次执行）
    recent_executions = TestExecution.query.order_by(
        TestExecution.execution_time.desc()
    ).limit(100).all()

    if recent_executions:
        failed_rate = sum(1 for e in recent_executions if e.status == 'failed') / len(recent_executions) * 100
    else:
        failed_rate = 0

    return jsonify({
        'success': True,
        'health': {
            'executing_cases': executing_count,
            'long_no_exec_cases': long_no_exec,
            'running_plans': len(running_plans),
            'failed_plans': failed_plans,
            'recent_failure_rate': round(failed_rate, 2)
        },
        'status': 'healthy' if failed_rate < 10 and executing_count < 50 else 'warning'
    })


@dashboard_bp.route('/recent-activities')
def recent_activities():
    """获取最近活动记录"""
    # 最近的执行记录
    recent_executions = db.session.query(
        TestExecution,
        TestCase
    ).join(
        TestCase, TestCase.case_hash == TestExecution.case_hash
    ).order_by(
        TestExecution.execution_time.desc()
    ).limit(10).all()

    activities = []
    for execution, test_case in recent_executions:
        activities.append({
            'type': 'execution',
            'status': execution.status,
            'case_name': test_case.name if test_case else 'Unknown',
            'case_path': test_case.relative_path if test_case else None,
            'execution_time': execution.execution_time.isoformat() if execution.execution_time else None,
            'duration': execution.duration,
            'executed_by': execution.executed_by
        })

    return jsonify({
        'success': True,
        'activities': activities
    })
