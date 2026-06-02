# WC3 Replay Viewer

A real-time overlay for Warcraft III Reforged replays. Displays hero stats, damage, unit counts and resources as a transparent PyQt6 panel overlaid directly on the game window — no browser involved.

## Quick Start

```
1. Run setup.bat  (first time only — installs Python dependencies)
2. Double-click 启动.bat  (every time)
3. Open WC3 and play a replay — panels appear automatically
```

The overlay hides itself when no game is active and reappears when a replay starts playing.

## Features

- **Hero cards** — portrait, level badge, HP / MP bars, XP bar (gold ★ at max), items (2 × 3 grid), skills (vertical, beside items), damage dealt / received / healed
- **Dead hero** — card shown at reduced opacity
- **Unit tracker** — alive count `N`, deaths `(M)` in red, production queue `+K` in yellow; merged across all players on a team; 2-column grid
- **Resources** — 💰 gold · 🪵 lumber · 🍖 food per player
- **Stable hero order** — first hero recruited stays on top throughout the game
- **Last-game retention** — data from the previous game stays visible until the next one starts
- **1v1 and 2v2** — teams auto-detected; left panel = team A, right panel = team B (mirrored)
- **No OCR / no memory injection** — uses Blizzard's official Observer Shared Memory API

## Requirements

- Windows 10 / 11
- Warcraft III Reforged 1.36+
- [MSYS2](https://www.msys2.org/) with `mingw-w64-ucrt-x86_64-python-pyqt6` installed via pacman
- Python 3.10+ venv (created by `setup.bat`) for the analyzer backend

## Hotkeys

| Hotkey | Action |
|---|---|
| `Ctrl+Shift+F9` | Toggle **interact / passthrough** mode |
| `Ctrl+Shift+F10` | **Hide / show** both panels |
| `Ctrl+Shift+F11` | **Quit** |

## Positioning Panels

1. Press `Ctrl+Shift+F9` to enter **interact mode** (purple border appears).
2. Drag either panel to the desired position.
   - Moving a panel **vertically** syncs both panels automatically.
   - Moving a panel **horizontally** only moves that panel (left/right are independent).
3. Release — position is saved automatically to `overlay_native/config.json`.
4. Press `Ctrl+Shift+F9` again to return to **passthrough mode** (clicks go through to the game).

Positions are restored on the next launch.

## How It Works

```
WC3 Reforged
  └─(shared memory)─► analyzer/reader.py
                            │  WebSocket ws://localhost:8125  (1 s interval)
                            ▼
                      overlay_native/   ← pure PyQt6, no browser
                        panel.py        transparent layered windows
                        controller.py   data → panels
```

`启动.bat` launches everything in one step:
- `overlay_native/__main__.py` starts first (MSYS2 Python with PyQt6)
- It then spawns `python -m analyzer` as a subprocess using the venv Python
- Closing the overlay (or pressing F11) terminates the analyzer automatically

## Project Structure

```
wc3rep/
├── analyzer/               Python backend (WebSocket + shared memory reader)
│   ├── __main__.py
│   ├── server.py           WebSocket ws://8125 (game state push)
│   └── reader.py           war3structs shared memory reader
├── overlay_native/         Native PyQt6 overlay (the only frontend)
│   ├── __main__.py         Entry point + subprocess launcher
│   ├── panel.py            TeamPanel — transparent window + all widgets
│   ├── controller.py       WebSocket data → death tracking → panel render
│   ├── wsclient.py         QWebSocket client (3 s auto-reconnect)
│   ├── deaths.py           Frame-by-frame death inference
│   ├── names.py            Unit name map + helpers
│   ├── icons.py            QPixmap cache (overlay_native/icons/*.jpg)
│   ├── hotkeys.py          WM_HOTKEY via QAbstractNativeEventFilter
│   ├── icons/              ~2 000 unit/hero/item icons from WC3
│   └── config.json         Saved panel positions (auto-created)
├── 启动.bat                 Double-click launcher
└── setup.bat               First-time dependency installer
```

## Compatibility

Tested with WC3 Reforged **1.36** (2026). Uses Blizzard's official `War3StatsObserverSharedMemory` API — no hacks, no memory injection.

## License

MIT
