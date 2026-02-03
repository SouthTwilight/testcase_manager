from datetime import datetime, timedelta

from flask import Blueprint, jsonify
from extra.extensions import db
from models import TestCase, TestExecution

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
