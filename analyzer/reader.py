"""
Reader: 从 War3StatsObserverSharedMemory 读取游戏状态
兼容 WC3 1.36（已验证）
"""
import mmap
import struct
from war3structs.observer import ObserverGame, ObserverPlayer

SHARED_MEM_NAME = "War3StatsObserverSharedMemory"
ALLOC_GRAN = mmap.ALLOCATIONGRANULARITY

GAME_SIZE   = ObserverGame.sizeof()    # 522
PLAYER_SIZE = ObserverPlayer.sizeof()  # 6416738


def _open_mm(abs_offset, size, write=False):
    seek = abs_offset % ALLOC_GRAN
    return mmap.mmap(
        -1, size + seek,
        SHARED_MEM_NAME,
        offset=abs_offset - seek,
        access=mmap.ACCESS_WRITE if write else mmap.ACCESS_READ,
    ), seek


def activate(refresh_ms: int = 1000):
    """激活 observer API（写入刷新率）"""
    try:
        mm, seek = _open_mm(4, 4, write=True)
        mm.seek(seek)
        mm.write(struct.pack('<I', refresh_ms))
        mm.close()
    except Exception:
        pass  # WC3 还未运行


def _read_raw(abs_offset, size) -> bytes:
    mm, seek = _open_mm(abs_offset, size)
    mm.seek(seek)
    data = mm.read(size)
    mm.close()
    return data


def _hero_to_dict(hero) -> dict:
    return {
        'id':               hero.id,
        'level':            hero.level,
        'experience':       hero.experience,
        'experience_max':   hero.experience_max,
        'hitpoints':        hero.hitpoints,
        'hitpoints_max':    hero.hitpoints_max,
        'mana':             hero.mana,
        'mana_max':         hero.mana_max,
        'damage_dealt':     getattr(hero, 'damage_dealt', 0),
        'damage_received':  getattr(hero, 'damage_received', 0),
        'damage_healed':    getattr(hero, 'damage_healed', 0),
        'kills_count':      getattr(hero, 'kills_count', 0),
        'abilities': [
            {'id': a.id, 'level': a.level}
            for a in hero.abilities
            if a.id and not a.id.startswith('\x00')
        ],
        'inventory': [
            {'id': item.id, 'charges': getattr(item, 'charges', 0)}
            for item in hero.inventory
            if item.id and not item.id.startswith('\x00')
        ],
    }


def _unit_to_dict(unit) -> dict:
    alive = getattr(unit, 'alive_count', 0)
    total = getattr(unit, 'total_count', alive)
    return {
        'id':           unit.id,
        'alive':        alive,
        'total':        total,
        'dead':         max(0, total - alive),
        'dmg_dealt':    getattr(unit, 'damage_dealt', 0),
        'dmg_received': getattr(unit, 'damage_received', 0),
    }


def _building_to_dict(b) -> dict:
    return {
        'id':       b.id,
        'progress': getattr(b, 'progress', 100),
        'upgrade_progress': getattr(b, 'upgrade_progress', 0),
    }


def _player_to_dict(player) -> dict:
    # 生产队列：researches_in_progress 实际存放正在训练的单位 ID
    # 每种单位记录：count（队列中数量）+ progress（当前正在制造那个的进度%）
    # progress_percent 与游戏内建筑生产进度条一致；取同类中最大值=正在制造的那个
    queue: dict[str, dict] = {}
    for r in player.researches_in_progress:
        uid = r.id
        if uid and not uid.startswith('\x00'):
            prog = getattr(r, 'progress_percent', 0)
            e = queue.get(uid)
            if e is None:
                queue[uid] = {'count': 1, 'progress': prog}
            else:
                e['count'] += 1
                if prog > e['progress']:
                    e['progress'] = prog

    return {
        'name':       player.name,
        'race':       str(player.race),
        'id':         player.id,
        'team_index': player.team_index,
        'color':      player.team_color,
        'gold':       player.gold,
        'lumber':     player.lumber,
        'food':       player.food,
        'food_max':   player.food_max,
        'apm':        player.apm,
        'heroes':     [_hero_to_dict(h) for h in player.heroes],
        'units':      [_unit_to_dict(u) for u in player.units_on_map],
        'buildings':  [_building_to_dict(b) for b in player.buildings_on_map],
        'upgrades':   [u.id for u in player.upgrades_completed if u.id],
        'queue':      queue,   # {'ucry': {'count': 2, 'progress': 47}, ...}
    }


class GameReader:
    """主读取器：读取完整游戏状态"""

    def __init__(self, refresh_ms: int = 1000):
        self._refresh_ms = refresh_ms
        activate(refresh_ms)
        self._last_state = {'game': {'is_in_game': False}, 'teams': {}}
        self._player_slots: list[int] = []  # 缓存有效 slot 索引

    def read(self) -> dict:
        """读取并返回完整游戏状态字典（可直接序列化为 JSON）"""
        # 每次读取前重新写入 refresh_rate，避免 WC3 重开游戏后清零
        activate(self._refresh_ms)
        try:
            game_raw = _read_raw(4, GAME_SIZE)
            game = ObserverGame.parse(game_raw)
        except Exception as e:
            return {'game': {'is_in_game': False, 'error': str(e)}, 'teams': {}}

        game_dict = {
            'is_in_game':    bool(game.is_in_game),
            'game_time':     game.game_time,
            'players_count': game.players_count,
            'map_name':      game.map_name,
            'game_name':     game.game_name,
        }

        if not game.is_in_game:
            self._player_slots = []
            return {'game': game_dict, 'teams': {}}

        # 如果玩家数量变化则重新查找 slot
        if len(self._player_slots) != game.players_count:
            self._player_slots = self._find_player_slots(game.players_count)

        # 读取所有玩家数据并按队伍分组
        teams: dict[str, list] = {}
        for slot in self._player_slots:
            try:
                abs_off = 4 + GAME_SIZE + PLAYER_SIZE * slot
                raw = _read_raw(abs_off, PLAYER_SIZE)
                player = ObserverPlayer.parse(raw)
                pdict = _player_to_dict(player)
                team_key = str(player.team_index)
                teams.setdefault(team_key, []).append(pdict)
            except Exception:
                pass

        self._last_state = {'game': game_dict, 'teams': teams}
        return self._last_state

    def _find_player_slots(self, count: int) -> list[int]:
        """
        遍历前24个 slot，只读 header 前 50 字节检查 type 字段。
        type 字节偏移 = 41（name36 + race_pref1 + race1 + id1 + team1 + color1 = 41）
        type: 1=PLAYER, 2=COMPUTER, 4=observer/Blizzard, 0=空
        """
        slots = []
        for i in range(24):
            if len(slots) >= count:
                break
            try:
                abs_off = 4 + GAME_SIZE + PLAYER_SIZE * i
                header = _read_raw(abs_off, 50)   # 只读 50 字节
                ptype = header[41]
                if ptype in (1, 2):               # PLAYER or COMPUTER
                    slots.append(i)
            except Exception:
                pass
        return slots
