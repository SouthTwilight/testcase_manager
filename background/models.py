import json
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import hashlib
from extra.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True)
    password_hash = db.Column(db.String(256))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)


class TestCase(db.Model):
    __tablename__ = 'test_cases'

    id = db.Column(db.Integer, primary_key=True)
    # 用例唯一标识（基于相对路径的哈希）
    case_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
    name = db.Column(db.String(512), nullable=False)
    full_path = db.Column(db.Text, nullable=False)
    relative_path = db.Column(db.Text, nullable=False)

    # 文件信息（用于检测变更）
    file_size = db.Column(db.Integer)
    file_mtime = db.Column(db.DateTime)
    content_hash = db.Column(db.String(64))

    # 执行状态
    STATUS_CHOICES = ['not_executed', 'passed', 'failed', 'blocked', 'skipped', 'executing']
    status = db.Column(db.Enum(*STATUS_CHOICES), default='not_executed', index=True)

    # 执行信息
    last_execution_time = db.Column(db.DateTime, default=lambda: datetime.now() - timedelta(days=1))
    execution_duration = db.Column(db.Float, default=0.0)  # 执行时长（秒）
    total_executions = db.Column(db.Integer, default=0)
    avg_duration = db.Column(db.Float, default=0.0)

    # 结果详情
    result_details = db.Column(db.Text)
    error_message = db.Column(db.Text)
    stack_trace = db.Column(db.Text)

    # 人工校验信息
    verified_by = db.Column(db.String(64))
    verified_at = db.Column(db.DateTime)
    verification_notes = db.Column(db.Text)
    is_manually_modified = db.Column(db.Boolean, default=False)

    # 元数据
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    is_active = db.Column(db.Boolean, default=True)

    # 索引
    __table_args__ = (
        db.Index('idx_relative_path', db.text('relative_path(128)')),
        db.Index('idx_status_execution', 'status', 'last_execution_time'),
        db.Index('idx_path_status', db.text('relative_path(128)'), 'status'),
    )

    @staticmethod
    def generate_case_hash(relative_path):
        """生成用例哈希（机器无关）"""
        # 统一路径格式，避免不同系统路径分隔符差异
        normalized_path = relative_path.replace('\\', '/')
        return hashlib.sha256(normalized_path.encode()).hexdigest()

    @property
    def case_id(self):
        """兼容旧的case_id属性"""
        return self.case_hash


class TestExecution(db.Model):
    __tablename__ = 'test_executions'

    id = db.Column(db.Integer, primary_key=True)
    case_hash = db.Column(db.String(64), db.ForeignKey('test_cases.case_hash'), index=True)
    execution_time = db.Column(db.DateTime, default=datetime.now, index=True)
    status = db.Column(db.String(32))
    duration = db.Column(db.Float)
    details = db.Column(db.Text)
    executed_by = db.Column(db.String(32), default='scheduler')
    machine_id = db.Column(db.String(64))  # 执行机器标识
    plan_id = db.Column(db.Integer, db.ForeignKey('test_plans.id'))

    # 关联到用例
    test_case = db.relationship('TestCase', backref='executions', foreign_keys=[case_hash])


class TestPlan(db.Model):
    __tablename__ = 'test_plans'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)
    description = db.Column(db.Text)

    # 计划类型：scheduled(定时), manual(手动), custom(自定义), auto(自动)
    plan_type = db.Column(db.String(32), nullable=False)

    # 执行配置
    schedule_cron = db.Column(db.String(64))  # 定时任务的cron表达式
    include_paths = db.Column(db.Text)  # JSON字符串，包含的路径
    exclude_paths = db.Column(db.Text)  # JSON字符串，排除的路径

    # 新增：根据case_ids执行
    case_ids = db.Column(db.Text)  # JSON字符串，存储用例ID列表

    # 新增：优先级配置
    priorities = db.Column(db.Text)  # JSON字符串，存储优先级列表

    # 新增：重试次数
    retry_count = db.Column(db.Integer, default=0)

    # 新增：超时时间（分钟）
    timeout_minutes = db.Column(db.Integer, default=0)

    # 执行状态
    STATUS_CHOICES = ['pending', 'running', 'completed', 'failed', 'paused']
    status = db.Column(db.Enum(*STATUS_CHOICES), default='pending', index=True)
    last_execution_time = db.Column(db.DateTime)
    next_execution_time = db.Column(db.DateTime)
    total_cases = db.Column(db.Integer, default=0)
    executed_cases = db.Column(db.Integer, default=0)
    passed_cases = db.Column(db.Integer, default=0)
    failed_cases = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.now)
    created_by = db.Column(db.String(64))

    # 分布式执行相关
    distributed = db.Column(db.Boolean, default=False)
    assigned_machines = db.Column(db.Text)  # JSON字符串，分配的机器列表

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'plan_type': self.plan_type,
            'distributed': self.distributed,
            'case_ids': json.loads(self.case_ids) if self.case_ids else [],
            'priorities': json.loads(self.priorities) if self.priorities else [],
            'retry_count': self.retry_count,
            'timeout_minutes': self.timeout_minutes,
            'status': self.status,
            'total_cases': self.total_cases,
            'executed_cases': self.executed_cases,
            'passed_cases': self.passed_cases,
            'failed_cases': self.failed_cases,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by,
            'include_paths': json.loads(self.include_paths) if self.include_paths else [],
            'exclude_paths': json.loads(self.exclude_paths) if self.exclude_paths else [],
            'assigned_machines': json.loads(self.assigned_machines) if self.assigned_machines else []
        }


class ExecutionTask(db.Model):
    __tablename__ = 'execution_tasks'

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.String(128), unique=True, index=True)  # Celery任务ID
    case_hash = db.Column(db.String(64), db.ForeignKey('test_cases.case_hash'), index=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('test_plans.id'), index=True)
    machine_id = db.Column(db.String(64))  # 执行机器
    status = db.Column(db.String(32), default='pending')  # pending, running, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.now)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    result = db.Column(db.Text)


class MachineStatus(db.Model):
    __tablename__ = 'machine_status'

    id = db.Column(db.Integer, primary_key=True)
    machine_id = db.Column(db.String(64), unique=True, index=True)
    machine_ip = db.Column(db.String(45))
    machine_name = db.Column(db.String(128))
    status = db.Column(db.String(32), default='offline')  # online, offline, busy, idle
    last_heartbeat = db.Column(db.DateTime, default=datetime.now)
    cpu_usage = db.Column(db.Float)
    memory_usage = db.Column(db.Float)
    disk_usage = db.Column(db.Float)
    current_tasks = db.Column(db.Integer, default=0)
    max_tasks = db.Column(db.Integer, default=5)

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


class DistributedLock(db.Model):
    __tablename__ = 'distributed_locks'

    id = db.Column(db.Integer, primary_key=True)
    lock_key = db.Column(db.String(128), unique=True, index=True)
    machine_id = db.Column(db.String(64))
    acquired_at = db.Column(db.DateTime, default=datetime.now)
    expires_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)


# 添加批量执行记录模型
class BatchExecution(db.Model):
    __tablename__ = 'batch_executions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    plan_ids = db.Column(db.Text)  # 逗号分隔的计划ID
    execution_config = db.Column(db.Text)  # JSON配置
    status = db.Column(db.String(20), default='waiting')  # waiting, running, completed, failed
    created_by = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.now)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    error_message = db.Column(db.Text)

    def __repr__(self):
        return f'<BatchExecution {self.name}>'
