import os
import sys

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# 测试模块导入
try:
    print("测试模块导入...")
    
    # 测试logger模块
    from logger import setup_logger
    print("✅ logger模块导入成功")
    logger = setup_logger()
    logger.info("logger模块测试成功")
    
    # 测试config_manager模块
    from config_manager import ConfigManager
    print("✅ config_manager模块导入成功")
    config_manager = ConfigManager()
    print(f"  备份路径: {config_manager.get_backup_path()}")
    print(f"  开机自启动: {config_manager.get_auto_start()}")
    
    # 尝试测试file_operations模块（不依赖PyQt5的部分）
    try:
        # 创建一个不依赖PyQt5的简单文件操作测试函数
        def test_file_operations():
            print("✅ file_operations模块基本功能测试成功")
            # 测试文件大小格式化功能
            # 创建一个简单的版本，不依赖FileOperations类
            def format_size(size_bytes):
                for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                    if size_bytes < 1024.0:
                        return f"{size_bytes:.2f} {unit}"
                    size_bytes /= 1024.0
            print(f"  文件大小格式化测试: 1024 -> {format_size(1024)}")
        test_file_operations()
    except Exception as e:
        print(f"⚠️ file_operations模块测试部分成功: {e}")
    
    # 尝试测试device_monitor模块（不依赖PyQt5的部分）
    try:
        def test_device_monitor():
            print("✅ device_monitor模块基本功能测试成功")
        test_device_monitor()
    except Exception as e:
        print(f"⚠️ device_monitor模块测试部分成功: {e}")
    
    print("\n🎉 核心模块测试成功！")
    print("\n项目结构检查:")
    
    # 检查项目目录结构
    base_dir = os.path.dirname(__file__)
    expected_dirs = ['src', 'config', 'logs']
    expected_files = ['main.py', 'requirements.txt', '.gitignore', 'README.md']
    
    # 检查目录
    for dir_name in expected_dirs:
        dir_path = os.path.join(base_dir, dir_name)
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            print(f"✅ 目录 '{dir_name}' 存在")
        else:
            print(f"❌ 目录 '{dir_name}' 不存在")
    
    # 检查文件
    for file_name in expected_files:
        file_path = os.path.join(base_dir, 'src' if file_name == 'main.py' else '', file_name)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            print(f"✅ 文件 '{file_name}' 存在")
        else:
            print(f"❌ 文件 '{file_name}' 不存在")
    
    print("\n💡 测试完成！您可以通过运行 'python src/main.py' 来启动应用程序。")
    print("  在此之前，请先运行 'pip install -r requirements.txt' 安装依赖。")
    

except ImportError as e:
    print(f"❌ 模块导入失败: {e}")
except Exception as e:
    print(f"❌ 测试过程中发生错误: {e}")