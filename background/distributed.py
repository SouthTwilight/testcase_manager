import redis
import json
import time
import threading
from datetime import datetime, timedelta
from contextlib import contextmanager
from models import db, DistributedLock, MachineStatus
from config import Config


class DistributedManager:
    """分布式任务管理器"""

    def __init__(self, app=None):
        self.app = app
        self.redis_client = redis.from_url(Config.REDIS_URL)
        self.machine_id = Config.MACHINE_ID
        self.lock_prefix = 'lock:'
        self.heartbeat_interval = 30  # 心跳间隔（秒）

    def init_app(self, app):
        self.app = app
        # 启动心跳线程
        heartbeat_thread = threading.Thread(target=self._heartbeat_worker, daemon=True)
        heartbeat_thread.start()

    def acquire_lock(self, lock_key, timeout=300):
        """获取分布式锁"""
        full_key = f"{self.lock_prefix}{lock_key}"
        lock_value = f"{self.machine_id}:{time.time()}"

        # 尝试获取Redis锁
        acquired = self.redis_client.setnx(full_key, lock_value)
        if acquired:
            self.redis_client.expire(full_key, timeout)

            # 记录到数据库
            with self.app.app_context():
                lock = DistributedLock(
                    lock_key=lock_key,
                    machine_id=self.machine_id,
                    acquired_at=datetime.now(),
                    expires_at=datetime.now() + timedelta(seconds=timeout)
                )
                db.session.add(lock)
                db.session.commit()

            return True

        # 检查锁是否已过期
        current_value = self.redis_client.get(full_key)
        if current_value:
            try:
                # 检查是否是本机持有的旧锁
                machine, timestamp = current_value.decode().split(':')
                if machine == self.machine_id and time.time() - float(timestamp) > timeout:
                    # 锁已过期，重新获取
                    self.redis_client.delete(full_key)
                    return self.acquire_lock(lock_key, timeout)
            except:
                pass

        return False

    def release_lock(self, lock_key):
        """释放分布式锁"""
        full_key = f"{self.lock_prefix}{lock_key}"

        # 检查是否为本机持有的锁
        current_value = self.redis_client.get(full_key)
        if current_value:
            machine = current_value.decode().split(':')[0]
            if machine == self.machine_id:
                self.redis_client.delete(full_key)

                # 更新数据库记录
                with self.app.app_context():
                    lock = DistributedLock.query.filter_by(
                        lock_key=lock_key,
                        machine_id=self.machine_id,
                        is_active=True
                    ).first()
                    if lock:
                        lock.is_active = False
                        db.session.commit()

        return True

    @contextmanager
    def distributed_lock(self, lock_key, timeout=300):
        """分布式锁上下文管理器"""
        acquired = False
        try:
            acquired = self.acquire_lock(lock_key, timeout)
            if acquired:
                yield True
            else:
                yield False
        finally:
            if acquired:
                self.release_lock(lock_key)

    def _heartbeat_worker(self):
        """心跳工作线程"""
        while True:
            try:
                with self.app.app_context():
                    # 更新机器状态
                    machine = MachineStatus.query.filter_by(machine_id=self.machine_id).first()
                    if not machine:
                        machine = MachineStatus(
                            machine_id=self.machine_id,
                            machine_ip=Config.MACHINE_IP,
                            machine_name=Config.MACHINE_ID,
                            status='online'
                        )
                        db.session.add(machine)

                    machine.last_heartbeat = datetime.now()
                    machine.status = 'online'
                    # 这里可以添加获取系统资源使用情况的代码
                    # machine.cpu_usage = get_cpu_usage()
                    # machine.memory_usage = get_memory_usage()

                    db.session.commit()

                    # 清理过期的心跳记录
                    cutoff = datetime.now() - timedelta(minutes=5)
                    expired_machines = MachineStatus.query.filter(
                        MachineStatus.last_heartbeat < cutoff,
                        MachineStatus.status != 'offline'
                    ).all()

                    for expired in expired_machines:
                        expired.status = 'offline'

                    db.session.commit()

            except Exception as e:
                print(f"Heartbeat error: {e}")

            time.sleep(self.heartbeat_interval)

    def get_available_machines(self):
        """获取可用的执行机器"""
        with self.app.app_context():
            cutoff = datetime.now() - timedelta(minutes=2)
            machines = MachineStatus.query.filter(
                MachineStatus.last_heartbeat >= cutoff,
                MachineStatus.status == 'online'
            ).order_by(MachineStatus.current_tasks).all()

            return machines

    def assign_task_to_machine(self, task_data):
        """分配任务到机器"""
        machines = self.get_available_machines()

        if not machines:
            return None

        # 选择负载最低的机器
        selected_machine = min(machines, key=lambda m: m.current_tasks / m.max_tasks)

        # 更新机器任务计数
        selected_machine.current_tasks += 1
        db.session.commit()

        # 将任务发布到Redis队列
        queue_key = f"tasks:{selected_machine.machine_id}"
        self.redis_client.rpush(queue_key, json.dumps(task_data))

        return selected_machine.machine_id
