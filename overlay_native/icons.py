# -*- coding: utf-8 -*-
import os
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel

ICONS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), '..', 'overlay', 'icons'))

_cache: dict = {}


def get_pixmap(uid: str, size: int) -> QPixmap:
    key = (uid, size)
    if key in _cache:
        return _cache[key]
    path = os.path.join(ICONS_DIR, f'{uid}.jpg')
    pm = QPixmap(path)
    if not pm.isNull():
        pm = pm.scaled(size, size,
                       Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                       Qt.TransformationMode.SmoothTransformation)
        # crop to exact square
        if pm.width() > size or pm.height() > size:
            x = (pm.width()  - size) // 2
            y = (pm.height() - size) // 2
            pm = pm.copy(x, y, size, size)
    _cache[key] = pm
    return pm


def icon_label(uid: str, size: int) -> QLabel:
    """返回一个固定尺寸的 QLabel，有图用图，无图显示 id 前4字符。"""
    lbl = QLabel()
    lbl.setFixedSize(size, size)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    pm = get_pixmap(uid, size)
    if pm.isNull():
        lbl.setText(uid[:4])
        fs = max(7, size // 6)
        lbl.setStyleSheet(
            f'background:#1a1a2a; border-radius:3px;'
            f'color:#666; font-size:{fs}px;')
    else:
        lbl.setPixmap(pm)
        lbl.setStyleSheet('background:#050510; border-radius:3px;')
    return lbl
