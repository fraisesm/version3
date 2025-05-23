from fastapi import WebSocket
from typing import Dict
from datetime import datetime
import json
from sqlalchemy import update
from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import Team

class WebSocketManager:
    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}

    async def connect(self, team_name: str, websocket: WebSocket):
        await websocket.accept()
        self.connections[team_name] = websocket
        await self.update_team_status(team_name, True)

    def disconnect(self, team_name: str):
        if team_name in self.connections:
            del self.connections[team_name]
            self.update_team_status_sync(team_name, False)

    async def send_message(self, team_name: str, message: str):
        if team_name in self.connections:
            await self.connections[team_name].send_text(message)

    async def broadcast(self, message: str):
        for connection in self.connections.values():
            await connection.send_text(message)

    async def update_team_status(self, team_name: str, is_online: bool):
        db = SessionLocal()
        try:
            db.execute(
                update(Team)
                .where(Team.name == team_name)
                .values(last_seen=datetime.utcnow())
            )
            db.commit()
            status = "online" if is_online else "offline"
            await self.broadcast(json.dumps({
                "type": "status_update",
                "team": team_name,
                "status": status
            }))
        finally:
            db.close()

    def update_team_status_sync(self, team_name: str, is_online: bool):
        db = SessionLocal()
        try:
            db.execute(
                update(Team)
                .where(Team.name == team_name)
                .values(last_seen=datetime.utcnow())
            )
            db.commit()
        finally:
            db.close()

ws_manager = WebSocketManager()