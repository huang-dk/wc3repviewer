# -*- coding: utf-8 -*-
import json
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QUrl
from PyQt6.QtWebSockets import QWebSocket
from PyQt6.QtNetwork import QAbstractSocket

WS_URL        = 'ws://localhost:8125'
RECONNECT_MS  = 3000


class WsClient(QObject):
    state_received = pyqtSignal(dict)
    conn_changed   = pyqtSignal(bool)   # True=connected, False=disconnected

    def __init__(self, parent=None):
        super().__init__(parent)
        self._ws = QWebSocket()
        self._ws.connected.connect(self._on_connected)
        self._ws.disconnected.connect(self._on_disconnected)
        self._ws.textMessageReceived.connect(self._on_message)
        self._ws.errorOccurred.connect(self._on_error)

        self._timer = QTimer(singleShot=True)
        self._timer.timeout.connect(self.connect)

    def connect(self):
        if self._ws.state() == QAbstractSocket.SocketState.UnconnectedState:
            self._ws.open(QUrl(WS_URL))

    def _on_connected(self):
        self._timer.stop()
        self.conn_changed.emit(True)
        print(f'[ws] connected {WS_URL}')

    def _on_disconnected(self):
        self.conn_changed.emit(False)
        print(f'[ws] disconnected, retry {RECONNECT_MS}ms')
        self._timer.start(RECONNECT_MS)

    def _on_error(self, err):
        # 连接失败时也触发断开流程
        if self._ws.state() == QAbstractSocket.SocketState.UnconnectedState:
            if not self._timer.isActive():
                self._timer.start(RECONNECT_MS)

    def _on_message(self, text: str):
        try:
            self.state_received.emit(json.loads(text))
        except Exception:
            pass
