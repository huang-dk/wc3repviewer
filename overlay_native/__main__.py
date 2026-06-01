# -*- coding: utf-8 -*-
import ctypes, sys, json, os, subprocess

try:
    ctypes.windll.shcore.SetProcessDpiAwarenessContext(-4)
except Exception:
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore    import QTimer
from overlay_native.panel      import TeamPanel
from overlay_native.controller import Controller
from overlay_native.hotkeys    import install as hk_install, uninstall as hk_uninstall

_ROOT = os.path.dirname(os.path.dirname(__file__))   # wc3rep/
_CFG  = os.path.join(os.path.dirname(__file__), 'config.json')

PANEL_W_DEFAULT = 210
PANEL_H_DEFAULT = 820


# ── analyzer 子进程管理 ────────────────────────────────────────────────────
def _start_analyzer() -> subprocess.Popen | None:
    """用 venv Python 启动 analyzer 服务器子进程。"""
    # 兼容 MSYS2 venv（bin/）和 Windows venv（Scripts/）
    for rel in ('.venv/bin/python.exe', '.venv/Scripts/python.exe'):
        venv_py = os.path.normpath(os.path.join(_ROOT, rel))
        if os.path.exists(venv_py):
            proc = subprocess.Popen([venv_py, '-m', 'analyzer'], cwd=_ROOT)
            print(f'[launcher] analyzer started (pid {proc.pid})')
            return proc
    print('[launcher] venv Python not found — start analyzer manually')
    return None


# ── 位置持久化 ─────────────────────────────────────────────────────────────
def _load_cfg() -> dict:
    try:
        with open(_CFG, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def _save_cfg(left: TeamPanel, right: TeamPanel):
    data = {
        'left':  {'x': left.x(),  'y': left.y(),
                  'w': left.width(),  'h': left.height()},
        'right': {'x': right.x(), 'y': right.y(),
                  'w': right.width(), 'h': right.height()},
    }
    os.makedirs(os.path.dirname(_CFG), exist_ok=True)
    with open(_CFG, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


# ── 主程序 ─────────────────────────────────────────────────────────────────
def main():
    # 启动 analyzer 子进程
    analyzer = _start_analyzer()

    app = QApplication(sys.argv)
    app.setApplicationName('WC3 Overlay Native')

    cfg    = _load_cfg()
    screen = QApplication.primaryScreen().geometry()

    ldef = cfg.get('left',  {})
    rdef = cfg.get('right', {})
    lx = ldef.get('x', 10)
    ly = ldef.get('y', 60)
    lw = ldef.get('w', PANEL_W_DEFAULT)
    lh = ldef.get('h', PANEL_H_DEFAULT)
    rx = rdef.get('x', screen.width() - PANEL_W_DEFAULT - 10)
    ry = rdef.get('y', 60)
    rw = rdef.get('w', PANEL_W_DEFAULT)
    rh = rdef.get('h', PANEL_H_DEFAULT)

    left  = TeamPanel(mirror=False)
    right = TeamPanel(mirror=True)
    left._peer  = right
    right._peer = left
    save = lambda: _save_cfg(left, right)
    left._save_cb  = save
    right._save_cb = save

    left.show()
    right.show()
    # show() 后再设置位置：Windows 窗口管理器在首次显示时会重置位置
    QTimer.singleShot(50, lambda: left.setGeometry(lx, ly, lw, lh))
    QTimer.singleShot(50, lambda: right.setGeometry(rx, ry, rw, rh))

    ctrl    = Controller(left, right)
    _hidden = [False]

    def _quit():
        _save_cfg(left, right)
        if analyzer and analyzer.poll() is None:
            analyzer.terminate()
            print('[launcher] analyzer terminated')
        app.quit()

    def on_toggle(): ctrl.toggle_both()
    def on_hide():
        _hidden[0] = not _hidden[0]
        ctrl.hide_both(_hidden[0])

    hk = hk_install(app, on_toggle, on_hide, _quit)

    # 监控 analyzer：子进程意外退出时关闭 overlay
    if analyzer:
        watcher = QTimer()
        watcher.timeout.connect(
            lambda: _quit() if analyzer.poll() is not None else None)
        watcher.start(2000)

    def hint():
        print('WC3 Overlay 已启动（analyzer + overlay 一体）')
        print('  Ctrl+Shift+F9   穿透/交互  |  F10 隐藏  |  F11 退出')

    QTimer.singleShot(400, hint)

    ret = app.exec()
    _save_cfg(left, right)
    hk_uninstall(app, hk)
    sys.exit(ret)


if __name__ == '__main__':
    main()
