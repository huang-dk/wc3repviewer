# CLAUDE.md — WC3 Replay Viewer

This file documents the codebase for AI assistants (Claude) working on this project.

## What this project does

Reads Warcraft III Reforged's **Observer Shared Memory API** (`War3StatsObserverSharedMemory`) in real-time while a replay is playing, and renders a browser overlay with game statistics.

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

The Observer API does NOT track unit deaths (`total_count == alive_count` always). Deaths are computed in `overlay/app.js`:

```javascript
// _dt: { "teamKey:unitId": {prev, dead} }
// On each frame: if alive < prev → dead += diff
// If unit disappears from units_on_map → remaining prev units died
```

Reset when `map_name` changes or `game_time` goes backwards (replay seek).

## File descriptions

### `analyzer/reader.py`
- `GameReader` class — main entry point
- `activate(ms)` — writes refresh rate to shared memory (must be called every read)
- `_find_player_slots()` — scans first 24 slots, reads only 50 bytes each to check type byte
- `_player_to_dict()` — converts parsed player to JSON-serializable dict, includes `queue` dict from `researches_in_progress`

### `analyzer/server.py`
- `AnalyzerServer` — runs two servers in one process:
  - `asyncio`/`websockets` on port 8125 for game state push (1 s interval)
  - `threading.Thread` + `http.server.HTTPServer` on port 8126 for static files
- HTTP handler overrides `do_GET` to inject a timestamp version into `index.html` script tags → prevents browser caching of `app.js`/`style.css`
- HTTP handler also sends `Cache-Control: no-store` on all responses

### `overlay/app.js`
Key functions:
- `trackDeaths(teams, gameTime, mapName)` — updates `_dt` death tracker each frame
- `buildUnits(players, container, teamKey)` — renders center panel unit rows
- `buildHeroCard(hero)` — renders one hero card with portrait, bars, damage, items, abilities
- `buildPlayerCard(player)` — renders one player card (resources + heroes + construction)
- `render(state)` — full re-render each WebSocket message (1 s)
- `unitName(id)` — looks up Chinese name; falls back to raw ID

### `overlay/icons/`
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
2. **Browser caches JS** — the server dynamically injects `?v=<timestamp>` into script tags on every page load.
3. **`edcm`** = Druid of the Claw morphed (Bear Form) — different ID from `edoc`.
4. **`ubsp`** = Obsidian Destroyer (upgraded from `uobs`).
5. **`ocat`** = Demolisher (Orc siege weapon), NOT Catapult.
6. **`ospw`** = Spirit Walker, NOT Demolisher.
7. Night Elf buildings: `eaom`=AncientOfWar, `etoa`=TreeOfAges, `etol`=TreeOfLife (not reversed).

## Development

```bash
# Start server with live Python changes
python -m analyzer

# Browser: http://localhost:8126
# Edit overlay/app.js or overlay/style.css → new-tab the browser (cache-busting kicks in)
```

## Dependencies

| Package | Purpose |
|---|---|
| `war3structs` | Parse ObserverGame/ObserverPlayer from shared memory |
| `websockets` | Async WebSocket server |
| `construct` | Binary parsing (war3structs dependency) |
| `lark-parser` | Grammar parsing (war3structs dependency) |
