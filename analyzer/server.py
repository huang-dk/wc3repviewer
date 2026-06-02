"""
WebSocket 服务器
- WebSocket: ws://localhost:8125  (推送游戏状态)
"""
import asyncio
import json
import logging

import websockets
from .reader import GameReader

log = logging.getLogger(__name__)


class AnalyzerServer:
    def __init__(self, host='localhost', ws_port=8125, refresh_ms=1000):
        self._host = host
        self._ws_port = ws_port
        self._refresh_ms = refresh_ms
        self._reader = GameReader(refresh_ms=refresh_ms)
        self._clients: set = set()

    def serve(self):
        logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
        log.info('=' * 50)
        log.info('War3 Replay Analyzer 已启动')
        log.info(f'  WebSocket : ws://{self._host}:{self._ws_port}')
        log.info('=' * 50)
        asyncio.run(self._ws_main())

    async def _ws_main(self):
        async with websockets.serve(self._handler, self._host, self._ws_port):
            log.info('等待 WC3 启动...')
            await asyncio.Future()

    async def _handler(self, ws):
        self._clients.add(ws)
        log.info(f'客户端连接: {ws.remote_address}')
        try:
            await self._push_loop(ws)
        except websockets.exceptions.ConnectionClosedOK:
            pass
        except websockets.exceptions.ConnectionClosedError:
            pass
        except Exception as e:
            log.warning(f'客户端异常: {e}')
        finally:
            self._clients.discard(ws)

    async def _push_loop(self, ws):
        interval = self._refresh_ms / 1000.0
        while True:
            try:
                state = self._reader.read()
                msg = json.dumps(state, default=lambda o: None)
                await ws.send(msg)
            except (websockets.exceptions.ConnectionClosedOK,
                    websockets.exceptions.ConnectionClosedError):
                raise
            except Exception as e:
                log.error(f'读取/发送错误: {e}')
            await asyncio.sleep(interval)
