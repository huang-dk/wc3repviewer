# -*- coding: utf-8 -*-
# TeamPanel  ——  单侧透明悬浮窗口（完整实现）
import ctypes

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGridLayout,
    QFrame, QProgressBar, QScrollArea, QApplication,
    QGraphicsOpacityEffect,
)

from overlay_native.names  import race_key, race_label, fmt_num, pct, filter_abilities
from overlay_native.icons  import icon_label

user32 = ctypes.windll.user32
GWL_EXSTYLE       = -20
WS_EX_TRANSPARENT = 0x00000020
WS_EX_LAYERED     = 0x00080000

PORTRAIT   = 66    # 英雄头像尺寸 px  (44 * 1.5)
UNIT_ICON  = 48    # 单位图标尺寸 px  (32 * 1.5)
ITEM_SIZE  = 24    # 物品格尺寸 px
SKILL_SIZE = 27    # 技能图标尺寸 px


# ── 颜色常量 ──────────────────────────────────────────────────────────────
C_GOLD   = '#f0c050'
C_LUMBER = '#60d060'
C_FOOD   = '#80c0ff'
C_APM    = '#c090ff'
C_ALIVE  = '#d8d8d8'
C_DEAD   = '#cc3030'
C_QUEUE  = '#e0b030'
C_HP0    = '#1a8020';  C_HP1    = '#40c050'
C_MP0    = '#0e50b0';  C_MP1    = '#1878e8'
C_XP0    = '#4a2a80';  C_XP1    = '#8040c0'
C_DMG    = '#ff7060';  C_RCV    = '#60a0ff';  C_HEL = '#50d080'

RACE_STYLE = {
    'HUM': ('background:#1a3860;color:#80b4ff;',),
    'ORC': ('background:#402010;color:#ff9040;',),
    'NE':  ('background:#102030;color:#40d0a0;',),
    'UD':  ('background:#201430;color:#b060ff;',),
    'RAN': ('background:#2a2a2a;color:#aaa;',),
}


def _lbl(text: str, color: str, fs: int = 10, bold: bool = False) -> QLabel:
    w = QLabel(str(text))
    fw = 'bold' if bold else 'normal'
    w.setStyleSheet(
        f'color:{color};font-size:{fs}px;font-weight:{fw};background:transparent;')
    return w


def _bar(frac: float, c0: str, c1: str,
         h: int = 5, w: int = 0, mirror: bool = False) -> QProgressBar:
    b = QProgressBar()
    b.setRange(0, 1000)
    b.setValue(int(frac * 1000))
    b.setTextVisible(False)
    b.setFixedHeight(h)
    if w:
        b.setFixedWidth(w)
    if mirror:
        b.setInvertedAppearance(True)
    r = h // 2
    b.setStyleSheet(f"""
        QProgressBar {{
            background:#1a1a1a; border-radius:{r}px; border:none;
        }}
        QProgressBar::chunk {{
            background:qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 {c0}, stop:1 {c1});
            border-radius:{r}px;
        }}
    """)
    return b


