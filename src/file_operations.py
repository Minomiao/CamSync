import os
import shutil
import logging
import time
from datetime import datetime
from PyQt5.QtCore import QThread, pyqtSignal

class FileOperations(QThread):
    # 信号定义
    operation_completed = pyqtSignal(tuple)  # (success, message)
    progress_updated = pyqtSignal(tuple)     # (current, total, status)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.logger = logging.getLogger('CamSync')
        self.is_running = False
        self.files_to_copy = []
        self.current_operation = None
    
    def get_files_to_copy(self, src_dir, dest_dir, incremental=True):
        """获取需要复制的文件列表
        
        Args:
            src_dir: 源目录
            dest_dir: 目标目录
            incremental: 是否为增量备份
        
        Returns:
            list: 需要复制的文件路径列表 [(src_path, dest_path), ...]
        """
        files_to_copy = []
        
        try:
            # 确保目标目录存在
            os.makedirs(dest_dir, exist_ok=True)
            
            # 遍历源目录
            for root, dirs, files in os.walk(src_dir):
                # 计算相对路径
                rel_path = os.path.relpath(root, src_dir)
                # 如果是根目录，相对路径为 '.'
                if rel_path == '.':
                    rel_path = ''
                
                # 遍历文件
                for file in files:
                    src_path = os.path.join(root, file)
                    dest_path = os.path.join(dest_dir, rel_path, file)
                    
                    # 确保目标子目录存在
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    
                    # 检查是否需要复制
                    if not incremental or not self._should_skip_file(src_path, dest_path):
                        files_to_copy.append((src_path, dest_path))
        except Exception as e:
            self.logger.error(f"获取文件列表时发生错误: {str(e)}")
        
        return files_to_copy
    
    def _should_skip_file(self, src_path, dest_path):
        """判断是否应该跳过文件（用于增量备份）"""
        # 如果目标文件不存在，需要复制
        if not os.path.exists(dest_path):
            return False
        
        # 比较源文件和目标文件的大小和修改时间
        src_stat = os.stat(src_path)
        dest_stat = os.stat(dest_path)
        
        # 如果大小不同，需要复制
        if src_stat.st_size != dest_stat.st_size:
            return False
        
        # 如果源文件更新，需要复制
        if src_stat.st_mtime > dest_stat.st_mtime:
            return False
        
        # 否则跳过
        return True
    
    def start_copy_operation(self, files_to_copy):
        """开始文件复制操作"""
        self.files_to_copy = files_to_copy
        self.current_operation = 'copy'
        if not self.isRunning():
            self.start()
    
    def start_copy_operation_without_preview(self, src_dir, dest_dir, incremental=True):
        """不预览直接开始复制操作"""
        self.logger.info(f"开始复制操作: {src_dir} -> {dest_dir} (增量: {incremental})")
        self.current_operation = {
            'type': 'copy_without_preview',
            'src_dir': src_dir,
            'dest_dir': dest_dir,
            'incremental': incremental
        }
        if not self.isRunning():
            self.start()
    
    def run(self):
        """线程运行方法，执行文件复制操作"""
        self.is_running = True
        success = False
        message = ""
        
        try:
            if self.current_operation == 'copy':
                # 执行预览后的复制操作
                success, message = self._execute_copy_operation(self.files_to_copy)
            elif isinstance(self.current_operation, dict) and self.current_operation['type'] == 'copy_without_preview':
                # 执行不预览的复制操作
                src_dir = self.current_operation['src_dir']
                dest_dir = self.current_operation['dest_dir']
                incremental = self.current_operation['incremental']
                
                # 获取文件列表
                files_to_copy = self.get_files_to_copy(src_dir, dest_dir, incremental)
                if not files_to_copy:
                    success = True
                    message = "没有文件需要复制"
                else:
                    success, message = self._execute_copy_operation(files_to_copy)
        except Exception as e:
            success = False
            message = f"操作执行过程中发生错误: {str(e)}"
            self.logger.error(message)
        finally:
            # 发送操作完成信号
            self.operation_completed.emit((success, message))
            self.is_running = False
    
    def _execute_copy_operation(self, files_to_copy):
        """执行文件复制操作的实际逻辑"""
        total_files = len(files_to_copy)
        copied_files = 0
        failed_files = []
        
        start_time = time.time()
        
        for i, (src_path, dest_path) in enumerate(files_to_copy):
            try:
                # 复制文件
                shutil.copy2(src_path, dest_path)
                copied_files += 1
                
                # 更新进度
                status = f"正在复制: {os.path.basename(src_path)}"
                self.progress_updated.emit((i + 1, total_files, status))
                self.logger.info(f"已复制: {src_path} -> {dest_path}")
            except Exception as e:
                failed_files.append((src_path, str(e)))
                self.logger.error(f"复制文件失败: {src_path} -> {dest_path}, 错误: {str(e)}")
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        if failed_files:
            # 有文件复制失败
            message = f"复制完成，但有 {len(failed_files)} 个文件失败\n"
            message += "失败的文件:\n"
            for file_path, error in failed_files[:5]:  # 只显示前5个失败的文件
                message += f"- {file_path}: {error}\n"
            if len(failed_files) > 5:
                message += f"... 还有 {len(failed_files) - 5} 个失败文件未显示"
            return False, message
        else:
            # 所有文件复制成功
            message = f"成功复制 {copied_files} 个文件，用时 {elapsed_time:.2f} 秒"
            return True, message
    
    def stop_operation(self):
        """停止当前操作"""
        self.is_running = False
        self.wait()
    
    def calculate_folder_size(self, folder_path):
        """计算文件夹大小"""
        total_size = 0
        try:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        total_size += os.path.getsize(file_path)
                    except:
                        continue
        except Exception as e:
            self.logger.error(f"计算文件夹大小错误: {str(e)}")
        return total_size
    
    def format_size(self, size_bytes):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
    
    def compare_directories(self, src_dir, dest_dir):
        """比较两个目录，返回差异信息"""
        diff_info = {
            'only_in_source': [],    # 仅在源目录中存在的文件
            'only_in_dest': [],      # 仅在目标目录中存在的文件
            'different_files': [],   # 两边都有但内容不同的文件
            'total_size_diff': 0     # 总大小差异
        }
        
        # 收集源目录中的所有文件路径
        source_files = set()
        source_size = 0
        for root, _, files in os.walk(src_dir):
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), src_dir)
                source_files.add(rel_path)
                source_size += os.path.getsize(os.path.join(root, file))
        
        # 收集目标目录中的所有文件路径
        dest_files = set()
        dest_size = 0
        for root, _, files in os.walk(dest_dir):
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), dest_dir)
                dest_files.add(rel_path)
                dest_size += os.path.getsize(os.path.join(root, file))
        
        # 计算差异
        diff_info['only_in_source'] = list(source_files - dest_files)
        diff_info['only_in_dest'] = list(dest_files - source_files)
        
        # 检查两边都有的文件是否相同
        common_files = source_files & dest_files
        for rel_path in common_files:
            src_path = os.path.join(src_dir, rel_path)
            dest_path = os.path.join(dest_dir, rel_path)
            
            try:
                src_stat = os.stat(src_path)
                dest_stat = os.stat(dest_path)
                
                if src_stat.st_size != dest_stat.st_size or src_stat.st_mtime != dest_stat.st_mtime:
                    diff_info['different_files'].append(rel_path)
            except:
                continue
        
        # 计算总大小差异
        diff_info['total_size_diff'] = source_size - dest_size
        
        return diff_info