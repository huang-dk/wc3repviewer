# -*- coding: utf-8 -*-
from overlay_native.wsclient import WsClient
from overlay_native.deaths   import DeathTracker


class Controller:
    def __init__(self, left, right):
        self._left   = left
        self._right  = right
        self._deaths = DeathTracker()
        # 稳定英雄顺序：player_id -> [hero_id, ...]（首次见到的顺序）
        self._hero_order: dict = {}
        self._last_map: str   = ''

        self._ws = WsClient()
        self._ws.state_received.connect(self._on_state)
        self._ws.conn_changed.connect(self._on_conn)
        self._ws.connect()

    def _on_conn(self, connected: bool):
        if not connected:
            self._left.show_waiting()
            self._right.show_waiting()

    def _on_state(self, state: dict):
        game  = state.get('game') or {}
        teams = state.get('teams') or {}
        map_name = game.get('map_name', '')

        # 新地图（新局）→ 清空英雄顺序缓存
        if map_name != self._last_map:
            self._hero_order.clear()
            self._last_map = map_name

        if not game.get('is_in_game'):
            # 没有游戏进行时自动隐藏面板
            self._left.setVisible(False)
            self._right.setVisible(False)
            return

        # 游戏开始 → 恢复显示，并强制回到上次位置（layered window 可能漂移）
        for p in (self._left, self._right):
            if not p.isVisible():
                p.setVisible(True)
                p.move(p.x(), p.y())   # 强制重新定位

        self._deaths.update(teams, game.get('game_time', 0), map_name)

        keys = sorted(teams.keys())
        tk0  = keys[0] if len(keys) > 0 else '0'
        tk1  = keys[1] if len(keys) > 1 else '1'

        self._left.render_team(
            [self._stable_player(p) for p in teams.get(tk0, [])],
            self._deaths.get_deaths(tk0),
        )
        self._right.render_team(
            [self._stable_player(p) for p in teams.get(tk1, [])],
            self._deaths.get_deaths(tk1),
        )

    def _stable_player(self, player: dict) -> dict:
        """
        把 player['heroes'] 替换为稳定顺序的版本：
        首次见到一个英雄就把它追加到该玩家的顺序列表末尾；
        同一英雄后续帧永远保持同一位置。
        """
        pid = str(player.get('id', player.get('name', '')))
        heroes = [h for h in (player.get('heroes') or [])
                  if h.get('id') and h.get('level', 0) > 0]

        if pid not in self._hero_order:
            self._hero_order[pid] = [h['id'] for h in heroes]
        else:
            known = set(self._hero_order[pid])
            for h in heroes:
                if h['id'] not in known:
                    self._hero_order[pid].append(h['id'])

        rank = {hid: i for i, hid in enumerate(self._hero_order[pid])}
        return {**player,
                'heroes': sorted(heroes,
                                  key=lambda h: rank.get(h['id'], 999))}

    def toggle_both(self):
        self._left.toggle_interact()
        self._right.toggle_interact()

    def hide_both(self, hidden: bool):
        self._left.setVisible(not hidden)
        self._right.setVisible(not hidden)