# ── 英雄卡 ────────────────────────────────────────────────────────────────
def _hero_card(hero: dict, mirror: bool) -> QWidget:
    card = QWidget()
    card.setStyleSheet('background:rgba(14,14,24,0.72);border-radius:4px;')
    outer = QVBoxLayout(card)
    outer.setContentsMargins(3, 3, 3, 3)
    outer.setSpacing(2)

    uid    = hero.get('id', '')
    hp_max = hero.get('hitpoints_max', 1) or 1
    mp_max = hero.get('mana_max', 0)
    xp_max = hero.get('experience_max', 1) or 1
    is_dead = (hp_max > 0 and hero.get('hitpoints', 0) == 0)

    # 死亡：整张卡半透明（QGraphicsOpacityEffect，CSS opacity 对 QWidget 无效）
    if is_dead:
        eff = QGraphicsOpacityEffect(card)
        eff.setOpacity(0.55)   # 死亡：比活着暗但仍可见
        card.setGraphicsEffect(eff)

    # ══ 左列：头像 → HP → MP → XP（全部顶部对齐，宽度固定 = PORTRAIT）
    left_col = QVBoxLayout()
    left_col.setSpacing(2)
    left_col.setContentsMargins(0, 0, 0, 0)

    lv_wrap = QWidget()
    lv_wrap.setFixedSize(PORTRAIT, PORTRAIT)
    lv_wrap.setStyleSheet('background:transparent;')
    av = icon_label(uid, PORTRAIT)
    av.setParent(lv_wrap)
    av.move(0, 0)
    if hero.get('level'):
        badge = QLabel(str(hero['level']), lv_wrap)
        badge.setStyleSheet(
            'background:rgba(0,0,0,0.85);color:#f0c050;'
            'font-size:11px;font-weight:bold;padding:0 2px;border-radius:2px;')
        badge.adjustSize()
        badge.move(PORTRAIT - badge.width() - 2, PORTRAIT - badge.height() - 2)

    left_col.addWidget(lv_wrap)
    left_col.addWidget(_bar(pct(hero.get('hitpoints', 0), hp_max),
                            C_HP0, C_HP1, w=PORTRAIT, mirror=mirror))
    if mp_max > 0:
        left_col.addWidget(_bar(pct(hero.get('mana', 0), mp_max),
                                C_MP0, C_MP1, w=PORTRAIT, mirror=mirror))

    # XP 行：进度条宽度 = PORTRAIT，右端对齐血条；满格时金色 + ★
    xp_frac = pct(hero.get('experience', 0), xp_max)
    xp_full  = (xp_frac >= 0.999) or (hero.get('level', 0) >= 10)
    xp_c0, xp_c1 = ('#b07800', '#f0d050') if xp_full else (C_XP0, C_XP1)
    xp_b = _bar(xp_frac, xp_c0, xp_c1, h=4, w=PORTRAIT, mirror=mirror)

    xp_h = QHBoxLayout()
    xp_h.setSpacing(2)
    xp_h.setContentsMargins(0, 0, 0, 0)
    if xp_full:
        star = _lbl('★', '#f0d050', 9, True)  # 满级/满经验标记
        if mirror:
            xp_h.addWidget(xp_b)
            xp_h.addWidget(star)
        else:
            xp_h.addWidget(star)
            xp_h.addWidget(xp_b)
    else:
        xp_h.addWidget(xp_b)   # 无满格时仅条，宽度 = PORTRAIT
    left_col.addLayout(xp_h)
    left_col.addStretch()

    # ══ 物品格 2×3
    items_w = QWidget()
    items_w.setStyleSheet('background:transparent;')
    igrid = QGridLayout(items_w)
    igrid.setContentsMargins(0, 0, 0, 0)
    igrid.setSpacing(2)
    inv = hero.get('inventory') or []
    for r in range(3):
        for c in range(2):
            idx  = r * 2 + c
            item = inv[idx] if idx < len(inv) else None
            if item and item.get('id'):
                slot = icon_label(item['id'], ITEM_SIZE)
                if item.get('charges', 0) > 0:
                    ch = QLabel(str(item['charges']), slot)
                    ch.setStyleSheet(
                        'background:rgba(0,0,0,0.8);color:#ff0;'
                        'font-size:7px;padding:0 1px;')
                    ch.adjustSize()
                    ch.move(ITEM_SIZE - ch.width(), ITEM_SIZE - ch.height())
            else:
                slot = QLabel()
                slot.setFixedSize(ITEM_SIZE, ITEM_SIZE)
                slot.setStyleSheet(
                    'background:rgba(10,10,22,0.90);'
                    'border:1px solid #2a2840;border-radius:2px;')
            igrid.addWidget(slot, r, c)

    # ══ 技能竖列（与物品上下对齐，放物品右侧；镜像时放左侧）
    abils = filter_abilities(hero.get('abilities') or [])
    sk_col_w = QWidget()
    sk_col_w.setStyleSheet('background:transparent;')
    sk_vbox = QVBoxLayout(sk_col_w)
    sk_vbox.setContentsMargins(0, 0, 0, 0)
    sk_vbox.setSpacing(2)
    for a in abils:
        sl = icon_label(a['id'], SKILL_SIZE)
        if a.get('level', 0) > 0:
            b2 = QLabel(str(a['level']), sl)
            b2.setStyleSheet(
                'background:rgba(0,0,0,0.8);color:#f0c050;'
                'font-size:7px;padding:0 1px;')
            b2.adjustSize()
            b2.move(SKILL_SIZE - b2.width(), SKILL_SIZE - b2.height())
        sk_vbox.addWidget(sl)
    sk_vbox.addStretch()

    # 物品 + 技能竖列 横向并排（items | skills 或 skills | items）
    items_skills = QHBoxLayout()
    items_skills.setSpacing(3)
    items_skills.setContentsMargins(0, 0, 0, 0)
    if mirror:
        items_skills.addWidget(sk_col_w, 0, Qt.AlignmentFlag.AlignTop)
        items_skills.addWidget(items_w,  0, Qt.AlignmentFlag.AlignTop)
    else:
        items_skills.addWidget(items_w,  0, Qt.AlignmentFlag.AlignTop)
        items_skills.addWidget(sk_col_w, 0, Qt.AlignmentFlag.AlignTop)

    # ══ 横排：左列（头像/条）| 物品+技能组，整体从左上角起
    top = QHBoxLayout()
    top.setSpacing(4)
    top.setContentsMargins(0, 0, 0, 0)
    if mirror:
        top.addStretch()
        top.addLayout(items_skills)
        top.addLayout(left_col)
    else:
        top.addLayout(left_col)
        top.addLayout(items_skills)
        top.addStretch()
    outer.addLayout(top)

    # ══ 伤害行（底部，完整宽度）
    dmg_w = QWidget()
    dmg_w.setStyleSheet(
        'background:rgba(8,8,15,0.80);border-top:1px solid #1a1a28;')
    dmg_lay = QHBoxLayout(dmg_w)
    dmg_lay.setContentsMargins(3, 1, 3, 1)
    dmg_lay.setSpacing(2)
    if mirror:
        dmg_lay.addStretch()
    for i, (sym, val, color) in enumerate([
        ('⚔',          fmt_num(hero.get('damage_dealt',    0)), C_DMG),
        ('\U0001F6E1', fmt_num(hero.get('damage_received', 0)), C_RCV),
        ('✚',          fmt_num(hero.get('damage_healed',   0)), C_HEL),
    ]):
        if i > 0:
            dmg_lay.addSpacing(6)
        dmg_lay.addWidget(_lbl(f'{sym}{val}', color, 9))
    if not mirror:
        dmg_lay.addStretch()
    outer.addWidget(dmg_w)

    return card


