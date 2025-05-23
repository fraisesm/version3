from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from datetime import datetime
from .database import Base

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True)
    token = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(50))
    content = Column(Text)
    answer = Column(Text)
    is_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer)
    task_id = Column(Integer)
    content = Column(Text)
    status = Column(String(20), default="pending")
    received_at = Column(DateTime, default=datetime.utcnow)
    processing_time = Column(Integer)