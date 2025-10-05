@echo off

REM CamSync 安装和运行脚本

REM 设置中文编码
chcp 65001 >nul

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
echo 错误: 未找到Python。请先安装Python 3.8或更高版本。
pause
exit /b 1
)

REM 安装依赖
pip install -r requirements.txt
if %errorlevel% neq 0 (
echo 错误: 依赖安装失败。请检查网络连接和权限。
echo 尝试使用以下命令手动安装: pip install PyQt5 watchdog psutil pywin32
pause
exit /b 1
)

echo 依赖安装成功！

REM 等待用户选择操作
echo.
echo ===========================
echo 请选择要执行的操作：
echo 1. 启动CamSync应用程序
echo 2. 只安装依赖，不启动程序
echo ===========================
set /p choice="请输入选择 (1/2): "

REM 切换到src目录运行程序
if "%choice%" equ "1" (
echo 启动CamSync应用程序...
cd src
python main.py
cd ..
)

if "%choice%" equ "2" (
echo 依赖已安装完成。
echo 您可以通过运行 "cd src && python main.py" 手动启动应用程序。
)

pause