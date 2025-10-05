import os
import json
import logging
import winreg
from datetime import datetime

class ConfigManager:
    def __init__(self):
        # 本地配置文件目录
        self.local_config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')
        # 确保配置目录存在
        os.makedirs(self.local_config_dir, exist_ok=True)
        # 主配置文件路径
        self.main_config_path = os.path.join(self.local_config_dir, 'main_config.json')
        # 默认配置
        self.default_config = {
            'backup_path': os.path.join(os.path.expanduser('~'), 'Pictures', 'CamSync'),
            'auto_start': False
        }
        # 加载主配置
        self.main_config = self.load_main_config()
        # 确保备份路径存在
        os.makedirs(self.main_config['backup_path'], exist_ok=True)
        # 日志记录器
        self.logger = logging.getLogger('CamSync')
        # U盘配置文件名
        self.USB_CONFIG_FILENAME = 'CamSyncConfig.json'
    
    def load_main_config(self):
        """加载主配置文件"""
        if os.path.exists(self.main_config_path):
            try:
                with open(self.main_config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # 合并默认配置（如果有缺失的键）
                for key, value in self.default_config.items():
                    if key not in config:
                        config[key] = value
                return config
            except Exception as e:
                self.logger.error(f"加载主配置文件时发生错误: {str(e)}")
        # 如果配置文件不存在或加载失败，返回默认配置
        return self.default_config.copy()
    
    def save_main_config(self):
        """保存主配置文件"""
        try:
            with open(self.main_config_path, 'w', encoding='utf-8') as f:
                json.dump(self.main_config, f, ensure_ascii=False, indent=4)
            self.logger.info("主配置文件已保存")
        except Exception as e:
            self.logger.error(f"保存主配置文件时发生错误: {str(e)}")
    
    def get_backup_path(self):
        """获取备份路径"""
        return self.main_config['backup_path']
    
    def set_backup_path(self, path):
        """设置备份路径"""
        self.main_config['backup_path'] = path
        # 确保新的备份路径存在
        os.makedirs(path, exist_ok=True)
        self.save_main_config()
        self.logger.info(f"备份路径已设置为: {path}")
    
    def get_auto_start(self):
        """获取开机自启动状态"""
        return self.main_config['auto_start']
    
    def set_auto_start(self, enabled):
        """设置开机自启动状态"""
        self.main_config['auto_start'] = enabled
        self.save_main_config()
        
        # 更新Windows注册表
        try:
            # 获取当前可执行文件路径
            exe_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'main.py'))
            python_exe = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.venv', 'Scripts', 'python.exe'))
            # 命令行参数
            command = f'"{python_exe}" "{exe_path}"' if enabled else ''
            
            # 打开注册表键
            key_path = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Run'
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            
            if enabled:
                # 设置开机自启动
                winreg.SetValueEx(key, 'CamSync', 0, winreg.REG_SZ, command)
                self.logger.info("开机自启动已启用")
            else:
                # 删除开机自启动
                try:
                    winreg.DeleteValue(key, 'CamSync')
                    self.logger.info("开机自启动已禁用")
                except FileNotFoundError:
                    # 如果值不存在，忽略错误
                    pass
            
            winreg.CloseKey(key)
        except Exception as e:
            self.logger.error(f"更新开机自启动设置时发生错误: {str(e)}")
    
    def get_folder_config_path(self, device_path, folder_name):
        """获取文件夹配置文件路径"""
        # 配置文件保存在U盘根目录
        return os.path.join(device_path, self.USB_CONFIG_FILENAME)
    
    def get_folder_config(self, device_path, folder_name):
        """获取文件夹配置"""
        config_path = self.get_folder_config_path(device_path, folder_name)
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                # 从配置数据中获取指定文件夹的配置
                if folder_name in config_data.get('folders', {}):
                    return config_data['folders'][folder_name]
                return None
            except Exception as e:
                self.logger.error(f"加载U盘配置文件时发生错误: {str(e)}")
        return None
    
    def save_folder_config(self, device_path, folder_name, config):
        """保存文件夹配置到U盘"""
        config_path = self.get_folder_config_path(device_path, folder_name)
        try:
            # 读取现有配置或创建新配置
            config_data = {}
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
            
            # 确保folders字段存在
            if 'folders' not in config_data:
                config_data['folders'] = {}
            
            # 更新指定文件夹的配置
            config_data['folders'][folder_name] = config
            
            # 保存配置文件
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=4)
            self.logger.info(f"文件夹配置已保存到U盘: {folder_name}")
        except Exception as e:
            self.logger.error(f"保存U盘配置文件时发生错误: {str(e)}")
    
    def create_default_config(self, device_path, folder_name):
        """创建默认文件夹配置"""
        config = {
            'device_path': device_path,
            'folder_name': folder_name,
            'backup_strategy': 'incremental',  # 默认为增量备份
            'preview_before_copy': True,       # 默认为复制前预览
            'include_subfolders': True,        # 默认为包含子文件夹
            'last_backup_time': None,          # 上次备份时间
            'file_patterns': ['*'],            # 文件匹配模式
            'exclude_patterns': [],            # 排除文件模式
            'saved_files': [],                 # 已保存的文件列表
            'unsaved_files': []                # 未保存的文件列表
        }
        # 保存配置
        self.save_folder_config(device_path, folder_name, config)
        return config
    
    def update_last_backup_time(self, device_path, folder_name):
        """更新上次备份时间"""
        config = self.get_folder_config(device_path, folder_name)
        if config:
            config['last_backup_time'] = datetime.now().isoformat()
            self.save_folder_config(device_path, folder_name, config)
    
    def get_all_folder_configs(self):
        """获取所有文件夹配置（注意：现在配置存储在U盘上，此方法不再适用）"""
        self.logger.warning("get_all_folder_configs 方法不再适用，因为配置现在存储在U盘上")
        return []
    
    def update_folder_file_info(self, device_path, folder_name, saved_files, unsaved_files):
        """更新文件夹的保存和未保存文件信息"""
        config = self.get_folder_config(device_path, folder_name)
        if not config:
            # 如果配置不存在，创建默认配置
            config = self.create_default_config(device_path, folder_name)
        
        # 更新文件信息
        config['saved_files'] = saved_files  # 已保存的文件列表
        config['unsaved_files'] = unsaved_files  # 未保存的文件列表
        
        # 保存更新后的配置
        self.save_folder_config(device_path, folder_name, config)