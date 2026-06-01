# overlay_native — 设计与实现记录

> 原目标：用纯 PyQt6 原生控件替代基于浏览器的 overlay，消除 Chromium 合成器灰底问题。
> 本文档同时记录原始方案和最终实现的差异。

---

## 已实现功能

### 启动

```
双击 启动.bat
```

`overlay_native/__main__.py`（MSYS2 Python + PyQt6）启动后自动把
`python -m analyzer`（venv Python）作为子进程拉起。退出 overlay 时同步终止 analyzer。

### 面板布局

两个独立透明窗口，左侧 = 队伍 A，右侧 = 队伍 B（整体镜像）。

```
左侧面板                              右侧面板（镜像）
─────────────────────────            ─────────────────────────
玩家名  💰金  🪵木  🍖人口            人口🍖  木🪵  金💰  玩家名
─────────────────────────            ─────────────────────────
[头像] [物][物] [技]                  [技] [物][物] [头像]
       [物][物] [技]                  [技] [物][物]
       [物][物] [技]                  [技] [物][物]
▓▓▓▓▓░ HP绿                              HP绿 ░▓▓▓▓▓
▓▓▓░░░ MP蓝                              MP蓝 ░░░▓▓▓
Lv5 ▓▓▓░ XP (★ 满格变金色)       XP ░▓▓▓ Lv5 ★
⚔2.3k  🛡1.1k  ✚500              500✚  1.1k🛡  2.3k⚔
─────────────────────────            ─────────────────────────
[图标] N(M)K    [图标] N(M)K        N(M)K [图标]    N(M)K [图标]
...（2 列网格）                      ...（2 列网格，从右列起填）
```

- `N` = 存活（白色），`(M)` = 死亡（红色），`K` = 队列（黄色）
- 死亡英雄卡：`QGraphicsOpacityEffect(0.55)` 半透明
- 英雄顺序：首次见到即锁定，整局不变（`controller._hero_order`）
- 游戏结束后保留数据，下局开始时才刷新
- 无游戏时面板自动隐藏，游戏开始时自动显示

### 热键

| 热键 | 功能 |
|---|---|
| `Ctrl+Shift+F9` | 穿透 ↔ 交互模式切换（交互模式显紫色边框） |
| `Ctrl+Shift+F10` | 隐藏 / 显示 |
| `Ctrl+Shift+F11` | 退出（同时关闭 analyzer 子进程） |

热键通过 `QAbstractNativeEventFilter` 在 Qt 主线程拦截 `WM_HOTKEY`（RegisterHotKey 注册，hwnd=NULL）。

### 面板定位

- 初始位置：屏幕左右边缘
- **交互模式下可拖动**：垂直方向两侧同步，水平方向各自独立
- 松手即写入 `overlay_native/config.json`（`pathlib.Path.resolve()` 保证 MSYS2/Windows 路径一致）
- 重启后从 config 恢复位置（`show()` 后 50ms 通过 `QTimer` 应用，绕开 Windows 首次显示时的位置覆盖）

---

## 文件结构（实际）

```
overlay_native/
  __main__.py     入口 + analyzer 子进程管理 + 位置持久化
  panel.py        TeamPanel — 透明窗口 + 英雄卡 + 单位网格 + 拖动
  controller.py   WebSocket 数据 → 死亡追踪 → 英雄稳定排序 → 面板渲染
  wsclient.py     QWebSocket + 3s 自动重连
  deaths.py       DeathTracker（逐帧比较 alive 推算死亡，含换图/回退重置）
  names.py        UNIT_NAMES + raceKey/raceLabel + fmt_num/pct
  icons.py        QPixmap 缓存，指向 ../overlay/icons/*.jpg，缺图回退文字
  hotkeys.py      HotkeyFilter(QAbstractNativeEventFilter)
  config.json     面板几何（自动创建和更新）
  widgets/
    __init__.py   （空，保留目录）
```

---

## 与原始方案的差异

| 项目 | 原计划 | 实际实现 |
|---|---|---|
| WC3 窗口吸附 | `attach.py` 自动贴 WC3 客户区 | **未实现**；改为手动拖动 + config 记忆位置 |
| 热键 | `Ctrl+Shift+X/H/Q` | `Ctrl+Shift+F9/F10/F11`（原热键被系统占用） |
| 启动方式 | 两个独立进程 | overlay 自动把 analyzer 作为子进程拉起，单命令启动 |
| 控件结构 | `widgets/` 下多个文件 | 全部合并在 `panel.py` 的函数中 |
| 样式 | `style.qss` 文件 | 内联 QSS 字符串 |
| 建造中进度 | 单独区块 | **已移除**（占用空间，用户不需要） |
| 等待占位 | "等待 WC3…" 文字 | 面板直接隐藏，游戏开始再显示 |
| 资源行 | 种族徽章 + 完整资源 | 玩家名 + 💰🪵🍖 紧凑显示，无族名 |
| 英雄技能位置 | 横排在英雄卡底部 | **竖排在物品格右侧**，与物品上沿对齐 |
| 单位显示 | 单列 | **双列网格**，节省纵向空间 |
| 英雄排序 | 按 level 降序 | **首次出现顺序锁定**，整局不变 |
| 游戏结束行为 | 立即隐藏面板 | **保留最后一局数据**，下局开始才刷新 |

---

## 关键技术点

### 透明不发灰
- `WA_TranslucentBackground` + 无边框窗口，不包含任何 QWebEngineView
- 卡片用 `background: rgba(...)` 半透明，窗口空白处完全透明

### 热键正确接收
- 旧方案（background thread + `PeekMessageW(hwnd)`）：后台线程只能看到自己的消息队列，主线程收到的 `WM_HOTKEY` 永远收不到
- 正确方案：`RegisterHotKey(None, ...)` + `QAbstractNativeEventFilter.nativeEventFilter()` 在主线程直接拦截

### 死亡推算
- Observer API `total_count == alive_count` 恒成立（不记录死亡）
- `deaths.py` 逐帧比较 `alive` 变化：`alive < prev` 则 `dead += diff`
- 单位消失（不再出现在 `units_on_map`）：剩余 `prev` 全部计为死亡
- 换地图或 `game_time` 倒退（replay seek）时重置

### 位置持久化可靠性
- `pathlib.Path(__file__).resolve()` 避免 MSYS2 POSIX 路径 vs Windows 路径不一致
- `show()` 后 50ms 再 `setGeometry()`：绕开 Windows 首次显示时窗口管理器覆盖位置的问题
- `moveEvent` 重写：任何移动（拖动/同步）都触发保存，不依赖 `mouseReleaseEvent`
