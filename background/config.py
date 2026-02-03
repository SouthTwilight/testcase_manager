import os
from datetime import time


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    DATABASE_HOST = os.environ.get('DATABASE_HOST') or '10.94.176.36'
    DATABASE_USER = os.environ.get('DATABASE_USER') or 'petal'
    DATABASE_PASSWORD = os.environ.get('DATABASE_PASSWORD') or '123456'
    DATABASE_NAME = os.environ.get('DATABASE_NAME') or 'petal'

    # MySQL数据库配置
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}/{DATABASE_NAME}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_SIZE = 10
    SQLALCHEMY_MAX_OVERFLOW = 20
    SQLALCHEMY_POOL_RECYCLE = 3600

    # 用例目录配置
    TEST_CASE_ROOT = os.environ.get('TEST_CASE_ROOT') or r'D:\temp\ADS1_0_TEST\robotest_ver2\test_script\06_花瓣适配'

    # 定时任务配置
    SCHEDULE_START_TIME = time(23, 0)  # 晚上11点
    SCHEDULE_END_TIME = time(8, 0)  # 次日8点

    # 执行器配置
    # 注意：由于测试用例依赖唯一的硬件资源（测试机），必须串行执行
    MAX_CONCURRENT_TESTS = 1  # 串行执行，一次只能执行一条用例
    TEST_TIMEOUT = 600  # 10分钟超时

    # 执行优先级权重
    PRIORITY_WEIGHTS = {
        'new_case': 1.0,
        'failed_case': 0.8,
        'long_interval': 0.6,
        'high_priority_dir': 0.5,
        'short_duration': 0.3
    }

    # 优先目录配置
    HIGH_PRIORITY_DIRS = [
        '00_红线用例/'
    ]

    # Redis配置（用于分布式锁和缓存）
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://10.94.176.36:6379/0'

    # Celery配置
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL') or 'redis://10.94.176.36:6379/1'
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND') or 'redis://10.94.176.36:6379/2'

    # 机器标识
    MACHINE_ID = os.environ.get('MACHINE_ID') or 'default'
    MACHINE_IP = os.environ.get('MACHINE_IP') or '127.0.0.1'

    # 分布式任务配置
    ENABLE_DISTRIBUTED = os.environ.get('ENABLE_DISTRIBUTED', 'false').lower() == 'true'
    DISTRIBUTED_LOCK_TIMEOUT = 300  # 分布式锁超时时间（秒）

    # 文件监控配置
    WATCHDOG_ENABLED = True
    WATCHDOG_INTERVAL = 30  # 监控间隔（秒）
