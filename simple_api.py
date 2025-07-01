#!/usr/bin/env python3
"""
Simple Voice Assistant API Server
A minimal FastAPI server that provides essential voice assistant functionality.
"""

import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
import uvicorn

from models import create_tables, get_db, CommandLog, SystemMetric, UserPreference

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Voice Assistant API",
    description="A simple voice assistant API providing natural language processing and automation features",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class CommandRequest(BaseModel):
    """Request model for processing voice commands"""
    command: str  # The voice command to process
    source: str = "api"  # Source of the command (api, voice, etc.)
    user_id: Optional[str] = None  # Optional user identifier for tracking
    
    class Config:
        json_schema_extra = {
            "example": {
                "command": "what time is it?",
                "source": "api",
                "user_id": "user123"
            }
        }

class CommandResponse(BaseModel):
    """Response model for processed voice commands"""
    success: bool  # Whether the command was processed successfully
    response: str  # The assistant's response to the command
    command: str   # The original command that was processed
    timestamp: datetime  # When the command was processed
    processing_time_ms: float = 0.0  # Processing time in milliseconds, defaults to 0 if unknown
    log_id: Optional[int] = None  # Database log ID if successfully stored, None if logging failed
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "response": "The current time is 10:30 AM on July 01, 2025",
                "command": "what time is it?",
                "timestamp": "2025-07-01T10:30:00.123456",
                "processing_time_ms": 15.5,
                "log_id": 123
            }
        }

class StatusResponse(BaseModel):
    """System status and capabilities response"""
    status: str  # Current system status
    version: str  # API version
    features: Dict[str, bool]  # Available features and their status
    uptime_seconds: float  # Server uptime in seconds
    total_commands: int  # Total commands processed
    database_status: str  # Database connection status
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "running",
                "version": "1.0.0",
                "features": {
                    "text_processing": True,
                    "database_logging": True,
                    "voice_synthesis": False
                },
                "uptime_seconds": 3600.5,
                "total_commands": 42,
                "database_status": "connected"
            }
        }

class CommandHistoryResponse(BaseModel):
    id: int
    command: str
    response: str
    success: bool
    timestamp: datetime
    processing_time_ms: float = 0.0  # Always provide processing time, default to 0 if not recorded

class DatabaseStatsResponse(BaseModel):
    """Database analytics and statistics response"""
    total_commands: int  # Total number of commands processed
    successful_commands: int  # Number of successfully processed commands
    failed_commands: int  # Number of failed commands
    average_processing_time_ms: float = 0.0  # Average processing time, defaults to 0 if no data
    most_recent_command: Optional[datetime] = None  # Timestamp of most recent command, None if database is empty
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_commands": 150,
                "successful_commands": 147,
                "failed_commands": 3,
                "average_processing_time_ms": 12.5,
                "most_recent_command": "2025-07-01T10:30:00.123456"
            }
        }

# Global state
start_time = datetime.now()

# Initialize database on startup
try:
    create_tables()
    logger.info("Database tables created successfully")
except Exception as e:
    logger.error(f"Error creating database tables: {e}")

