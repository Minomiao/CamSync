import sys
import os
import logging
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QTextEdit, 
                            QFileDialog, QMessageBox, QCheckBox, QGroupBox, 
                            QGridLayout, QTabWidget, QSystemTrayIcon, QMenu, QAction,
                            QDialog, QScrollArea, QListWidget, QListWidgetItem)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt5.QtGui import QIcon, QFont

# 导入其他模块
from device_monitor import DeviceMonitor
from config_manager import ConfigManager
from file_operations import FileOperations
from logger import setup_logger

class FileConfirmationDialog(QDialog):
    def __init__(self, parent=None, files_to_copy=None):
        super().__init__(parent)
        self.setWindowTitle('文件确认')
        self.resize(800, 600)
        
        # 设置文件列表
        self.files_to_copy = files_to_copy if files_to_copy else []
        self.selected_files = self.files_to_copy.copy()  # 默认选中所有文件
        
        # 创建UI
        self.init_ui()
    
    def init_ui(self):
        # 创建主布局
        main_layout = QVBoxLayout(self)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # 显示文件数量和总大小
        total_size = 0
        for src_path, _ in self.files_to_copy:
            if os.path.exists(src_path):
                total_size += os.path.getsize(src_path)
        
        info_label = QLabel(f'找到 {len(self.files_to_copy)} 个文件，总大小: {self.format_size(total_size)}')
        info_label.setStyleSheet("font-weight: bold;")
        scroll_layout.addWidget(info_label)
        
        # 添加全选复选框
        self.select_all_check = QCheckBox('全选')
        self.select_all_check.setChecked(True)
        self.select_all_check.stateChanged.connect(self.toggle_select_all)
        scroll_layout.addWidget(self.select_all_check)
        
        # 创建文件列表
        self.file_list = QListWidget()
        
        # 添加文件项
        for src_path, dest_path in self.files_to_copy:
            if os.path.exists(src_path):
                size = os.path.getsize(src_path)
                size_str = self.format_size(size)
                item = QListWidgetItem(f'{os.path.basename(src_path)} ({size_str})')
                item.setCheckState(Qt.Checked)
                # 存储完整路径信息
                item.setData(Qt.UserRole, (src_path, dest_path))
                self.file_list.addItem(item)
        
        # 连接信号
        self.file_list.itemChanged.connect(self.on_item_changed)
        
        # 添加到滚动区域
        scroll_layout.addWidget(self.file_list)
        scroll_area.setWidget(scroll_content)
        scroll_area.setWidgetResizable(True)
        
        # 创建按钮区域
        button_layout = QHBoxLayout()
        
        self.cancel_button = QPushButton('取消')
        self.cancel_button.clicked.connect(self.reject)
        
        self.ok_button = QPushButton('确认复制')
        self.ok_button.clicked.connect(self.accept)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)
        
        # 添加到主布局
        main_layout.addWidget(scroll_area)
        main_layout.addLayout(button_layout)
    
    def toggle_select_all(self, state):
        # 全选/取消全选
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            item.setCheckState(state)
    
    def on_item_changed(self, item):
        # 检查是否所有项都被选中
        all_checked = True
        for i in range(self.file_list.count()):
            if self.file_list.item(i).checkState() != Qt.Checked:
                all_checked = False
                break
        
        # 更新全选复选框状态
        self.select_all_check.setChecked(all_checked)
    
    def get_selected_files(self):
        # 获取选中的文件
        selected_files = []
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            if item.checkState() == Qt.Checked:
                selected_files.append(item.data(Qt.UserRole))
        
        return selected_files
    
    def format_size(self, size_bytes):
        # 格式化文件大小
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0

class CamSyncApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # 设置日志
        self.logger = setup_logger()
        self.logger.info("CamSync application started")
        
        # 初始化配置管理器
        self.config_manager = ConfigManager()
        
        # 初始化设备监控器
        self.device_monitor = DeviceMonitor(self)
        self.device_monitor.device_detected.connect(self.on_device_detected)
        
        # 初始化文件操作管理器
        self.file_operations = FileOperations(self)
        self.file_operations.operation_completed.connect(self.on_operation_completed)
        
        # 设置UI
        self.init_ui()
        
        # 检查开机自启动设置
        self.check_auto_start()
        
        # 初始化系统托盘
        self.init_system_tray()
        
        # 初始化不再询问选项
        self.skip_close_dialog = False
        # 初始化默认关闭行为（默认最小化到托盘）
        self.default_close_action = 'minimize'
        # 从配置中加载相关设置
        self.load_close_settings()
        
    def init_ui(self):
        # 设置窗口标题和大小
        self.setWindowTitle('CamSync - 相机文件同步工具')
        self.setGeometry(100, 100, 900, 600)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建状态区域
        status_group = QGroupBox("运行状态")
        status_layout = QHBoxLayout()
        
        self.status_label = QLabel("等待启动监控")
        self.status_label.setStyleSheet("color: orange; font-weight: bold;")
        
        self.start_stop_button = QPushButton("开始监控")
        self.start_stop_button.clicked.connect(self.toggle_monitoring)
        
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.start_stop_button)
        status_group.setLayout(status_layout)
        
        # 创建配置区域
        config_group = QGroupBox("备份配置")
        config_layout = QGridLayout()
        
        self.backup_path_label = QLabel("备份路径:")
        self.backup_path_edit = QLabel(self.config_manager.get_backup_path())
        self.backup_path_button = QPushButton("浏览...")
        self.backup_path_button.clicked.connect(self.select_backup_path)
        
        self.auto_start_check = QCheckBox("开机自启动")
        self.auto_start_check.stateChanged.connect(self.toggle_auto_start)
        
        config_layout.addWidget(self.backup_path_label, 0, 0)
        config_layout.addWidget(self.backup_path_edit, 0, 1)
        config_layout.addWidget(self.backup_path_button, 0, 2)
        config_layout.addWidget(self.auto_start_check, 1, 0, 1, 3)
        config_group.setLayout(config_layout)
        
        # 创建日志和信息区域
        tab_widget = QTabWidget()
        
        # 日志标签页
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        tab_widget.addTab(self.log_text, "操作日志")
        
        # 文件预览标签页
        self.file_preview_text = QTextEdit()
        self.file_preview_text.setReadOnly(True)
        tab_widget.addTab(self.file_preview_text, "文件预览")
        
        # 添加所有组件到主布局
        main_layout.addWidget(status_group)
        main_layout.addWidget(config_group)
        main_layout.addWidget(tab_widget)
        
        # 显示初始日志
        self.update_log("应用程序已启动\n")
        
    def toggle_monitoring(self):
        if not self.device_monitor.is_monitoring:
            # 开始监控
            self.device_monitor.start_monitoring()
            self.status_label.setText("正在监控设备...")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            self.start_stop_button.setText("停止监控")
            self.update_log("开始监控USB存储设备\n")
        else:
            # 停止监控
            self.device_monitor.stop_monitoring()
            self.status_label.setText("监控已停止")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.start_stop_button.setText("开始监控")
            self.update_log("停止监控USB存储设备\n")
    
    def select_backup_path(self):
        path = QFileDialog.getExistingDirectory(self, "选择备份路径", self.config_manager.get_backup_path())
        if path:
            self.config_manager.set_backup_path(path)
            self.backup_path_edit.setText(path)
            self.update_log(f"备份路径已设置为: {path}\n")
    
    def toggle_auto_start(self, state):
        enabled = state == Qt.Checked
        self.config_manager.set_auto_start(enabled)
        status = "已启用" if enabled else "已禁用"
        self.update_log(f"开机自启动 {status}\n")
    
    def check_auto_start(self):
        enabled = self.config_manager.get_auto_start()
        self.auto_start_check.setChecked(enabled)
        
    def load_close_settings(self):
        """从配置中加载关闭窗口相关的设置"""
        try:
            # 直接访问配置管理器的main_config属性
            if 'skip_close_dialog' in self.config_manager.main_config:
                self.skip_close_dialog = self.config_manager.main_config['skip_close_dialog']
            
            # 加载用户首选的关闭行为
            if 'default_close_action' in self.config_manager.main_config:
                self.default_close_action = self.config_manager.main_config['default_close_action']
        except Exception as e:
            self.logger.error(f"加载关闭设置时出错: {str(e)}")
            # 如果出错，使用默认值
            self.skip_close_dialog = False
            self.default_close_action = 'minimize'
    
    def on_device_detected(self, device_info):
        # 设备检测到后的处理逻辑
        device_path, device_name = device_info
        self.update_log(f"检测到新设备: {device_name} ({device_path})\n")
        
        # 检查是否存在DCIM、PRIVATE、MISC文件夹
        target_folders = self.device_monitor.check_target_folders(device_path)
        if target_folders:
            self.update_log(f"在设备上找到目标文件夹: {', '.join(target_folders)}\n")
            # 显示配置对话框并处理文件操作
            self.process_detected_folders(device_path, target_folders)
        else:
            self.update_log(f"在设备上未找到目标文件夹\n")
    
    def process_detected_folders(self, device_path, folders):
        # 处理检测到的文件夹（这里是简化版本，后续会实现完整的配置和文件操作流程）
        for folder in folders:
            # 获取或创建配置
            config = self.config_manager.get_folder_config(device_path, folder)
            if not config:
                # 如果没有配置，创建默认配置
                config = self.config_manager.create_default_config(device_path, folder)
                self.update_log(f"为文件夹 {folder} 创建默认配置\n")
            
            # 根据配置决定操作
            if config['backup_strategy'] != 'none':
                # 预览文件
                if config['preview_before_copy']:
                    files_to_copy = self.file_operations.get_files_to_copy(
                        os.path.join(device_path, folder), 
                        os.path.join(self.config_manager.get_backup_path(), folder),
                        config['backup_strategy'] == 'incremental'
                    )
                    
                    if files_to_copy:
                        # 使用文件确认对话框
                        try:
                            dialog = FileConfirmationDialog(self, files_to_copy)
                            # 显示对话框并等待用户选择
                            result = dialog.exec_()
                            
                            # 如果用户点击确认按钮
                            if result == QDialog.Accepted:
                                # 获取用户选中的文件
                                selected_files = dialog.get_selected_files()
                                
                                if selected_files:
                                    # 显示文件预览
                                    self.show_file_preview(selected_files)
                                    self.update_log(f"用户选择了 {len(selected_files)} 个文件进行复制\n")
                                    # 开始复制文件
                                    self.file_operations.start_copy_operation(selected_files)
                                else:
                                    self.update_log(f"用户未选择任何文件进行复制\n")
                            else:
                                # 如果用户关闭对话框或点击取消按钮，默认执行取消复制操作
                                self.update_log(f"用户取消了文件复制操作\n")
                        except Exception as e:
                            self.update_log(f"显示文件确认对话框时发生错误: {str(e)}\n")
                            self.logger.error(f"显示文件确认对话框错误: {str(e)}")
                    else:
                        self.update_log(f"没有文件需要复制到 {folder}\n")
                else:
                    # 不预览，直接复制
                    self.file_operations.start_copy_operation_without_preview(
                        os.path.join(device_path, folder),
                        os.path.join(self.config_manager.get_backup_path(), folder),
                        config['backup_strategy'] == 'incremental'
                    )
            else:
                self.update_log(f"文件夹 {folder} 配置为不备份\n")
    
    def show_file_preview(self, files_to_copy):
        # 显示文件预览
        preview_text = "待复制文件列表:\n\n"
        total_size = 0
        
        for src_path, dest_path in files_to_copy:
            size = os.path.getsize(src_path) if os.path.exists(src_path) else 0
            total_size += size
            size_str = self.format_size(size)
            preview_text += f"{src_path}\n  -> {dest_path}\n  大小: {size_str}\n\n"
        
        preview_text += f"总计: {len(files_to_copy)} 个文件，总大小: {self.format_size(total_size)}"
        self.file_preview_text.setText(preview_text)
        self.update_log(f"显示 {len(files_to_copy)} 个文件的预览\n")
    
    def on_operation_completed(self, result):
        # 处理操作完成事件
        success, message = result
        if success:
            self.update_log(f"文件复制成功: {message}\n")
            QMessageBox.information(self, "操作成功", message)
        else:
            self.update_log(f"文件复制失败: {message}\n")
            QMessageBox.critical(self, "操作失败", message)
    
    def update_log(self, message):
        # 更新日志显示
        self.log_text.append(message)
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
        # 同时写入日志文件
        self.logger.info(message.strip())
    
    def format_size(self, size_bytes):
        # 格式化文件大小
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
    
    def init_system_tray(self):
        """初始化系统托盘"""
        # 创建系统托盘图标
        self.tray_icon = QSystemTrayIcon(self)
        
        # 尝试加载SVG图标
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tray_icon.svg')
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            # 如果SVG图标不存在，使用默认图标
            self.tray_icon.setIcon(self.style().standardIcon(QApplication.MessageBoxInformation))
        
        self.tray_icon.setToolTip('CamSync - 相机文件同步工具')
        
        # 创建托盘菜单
        self.tray_menu = QMenu()
        
        # 显示窗口动作
        self.show_action = QAction('显示窗口', self)
        self.show_action.triggered.connect(self.show_window)
        
        # 退出动作
        self.exit_action = QAction('退出', self)
        self.exit_action.triggered.connect(self.exit_application)
        
        # 添加动作到菜单
        self.tray_menu.addAction(self.show_action)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(self.exit_action)
        
        # 设置托盘菜单
        self.tray_icon.setContextMenu(self.tray_menu)
        
        # 连接信号
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        
        # 显示托盘图标
        self.tray_icon.show()
    
    def on_tray_icon_activated(self, reason):
        # 单击或双击托盘图标都显示窗口
        if reason == QSystemTrayIcon.Trigger or reason == QSystemTrayIcon.DoubleClick:
            self.show_window()
    
    def show_window(self):
        """显示主窗口"""
        self.show()
        self.raise_()  # 提升窗口到前台
        self.activateWindow()  # 激活窗口
    
    def exit_application(self):
        """完全退出应用程序"""
        if self.device_monitor.is_monitoring:
            self.device_monitor.stop_monitoring()
        self.logger.info("CamSync application closed")
        self.tray_icon.hide()
        QApplication.quit()
    
    def closeEvent(self, event):
        # 关闭应用程序时的处理逻辑
        if self.tray_icon.isVisible():
            # 检查是否需要显示关闭确认对话框
            if not self.skip_close_dialog:
                # 创建自定义消息框
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle('关闭确认')
                msg_box.setText('您想如何处理？')
                msg_box.setInformativeText('选择 "最小化到托盘" 将使程序在后台继续运行。\n选择 "直接关闭程序" 将完全退出应用程序。')
                
                # 添加按钮
                minimize_button = msg_box.addButton('最小化到托盘', QMessageBox.AcceptRole)
                exit_button = msg_box.addButton('直接关闭程序', QMessageBox.RejectRole)
                
                # 添加不再询问复选框
                self.skip_close_dialog_check = QCheckBox("不再询问")
                msg_box.setCheckBox(self.skip_close_dialog_check)
                
                # 显示对话框并获取用户选择
                msg_box.exec_()
                
                # 保存用户选择的不再询问设置
                self.skip_close_dialog = self.skip_close_dialog_check.isChecked()
                
                # 确定用户选择的关闭行为
                clicked_button = msg_box.clickedButton()
                selected_action = 'minimize' if clicked_button == minimize_button else 'exit'
                
                # 如果用户勾选了不再询问，保存选择的关闭行为
                if self.skip_close_dialog:
                    self.default_close_action = selected_action
                
                try:
                    # 保存到配置文件
                    self.config_manager.main_config['skip_close_dialog'] = self.skip_close_dialog
                    self.config_manager.main_config['default_close_action'] = self.default_close_action
                    self.config_manager.save_main_config()
                except Exception as e:
                    self.logger.error(f"保存关闭设置时出错: {str(e)}")
                
                # 根据用户选择执行相应操作
                if selected_action == 'minimize':
                    # 最小化到托盘
                    self.hide()
                    self.logger.info("应用程序最小化到系统托盘")
                    event.ignore()
                else:
                    # 直接关闭程序
                    if self.device_monitor.is_monitoring:
                        self.device_monitor.stop_monitoring()
                    self.logger.info("CamSync application closed")
                    event.accept()
            else:
                # 如果用户选择不再询问，使用保存的默认关闭行为
                if self.default_close_action == 'minimize':
                    self.hide()
                    self.logger.info("应用程序最小化到系统托盘")
                    event.ignore()
                else:
                    if self.device_monitor.is_monitoring:
                        self.device_monitor.stop_monitoring()
                    self.logger.info("CamSync application closed")
                    event.accept()
        else:
            # 如果系统托盘不可见，则正常退出
            if self.device_monitor.is_monitoring:
                self.device_monitor.stop_monitoring()
            self.logger.info("CamSync application closed")
            event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    # 设置应用程序样式
    app.setStyle('Fusion')
    
    # 创建并显示主窗口
    window = CamSyncApp()
    window.show()
    
    # 启动应用程序主循环
    sys.exit(app.exec_())