import time
import sys
import os
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMessageBox
from PyQt5.QtGui import QIcon

# 设置中文编码
sys.stdout.reconfigure(encoding='utf-8')

def test_tray_icon():
    """测试系统托盘功能"""
    # 检查系统是否支持系统托盘
    if not QSystemTrayIcon.isSystemTrayAvailable():
        print("错误: 您的系统不支持系统托盘功能")
        return False
    
    # 创建应用程序实例
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # 设置关闭最后一个窗口时不退出应用程序
    
    # 创建托盘图标
    tray = QSystemTrayIcon()
    
    # 尝试加载我们的图标
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'tray_icon.svg')
    if os.path.exists(icon_path):
        print(f"成功加载图标: {icon_path}")
        tray.setIcon(QIcon(icon_path))
    else:
        print(f"警告: 找不到图标文件: {icon_path}")
        # 使用默认图标
        tray.setIcon(app.style().standardIcon(QApplication.MessageBoxInformation))
    
    # 设置托盘提示
    tray.setToolTip('CamSync 测试托盘')
    
    # 显示托盘消息
    tray.show()
    tray.showMessage('CamSync 测试', '托盘图标已显示在系统托盘中', QSystemTrayIcon.Information, 3000)
    
    print("系统托盘图标已显示。请检查系统托盘区域。")
    print("测试将在5秒后自动退出...")
    
    # 等待5秒
    QApplication.processEvents()
    time.sleep(5)
    
    # 清理
    tray.hide()
    print("测试完成")
    return True

if __name__ == '__main__':
    test_tray_icon()