import time
from src.logger import setup_logger
from src.device_monitor import DeviceMonitor

# 设置日志
logger = setup_logger()
logger.info("开始测试设备监控功能...")

# 创建设备监控器实例
monitor = DeviceMonitor()

# 定义信号处理函数
def handle_device_detected(device_info):
    drive_path, drive_name = device_info
    logger.info(f"测试 - 检测到设备: {drive_name} ({drive_path})")

# 连接信号
device_monitor = DeviceMonitor()
device_monitor.device_detected.connect(handle_device_detected)

logger.info("启动设备监控...")
device_monitor.start_monitoring()

# 运行5秒钟进行测试
try:
    logger.info("监控将持续5秒钟...")
    time.sleep(5)
except KeyboardInterrupt:
    logger.info("测试被用户中断")
finally:
    logger.info("停止设备监控...")
    device_monitor.stop_monitoring()
    logger.info("设备监控测试完成")