# ── 玩家头部 ──────────────────────────────────────────────────────────────
def _player_header(p: dict, mirror: bool) -> QWidget:
    w = QWidget()
    w.setStyleSheet('background:rgba(20,19,32,0.88);border-radius:4px;')
    lay = QHBoxLayout(w)
    lay.setContentsMargins(5, 3, 5, 3)
    lay.setSpacing(4)

    rk  = race_key(p.get('race', ''))
    rl  = race_label(p.get('race', ''))
    rss = RACE_STYLE.get(rk, RACE_STYLE['RAN'])[0]
    rb  = QLabel(rl)
    rb.setStyleSheet(f'{rss}font-size:9px;font-weight:bold;'
                     'padding:1px 4px;border-radius:2px;')
    rb.setFixedHeight(16)

    name = _lbl(p.get('name', '?'), '#f0d090', 11, True)
    name.setMinimumWidth(0)

    gold  = _lbl(f'💰{p.get("gold",0)}',    C_GOLD,   10)
    lumber= _lbl(f'🪵{p.get("lumber",0)}',  C_LUMBER, 10)
    food  = _lbl(f'🍖{p.get("food",0)}/{p.get("food_max",0)}', C_FOOD, 10)
    apm   = _lbl(f'⚡{p.get("apm",0)}',     C_APM,    10)

    widgets = [rb, name, gold, lumber, food, apm]
    if mirror:
        for ww in reversed(widgets):
            lay.addWidget(ww)
    else:
        for ww in widgets:
            lay.addWidget(ww)

    return w


