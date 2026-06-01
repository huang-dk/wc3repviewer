# 方案：WC3 原生悬浮 UI（overlay_native）

> 目标：用**非 web**、可覆盖在游戏画面上的原生 UI 替代当前的浏览器 overlay。
> 每侧一个贴边透明面板，左队 / 右队，右侧整体镜像。

## 0. 背景与决策

当前已有两套 overlay 实验（`overlay_qt.py` = PyQt6+WebEngine，未跟踪的 `main.js`/`preload.js` = Electron），
两者都把 web overlay（`http://localhost:8126`）塞进透明窗口，都会撞上 Chromium 合成器的"灰底"问题。

**结论：丢掉浏览器内核，用 PyQt6 原生控件（QWidget + QSS）直接绘制。**
Windows 分层窗口（layered window）对纯 Qt 控件支持真正的逐像素 alpha，只要窗口里不放 QWebEngineView 就不发灰。

### 已确认的关键决策

| 项 | 决定 |
|---|---|
| UI 工具包 | **PyQt6 原生控件**（已安装，零额外第三方包） |
| 数据来源 | **保留现有 WebSocket 服务器**（`ws://localhost:8125`），新前端作为另一个客户端 |
| 定位方式 | **自动吸附 WC3 窗口客户区** + 找不到时手动对齐兜底 |
| 内容范围 | **全量移植**（full parity）现 web overlay 的数据 |
| 版面 | **去掉中央面板**，单位数据下沉到各自面板底部 |
| 镜像 | **右侧面板整体镜像**（英雄卡 / 单位行 / 资源行全部翻转、右对齐） |
| WebSocket 客户端 | PyQt6 自带 `QtWebSockets.QWebSocket`，**无新依赖** |
| 全屏 | 用户使用窗口模式（已确认不用独占全屏；独占全屏下任何悬浮窗都不显示） |

## 1. 整体架构

```
[WC3 共享内存] → analyzer/reader.py → analyzer/server.py (ws://localhost:8125, 保留不动)
                                              │  每秒推送 JSON state
                                              ▼
                                   overlay_native/  (新增, 纯 PyQt6)
                                   QWebSocket 收 state → 渲染原生控件
                                   ctypes 吸附 WC3 窗口客户区
```

- 数据层完全不动；新前端只是 8125 的另一个客户端，协议与现 `app.js` 一致。
- 老 web overlay（8126）仍可同时打开，便于对照调试。
- HTTP(8126) 在新方案中不再需要，但保留无害。

## 2. 最终布局

每侧一个独立透明窗口；左窗贴游戏客户区左缘，右窗贴右缘，右窗整体镜像。

```
┌─ 左侧窗口（吸附客户区左缘）──────┐   ┌─ 右侧窗口（吸附右缘, 镜像）─┐
│ [种族] 玩家名 💰金 🪵木 🍖人口 ⚡APM │   │ APM⚡ 人口🍖 木🪵 金💰 玩家名 [种族] │
│ ┌─英雄卡──────────────────────┐ │   │ ┌─英雄卡(镜像)──────────────┐ │
│ │ [头像]      [物][物]         │ │   │ │  [物][物]      [头像]      │ │
│ │             [物][物]         │ │   │ │  [物][物]                  │ │
│ │             [物][物]         │ │   │ │  [物][物]                  │ │
│ │ ▓▓▓▓▓░░ HP绿                 │ │   │ │              HP绿 ░░▓▓▓▓▓  │ │
│ │ ▓▓░░░░░ MP蓝                 │ │   │ │              MP蓝 ░░░░░▓▓  │ │
│ │ Lv5 ▓▓▓░░ 经验               │ │   │ │            经验 ░░▓▓▓ Lv5  │ │
│ │ [技][技][技]                 │ │   │ │                [技][技][技]│ │
│ └──────────────────────────────┘ │   │ └────────────────────────────┘ │
│ （建造中：▓▓░ 60% ...）           │   │           （... 建造中 ...）    │
│ ───────────────────────────────  │   │  ─────────────────────────────  │
│ [icon] 12(3)2                    │   │                    12(3)2 [icon] │
│ [icon] 6(1)                       │   │                      6(1) [icon] │
│ [icon] 5                          │   │                         5 [icon] │
│  (N存活默认色 (M)死亡红 K建造黄)   │   │  (N存活默认色 (M)死亡红 K建造黄)  │
└──────────────────────────────────┘   └────────────────────────────────┘
```

