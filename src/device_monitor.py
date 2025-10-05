import os
import time
import logging
import os
import win32api
import win32file
import win32con
from PyQt5.QtCore import QThread, pyqtSignal

class DeviceMonitor(QThread):
    # 信号定义
    device_detected = pyqtSignal(tuple)  # (device_path, device_name)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.is_monitoring = False
        self.logger = logging.getLogger('CamSync')
        self.monitored_devices = set()  # 存储已监控的设备路径
        self.target_folders = ['DCIM', 'PRIVATE', 'MISC']  # 目标文件夹
    
    def run(self):
        """线程运行方法，持续监控 USB 存储设备"""
        self.is_monitoring = True
        self.logger.info("开始监控 USB 存储设备")
        
        while self.is_monitoring:
            try:
                # 获取当前所有逻辑驱动器
                drives = self.get_removable_drives()
                
                # 检查新增的设备
                for drive_path, drive_name in drives:
                    if drive_path not in self.monitored_devices:
                        self.monitored_devices.add(drive_path)
                        self.logger.info(f"检测到新设备: {drive_name} ({drive_path})")
                        # 发送设备检测信号
                        self.device_detected.emit((drive_path, drive_name))
                
                # 检查移除的设备
                for drive_path in list(self.monitored_devices):
                    if not any(drive_path == d[0] for d in drives):
                        self.monitored_devices.remove(drive_path)
                        self.logger.info(f"设备已移除: {drive_path}")
                
                # 短暂休眠，避免CPU占用过高
                time.sleep(2)
            except Exception as e:
                self.logger.error(f"监控设备时发生错误: {str(e)}")
                time.sleep(2)
    
    def stop_monitoring(self):
        """停止监控设备"""
        self.is_monitoring = False
        self.monitored_devices.clear()
        self.logger.info("停止监控 USB 存储设备")
        self.wait()
    
    def start_monitoring(self):
        """开始监控设备"""
        if not self.isRunning():
            self.start()
    
    def get_removable_drives(self):
        """获取所有可移动驱动器"""
        drives = []
        # 获取所有逻辑驱动器
        bitmask = win32api.GetLogicalDrives()
        
        for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            # 检查驱动器是否存在
            if bitmask & 1:
                drive_path = f"{letter}:\\"
                try:
                    # 获取驱动器类型
                    drive_type = win32file.GetDriveType(drive_path)
                    # 检查是否为可移动驱动器（USB存储设备通常为2）
                    if drive_type == win32con.DRIVE_REMOVABLE:
                        # 获取驱动器卷标
                        try:
                            volume_info = win32api.GetVolumeInformation(drive_path)
                            drive_name = volume_info[0] or f"可移动磁盘 ({letter}:)"
                        except:
                            drive_name = f"可移动磁盘 ({letter}:)"
                        drives.append((drive_path, drive_name))
                except Exception as e:
                    self.logger.error(f"检查驱动器 {drive_path} 时发生错误: {str(e)}")
            # 移动到下一个驱动器
            bitmask >>= 1
        
        return drives
    
    def check_target_folders(self, device_path):
        """检查设备上是否存在目标文件夹"""
        found_folders = []
        
        try:
            # 列出设备根目录下的所有项目
            items = os.listdir(device_path)
            
            # 检查每个目标文件夹是否存在
            for folder in self.target_folders:
                if folder in items:
                    folder_path = os.path.join(device_path, folder)
                    # 确保是文件夹
                    if os.path.isdir(folder_path):
                        found_folders.append(folder)
                        self.logger.info(f"在设备 {device_path} 上找到文件夹: {folder}")
        except Exception as e:
            self.logger.error(f"检查设备 {device_path} 上的文件夹时发生错误: {str(e)}")
        
        return found_folders
    
    def get_folder_info(self, folder_path):
        """获取文件夹信息，包括文件数量和总大小"""
        file_count = 0
        total_size = 0
        
        try:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        file_count += 1
                        total_size += os.path.getsize(file_path)
                    except:
                        # 忽略无法访问的文件
                        continue
        except Exception as e:
            self.logger.error(f"获取文件夹 {folder_path} 信息时发生错误: {str(e)}")
        
        return file_count, total_size