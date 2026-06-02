# CLAUDE.md — WC3 Replay Viewer

This file documents the codebase for AI assistants (Claude) working on this project.

## What this project does

Reads Warcraft III Reforged's **Observer Shared Memory API** (`War3StatsObserverSharedMemory`) in real-time while a replay is playing, and renders a transparent **PyQt6 overlay** (`overlay_native/`) with game statistics directly over the game window.

The analyzer (`analyzer/`) reads shared memory and pushes game state over a WebSocket (`ws://localhost:8125`); the PyQt6 frontend (`overlay_native/`) connects to it and draws the panels. There is no browser frontend or HTTP server — those were removed.

## Verified facts about WC3 1.36

- Shared memory name: `War3StatsObserverSharedMemory`
- To activate: write a `uint32` refresh rate (ms) to absolute offset `4`
- **Without writing the refresh rate each poll cycle, WC3 clears the data.** The `activate()` call in `reader.py` must run on every `read()`.
- `ObserverGame.sizeof()` = 522 bytes (verified correct for 1.36)
- `ObserverPlayer.sizeof()` = 6,416,738 bytes (each player slot is ~6 MB)
- Player slot `i` starts at absolute offset: `4 + 522 + 6416738 * i`
- Player type byte is at offset `41` within each player slot (1 = PLAYER, 2 = COMPUTER)

## Key data structures (war3structs)

### ObserverGame (522 bytes at abs offset 4)
| Field | Type | Offset |
|---|---|---|
| refresh_rate | uint32 | 0 |
| is_in_game | bool/byte | 4 |
| game_time | uint32 (ms) | 5 |
| players_count | byte | 9 |
| game_name | string[256] | 10 |
| map_name | string[256] | 266 |

### ObserverPlayerHero — damage fields verified working
- `damage_dealt` — total damage this hero has dealt this game
- `damage_received` — total damage received
- `damage_healed` — total healing provided
- `kills_count` — total units killed

### ObserverPlayerUnit — per unit-type stats
- `alive_count` — currently alive
- `total_count` — **always equals `alive_count`** (does NOT track deaths)
- `damage_dealt`, `damage_received` — cumulative damage for this unit type

### Production queue
`player.researches_in_progress` contains unit IDs currently being trained (not just tech research). Aggregate by unit ID to get queue counts.

## Death tracking — important implementation note

The Observer API does NOT track unit deaths (`total_count == alive_count` always). Deaths are computed client-side in `overlay_native/deaths.py` (driven each frame by `overlay_native/controller.py`):

```
# tracker: { "teamKey:unitId": {prev, dead} }
# On each frame: if alive < prev → dead += diff
# If unit disappears from units_on_map → remaining prev units died
```

Reset when `map_name` changes or `game_time` goes backwards (replay seek).

## File descriptions

### `analyzer/reader.py`
- `GameReader` class — main entry point
- `activate(ms)` — writes refresh rate to shared memory (must be called every read)
- `_find_player_slots()` — scans first 24 slots, reads only 50 bytes each to check type byte
- `_player_to_dict()` — converts parsed player to JSON-serializable dict, includes `queue` dict from `researches_in_progress`

### `analyzer/server.py`
- `AnalyzerServer` — single `asyncio`/`websockets` server on port 8125 that pushes game state to connected clients (1 s interval). No HTTP server (the browser overlay was removed).

### `overlay_native/` (PyQt6 frontend — the only frontend)
- `__main__.py` — entry point; spawns `python -m analyzer` as a subprocess, creates the panels, installs hotkeys
- `panel.py` — `TeamPanel`: transparent layered window + all widgets (hero cards, unit grid, resources)
- `controller.py` — consumes WebSocket messages, runs death tracking, triggers panel re-render each frame
- `wsclient.py` — `QWebSocket` client with 3 s auto-reconnect to `ws://localhost:8125`
- `deaths.py` — frame-by-frame death inference (see "Death tracking" above)
- `names.py` — unit name lookup (Chinese names); falls back to raw ID
- `icons.py` — lazy `QPixmap` cache; loads from `overlay_native/icons/*.jpg`
- `hotkeys.py` — native `WM_HOTKEY` registration via `QAbstractNativeEventFilter`
- `config.json` — saved panel positions (auto-created)

### `overlay_native/icons/`
~2000 `.jpg` files named by WC3 unit rawcode (e.g., `Hamg.jpg`, `hfoo.jpg`).  
Extracted from WC3 CASC storage using `tools/extract_icons_pure.py` (not included in this repo).  
Icon format: 64×64 JPEG.

## Unit ID reference

Unit IDs come from `war3.w3mod:units/unitui.slk` (read from WC3 CASC).

Key melee units:
- Human: `hpea` `hfoo` `hrif` `hkni` `hmpr` `hsor` `hmtm` `hgry` `hgyr` `hspt`
- Orc: `opeo` `ogru` `ocat`(Demolisher) `oshm` `ospw`(SpiritWalker) `otau` `owyv` `odoc` `ohun` `otbr`
- Night Elf: `ewsp` `earc` `esen`(Huntress) `edry` `emtg` `edot` `edoc` `edcm`(BearForm) `ehip` `echm`
- Undead: `uaco`(Acolyte) `ugho` `uabo` `ucry` `uban` `unec` `ugar` `ufro` `umtw` `ushd` `uobs` `ubsp`(Destroyer)

## Common gotchas

1. **`is_in_game` stays False** if `activate()` is not called before each read — WC3 clears the data between polls.
2. **`edcm`** = Druid of the Claw morphed (Bear Form) — different ID from `edoc`.
3. **`ubsp`** = Obsidian Destroyer (upgraded from `uobs`).
4. **`ocat`** = Demolisher (Orc siege weapon), NOT Catapult.
5. **`ospw`** = Spirit Walker, NOT Demolisher.
6. Night Elf buildings: `eaom`=AncientOfWar, `etoa`=TreeOfAges, `etol`=TreeOfLife (not reversed).

## Development

```bash
# Run the full app (overlay + analyzer subprocess); double-click 启动.bat, or:
python -m overlay_native

# Run only the analyzer backend (WebSocket on ws://localhost:8125):
python -m analyzer
```

PyQt6 must come from an interpreter that actually has it installed. On the dev
machine the `.venv` (MSYS2 Python) lacks PyQt6, so the overlay is launched with
the system Python instead — see the `run-wc3overlay` skill in `.claude/skills/`
for the exact launch/restart sequence.

## Dependencies

| Package | Purpose |
|---|---|
| `war3structs` | Parse ObserverGame/ObserverPlayer from shared memory |
| `websockets` | Async WebSocket server |
| `construct` | Binary parsing (war3structs dependency) |
| `lark-parser` | Grammar parsing (war3structs dependency) |
