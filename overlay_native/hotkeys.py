# -*- coding: utf-8 -*-
# 全局热键管理：用 QAbstractNativeEventFilter 在主线程拦截 WM_HOTKEY
import ctypes
import ctypes.wintypes
from PyQt6.QtCore import QAbstractNativeEventFilter

user32 = ctypes.windll.user32

MOD_NOREPEAT = 0x4000
MOD_CONTROL  = 0x0002
MOD_SHIFT    = 0x0004

WM_HOTKEY = 0x0312

VK_F9  = 0x78
VK_F10 = 0x79
VK_F11 = 0x7A

HOTKEY_TOGGLE = 1
HOTKEY_HIDE   = 2
HOTKEY_QUIT   = 3


class HotkeyFilter(QAbstractNativeEventFilter):
    """在 Qt 主线程拦截 WM_HOTKEY，分发到已注册的回调。"""

    def __init__(self):
        super().__init__()
        self._cbs: dict = {}

    def register(self, hotkey_id: int, cb):
        self._cbs[hotkey_id] = cb

    def nativeEventFilter(self, event_type, message):
        if event_type == b'windows_generic_MSG':
            try:
                msg = ctypes.cast(
                    int(message),
                    ctypes.POINTER(ctypes.wintypes.MSG)
                ).contents
                if msg.message == WM_HOTKEY:
                    cb = self._cbs.get(msg.wParam)
                    if cb:
                        cb()
            except Exception:
                pass
        return False, 0


def install(app, on_toggle, on_hide, on_quit) -> HotkeyFilter:
    """
    注册三个热键并把 filter 装到 app 上。
    hwnd=NULL -> WM_HOTKEY 投递到主线程队列 -> filter 拦截到。
    返回 filter 对象（调用方需持有引用，防止被 GC）。
    """
    mods = MOD_CONTROL | MOD_SHIFT | MOD_NOREPEAT
    ok1 = user32.RegisterHotKey(None, HOTKEY_TOGGLE, mods, VK_F9)
    ok2 = user32.RegisterHotKey(None, HOTKEY_HIDE,   mods, VK_F10)
    ok3 = user32.RegisterHotKey(None, HOTKEY_QUIT,   mods, VK_F11)
    print(f'[hotkey] Ctrl+Shift+F9(toggle)={bool(ok1)} '
          f'F10(hide)={bool(ok2)} F11(quit)={bool(ok3)}')

    flt = HotkeyFilter()
    flt.register(HOTKEY_TOGGLE, on_toggle)
    flt.register(HOTKEY_HIDE,   on_hide)
    flt.register(HOTKEY_QUIT,   on_quit)
    app.installNativeEventFilter(flt)
    return flt


def uninstall(app, flt: HotkeyFilter):
    app.removeNativeEventFilter(flt)
    mods = MOD_CONTROL | MOD_SHIFT | MOD_NOREPEAT
    for hid in (HOTKEY_TOGGLE, HOTKEY_HIDE, HOTKEY_QUIT):
        user32.UnregisterHotKey(None, hid)
