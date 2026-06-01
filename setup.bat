@echo off
chcp 65001 >nul
echo ============================================
echo  WC3 Replay Analyzer - 首次安装
echo ============================================
echo.

:: 查找 Python（按优先级）
set PYTHON=
where python >nul 2>&1 && set PYTHON=python
if "%PYTHON%"=="" (
    if exist "C:\msys64\ucrt64\bin\python.exe" set PYTHON=C:\msys64\ucrt64\bin\python.exe
)
if "%PYTHON%"=="" (
    if exist "C:\Python312\python.exe" set PYTHON=C:\Python312\python.exe
)
if "%PYTHON%"=="" (
    if exist "C:\Python311\python.exe" set PYTHON=C:\Python311\python.exe
)
if "%PYTHON%"=="" (
    echo [错误] 未找到 Python，请先安装 Python 3.10+
    echo        下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo 使用 Python: %PYTHON%
%PYTHON% --version

echo.
echo 创建虚拟环境 .venv ...
%PYTHON% -m venv .venv
if errorlevel 1 (
    echo [错误] 创建虚拟环境失败
    pause
    exit /b 1
)

:: venv 的 pip 路径（兼容 Windows 和 MSYS2）
set PIP=.venv\Scripts\pip.exe
if not exist %PIP% set PIP=.venv\bin\pip.exe

echo.
echo 安装依赖包（需要网络连接）...
%PIP% install -r requirements.txt
if errorlevel 1 (
    echo [错误] 依赖安装失败，请检查网络连接
    pause
    exit /b 1
)

echo.
echo ============================================
echo  安装完成！运行 start.bat 启动工具
echo ============================================
pause
