from fastapi import WebSocket
from typing import Dict

class WebSocketManager:
    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}

    async def connect(self, team: str, websocket: WebSocket):
        await websocket.accept()
        self.connections[team] = websocket

    def disconnect(self, team: str):
        self.connections.pop(team, None)

    async def broadcast(self, message: str):
        for ws in self.connections.values():
            await ws.send_text(message)

ws_manager = WebSocketManager()