### 2.1 英雄卡版式

**左侧（正常朝向）：**
```
[头像 Lv]      [物][物]      ← 物品 6 格, 2列×3行 (游戏内小键盘式 7/8·4/5·1/2), 紧挨头像
               [物][物]
               [物][物]
▓▓▓▓▓▓░░░░  HP 绿条          ← 头像下方, 整行, 不写数值
▓▓▓░░░░░░░  MP 蓝条          ← 不写数值
Lv5  ▓▓▓▓░░░  经验条         ← 等级数 + 经验条同行
[技][技][技][技]             ← 技能图标行(最底)
```

**右侧（整体镜像）：** 物品在左、头像在右；HP/MP/经验条右对齐；等级数在经验条右侧；技能行右对齐。

规则：
- 头像**正常大小**（≈游戏内大小，配置可调）+ 右下角等级角标。
- **不显示英雄名**。
- HP=绿色条、MP=蓝色条，各一行、在头像下方、**不写数值文字**。
- 经验条单独一行，行内带 `Lv5` 等级数字。
- 造成/承受/治疗伤害：保留（按 full parity；如嫌挤可后续做开关）。
- 物品×6、技能图标保留。

### 2.2 单位行

- 格式：**`N(M)K`**（括号必须保留）
  - `N` = 当前存活，**默认色**
  - `(M)` = 死亡，**括号包裹 + 红色数字**（>0 才显示括号段）
  - `K` = 训练/建造队列，**黄色**（可调，>0 才显示）
- 左侧：`[图标] N(M)K`
- 右侧（镜像）：`N(M)K [图标]`（数字串顺序不变，仅图标移到右侧）
- 示例：存活12/死亡3/建造2 → `12(3)2`；存活6/死亡1 → `6(1)`；仅存活5 → `5`。
- **不显示单位名**（只图标），**不带伤害数字**。
- 一队多玩家（2v2）：上半英雄区按玩家各一张卡，下半单位区合并整队统计。

### 2.3 资源行（玩家头部）

种族徽章 + 玩家名 + 💰金 / 🪵木 / 🍖人口 / ⚡APM。右侧镜像右对齐。

### 2.4 建造中

`progress < 100` 的建筑，进度条列表，放英雄区与单位区之间（沿用原逻辑）。

## 3. 窗口吸附与对齐

- `attach.py`：`EnumWindows` 遍历，标题子串匹配 **"Warcraft III"**（不区分大小写）；
  `config.json` 可用 `window_title` / `window_class` 覆盖。
- 取 **`GetClientRect` + `ClientToScreen`** 得游戏**客户区**屏幕矩形 → 窗口模式下自动排除标题栏/边框。
  - 左窗贴左缘、右窗贴右缘；宽度按客户区宽度比例（默认每侧 ~22%，可调），高度贴满客户区。
- 250ms QTimer 跟随：游戏移动/缩放→重定位；最小化或切到别的前台全屏→隐藏；找回→恢复。
- **三种模式**（config `mode`）：
  - `auto`：跟随游戏客户区 + 可选手动微调偏移（`offset_x/y/w/h`）。
  - `manual`：找不到游戏或主动选择时，用保存的绝对几何，自己拖拽对齐。
  - 自动降级：`auto` 下找不到窗口 → 临时切 `manual` 用上次几何并提示。
- **DPI**：启动设 `PER_MONITOR_AWARE_V2`，按 `devicePixelRatio` 换算 Win32 物理像素 ↔ Qt 逻辑像素，避免错位。

## 4. 交互（沿用 overlay_qt.py 已验证机制）

- 全局热键：
  - `Ctrl+Shift+X` 穿透 / 编辑 切换
  - `Ctrl+Shift+H` 隐藏 / 显示
  - `Ctrl+Shift+Q` 退出
  - `Ctrl+Shift+L` 锁定 / 解锁对齐
- 编辑模式：两侧面板显边框，可拖动 + 缩放，松手即写回 `config.json`。
- 穿透模式：`WS_EX_TRANSPARENT`，鼠标全部穿透到游戏。

## 5. 透明不发灰（核心技术点）

