from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import json
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import Task
from .websocket import ws_manager

scheduler = AsyncIOScheduler()
TASKS_POOL_DIR = "app/tasks_pool"

async def issue_task():
    db = SessionLocal()
    try:
        task = db.scalar(
            select(Task)
            .where(Task.is_sent == False)
            .order_by(Task.id)
        )
        if not task:
            print("All tasks have been issued")
            return

        db.execute(
            update(Task)
            .where(Task.id == task.id)
            .values(is_sent=True)
        )
        db.commit()

        task_data = {
            "task_id": task.id,
            "filename": task.filename,
            "content": json.loads(str(task.content)),
            "issued_at": datetime.utcnow().isoformat()
        }

        await ws_manager.broadcast(json.dumps({
            "type": "new_task",
            "data": task_data
        }))

    except Exception as e:
        print(f"Error issuing task: {str(e)}")
    finally:
        db.close()

def start_scheduler():
    scheduler.add_job(issue_task, "interval", seconds=30)
    scheduler.start()