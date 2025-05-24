from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.auth import create_token, verify_token
from app.database import SessionLocal, init_db
from app.models import Team, Task, Submission
from app.websocket import ws_manager
from app.scheduler import start_scheduler
from datetime import datetime
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    init_db()
    start_scheduler()

@app.post("/teams/login")
def register_team(name: str):
    db = SessionLocal()
    existing = db.query(Team).filter(Team.name == name).first()
    if existing:
        raise HTTPException(400, "Team already exists")
    token = create_token(name)
    team = Team(name=name, token=token)
    db.add(team)
    db.commit()
    return {"token": token}

@app.get("/teams/count")
async def team_count():
    return {"count": len(ws_manager.connections)}

@app.websocket("/ws/{team_name}")
async def ws(team_name: str, websocket: WebSocket):
    await ws_manager.connect(team_name, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(team_name)

@app.get("/task")
async def get_task(team_name: str = Depends(verify_token), db: Session = Depends(SessionLocal)):
    task = db.query(Task).filter(Task.is_sent == True).order_by(Task.id.desc()).first()
    if not task:
        raise HTTPException(404, "No task available")
    return {
        "taskId": task.id,
        "name": task.name,
        "content": json.loads(task.content)
    }

@app.post("/solution")
async def submit_solution(payload: dict, team_name: str = Depends(verify_token), db: Session = Depends(SessionLocal)):
    task_id = payload["taskId"]
    answer = payload["answer"]
    task = db.query(Task).filter(Task.id == task_id).first()
    team = db.query(Team).filter(Team.name == team_name).first()
    if not task or not team:
        raise HTTPException(404, "Task or team not found")
    try:
        data = json.loads(answer)
        assert "selections" in data
    except:
        raise HTTPException(400, "Invalid answer format")
    existing = db.query(Submission).filter(Submission.team_id == team.id, Submission.task_id == task.id).first()
    if existing:
        db.delete(existing)
    processing_time = 5  # можно заменить на расчет разницы по времени, если добавить sent_at
    submission = Submission(
        team_id=team.id,
        task_id=task.id,
        content=answer,
        status="submitted",
        created_at=datetime.utcnow(),
        processing_time=processing_time
    )
    db.add(submission)
    db.commit()
    return {"status": "accepted"}