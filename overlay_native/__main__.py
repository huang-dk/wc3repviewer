# -*- coding: utf-8 -*-
import ctypes, sys, json, os

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

# ── 配置文件（记忆面板位置）──────────────────────────────────────────────────
_CFG = os.path.join(os.path.dirname(__file__), 'config.json')

PANEL_W_DEFAULT = 210   # 初始宽度；拖动后由 config 覆盖
PANEL_H_DEFAULT = 820


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


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('WC3 Overlay Native')

    cfg    = _load_cfg()
    screen = QApplication.primaryScreen().geometry()

    # ── 默认位置（首次或无 config）
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

    left.setGeometry(lx, ly, lw, lh)
    right.setGeometry(rx, ry, rw, rh)

    # ── 同步拖动 + 持久化
    left._peer   = right
    right._peer  = left
    save = lambda: _save_cfg(left, right)
    left._save_cb  = save
    right._save_cb = save

    left.show()
    right.show()

    ctrl    = Controller(left, right)
    _hidden = [False]

    def on_toggle():
        ctrl.toggle_both()

    def on_hide():
        _hidden[0] = not _hidden[0]
        ctrl.hide_both(_hidden[0])

    def on_quit():
        _save_cfg(left, right)
        app.quit()

    hk = hk_install(app, on_toggle, on_hide, on_quit)

    def hint():
        print('WC3 Overlay Native 已启动')
        print(f'  位置已从 config 读取: L({lx},{ly}) R({rx},{ry})')
        print('  Ctrl+Shift+F9   穿透/交互  |  F10 隐藏  |  F11 退出')
        print('  交互模式下拖动任意面板 → 两侧同步移动，松手自动保存位置')

    QTimer.singleShot(400, hint)

    ret = app.exec()
    _save_cfg(left, right)
    hk_uninstall(app, hk)
    sys.exit(ret)


if __name__ == '__main__':
    main()
