"""
WC3 Replay Analyzer — Qt Overlay
透明无边框悬浮窗，加载 http://localhost:8126
用法：先启动 python -m analyzer，再运行本脚本
"""

import sys
import ctypes
import ctypes.wintypes
import threading
import time
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import Qt, QUrl, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QColor

user32 = ctypes.windll.user32
GWL_EXSTYLE       = -20
WS_EX_TRANSPARENT = 0x00000020

MOD_NOREPEAT = 0x4000
MOD_CONTROL  = 0x0002
MOD_SHIFT    = 0x0004
VK_X = 0x58
VK_H = 0x48
VK_Q = 0x51
WM_HOTKEY    = 0x0312
HOTKEY_TOGGLE, HOTKEY_HIDE, HOTKEY_QUIT = 1, 2, 3


class HotkeySignals(QObject):
    toggle = pyqtSignal()
    hide   = pyqtSignal()
    quit   = pyqtSignal()


class OverlayWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._click_through = True
        self._visible = True
        self._drag_pos = None
        self._signals = HotkeySignals()
        self._signals.toggle.connect(self._on_toggle)
        self._signals.hide.connect(self._on_hide)
        self._signals.quit.connect(QApplication.quit)

        self._setup_window()
        self._setup_webview()

    # ── 窗口设置 ────────────────────────────────────────────────────────
    def _setup_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        screen = QApplication.primaryScreen().geometry()
        w = int(screen.width()  * 0.82)
        h = int(screen.height() * 0.88)
        x = (screen.width()  - w) // 2
        y = (screen.height() - h) // 2
        self.setGeometry(x, y, w, h)

    def _setup_webview(self):
        self.view = QWebEngineView(self)
        # 不覆盖 WebEngine 背景色，让 HTML 自己的 CSS 背景生效
        self.view.setUrl(QUrl('http://localhost:8126'))
        self.setCentralWidget(self.view)

    # ── 窗口显示后再设置 click-through ─────────────────────────────────
    def showEvent(self, event):
        super().showEvent(event)
        # 延迟一帧确保 HWND 已初始化
        QTimer.singleShot(100, self._apply_click_through)
        QTimer.singleShot(200, self._register_hotkeys)
        QTimer.singleShot(200, self._start_hotkey_listener)

    def _apply_click_through(self):
        hwnd = int(self.winId())
        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        if self._click_through:
            style |= WS_EX_TRANSPARENT
        else:
            style &= ~WS_EX_TRANSPARENT
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)

    # ── 热键 ────────────────────────────────────────────────────────────
    def _register_hotkeys(self):
        hwnd = int(self.winId())
        mods = MOD_CONTROL | MOD_SHIFT | MOD_NOREPEAT
        user32.RegisterHotKey(hwnd, HOTKEY_TOGGLE, mods, VK_X)
        user32.RegisterHotKey(hwnd, HOTKEY_HIDE,   mods, VK_H)
        user32.RegisterHotKey(hwnd, HOTKEY_QUIT,   mods, VK_Q)

    def _unregister_hotkeys(self):
        hwnd = int(self.winId())
        for hid in (HOTKEY_TOGGLE, HOTKEY_HIDE, HOTKEY_QUIT):
            user32.UnregisterHotKey(hwnd, hid)

    def _start_hotkey_listener(self):
        hwnd = int(self.winId())
        def _loop():
            msg = ctypes.wintypes.MSG()
            while self._visible or True:
                if user32.PeekMessageW(ctypes.byref(msg), hwnd, WM_HOTKEY, WM_HOTKEY, 1):
                    hid = msg.wParam
                    if   hid == HOTKEY_TOGGLE: self._signals.toggle.emit()
                    elif hid == HOTKEY_HIDE:   self._signals.hide.emit()
                    elif hid == HOTKEY_QUIT:   self._signals.quit.emit()
                time.sleep(0.05)
        threading.Thread(target=_loop, daemon=True).start()

    # ── 动作 ────────────────────────────────────────────────────────────
    def _on_toggle(self):
        self._click_through = not self._click_through
        self._apply_click_through()
        if self._click_through:
            msg = '○ 穿透模式'
        else:
            msg = '● 交互模式 — 可拖动窗口移动，Ctrl+Shift+X 恢复穿透'
        self.view.page().runJavaScript(_hint_js(msg))

    def _on_hide(self):
        self._visible = not self._visible
        self.setVisible(self._visible)

    def closeEvent(self, event):
        self._unregister_hotkeys()
        super().closeEvent(event)

    # ── 交互模式下拖动移动窗口 ──────────────────────────────────────────
    def mousePressEvent(self, event):
        if not self._click_through and event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if (not self._click_through
                and event.buttons() == Qt.MouseButton.LeftButton
                and self._drag_pos is not None):
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None


def _hint_js(text: str) -> str:
    safe = text.replace("'", "\\'")
    return f"""
(function(){{
  let h = document.getElementById('_qt_hint');
  if (h) h.remove();
  h = document.createElement('div');
  h.id = '_qt_hint';
  h.style.cssText = 'position:fixed;bottom:8px;left:50%;transform:translateX(-50%);'
    + 'background:rgba(0,0,0,0.85);color:#ddd;font-size:11px;padding:4px 14px;'
    + 'border-radius:5px;z-index:99999;pointer-events:none;font-family:monospace;white-space:nowrap;';
  h.textContent = '{safe}';
  document.body.appendChild(h);
  setTimeout(() => h && h.remove(), 3500);
}})();
"""


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('WC3 Overlay')

    win = OverlayWindow()
    win.show()

    def _startup_hint():
        win.view.page().runJavaScript(
            _hint_js('Ctrl+Shift+X 交互/穿透  |  Ctrl+Shift+H 隐藏  |  Ctrl+Shift+Q 退出')
        )
    QTimer.singleShot(2500, _startup_hint)

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