# ── 玩家名条：名字 + 金/木/人口，无族名，单行紧凑 ──────────────────────────
def _name_bar(p: dict, mirror: bool) -> QWidget:
    name = p.get('name', '')
    if not name:
        return None

    gold  = fmt_num(p.get('gold',     0))
    lumb  = fmt_num(p.get('lumber',   0))
    food  = p.get('food',     0)
    fmax  = p.get('food_max', 0)

    nm = _lbl(name,             '#e0c880', 9, True)
    g  = _lbl(f'\U0001F4B0{gold}',       C_GOLD,   9)   # 💰
    wo = _lbl(f'\U0001FAB5{lumb}',       C_LUMBER, 9)   # 🪵
    fo = _lbl(f'\U0001F356{food}/{fmax}', C_FOOD,  9)   # 🍖

    w = QWidget()
    w.setStyleSheet('background:rgba(16,14,28,0.80);border-radius:3px;')
    lay = QHBoxLayout(w)
    lay.setContentsMargins(4, 2, 4, 2)
    lay.setSpacing(4)

    items = [nm, g, wo, fo]
    if mirror:
        lay.addStretch()           # 内容靠右
        for ww in reversed(items):
            lay.addWidget(ww)
    else:
        for ww in items:
            lay.addWidget(ww)
    return w


# ── 已研究科技行 ──────────────────────────────────────────────────────────
def _upgrades_widget(upgrades: list, mirror: bool) -> 'QWidget | None':
    if not upgrades:
        return None
    counts: dict[str, int] = {}
    for uid in upgrades:
        if uid:
            counts[uid] = counts.get(uid, 0) + 1
    if not counts:
        return None

    w = QWidget()
    w.setStyleSheet('background:transparent;')
    lay = QHBoxLayout(w)
    lay.setContentsMargins(2, 2, 2, 2)
    lay.setSpacing(3)

    if mirror:
        lay.addStretch()
    for uid, count in counts.items():
        wrap = QWidget()
        wrap.setFixedSize(SKILL_SIZE, SKILL_SIZE)
        wrap.setStyleSheet('background:transparent;')
        ico = icon_label(uid, SKILL_SIZE)
        ico.setParent(wrap)
        ico.move(0, 0)
        if count > 1:
            badge = QLabel(str(count), wrap)
            badge.setStyleSheet(
                'background:rgba(0,0,0,0.85);color:#f0c050;'
                'font-size:7px;padding:0 1px;border-radius:2px;')
            badge.adjustSize()
            badge.move(SKILL_SIZE - badge.width(),
                       SKILL_SIZE - badge.height())
        lay.addWidget(wrap)
    if not mirror:
        lay.addStretch()

    return w


# ── 单位格：图标（存活数徽章）+ 可选生产进度条 ────────────────────────────────
def _unit_row(uid: str, alive: int, dead: int, queue: int,
              mirror: bool) -> QWidget:
    w = QWidget()
    w.setStyleSheet('background:transparent;')
    outer = QVBoxLayout(w)
    outer.setContentsMargins(2, 1, 2, 1)
    outer.setSpacing(2)

    # ── 图标行：48px 图标 + 存活数徽章（右下角）+ 死亡数文字 ──
    top = QHBoxLayout()
    top.setSpacing(4)
    top.setContentsMargins(0, 0, 0, 0)

    ico_wrap = QWidget()
    ico_wrap.setFixedSize(UNIT_ICON, UNIT_ICON)
    ico_wrap.setStyleSheet('background:transparent;')
    ico = icon_label(uid, UNIT_ICON)
    ico.setParent(ico_wrap)
    ico.move(0, 0)

    alive_badge = QLabel(str(alive), ico_wrap)
    alive_badge.setStyleSheet(
        'background:rgba(0,0,0,0.85);color:#e0d8c0;'
        'font-size:9px;font-weight:bold;padding:0 2px;border-radius:2px;')
    alive_badge.adjustSize()
    alive_badge.move(UNIT_ICON - alive_badge.width() - 1,
                     UNIT_ICON - alive_badge.height() - 1)

    if mirror:
        top.addStretch()
        if dead > 0:
            top.addWidget(_lbl(f'✝{dead}', C_DEAD, 9, True))
        top.addWidget(ico_wrap)
    else:
        top.addWidget(ico_wrap)
        if dead > 0:
            top.addWidget(_lbl(f'✝{dead}', C_DEAD, 9, True))
        top.addStretch()
    outer.addLayout(top)

    # ── 生产队列：不定态进度条（表示1个正在制造）+ 黄色+N ──
    if queue > 0:
        prod = QHBoxLayout()
        prod.setSpacing(3)
        prod.setContentsMargins(0, 0, 0, 0)

        bar = QProgressBar()
        bar.setRange(0, 0)      # 不定态动画
        bar.setTextVisible(False)
        bar.setFixedHeight(3)
        bar.setStyleSheet("""
            QProgressBar {
                background:#1a1808; border-radius:1px; border:none;
            }
            QProgressBar::chunk {
                background:#c8a060; border-radius:1px;
            }
        """)

        if mirror:
            prod.addStretch()
            if queue > 1:
                prod.addWidget(_lbl(f'+{queue - 1}', C_QUEUE, 9, True))
            prod.addWidget(bar)
        else:
            prod.addWidget(bar)
            if queue > 1:
                prod.addWidget(_lbl(f'+{queue - 1}', C_QUEUE, 9, True))
            prod.addStretch()
        outer.addLayout(prod)

    return w