- 顶层窗口：`FramelessWindowHint | WindowStaysOnTopHint | Tool` + `WA_TranslucentBackground`。
- 窗口本体背景全透明；只有卡片 / 行用 QSS `background: rgba(...)` 画半透明底。
- 不放任何 QWebEngineView / Chromium 控件——灰底的根源，原生控件无合成器中间层。

## 6. 渲染策略

- `wsclient` 每秒收 state → `deaths.update(...)` → 控制器把 `teams` 排序：第一队→左窗、第二队→右窗。
- **复用控件、只更新数据**（按玩家 id / 单位 id 复用卡片和行，增量改文字 / 进度 / 图标），
  不每秒重建整棵树，避免闪烁和卡顿。
- 无 `is_in_game` / 未连接：两窗显示精简"等待 WC3…"占位。

## 7. 文件结构（仓库内，复用现有 icons，零新依赖）

```
overlay_native/
  __main__.py        # 入口: python -m overlay_native
  controller.py      # 主控: 建左右两窗 + 吸附定时器 + ws客户端 + 派发渲染 + 热键 + 配置
  panel.py           # 单侧 TeamPanel 窗口: 透明/无边框/穿透 + 上英雄区/下单位区 + mirror 参数
  attach.py          # 找 WC3 窗口 + 客户区跟踪 (ctypes user32) + DPI
  wsclient.py        # PyQt6.QtWebSockets.QWebSocket 封装 + 3s 重连 → state 信号
  deaths.py          # DeathTracker (移植 app.js trackDeaths/getTrackedDeaths)
  names.py           # UNIT_NAMES + raceKey/raceLabel + fmtNum/fmtTime/pct
  icons.py           # QPixmap 缓存加载, 缺图回退文字, 指向 ../overlay/icons
  widgets/
    player_header.py # 种族徽章 + 名字 + 金/木/人口/APM (支持 mirror)
    hero_card.py     # 英雄卡 (移植 buildHeroCard, 支持 mirror)
    unit_row.py      # [图标] N(✝M)+K (支持 mirror)
    build_row.py     # 建造中进度条
  style.qss          # 从 overlay/style.css 移植
  config.json        # mode / 几何 / 偏移 / 不透明度 / 刷新率 / 热键 / 每侧宽度比例 / 窗口匹配串
run_overlay.bat      # 一键起 analyzer 服务器 + overlay_native
```

- 图标**不复制**，`icons.py` 直接指向已有的 `overlay/icons/*.jpg`。

## 8. 移植对照（app.js → 原生）

| app.js | 原生实现 |
|---|---|
| `UNIT_NAMES` / `raceKey` / `raceLabel` / `fmtNum` / `fmtTime` / `pct` | `names.py` 直接搬 |
| `iconEl(id,size)` | `icons.py`: QLabel + QPixmap 缓存 + 缺图回退前 4 字符 |
| `buildHeroCard` | `widgets/hero_card.py`（新版式 + mirror） |
| 资源行 (`buildPlayerCard` 头部) | `widgets/player_header.py` |
| `buildUnits` 合并 / 队列 / 死亡注入 | `widgets/unit_row.py` + 面板下半区聚合 |
| 建造中段 | `widgets/build_row.py` |
| `trackDeaths` / `getTrackedDeaths` | `deaths.py`（含换图 / replay 回退重置） |
| HP/MP/经验/建造进度条 | QFrame 轨道+填充子 QFrame（或样式化 QProgressBar），QSS `qlineargradient` 还原渐变 |
| `style.css` | `style.qss`（rgba 背景、渐变、圆角、内边距、字号 ≈1:1 翻译；flex→QHBox/QVBoxLayout） |

## 9. 数据字段参考（来自 reader.py，state JSON）

- `game`: `is_in_game`, `game_time`(ms), `players_count`, `map_name`, `game_name`
- `teams`: `{ team_index: [player, ...] }`
- `player`: `name`, `race`, `id`, `team_index`, `color`, `gold`, `lumber`, `food`, `food_max`, `apm`,
  `heroes[]`, `units[]`, `buildings[]`, `upgrades[]`, `queue{id:count}`
- `hero`: `id`, `level`, `experience`, `experience_max`, `hitpoints`, `hitpoints_max`,
  `mana`, `mana_max`, `damage_dealt`, `damage_received`, `damage_healed`, `kills_count`,
  `abilities[{id,level}]`, `inventory[{id,charges}]`
