# -*- coding: utf-8 -*-
# 移植自 overlay/app.js  trackDeaths / getTrackedDeaths
# Observer API 的 total_count 始终 == alive_count，死亡数靠逐帧比较推算


class DeathTracker:
    def __init__(self):
        self._dt: dict  = {}   # "teamKey:unitId" -> {prev, dead}
        self._map: str  = ''
        self._time: int = 0

    def update(self, teams: dict, game_time: int, map_name: str):
        # 换地图或时间倒退（replay seek）→ 清零
        if map_name != self._map or game_time < self._time - 5000:
            self._dt.clear()
        self._map  = map_name
        self._time = game_time

        for tk, players in teams.items():
            seen: set = set()
            for p in players:
                for u in (p.get('units') or []):
                    key = f'{tk}:{u["id"]}'
                    seen.add(key)
                    alive = u.get('alive', 0)
                    if key not in self._dt:
                        self._dt[key] = {'prev': alive, 'dead': 0}
                    else:
                        entry = self._dt[key]
                        if alive < entry['prev']:
                            entry['dead'] += entry['prev'] - alive
                        entry['prev'] = alive

            # 上帧有、这帧消失的单位 → 剩余全部算死亡
            for key, entry in self._dt.items():
                if not key.startswith(tk + ':'):
                    continue
                if key not in seen and entry['prev'] > 0:
                    entry['dead'] += entry['prev']
                    entry['prev'] = 0

    def get_deaths(self, team_key: str) -> dict:
        """返回 {unitId: deaths} 字典，仅包含有死亡记录的单位。"""
        prefix = team_key + ':'
        return {
            k[len(prefix):]: v['dead']
            for k, v in self._dt.items()
            if k.startswith(prefix) and v['dead'] > 0
        }
