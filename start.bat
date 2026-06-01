@echo off
chcp 65001 >nul
echo ============================================
echo  WC3 Replay Analyzer
echo ============================================
echo.

:: 确定 venv 里的 python 路径（兼容 Windows 和 MSYS2）
set VENV_PY=.venv\Scripts\python.exe
if not exist %VENV_PY% set VENV_PY=.venv\bin\python.exe

:: 没有 venv 则先运行 setup
if not exist %VENV_PY% (
    echo 未检测到虚拟环境，开始首次安装...
    call setup.bat
    if errorlevel 1 exit /b 1
)

echo 启动服务器...
echo   WebSocket : ws://localhost:8125
echo   前端页面  : http://localhost:8126
echo.
echo 请在 WC3 里播放 replay，然后在浏览器打开:
echo   http://localhost:8126
echo.
echo 按 Ctrl+C 或关闭此窗口停止服务器
echo.

:: 启动服务器（前台运行，关闭窗口即停止）
%VENV_PY% -m analyzer
