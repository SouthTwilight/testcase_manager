# database/init_db.py
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

# 创建应用实例
app, _ = create_app()

with app.app_context():
    from extra.extensions import db  # 在应用上下文中导入
    from models import User
    from werkzeug.security import generate_password_hash
    from scanner import TestCaseScanner

    # 创建所有表
    db.create_all()

    print("数据库初始化完成！")
    print(f"数据库URL: {app.config['SQLALCHEMY_DATABASE_URI']}")

    # 创建默认用户（如果不存在）
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            email='admin@example.com',
            password_hash=generate_password_hash('admin123')
        )
        db.session.add(admin)
        db.session.commit()
        print("创建默认用户: admin / admin123")

    # 初始化扫描测试用例
    scanner = TestCaseScanner()
    count = scanner.scan_all_cases(update_status=True)
    print(f"扫描到 {count} 个测试用例")
