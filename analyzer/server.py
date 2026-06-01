"""
WebSocket 服务器 + 内置 HTTP 服务器
- WebSocket: ws://localhost:8125  (推送游戏状态)
- HTTP:       http://localhost:8126 (托管 overlay 前端)
"""
import asyncio
import json
import logging
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler

import websockets
from .reader import GameReader

log = logging.getLogger(__name__)

OVERLAY_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'overlay')


class AnalyzerServer:
    def __init__(self, host='localhost', ws_port=8125, http_port=8126, refresh_ms=1000):
        self._host = host
        self._ws_port = ws_port
        self._http_port = http_port
        self._refresh_ms = refresh_ms
        self._reader = GameReader(refresh_ms=refresh_ms)
        self._clients: set = set()

    def serve(self):
        logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
        log.info('=' * 50)
        log.info('War3 Replay Analyzer 已启动')
        log.info(f'  WebSocket : ws://{self._host}:{self._ws_port}')
        log.info(f'  前端页面  : http://{self._host}:{self._http_port}')
        log.info('=' * 50)
        log.info('请用浏览器打开 http://localhost:8126')
        # 在独立线程启动 HTTP 服务器
        self._start_http_server()
        # 主线程运行 WebSocket 服务器
        asyncio.run(self._ws_main())

    def _start_http_server(self):
        """在后台线程运行 HTTP 服务器，托管 overlay/ 目录"""
        class Handler(SimpleHTTPRequestHandler):
            def __init__(self_, *args, **kwargs):
                super().__init__(*args, directory=OVERLAY_DIR, **kwargs)

            def log_message(self_, *args):
                pass  # 静默 HTTP 日志

            def end_headers(self_):
                self_.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
                self_.send_header('Pragma', 'no-cache')
                self_.send_header('Expires', '0')
                super().end_headers()

            def do_GET(self_):
                # 对 index.html 动态注入版本时间戳，强制浏览器重新加载 JS/CSS
                if self_.path in ('/', '/index.html'):
                    try:
                        import time
                        html_path = os.path.join(OVERLAY_DIR, 'index.html')
                        with open(html_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        # 在 app.js 和 style.css 的引用里加时间戳版本号
                        ts = int(time.time())
                        content = content.replace(
                            'src="app.js"', f'src="app.js?v={ts}"')
                        content = content.replace(
                            'href="style.css"', f'href="style.css?v={ts}"')
                        encoded = content.encode('utf-8')
                        self_.send_response(200)
                        self_.send_header('Content-Type', 'text/html; charset=utf-8')
                        self_.send_header('Content-Length', str(len(encoded)))
                        self_.end_headers()
                        self_.wfile.write(encoded)
                        return
                    except Exception:
                        pass  # 降级为默认处理
                super().do_GET()

        httpd = HTTPServer((self._host, self._http_port), Handler)
        t = threading.Thread(target=httpd.serve_forever, daemon=True)
        t.start()
        log.info(f'HTTP 服务器已启动，托管 {OVERLAY_DIR}')

    async def _ws_main(self):
        async with websockets.serve(self._handler, self._host, self._ws_port):
            log.info('等待 WC3 启动...')
            await asyncio.Future()

    async def _handler(self, ws):
        self._clients.add(ws)
        log.info(f'浏览器连接: {ws.remote_address}')
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
                raise  # 正常断开，向上传递
            except Exception as e:
                log.error(f'读取/发送错误: {e}')
            await asyncio.sleep(interval)
