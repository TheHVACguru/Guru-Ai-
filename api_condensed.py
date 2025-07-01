#!/usr/bin/env python3
"""
Condensed Voice Assistant API - Optimized for fewer lines of code
"""

import logging, time, os
from datetime import datetime
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
import uvicorn

from models_condensed import create_tables, get_db, CommandLog, SystemMetric

# Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Voice Assistant API", description="Condensed voice assistant API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

start_time = datetime.now()

# Condensed Pydantic models with shared config
class BaseResponse(BaseModel):
    class Config:
        json_schema_extra = {"example": {}}

class CommandRequest(BaseModel):
    command: str
    source: str = "api"
    user_id: Optional[str] = None

class CommandResponse(BaseResponse):
    success: bool
    response: str
    command: str
    timestamp: datetime
    processing_time_ms: float = 0.0
    log_id: Optional[int] = None

class StatusResponse(BaseResponse):
    status: str
    version: str
    features: Dict[str, bool]
    uptime_seconds: float
    total_commands: int
    database_status: str

class DatabaseStatsResponse(BaseResponse):
    total_commands: int
    successful_commands: int
    failed_commands: int
    average_processing_time_ms: float = 0.0
    most_recent_command: Optional[datetime] = None

# Database operations helper
class DbOps:
    @staticmethod
    def safe_execute(db: Session, operation, error_msg="Database operation failed"):
        try:
            return operation()
        except Exception as e:
            logger.error(f"{error_msg}: {e}")
            raise HTTPException(status_code=500, detail=error_msg)

    @staticmethod
    def log_command(db: Session, request: CommandRequest, response: str, success: bool, processing_time: float):
        try:
            log = CommandLog(command=request.command, response=response, source=request.source, 
                           success=success, processing_time_ms=processing_time, user_id=request.user_id)
            db.add(log)
            db.commit()
            db.refresh(log)
            return log.id
        except Exception as e:
            logger.error(f"Error logging command: {e}")
            return None

# Initialize database
try:
    create_tables()
    logger.info("Database tables created successfully")
except Exception as e:
    logger.error(f"Error creating database tables: {e}")

@app.on_event("startup")
async def startup():
    db = next(get_db())
    try:
        db.add(SystemMetric(metric_name="server_startup", metric_value=1.0, metric_unit="count"))
        db.commit()
        logger.info("Startup logged")
    except Exception as e:
        logger.error(f"Startup logging failed: {e}")
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
@app.head("/")
async def root():
    return """<!DOCTYPE html><html><head><title>JARVIS</title><style>
    body{font-family:monospace;background:#000;color:#00d4ff;text-align:center;padding:50px}
    .reactor{width:200px;height:200px;border:3px solid #00aaff;border-radius:50%;margin:50px auto;
    display:flex;align-items:center;justify-content:center;animation:glow 2s infinite}
    @keyframes glow{0%,100%{box-shadow:0 0 20px #00aaff}50%{box-shadow:0 0 40px #00ffaa}}
    input{background:#001122;color:#00d4ff;border:1px solid #00aaff;padding:10px;margin:10px;width:300px}
    button{background:#003366;color:#00d4ff;border:1px solid #00aaff;padding:10px 20px;cursor:pointer}
    </style></head><body><h1>JARVIS - Voice Assistant</h1><div class="reactor">🎤</div>
    <input id="cmd" placeholder="Type command..." onkeypress="if(event.key==='Enter')send()">
    <button onclick="send()">Execute</button><div id="response"></div>
    <script>
    function send(){
        const cmd=document.getElementById('cmd').value;
        fetch('/command',{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({command:cmd})}).then(r=>r.json()).then(d=>
        document.getElementById('response').innerHTML='<p>'+d.response+'</p>');
    }
    </script></body></html>"""

@app.get("/health")
@app.head("/health")
async def health(): return {"status": "ok"}

@app.get("/status", response_model=StatusResponse)
async def status(db: Session = Depends(get_db)):
    uptime = (datetime.now() - start_time).total_seconds()
    total_commands = DbOps.safe_execute(db, lambda: db.query(CommandLog).count())
    return StatusResponse(
        status="running", version="1.0.0", 
        features={"text_processing": True, "database_logging": True, "voice_synthesis": False},
        uptime_seconds=uptime, total_commands=total_commands, database_status="connected"
    )

@app.post("/command", response_model=CommandResponse)
async def process_command(request: CommandRequest, db: Session = Depends(get_db)):
    start = time.time()
    cmd = request.command.lower().strip()
    
    # Command processing with condensed logic
    responses = {
        ("time", "what time", "current time"): lambda: f"Current time: {datetime.now().strftime('%I:%M %p on %B %d, %Y')}",
        ("date", "what date", "today"): lambda: f"Today: {datetime.now().strftime('%A, %B %d, %Y')}",
        ("hello", "hi", "hey"): lambda: "Hello! I'm JARVIS, your AI assistant.",
        ("joke", "funny"): lambda: ["Why don't atoms trust electrons? They're always negative!", 
                                   "I told my computer a joke about UDP... but it didn't get it."][hash(cmd) % 2],
        ("help", "commands"): lambda: "I can help with: time/date, greetings, jokes, math, and system status."
    }
    
    response = "I heard you. Try asking about time, date, or say 'help' for commands."
    success = True
    
    try:
        for keywords, func in responses.items():
            if any(phrase in cmd for phrase in keywords):
                response = func()
                break
        
        # Simple math
        if "+" in cmd:
            try:
                parts = [float(p.strip().split()[-1 if i==0 else 0]) for i, p in enumerate(cmd.split("+")[:2])]
                response = f"{parts[0]} + {parts[1]} = {sum(parts)}"
            except: pass
            
    except Exception as e:
        response = f"Error: {str(e)}"
        success = False
    
    processing_time = (time.time() - start) * 1000
    log_id = DbOps.log_command(db, request, response, success, processing_time)
    
    return CommandResponse(success=success, response=response, command=request.command, 
                         timestamp=datetime.now(), processing_time_ms=processing_time, log_id=int(log_id) if log_id else None)

@app.get("/commands/history")
async def history(limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    return DbOps.safe_execute(db, lambda: [
        {"id": c.id, "command": c.command, "response": c.response, "success": c.success, 
         "timestamp": c.timestamp, "processing_time_ms": c.processing_time_ms or 0.0}
        for c in db.query(CommandLog).order_by(CommandLog.timestamp.desc()).offset(offset).limit(limit).all()
    ])

@app.get("/commands/stats", response_model=DatabaseStatsResponse)
async def stats(db: Session = Depends(get_db)):
    return DbOps.safe_execute(db, lambda: DatabaseStatsResponse(
        total_commands=(total := db.query(CommandLog).count()),
        successful_commands=(success := db.query(CommandLog).filter(CommandLog.success == True).count()),
        failed_commands=total - success,
        average_processing_time_ms=db.query(func.avg(CommandLog.processing_time_ms)).scalar() or 0.0,
        most_recent_command=db.query(func.max(CommandLog.timestamp)).scalar()
    ))

@app.delete("/commands/clear")
async def clear(db: Session = Depends(get_db)):
    return DbOps.safe_execute(db, lambda: (
        (count := db.query(CommandLog).count()),
        db.query(CommandLog).delete(),
        db.commit(),
        {"message": f"Cleared {count} commands"}
    )[-1])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))