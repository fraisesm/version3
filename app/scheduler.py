from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.database import SessionLocal
from app.models import Task
from app.websocket import ws_manager
from datetime import datetime
import json

scheduler = AsyncIOScheduler()

async def issue_task():
    db = SessionLocal()
    task = db.query(Task).filter(Task.is_sent == False).order_by(Task.id).first()
    if not task:
        return
    task.is_sent = True
    db.commit()
    await ws_manager.broadcast(json.dumps({"type": "new_task", "taskId": task.id}))
    db.close()

def start_scheduler():
    scheduler.add_job(issue_task, "interval", seconds=30)
    scheduler.start()