- `unit`: `id`, `alive`, `total`(==alive), `dead`(API 恒为 0, 用 DeathTracker 推算), `dmg_dealt`, `dmg_received`
- `building`: `id`, `progress`, `upgrade_progress`

> 注意：Observer API 不记录死亡（`total==alive`），死亡数由 `deaths.py` 按帧比较 `alive` 变化推算。

## 10. 启动与维护

- 开发：分别 `python -m analyzer` 与 `python -m overlay_native`（两进程，因保留服务器）。
- 日常：双击 `run_overlay.bat` 一键起两个进程。
- 依赖：仅 PyQt6（含自带 `QtWebSockets`）+ 已有 war3structs。无浏览器、无 node。

## 11. 开发顺序（每步先调试通过，确认无误再进行下一步）

> 原则：**先把透明 UI 这一最高风险点验证通过**（确保不发灰、置顶、穿透、无任何显示问题），
> 再逐步加吸附、数据、控件细节。每一步都有明确的调试/验收标准，**通过后才进入下一步**。

**第 1 步 — 透明穿透窗口骨架**（`panel.py` + 窗口基础）
- 实现：无边框 + 置顶 + `WA_TranslucentBackground` + `WS_EX_TRANSPARENT` 穿透，放几个假的 `rgba(...)` 卡片占位。
- 调试/验收：窗口空白处**完全透明**、**无灰底**、始终置顶、鼠标穿透到桌面/游戏；切换编辑/穿透模式正常。
- ✅ 通过后再继续。

**第 2 步 — 窗口吸附 + DPI**（`attach.py`）
- 实现：找 "Warcraft III" 客户区矩形，左右窗贴边；250ms 跟随；手动模式兜底。
- 调试/验收：开着游戏，左右窗精准贴客户区边缘；移动/缩放游戏窗口时跟随；最小化→隐藏；找回→恢复；
  不同 DPI 缩放下不错位；找不到窗口时可切手动拖拽对齐并保存。
- ✅ 通过后再继续。

**第 3 步 — 数据链路**（`wsclient.py`）
- 实现：`QWebSocket` 连 `ws://localhost:8125`，3s 重连，收到即解析 JSON。
- 调试/验收：起 `analyzer` 服务器，控制台打印收到的 `state`，字段与 reader.py 一致；断开能自动重连。
- ✅ 通过后再继续。

**第 4 步 — 纯逻辑模块**（`names.py` / `icons.py` / `deaths.py`）
- 实现：名称/工具函数、图标缓存加载+缺图回退、死亡推算。
- 调试/验收：图标按 id 正确加载、缺图回退文字；用一段录制的 state 序列喂 `deaths.py`，死亡数推算正确（含换图/回退重置）。
- ✅ 通过后再继续。

**第 5 步 — 控件 + 样式**（`widgets/*` + `style.qss`）
- 实现：英雄卡（头像+物品2×3+HP绿/MP蓝/经验条+技能）、资源行、单位行（存活默认色/死亡红色/+队列）、建造中条；含右侧 mirror。
- 调试/验收：用假 state 渲染单卡，逐个对照 §2 版式与配色；左右镜像正确；颜色（绿/蓝/红）符合预期。
- ✅ 通过后再继续。

**第 6 步 — 串联**（`controller.py`）
- 实现：双侧渲染、控件复用+增量更新、热键、配置持久化。
- 调试/验收：真实游戏/录像跑通；每秒更新不闪烁不卡；热键全部生效；重启后几何/设置恢复。
- ✅ 通过后再继续。

**第 7 步 — 一键启动**（`run_overlay.bat`）
- 实现：先起 `analyzer`，再起 `overlay_native`。
- 调试/验收：双击启动两进程、正常退出、可重复启动。

## 12. 风险 / 待实测点

- WC3 Reforged 实际窗口标题 / 类名需开着游戏确认（已规划子串匹配 + 配置覆盖兜底）。
- DPI 缩放下 Win32 物理像素与 Qt 逻辑像素的换算，需实测对齐。
- `PyQt6.QtWebSockets` 子模块可用性（PyQt6 通常自带，需确认）。
- 物品 2列×3行 的具体行列方向需对照游戏内物品栏微调（config 常量，易调）。
