import os
import hashlib
import json
from pathlib import Path
from datetime import datetime, timedelta
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from models import db, TestCase
from config import Config


class TestCaseScanner:
    def __init__(self, root_dir=None):
        self.root_dir = Path(root_dir or Config.TEST_CASE_ROOT)
        self.case_extensions = {'.py', '.java', '.js', '.ts', '.robot'}  # 根据实际情况扩展
        self.lock = threading.Lock()

    def scan_all_cases(self, update_status=True):
        """扫描所有用例，初始化或更新数据库"""
        with self.lock:
            all_cases = []
            scan_time = datetime.now()

            for ext in self.case_extensions:
                for file_path in self.root_dir.rglob(f'*{ext}'):
                    if self._is_test_case(file_path):
                        try:
                            case_info = self._extract_case_info(file_path, scan_time)
                            all_cases.append(case_info)
                        except Exception as e:
                            print(f"Error processing {file_path}: {e}")

            # 批量更新数据库
            updated_count = self._update_database(all_cases, update_status)
            return updated_count

    def scan_new_and_changed_cases(self):
        """扫描新增和修改的用例"""
        with self.lock:
            existing_cases = {}
            for case in TestCase.query.all():
                existing_cases[case.case_hash] = case

            new_or_changed = []
            deleted_cases = []
            scan_time = datetime.now()

            # 扫描文件系统
            for ext in self.case_extensions:
                for file_path in self.root_dir.rglob(f'*{ext}'):
                    if self._is_test_case(file_path):
                        try:
                            case_info = self._extract_case_info(file_path, scan_time)
                            case_hash = case_info['case_hash']

                            if case_hash in existing_cases:
                                existing = existing_cases[case_hash]
                                # 检查文件是否变更
                                if (existing.file_mtime is None or
                                        case_info['file_mtime'] > existing.file_mtime or
                                        case_info['content_hash'] != existing.content_hash):
                                    # 文件已变更
                                    case_info['id'] = existing.id
                                    case_info['status'] = 'not_executed'  # 变更后标记为未执行
                                    new_or_changed.append(case_info)
                                del existing_cases[case_hash]
                            else:
                                # 新增用例
                                case_info['status'] = 'not_executed'
                                new_or_changed.append(case_info)
                        except Exception as e:
                            print(f"Error processing {file_path}: {e}")

            # 标记已删除的用例
            for case_hash, case in existing_cases.items():
                if case.is_active:
                    case.is_active = False
                    db.session.add(case)
                    deleted_cases.append(case.relative_path)

            # 更新数据库
            if new_or_changed:
                self._update_database(new_or_changed, update_status=True)

            db.session.commit()

            return {
                'new_count': len([c for c in new_or_changed if 'id' not in c]),
                'changed_count': len([c for c in new_or_changed if 'id' in c]),
                'deleted_count': len(deleted_cases)
            }

    def _is_test_case(self, file_path):
        """判断是否为测试用例文件"""
        # 这里根据实际项目规则实现
        filename = file_path.name.lower()
        return 'tc_' in filename

    def _extract_case_info(self, file_path, scan_time):
        """提取用例信息"""
        relative_path = file_path.relative_to(self.root_dir)

        # 获取文件信息
        stat = file_path.stat()
        file_mtime = datetime.fromtimestamp(stat.st_mtime)

        # 生成机器无关的哈希
        case_hash = TestCase.generate_case_hash(str(relative_path))

        # 计算文件内容哈希（用于检测变更）
        content_hash = self._calculate_content_hash(file_path)

        return {
            'case_hash': case_hash,
            'name': file_path.stem,
            'full_path': str(file_path),
            'relative_path': str(relative_path),
            'file_size': stat.st_size,
            'file_mtime': file_mtime,
            'content_hash': content_hash,
            'updated_at': scan_time
        }

    def _calculate_content_hash(self, file_path):
        """计算文件内容哈希"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                # 只取前100KB计算哈希，避免大文件性能问题
                if len(content) > 102400:
                    content = content[:102400]
                return hashlib.md5(content).hexdigest()
        except:
            return ''

    def _update_database(self, cases, update_status=False):
        """批量更新数据库"""
        updated_count = 0

        for case_info in cases:
            existing = TestCase.query.filter_by(case_hash=case_info['case_hash']).first()

            if existing:
                # 更新已有用例
                for key, value in case_info.items():
                    if key != 'case_hash' and hasattr(existing, key):
                        setattr(existing, key, value)

                if update_status and not existing.is_manually_modified:
                    existing.status = 'not_executed'

                existing.updated_at = datetime.now()
                updated_count += 1
            else:
                # 新增用例
                case = TestCase(**case_info)
                if update_status:
                    case.status = 'not_executed'
                    # 初始化执行时间为前一天凌晨
                    yesterday = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
                    case.last_execution_time = yesterday
                db.session.add(case)
                updated_count += 1

        db.session.commit()
        return updated_count


class FileChangeHandler(FileSystemEventHandler):
    """文件变更监控处理器"""

    def __init__(self, scanner):
        self.scanner = scanner
        self.changes = []
        self.last_scan = datetime.now()

    def on_modified(self, event):
        if not event.is_directory and self._is_test_file(event.src_path):
            self._schedule_rescan()

    def on_created(self, event):
        if not event.is_directory and self._is_test_file(event.src_path):
            self._schedule_rescan()

    def on_deleted(self, event):
        if not event.is_directory and self._is_test_file(event.src_path):
            self._schedule_rescan()

    def _is_test_file(self, path):
        return any(path.endswith(ext) for ext in self.scanner.case_extensions)

    def _schedule_rescan(self):
        """安排重新扫描"""
        now = datetime.now()
        # 避免频繁扫描，至少间隔10秒
        if (now - self.last_scan).seconds > 10:
            threading.Timer(5, self.scanner.scan_new_and_changed_cases).start()
            self.last_scan = now
