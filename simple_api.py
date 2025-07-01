#!/usr/bin/env python3
"""
Simple Voice Assistant API Server
A minimal FastAPI server that provides essential voice assistant functionality.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

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
    command: str
    source: str = "api"

class CommandResponse(BaseModel):
    success: bool
    response: str
    command: str
    timestamp: datetime

class StatusResponse(BaseModel):
    status: str
    version: str
    features: Dict[str, bool]
    uptime_seconds: float

# Global state
start_time = datetime.now()

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
async def get_status():
    """Get system status and capabilities."""
    uptime = (datetime.now() - start_time).total_seconds()
    
    return StatusResponse(
        status="running",
        version="1.0.0",
        features={
            "text_processing": True,
            "time_queries": True,
            "basic_math": True,
            "weather": False,  # Would need API key
            "news": False,     # Would need API key
            "email": False,    # Would need credentials
            "voice_synthesis": False,  # Audio not available
            "voice_recognition": False,  # Audio not available
            "smart_home": False,  # Would need device integrations
        },
        uptime_seconds=uptime
    )

@app.post("/command", response_model=CommandResponse)
async def process_command(request: CommandRequest):
    """Process a voice command and return a response."""
    command = request.command.lower().strip()
    
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

For advanced features like weather, news, email, and smart home control, additional API keys and configurations are needed."""
            
        else:
            response = f"I heard you say: '{request.command}'. I'm a basic assistant right now. Try asking about the time, date, or say 'help' to see what I can do."
        
        return CommandResponse(
            success=True,
            response=response,
            command=request.command,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Error processing command '{command}': {e}")
        return CommandResponse(
            success=False,
            response=f"Sorry, I encountered an error processing your command: {str(e)}",
            command=request.command,
            timestamp=datetime.now()
        )

if __name__ == "__main__":
    logger.info("Starting Voice Assistant API server...")
    uvicorn.run(app, host="0.0.0.0", port=5000)