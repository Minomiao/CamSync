import os
import logging
import time
from datetime import datetime
from logging.handlers import RotatingFileHandler

def setup_logger():
    """设置日志记录器"""
    # 日志目录
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    # 确保日志目录存在
    os.makedirs(log_dir, exist_ok=True)
    
    # 日志文件名格式：YYYY-MM-DD.log
    log_filename = datetime.now().strftime('%Y-%m-%d.log')
    log_path = os.path.join(log_dir, log_filename)
    
    # 创建日志记录器
    logger = logging.getLogger('CamSync')
    logger.setLevel(logging.INFO)  # 设置日志级别为 INFO
    
    # 检查是否已经添加了处理器
    if not logger.handlers:
        # 创建文件处理器，使用RotatingFileHandler实现日志轮转
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=10 * 1024 * 1024,  # 每个日志文件最大10MB
            backupCount=10,              # 最多保留10个备份文件
            encoding='utf-8'
        )
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        
        # 设置日志格式
        log_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 设置处理器的日志格式
        file_handler.setFormatter(log_format)
        console_handler.setFormatter(log_format)
        
        # 添加处理器到日志记录器
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger

class LogManager:
    """日志管理器，提供高级日志记录功能"""
    def __init__(self):
        self.logger = setup_logger()
        
    def log_device_detection(self, device_path, device_name):
        """记录设备检测事件"""
        self.logger.info(f"检测到设备: {device_name} ({device_path})")
    
    def log_folder_detection(self, device_path, folder_name):
        """记录文件夹检测事件"""
        self.logger.info(f"在设备 {device_path} 上检测到文件夹: {folder_name}")
    
    def log_config_creation(self, device_path, folder_name):
        """记录配置创建事件"""
        self.logger.info(f"为设备 {device_path} 的文件夹 {folder_name} 创建配置文件")
    
    def log_file_copy_start(self, src_path, dest_path):
        """记录文件复制开始事件"""
        self.logger.info(f"开始复制文件: {src_path} -> {dest_path}")
    
    def log_file_copy_completed(self, src_path, dest_path):
        """记录文件复制完成事件"""
        self.logger.info(f"文件复制完成: {src_path} -> {dest_path}")
    
    def log_file_copy_failed(self, src_path, dest_path, error_message):
        """记录文件复制失败事件"""
        self.logger.error(f"文件复制失败: {src_path} -> {dest_path}, 错误: {error_message}")
    
    def log_operation_summary(self, success, total_files, copied_files, failed_files):
        """记录操作摘要"""
        if success:
            self.logger.info(f"操作成功: 共 {total_files} 个文件，成功复制 {copied_files} 个文件")
        else:
            self.logger.warning(f"操作部分失败: 共 {total_files} 个文件，成功复制 {copied_files} 个文件，失败 {failed_files} 个文件")
    
    def log_config_change(self, config_name, old_value, new_value):
        """记录配置更改事件"""
        self.logger.info(f"配置更改: {config_name} 从 '{old_value}' 更改为 '{new_value}'")
    
    def log_error(self, message, exception=None):
        """记录错误事件"""
        if exception:
            self.logger.error(f"{message}: {str(exception)}")
        else:
            self.logger.error(message)
    
    def log_warning(self, message):
        """记录警告事件"""
        self.logger.warning(message)
    
    def log_info(self, message):
        """记录信息事件"""
        self.logger.info(message)
    
    def get_latest_logs(self, max_lines=100):
        """获取最新的日志条目"""
        logs = []
        
        try:
            # 获取当前日志文件路径
            log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
            log_filename = datetime.now().strftime('%Y-%m-%d.log')
            log_path = os.path.join(log_dir, log_filename)
            
            if os.path.exists(log_path):
                with open(log_path, 'r', encoding='utf-8') as f:
                    # 读取所有行
                    lines = f.readlines()
                    # 获取最后 max_lines 行
                    logs = lines[-max_lines:] if len(lines) > max_lines else lines
                    # 去除换行符
                    logs = [line.strip() for line in logs]
        except Exception as e:
            self.logger.error(f"读取日志文件时发生错误: {str(e)}")
        
        return logs

# 创建全局日志管理器实例
log_manager = LogManager()