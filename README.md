# WC3 Replay Viewer

A real-time overlay tool for Warcraft III Reforged replays that displays hero stats, damage dealt/received, unit counts, and resources while watching replays in WC3.

## Features

- **Hero panels** — portraits, level, HP/MP bars, damage dealt / received / healed, kill count, item inventory, abilities
- **Unit tracker** — alive count, death count (tracked frame-by-frame), production queue count, damage stats per unit type
- **Resources** — gold, lumber, food, APM per player
- **Buildings under construction** — with progress bars
- **1v1 and 2v2 support** — teams auto-detected, scales to any n vs n
- **No OCR / no memory injection** — reads Blizzard's official Observer Shared Memory API

## Requirements

- Windows 10/11
- Warcraft III Reforged 1.36+
- Python 3.10+ ([download](https://www.python.org/downloads/))

## Quick Start

```
1. Double-click  setup.bat   (first time only — installs Python dependencies)
2. Double-click  start.bat   (every time you want to use it)
3. Open WC3 and play a replay
4. Browser opens automatically at http://localhost:8126
```

## How It Works

WC3 Reforged exposes a named Windows shared memory segment (`War3StatsObserverSharedMemory`) updated every second with live game state. This tool reads it using the [`war3structs`](https://github.com/sides/war3structs) library, pushes data over a WebSocket, and renders it in a browser overlay.

```
WC3 Reforged ──(shared memory)──► Python backend ──(WebSocket)──► Browser overlay
                                   analyzer/                        overlay/
```

## Project Structure

```
wc3rep/
├── analyzer/               Python backend
│   ├── __main__.py         Entry point: python -m analyzer
│   ├── server.py           WebSocket (ws://8125) + HTTP (http://8126) server
│   └── reader.py           Shared memory reader (war3structs)
├── overlay/
│   ├── index.html
│   ├── app.js              Rendering, death tracker, WebSocket client
│   ├── style.css
│   └── icons/              ~2000 unit/hero/item icons extracted from WC3
├── requirements.txt
├── setup.bat               First-time setup
└── start.bat               Launch script
```

## Ports

| Port | Use |
|---|---|
| `8125` | WebSocket — game state (1 s interval) |
| `8126` | HTTP — overlay UI |

## Compatibility

Tested with WC3 Reforged **1.36** (2026). The observer API compatibility was verified by comparing live shared memory values against known in-game values.

## License

MIT
