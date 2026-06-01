"""入口：python -m analyzer"""
from .server import AnalyzerServer

server = AnalyzerServer(host='localhost', ws_port=8125, http_port=8126, refresh_ms=1000)
server.serve()
