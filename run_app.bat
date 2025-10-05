@echo off

REM 简单的CamSync启动脚本

REM 设置中文编码
chcp 65001 >nul

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到Python。请先安装Python 3.8或更高版本。
    pause
    exit /b 1
)

REM 检查src目录是否存在
if not exist "src" (
    echo 错误: 未找到src目录。请确保脚本在正确的位置运行。
    pause
    exit /b 1
)

REM 切换到src目录并启动应用程序
echo 正在启动CamSync应用程序...
cd src
python main.py
cd ..

REM 如果应用程序意外退出，显示错误信息
if %errorlevel% neq 0 (
    echo 错误: CamSync应用程序启动失败。
    echo 请先运行 install_and_run.bat 安装所需依赖。
    pause
    exit /b 1
)