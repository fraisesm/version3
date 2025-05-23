from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class TeamCreate(BaseModel):
    name: str

class TeamResponse(BaseModel):
    name: str
    token: str

class TaskResponse(BaseModel):
    id: int
    filename: str
    content: str
    issued_at: datetime

class SubmissionCreate(BaseModel):
    task_id: int
    answer: str

class SubmissionResponse(BaseModel):
    id: int
    team_id: int
    task_id: int
    status: str
    received_at: datetime

class DashboardResponse(BaseModel):
    team_name: str
    status: str
    submissions: dict