# ── 等待占位 ──────────────────────────────────────────────────────────────
def _waiting_widget() -> QWidget:
    w = QWidget()
    w.setStyleSheet('background:transparent;')
    return w


# ══════════════════════════════════════════════════════════════════════════
class TeamPanel(QWidget):
    """单侧透明悬浮窗，mirror=False=左侧，mirror=True=右侧（整体镜像）。"""

    def __init__(self, mirror: bool = False, parent=None):
        super().__init__(parent)
        self.mirror          = mirror
        self._click_through  = False
        self._drag_pos       = None
        self._peer: 'TeamPanel | None' = None   # 另一侧面板，拖动时同步
        self._syncing        = False             # 防止递归同步
        self._save_cb        = None              # 拖动结束后持久化位置

        self._setup_window()
        self._build_chrome()
        self.show_waiting()
        self._apply_interact_style()

    # ── 窗口 ──────────────────────────────────────────────────────────────
    def _setup_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet('background:transparent;')

    def _build_chrome(self):
        """搭起窗口骨架：外层 VBox + QScrollArea（内容每次重建）。"""
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)   # 彻底隐藏，去掉右侧竖线
        self._scroll.setStyleSheet(
            'QScrollArea { background:transparent; border:none; }'
            'QScrollArea > QWidget > QWidget { background:transparent; }'
        )
        root.addWidget(self._scroll)

    def _set_content(self, widget: QWidget):
        old = self._scroll.takeWidget()
        if old:
            old.deleteLater()
        self._scroll.setWidget(widget)
        QTimer.singleShot(50, self._fit_height)

    def _fit_height(self):
        """根据内容自动调整窗口高度，最高不超过屏幕剩余空间。"""
        w = self._scroll.widget()
        if not w:
            return
        w.adjustSize()
        need_h = w.sizeHint().height()
        if need_h <= 0:
            return
        screen = QApplication.primaryScreen().geometry()
        max_h  = screen.height() - self.y() - 20
        new_h  = max(60, min(need_h + 6, max_h))
        if abs(new_h - self.height()) > 4:
            self.resize(self.width(), new_h)
            if self._save_cb and not self._syncing:
                self._save_cb()

    # ── 公开渲染接口 ──────────────────────────────────────────────────────
    def show_waiting(self):
        self._set_content(_waiting_widget())

    def render_team(self, players: list, deaths_map: dict):
        if not players:
            self.show_waiting()
            return
        self._set_content(self._build_team(players, deaths_map))

    def _build_team(self, players: list, deaths_map: dict) -> QWidget:
        root = QWidget()
        root.setStyleSheet('background:transparent;')
        lay = QVBoxLayout(root)
        lay.setContentsMargins(3, 3, 3, 3)
        lay.setSpacing(2)

        # ── 每名玩家：名字条 → 英雄卡 → 已研究科技
        for p in players:
            name_bar = _name_bar(p, self.mirror)
            if name_bar:
                lay.addWidget(name_bar)
            for h in (p.get('heroes') or []):
                lay.addWidget(_hero_card(h, self.mirror))
            upgs = _upgrades_widget(p.get('upgrades') or [], self.mirror)
            if upgs:
                lay.addWidget(upgs)

        # ── 单位区（双列网格，节省纵向空间）
        units = self._merge_units(players, deaths_map)
        if units:
            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.HLine)
            sep.setStyleSheet('color:rgba(42,37,53,0.7);')
            lay.addWidget(sep)
            lay.addWidget(self._unit_grid(units))

        lay.addStretch()
        return root

    @staticmethod
    def _merge_units(players: list, deaths_map: dict) -> list:
        merged: dict = {}

        def get(uid):
            if uid not in merged:
                merged[uid] = {'id': uid, 'alive': 0, 'dead': 0, 'queue': 0}
            return merged[uid]

        for p in players:
            for u in (p.get('units') or []):
                e = get(u['id'])
                e['alive'] += u.get('alive', 0)
            for uid, cnt in (p.get('queue') or {}).items():
                get(uid)['queue'] += cnt

        for uid, dead in deaths_map.items():
            get(uid)['dead'] = dead

        return [u for u in merged.values()
                if u['alive'] + u['dead'] + u['queue'] > 0]

    def _unit_grid(self, units: list) -> QWidget:
        """双列网格显示单位，节省纵向空间。镜像时从右列起填。"""
        w = QWidget()
        w.setStyleSheet('background:transparent;')
        grid = QGridLayout(w)
        grid.setContentsMargins(2, 0, 2, 0)
        grid.setSpacing(2)
        for i, u in enumerate(units):
            # mirror: col 1→0→1→0... 内容靠右堆叠
            col = (1 - i % 2) if self.mirror else (i % 2)
            cell = _unit_row(u['id'], u['alive'], u['dead'], u['queue'],
                             self.mirror)
            grid.addWidget(cell, i // 2, col)
        return w

    # ── 穿透 / 交互切换 ───────────────────────────────────────────────────
    def toggle_interact(self):
        self._click_through = not self._click_through
        self._apply_win32()
        if self._click_through:
            self._apply_passthrough_style()
        else:
            self._apply_interact_style()

    def _apply_win32(self):
        hwnd  = int(self.winId())
        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        if self._click_through:
            style |= WS_EX_TRANSPARENT | WS_EX_LAYERED
        else:
            style  = (style & ~WS_EX_TRANSPARENT) | WS_EX_LAYERED
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)

    def _apply_interact_style(self):
        self.setStyleSheet(
            'background:transparent;'
            'border:1px solid rgba(130,100,230,0.7);'
            'border-radius:4px;')

    def _apply_passthrough_style(self):
        self.setStyleSheet('background:transparent;')

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(100, self._apply_win32)

    # ── 拖动（含同步对侧面板）────────────────────────────────────────────────
    def mousePressEvent(self, e):
        if not self._click_through and e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = (e.globalPosition().toPoint()
                              - self.frameGeometry().topLeft())

    def mouseMoveEvent(self, e):
        if (not self._click_through
                and e.buttons() == Qt.MouseButton.LeftButton
                and self._drag_pos is not None):
            new_pos = e.globalPosition().toPoint() - self._drag_pos
            dx = new_pos.x() - self.x()
            dy = new_pos.y() - self.y()
            self.move(new_pos)
            # 只同步 Y 轴（垂直对齐），X 轴各自独立调整
            if self._peer and not self._syncing and dy != 0:
                self._peer._syncing = True
                self._peer.move(self._peer.x(), self._peer.y() + dy)
                self._peer._syncing = False

    def mouseReleaseEvent(self, e):
        self._drag_pos = None

    def moveEvent(self, event):
        """窗口任何移动（拖动/同步）都保存位置。"""
        super().moveEvent(event)
        if self._save_cb and not self._syncing:
            self._save_cb()

    def mouseReleaseEvent(self, e):
        self._drag_pos = None
