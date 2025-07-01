#!/usr/bin/env python3
"""Ultra-condensed Voice Assistant API - Maximum line reduction"""

import os, time, logging
from datetime import datetime
from typing import Dict, Optional
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, Float, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# One-liner database setup
engine = create_engine(os.environ.get("DATABASE_URL", "sqlite:///./voice_assistant.db"))
SessionLocal, Base = sessionmaker(autocommit=False, autoflush=False, bind=engine), declarative_base()

# Ultra-compact model
class CommandLog(Base):
    __tablename__ = "command_logs"
    id = Column(Integer, primary_key=True, index=True)
    command, response = Column(Text, nullable=False), Column(Text, nullable=False)
    source, success = Column(String(50), default="api"), Column(Boolean, default=True)
    processing_time_ms, timestamp = Column(Float), Column(DateTime, default=datetime.utcnow)
    user_id = Column(String(100))

# Compact models
class Req(BaseModel): command: str; source: str = "api"; user_id: Optional[str] = None
class Res(BaseModel): success: bool; response: str; command: str; timestamp: datetime; processing_time_ms: float = 0.0; log_id: Optional[int] = None
class Stats(BaseModel): total: int; success: int; failed: int; avg_time: float = 0.0; recent: Optional[datetime] = None

# Setup
app = FastAPI(title="Voice Assistant API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
Base.metadata.create_all(bind=engine)
start_time = datetime.now()

def get_db(): db = SessionLocal(); yield db; db.close()
def safe_db(db, op): 
    try: return op()
    except Exception as e: raise HTTPException(500, str(e))

@app.get("/")
async def root(): return """<html><body style="font-family:monospace;background:#000;color:#0af;text-align:center;padding:50px">
<h1>JARVIS</h1><div style="width:150px;height:150px;border:2px solid #0af;border-radius:50%;margin:30px auto;display:flex;align-items:center;justify-content:center">🎤</div>
<input id="c" placeholder="Command..." onkeypress="if(event.key==='Enter')fetch('/command',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({command:document.getElementById('c').value})}).then(r=>r.json()).then(d=>document.getElementById('r').innerHTML=d.response)">
<div id="r"></div></body></html>"""

@app.get("/health")
async def health(): return {"status": "ok"}

@app.post("/command", response_model=Res)
async def cmd(req: Req, db: Session = Depends(get_db)):
    start, cmd = time.time(), req.command.lower()
    
    # Ultra-compact command processing
    resp = (f"Time: {datetime.now().strftime('%I:%M %p')}" if any(w in cmd for w in ["time", "clock"]) else
            f"Date: {datetime.now().strftime('%B %d, %Y')}" if any(w in cmd for w in ["date", "today"]) else
            "Hello! I'm JARVIS." if any(w in cmd for w in ["hello", "hi", "hey"]) else
            "I can help with time, date, greetings, and more." if "help" in cmd else
            f"I heard: '{req.command}'. Try asking about time or date.")
    
    processing_time = (time.time() - start) * 1000
    log_id = None
    
    try:
        log = CommandLog(command=req.command, response=resp, source=req.source, processing_time_ms=processing_time, user_id=req.user_id)
        db.add(log); db.commit(); db.refresh(log); log_id = log.id
    except: pass
    
    return Res(success=True, response=resp, command=req.command, timestamp=datetime.now(), processing_time_ms=processing_time, log_id=log_id)

@app.get("/stats", response_model=Stats)
async def stats(db: Session = Depends(get_db)):
    return safe_db(db, lambda: Stats(
        total=(t := db.query(CommandLog).count()),
        success=(s := db.query(CommandLog).filter(CommandLog.success == True).count()),
        failed=t-s,
        avg_time=db.query(func.avg(CommandLog.processing_time_ms)).scalar() or 0.0,
        recent=db.query(func.max(CommandLog.timestamp)).scalar()
    ))

@app.get("/history")
async def history(limit: int = 10, db: Session = Depends(get_db)):
    return safe_db(db, lambda: [{"cmd": c.command, "resp": c.response, "time": c.timestamp} 
                               for c in db.query(CommandLog).order_by(CommandLog.timestamp.desc()).limit(limit)])

if __name__ == "__main__": 
    import uvicorn; uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))