@app.on_event("startup")
async def startup_event():
    """Initialize database and log startup"""
    db = None
    try:
        # Create a system metric for startup
        db = next(get_db())
        metric = SystemMetric(
            metric_name="server_startup",
            metric_value=1.0,
            metric_unit="count"
        )
        db.add(metric)
        db.commit()
        logger.info("Startup metric logged to database")
    except Exception as e:
        logger.error(f"Error logging startup metric: {e}")
    finally:
        if db:
            db.close()

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with a simple web interface."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Voice Assistant API</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; text-align: center; }
            .status { background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0; }
            .endpoint { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #007bff; }
            .method { background: #007bff; color: white; padding: 4px 8px; border-radius: 3px; font-size: 12px; }
            input, textarea { width: 100%; padding: 10px; margin: 5px 0; border: 1px solid #ddd; border-radius: 4px; }
            button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background: #0056b3; }
            .response { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; white-space: pre-wrap; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 Voice Assistant API</h1>
            
            <div class="status">
                <strong>Status:</strong> ✅ Running and Ready<br>
                <strong>Version:</strong> 1.0.0<br>
                <strong>API Documentation:</strong> <a href="/docs">/docs</a>
            </div>

            <h2>Quick Test</h2>
            <div>
                <input type="text" id="command" placeholder="Enter a command (e.g., 'what time is it?')" value="what time is it?">
                <button onclick="sendCommand()">Send Command</button>
                <div id="response" class="response" style="display:none;"></div>
            </div>

            <h2>Available Endpoints</h2>
            
            <div class="endpoint">
                <span class="method">GET</span> <strong>/health</strong><br>
                Health check endpoint
            </div>
            
            <div class="endpoint">
                <span class="method">GET</span> <strong>/status</strong><br>
                Get system status and capabilities
            </div>
            
            <div class="endpoint">
                <span class="method">POST</span> <strong>/command</strong><br>
                Process voice commands
            </div>
            
            <div class="endpoint">
                <span class="method">GET</span> <strong>/commands/history</strong><br>
                View command history from database
            </div>
            
            <div class="endpoint">
                <span class="method">GET</span> <strong>/commands/stats</strong><br>
                Get database analytics and statistics
            </div>
            
            <div class="endpoint">
                <span class="method">GET</span> <strong>/docs</strong><br>
                Interactive API documentation
            </div>
        </div>

        <script>
            async function sendCommand() {
                const command = document.getElementById('command').value;
                const responseDiv = document.getElementById('response');
                
                try {
                    const response = await fetch('/command', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({command: command})
                    });
                    
                    const data = await response.json();
                    responseDiv.innerHTML = JSON.stringify(data, null, 2);
                    responseDiv.style.display = 'block';
                } catch (error) {
                    responseDiv.innerHTML = 'Error: ' + error.message;
                    responseDiv.style.display = 'block';
                }
            }
        </script>
    </body>
    </html>
    """
    return html_content

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "voice-assistant-api", "version": "1.0.0"}

@app.get("/status", response_model=StatusResponse)
async def get_status(db: Session = Depends(get_db)):
    """Get system status and capabilities."""
    uptime = (datetime.now() - start_time).total_seconds()
    
    # Get total commands from database
    try:
        total_commands = db.query(CommandLog).count()
        database_status = "connected"
    except Exception as e:
        logger.error(f"Database error: {e}")
        total_commands = 0
        database_status = "error"
    
    return StatusResponse(
        status="running",
        version="1.0.0",
        features={
            "text_processing": True,
            "time_queries": True,
            "basic_math": True,
            "database_logging": database_status == "connected",
            "command_history": database_status == "connected",
            "analytics": database_status == "connected",
            "weather": False,  # Would need API key
            "news": False,     # Would need API key
            "email": False,    # Would need credentials
            "voice_synthesis": False,  # Audio not available
            "voice_recognition": False,  # Audio not available
            "smart_home": False,  # Would need device integrations
        },
        uptime_seconds=uptime,
        total_commands=total_commands,
        database_status=database_status
    )

@app.post("/command", response_model=CommandResponse)
async def process_command(request: CommandRequest, db: Session = Depends(get_db)):
    """Process a voice command and return a response."""
    start_time = time.time()
    command = request.command.lower().strip()
    success = True
    log_id = None
    
    try:
        # Simple command processing
        if any(phrase in command for phrase in ["time", "what time", "current time"]):
            current_time = datetime.now().strftime("%I:%M %p on %B %d, %Y")
            response = f"The current time is {current_time}"
            
        elif any(phrase in command for phrase in ["date", "what date", "today"]):
            current_date = datetime.now().strftime("%A, %B %d, %Y")
            response = f"Today is {current_date}"
            
        elif any(phrase in command for phrase in ["hello", "hi", "hey"]):
            response = "Hello! I'm your voice assistant. How can I help you today?"
            
        elif any(phrase in command for phrase in ["how are you", "how's it going"]):
            response = "I'm doing well, thank you for asking! All systems are running smoothly."
            
        elif any(phrase in command for phrase in ["weather", "temperature"]):
            response = "Weather information requires an API key. Please configure weather services to get current conditions."
            
        elif any(phrase in command for phrase in ["news", "headlines"]):
            response = "News features require an API key. Please configure news services to get latest headlines."
            
        elif "+" in command or "plus" in command or any(phrase in command for phrase in ["add", "sum"]):
            # Simple math
            try:
                # Basic addition parsing
                if "+" in command:
                    parts = command.split("+")
                    if len(parts) == 2:
                        num1 = float(parts[0].strip().split()[-1])
                        num2 = float(parts[1].strip().split()[0])
                        result = num1 + num2
                        response = f"{num1} + {num2} = {result}"
                    else:
                        response = "I can help with simple addition. Try saying something like '5 + 3'"
                else:
                    response = "I can help with simple math. Try saying something like '5 + 3'"
            except:
                response = "I can help with simple math. Try saying something like '5 + 3'"
                
        elif any(phrase in command for phrase in ["help", "what can you do", "commands"]):
            response = """I can help you with:
• Time and date queries
• Simple math calculations  
• Basic greetings and conversation
• System status information
• Command history and analytics

For advanced features like weather, news, email, and smart home control, additional API keys and configurations are needed."""
            
        else:
            response = f"I heard you say: '{request.command}'. I'm a basic assistant right now. Try asking about the time, date, or say 'help' to see what I can do."
        
    except Exception as e:
        logger.error(f"Error processing command '{command}': {e}")
        response = f"Sorry, I encountered an error processing your command: {str(e)}"
        success = False
    
    # Calculate processing time
    processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
    
    # Log to database
    try:
        command_log = CommandLog(
            command=request.command,
            response=response,
            source=request.source,
            success=success,
            processing_time_ms=processing_time,
            user_id=request.user_id
        )
        db.add(command_log)
        db.commit()
        db.refresh(command_log)
        log_id = command_log.id
        logger.info(f"Command logged to database with ID: {log_id}")
    except Exception as e:
        logger.error(f"Error logging command to database: {e}")
    
    return CommandResponse(
        success=success,
        response=response,
        command=request.command,
        timestamp=datetime.now(),
        processing_time_ms=processing_time if processing_time is not None else 0.0,
        log_id=log_id
    )

@app.get("/commands/history", response_model=List[CommandHistoryResponse])
async def get_command_history(limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    """Get command history from the database"""
    try:
        commands = db.query(CommandLog).order_by(CommandLog.timestamp.desc()).offset(offset).limit(limit).all()
        return [
            CommandHistoryResponse(
                id=cmd.id,
                command=cmd.command,
                response=cmd.response,
                success=cmd.success,
                timestamp=cmd.timestamp,
                processing_time_ms=cmd.processing_time_ms if cmd.processing_time_ms is not None else 0.0
            ) for cmd in commands
        ]
    except Exception as e:
        logger.error(f"Error fetching command history: {e}")
        raise HTTPException(status_code=500, detail="Error fetching command history")

@app.get("/commands/stats", response_model=DatabaseStatsResponse)
async def get_database_stats(db: Session = Depends(get_db)):
    """Get database statistics and analytics"""
    try:
        from sqlalchemy import func
        
        total_commands = db.query(CommandLog).count()
        successful_commands = db.query(CommandLog).filter(CommandLog.success == True).count()
        failed_commands = total_commands - successful_commands
        
        # Get average processing time
        avg_processing_time = db.query(func.avg(CommandLog.processing_time_ms)).scalar()
        
        # Get most recent command timestamp
        most_recent = db.query(func.max(CommandLog.timestamp)).scalar()
        
        return DatabaseStatsResponse(
            total_commands=total_commands,
            successful_commands=successful_commands,
            failed_commands=failed_commands,
            average_processing_time_ms=avg_processing_time if avg_processing_time is not None else 0.0,
            most_recent_command=most_recent
        )
    except Exception as e:
        logger.error(f"Error fetching database stats: {e}")
        raise HTTPException(status_code=500, detail="Error fetching database statistics")

@app.delete("/commands/clear")
async def clear_command_history(db: Session = Depends(get_db)):
    """Clear all command history (use with caution)"""
    try:
        deleted_count = db.query(CommandLog).count()
        db.query(CommandLog).delete()
        db.commit()
        logger.info(f"Cleared {deleted_count} commands from history")
        return {"message": f"Successfully cleared {deleted_count} commands from history"}
    except Exception as e:
        logger.error(f"Error clearing command history: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Error clearing command history")

if __name__ == "__main__":
    logger.info("Starting Voice Assistant API server...")
    uvicorn.run(app, host="0.0.0.0", port=5000)