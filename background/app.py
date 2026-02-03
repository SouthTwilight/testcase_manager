import json
from datetime import datetime
from flask import Flask, request, jsonify
from watchdog.observers import Observer

from config import Config
from extra.extensions import cors, db

from models import User
from scanner import TestCaseScanner, FileChangeHandler
from scheduler import TestScheduler

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # 初始化 CORS
    cors.init_app(app,
        supports_credentials=True,
        origins=["http://localhost:8080"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Requested-With"])

    # 初始化数据库
    db.init_app(app)

    # 注册蓝图 - 在初始化之后导入，避免循环导入
    from api.test_cases import test_cases_bp
    from api.test_plans import test_plans_bp
    from api.test_execution import test_execution_bp
    from api.dashboard import dashboard_bp
    from api.system import system_bp

    app.register_blueprint(test_cases_bp)
    app.register_blueprint(test_plans_bp)
    app.register_blueprint(test_execution_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(system_bp)

    # 创建数据库表
    with app.app_context():
        db.create_all()

        # 创建默认用户
        if not User.query.filter_by(username='admin').first():
            from werkzeug.security import generate_password_hash
            admin = User(
                username='admin',
                email='admin@example.com',
                password_hash=generate_password_hash('admin123')
            )
            db.session.add(admin)
            db.session.commit()

    # 初始化调度器
    scheduler = TestScheduler(app)
    scheduler.start()

    # 初始化文件监控
    if app.config.get('WATCHDOG_ENABLED', False):
        scanner = TestCaseScanner()
        event_handler = FileChangeHandler(scanner)
        observer = Observer()
        observer.schedule(event_handler, app.config['TEST_CASE_ROOT'], recursive=True)
        observer.start()

    # 根路由
    @app.route('/')
    def index():
        return jsonify({
            'name': 'Test Management API',
            'version': '1.0.0',
            'status': 'running'
        })

    # 确保app对象能访问scheduler
    app.scheduler = scheduler

    return app, scheduler

