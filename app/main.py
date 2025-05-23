from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import json
from typing import Annotated, List
from sqlalchemy.orm import Session
from sqlalchemy import select
from . import models, schemas
from .database import engine, get_db
from .auth import create_access_token, verify_token
from .websocket import ws_manager
from .scheduler import scheduler
from sqlalchemy import true  
from fastapi.responses import HTMLResponse

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    print("Starting scheduler...")
    scheduler.start()
    print("Server ready")

@app.websocket("/ws/{team_name}")
async def websocket_endpoint(websocket: WebSocket, team_name: str):
    await ws_manager.connect(team_name, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(team_name)

@app.post("/register", response_model=schemas.TeamResponse)
async def register_team(
    team: schemas.TeamCreate, 
    db: Annotated[Session, Depends(get_db)]
):
    existing_team = db.scalar(
        select(models.Team).where(models.Team.name == team.name)
    )
    
    if existing_team:
        raise HTTPException(status_code=400, detail="Team already registered")
    
    token = create_access_token(team.name)
    db_team = models.Team(name=team.name, token=token)
    db.add(db_team)
    db.commit()
    return {"name": team.name, "token": token}

@app.get("/task", response_model=schemas.TaskResponse)
async def get_current_task(
    team_name: Annotated[str, Depends(verify_token)],
    db: Annotated[Session, Depends(get_db)]
):
    task = db.scalar(
        select(models.Task)
        .where(models.Task.is_sent.is_(true()))
        .order_by(models.Task.id.desc())
    )
    
    if not task:
        raise HTTPException(status_code=404, detail="No tasks available")
    
    return task

@app.post("/submit", response_model=schemas.SubmissionResponse)
async def submit_solution(
    submission: schemas.SubmissionCreate,
    team_name: Annotated[str, Depends(verify_token)],
    db: Annotated[Session, Depends(get_db)]
):
    task = db.scalar(
        select(models.Task).where(models.Task.id == submission.task_id)
    )
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    team = db.scalar(
        select(models.Team).where(models.Team.name == team_name)
    )
    
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    db_submission = models.Submission(
        team_id=team.id,
        task_id=task.id,
        content=submission.answer,
        status="submitted",
        processing_time=5
    )
    
    db.add(db_submission)
    db.commit()
    
    await ws_manager.broadcast(json.dumps({
        "type": "submission_update",
        "team": team_name,
        "task_id": task.id,
        "status": "submitted"
    }))
    
    return db_submission

@app.get("/dashboard")
async def get_dashboard(db: Annotated[Session, Depends(get_db)]):
    # Получаем все необходимые данные из БД
    teams = db.scalars(select(models.Team)).all()
    tasks = db.scalars(
        select(models.Task)
        .where(models.Task.is_sent.is_(true()))
    ).all()
    
    submissions = db.scalars(select(models.Submission)).all()

    dashboard = []
    
    for team in teams:
        team_data = {
            "team_name": team.name,
            "status": "online" if team.name in ws_manager.connections else "offline",
            "submissions": {}
        }
        
        for task in tasks:
            # Правильное сравнение ID через list comprehension
            team_submissions = [
                s for s in submissions 
                if s.team_id == team.id and s.task_id == task.id # type: ignore
            ]
            
            # Берем последнюю submission если есть
            sub = team_submissions[-1] if team_submissions else None
            
            team_data["submissions"][task.id] = {
                "status": sub.status if sub else "not_started",
                "time": sub.processing_time if sub else None
            }
        
        dashboard.append(team_data)
    
    return dashboard

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head>
            <title>AI Contest Platform</title>
        </head>
        <body>
            <h1>Welcome to AI Contest Platform</h1>
            <p>API documentation: <a href="/docs">Swagger UI</a></p>
            <p>Alternative docs: <a href="/redoc">ReDoc</a></p>
        </body>
    </html>
    """