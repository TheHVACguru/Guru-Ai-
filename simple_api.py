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
@app.head("/")
async def root():
    """Root endpoint with a modern voice assistant interface."""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>JARVIS - Arc Reactor Interface</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: 'Courier New', monospace;
                background: #000;
                color: #00d4ff;
                overflow: hidden;
                height: 100vh;
                position: relative;
            }

            /* Main interface container */
            .interface-container {
                position: relative;
                width: 100%;
                height: 100vh;
                background: 
                    radial-gradient(ellipse at 30% 20%, rgba(0, 150, 255, 0.1) 0%, transparent 50%),
                    radial-gradient(ellipse at 70% 80%, rgba(255, 165, 0, 0.05) 0%, transparent 50%),
                    linear-gradient(135deg, #001122 0%, #000000 100%);
            }

            /* Top status bar */
            .top-status-bar {
                position: absolute;
                top: 20px;
                left: 20px;
                right: 20px;
                height: 60px;
                background: rgba(0, 50, 100, 0.2);
                border: 1px solid #00aaff;
                border-radius: 8px;
                display: flex;
                align-items: center;
                padding: 0 30px;
                backdrop-filter: blur(10px);
            }

            .status-display {
                display: flex;
                align-items: center;
                gap: 15px;
            }

            .status-icon {
                width: 40px;
                height: 40px;
                border: 2px solid #00aaff;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 14px;
                font-weight: bold;
                color: #00aaff;
            }

            .status-icon.listening {
                border-color: #ff6b6b;
                color: #ff6b6b;
                animation: pulse 1.5s infinite;
            }

            .status-icon.processing {
                border-color: #4ecdc4;
                color: #4ecdc4;
                animation: spin 2s linear infinite;
            }

            .status-text {
                font-size: 18px;
                color: #00d4ff;
                font-weight: bold;
            }

            .system-grid {
                position: absolute;
                top: 20px;
                right: 20px;
                width: 400px;
                height: 200px;
                display: grid;
                grid-template-columns: repeat(6, 1fr);
                grid-template-rows: repeat(4, 1fr);
                gap: 3px;
            }

            .grid-cell {
                background: rgba(0, 170, 255, 0.1);
                border: 1px solid #0099cc;
                border-radius: 3px;
                font-size: 10px;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.3s ease;
            }

            .grid-cell:hover {
                background: rgba(0, 170, 255, 0.3);
                box-shadow: 0 0 10px #00aaff;
            }

            /* Central arc reactor display */
            .arc-reactor {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                width: 350px;
                height: 350px;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
            }

            .reactor-outer-ring {
                position: absolute;
                width: 100%;
                height: 100%;
                border: 3px solid #00aaff;
                border-radius: 50%;
                opacity: 0.6;
            }

            .reactor-middle-ring {
                position: absolute;
                width: 85%;
                height: 85%;
                border: 2px solid #0099dd;
                border-radius: 50%;
                opacity: 0.8;
            }

            .reactor-segments {
                position: absolute;
                width: 90%;
                height: 90%;
                border-radius: 50%;
            }

            /* Energy level segments using conic gradient */
            .energy-segments {
                position: absolute;
                width: 95%;
                height: 95%;
                border-radius: 50%;
                background: conic-gradient(
                    from 0deg,
                    #ff9900 0deg 45deg,
                    #ffcc00 45deg 90deg,
                    #00aaff 90deg 180deg,
                    rgba(0, 170, 255, 0.3) 180deg 360deg
                );
                mask: radial-gradient(circle, transparent 70%, black 75%, black 85%, transparent 90%);
                animation: rotateEnergy 8s linear infinite;
            }

            .energy-segments.listening {
                background: conic-gradient(
                    from 0deg,
                    #ff6b6b 0deg 90deg,
                    #ff9900 90deg 180deg,
                    #ffcc00 180deg 270deg,
                    #ff6b6b 270deg 360deg
                );
                animation: rotateEnergy 3s linear infinite;
            }

            .energy-segments.processing {
                background: conic-gradient(
                    from 0deg,
                    #4ecdc4 0deg 90deg,
                    #00aaff 90deg 180deg,
                    #4ecdc4 180deg 270deg,
                    #00aaff 270deg 360deg
                );
                animation: rotateEnergy 1s linear infinite;
            }

            @keyframes rotateEnergy {
                from { transform: rotate(0deg); }
                to { transform: rotate(360deg); }
            }

            @keyframes pulse {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.05); }
            }

            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }

            /* Reactor core center */
            .reactor-core {
                position: relative;
                width: 120px;
                height: 120px;
                background: radial-gradient(circle, #00aaff 0%, #0066aa  50%, #003366 100%);
                border-radius: 50%;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                box-shadow: 
                    0 0 30px #00aaff,
                    inset 0 0 20px rgba(0, 170, 255, 0.3);
                animation: corePulse 3s ease-in-out infinite;
                transition: all 0.3s ease;
            }

            .reactor-core.listening {
                background: radial-gradient(circle, #ff6b6b 0%, #cc4444 50%, #993333 100%);
                box-shadow: 
                    0 0 50px #ff6b6b,
                    inset 0 0 30px rgba(255, 107, 107, 0.5);
            }

            .reactor-core.processing {
                background: radial-gradient(circle, #4ecdc4 0%, #44a08d 50%, #336666 100%);
                box-shadow: 
                    0 0 50px #4ecdc4,
                    inset 0 0 30px rgba(78, 205, 196, 0.5);
            }

            @keyframes corePulse {
                0%, 100% { 
                    box-shadow: 0 0 30px #00aaff, inset 0 0 20px rgba(0, 170, 255, 0.3);
                    transform: scale(1);
                }
                50% { 
                    box-shadow: 0 0 50px #00aaff, inset 0 0 30px rgba(0, 170, 255, 0.5);
                    transform: scale(1.05);
                }
            }

            .voice-status {
                font-size: 14px;
                font-weight: bold;
                color: #ffcc00;
                margin-bottom: 5px;
                min-height: 20px;
            }

            .voice-command {
                font-size: 10px;
                color: #00aaff;
                opacity: 0.8;
                text-align: center;
                max-width: 100px;
                line-height: 1.2;
            }

            /* Scale markings around reactor */
            .scale-marking {
                position: absolute;
                color: #00aaff;
                font-size: 14px;
                font-weight: bold;
            }

            .scale-5 { top: 10px; right: 120px; }
            .scale-15 { right: 10px; top: 120px; }
            .scale-25 { bottom: 10px; right: 120px; }
            .scale-75 { left: 10px; top: 120px; }

            .energy-label {
                position: absolute;
                bottom: -40px;
                left: 50%;
                transform: translateX(-50%);
                font-size: 16px;
                color: #00aaff;
                font-weight: bold;
                letter-spacing: 2px;
            }

            /* Technical readouts */
            .tech-readout {
                position: absolute;
                top: 100px;
                left: 20px;
                width: 250px;
                background: rgba(0, 50, 100, 0.1);
                border: 1px solid #00aaff;
                border-radius: 8px;
                padding: 15px;
                backdrop-filter: blur(10px);
            }

            .readout-line {
                display: flex;
                justify-content: space-between;
                margin-bottom: 8px;
                font-size: 11px;
                color: #00aaff;
            }

            .readout-value {
                color: #ffcc00;
                font-weight: bold;
            }

            /* Communication panel */
            .comm-panel {
                position: absolute;
                bottom: 20px;
                left: 20px;
                right: 20px;
                height: 120px;
                background: rgba(0, 50, 100, 0.15);
                border: 1px solid #00aaff;
                border-radius: 8px;
                backdrop-filter: blur(10px);
                padding: 20px;
            }

            .comm-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
            }

            .comm-title {
                font-size: 14px;
                color: #00aaff;
                font-weight: bold;
                letter-spacing: 1px;
            }

            .text-input {
                width: 100%;
                background: rgba(0, 50, 100, 0.2);
                border: 1px solid #00aaff;
                border-radius: 20px;
                padding: 10px 20px;
                color: #00d4ff;
                font-family: 'Courier New', monospace;
                font-size: 14px;
                outline: none;
                transition: all 0.3s ease;
            }

            .text-input::placeholder {
                color: rgba(0, 212, 255, 0.5);
            }

            .text-input:focus {
                border-color: #00ffaa;
                box-shadow: 0 0 10px rgba(0, 255, 170, 0.3);
            }

            .send-button {
                margin-top: 10px;
                padding: 8px 20px;
                background: linear-gradient(45deg, #ff9900, #ffcc00);
                border: none;
                color: #000;
                border-radius: 15px;
                font-size: 12px;
                font-weight: bold;
                cursor: pointer;
                transition: all 0.3s ease;
            }

            .send-button:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(255, 153, 0, 0.4);
            }

            /* Response display */
            .response-container {
                position: absolute;
                top: 50%;
                right: 20px;
                transform: translateY(-50%);
                width: 300px;
                max-height: 400px;
                background: rgba(0, 50, 100, 0.15);
                border: 1px solid #00aaff;
                border-radius: 8px;
                padding: 20px;
                backdrop-filter: blur(10px);
                display: none;
                overflow-y: auto;
            }

            .response-header {
                font-size: 12px;
                color: #ff9900;
                font-weight: bold;
                margin-bottom: 10px;
                letter-spacing: 1px;
            }

            .response-text {
                font-size: 12px;
                color: #00d4ff;
                line-height: 1.6;
                word-wrap: break-word;
            }

            /* Animated scan lines */
            .scan-line {
                position: absolute;
                width: 100%;
                height: 2px;
                background: linear-gradient(90deg, transparent, #00aaff, transparent);
                animation: scanMove 3s linear infinite;
                opacity: 0.6;
            }

            @keyframes scanMove {
                0% { top: 0%; opacity: 0; }
                50% { opacity: 0.6; }
                100% { top: 100%; opacity: 0; }
            }

            /* Power level indicators */
            .power-bars {
                position: absolute;
                top: 50%;
                left: 100px;
                transform: translateY(-50%);
                display: flex;
                flex-direction: column;
                gap: 3px;
            }

            .power-bar {
                width: 60px;
                height: 8px;
                background: rgba(0, 170, 255, 0.2);
                border: 1px solid #00aaff;
                border-radius: 2px;
                position: relative;
                overflow: hidden;
            }

            .power-bar.active::after {
                content: '';
                position: absolute;
                left: 0;
                top: 0;
                height: 100%;
                background: linear-gradient(90deg, #00aaff, #00ffaa);
                animation: powerFlow 2s ease-in-out infinite;
            }

            .power-bar:nth-child(1).active::after { width: 90%; animation-delay: 0s; }
            .power-bar:nth-child(2).active::after { width: 85%; animation-delay: 0.2s; }
            .power-bar:nth-child(3).active::after { width: 92%; animation-delay: 0.4s; }
            .power-bar:nth-child(4).active::after { width: 78%; animation-delay: 0.6s; }
            .power-bar:nth-child(5).active::after { width: 88%; animation-delay: 0.8s; }

            @keyframes powerFlow {
                0%, 100% { opacity: 0.7; }
                50% { opacity: 1; }
            }

            @media (max-width: 768px) {
                .system-grid { display: none; }
                .tech-readout { display: none; }
                .power-bars { display: none; }
                .response-container { 
                    position: fixed;
                    bottom: 160px;
                    left: 20px;
                    right: 20px;
                    width: auto;
                    transform: none;
                }
                .arc-reactor {
                    width: 280px;
                    height: 280px;
                }
                .reactor-core {
                    width: 100px;
                    height: 100px;
                }
            }
        </style>
    </head>
    <body>
        <div class="interface-container">
            <!-- Animated scan line -->
            <div class="scan-line"></div>

            <!-- Top status bar -->
            <div class="top-status-bar">
                <div class="status-display">
                    <div class="status-icon" id="statusIcon">🎤</div>
                    <div class="status-text" id="statusText">JARVIS READY</div>
                </div>
                
                <!-- System grid display -->
                <div class="system-grid" id="systemGrid">
                    <!-- Grid cells will be populated by JavaScript -->
                </div>
            </div>

            <!-- Technical readouts -->
            <div class="tech-readout">
                <div class="readout-line">
                    <span>VOICE ENGINE</span>
                    <span class="readout-value" id="voiceStatus">ONLINE</span>
                </div>
                <div class="readout-line">
                    <span>SPEECH REC</span>
                    <span class="readout-value" id="speechStatus">READY</span>
                </div>
                <div class="readout-line">
                    <span>API STATUS</span>
                    <span class="readout-value" id="apiStatus">CONNECTED</span>
                </div>
                <div class="readout-line">
                    <span>COMMANDS</span>
                    <span class="readout-value" id="commandCount">0</span>
                </div>
                <div class="readout-line">
                    <span>UPTIME</span>
                    <span class="readout-value" id="uptime">00:00:00</span>
                </div>
            </div>

            <!-- Power level bars -->
            <div class="power-bars">
                <div class="power-bar active"></div>
                <div class="power-bar active"></div>
                <div class="power-bar active"></div>
                <div class="power-bar active"></div>
                <div class="power-bar active"></div>
            </div>

            <!-- Central arc reactor -->
            <div class="arc-reactor" id="arcReactor" onclick="toggleListening()">
                <div class="reactor-outer-ring"></div>
                <div class="reactor-middle-ring"></div>
                <div class="energy-segments" id="energySegments"></div>
                
                <div class="reactor-core" id="reactorCore">
                    <div class="voice-status" id="voiceStatusText">PRESS TO TALK</div>
                    <div class="voice-command" id="voiceCommand">Touch reactor core</div>
                </div>
                
                <!-- Scale markings -->
                <div class="scale-marking scale-5">5</div>
                <div class="scale-marking scale-15">15</div>
                <div class="scale-marking scale-25">25</div>
                <div class="scale-marking scale-75">75</div>
                
                <div class="energy-label">VOICE INTERFACE</div>
            </div>

            <!-- Communication panel -->
            <div class="comm-panel">
                <div class="comm-header">
                    <div class="comm-title">VOICE COMMAND INPUT</div>
                </div>
                <input type="text" 
                       class="text-input" 
                       id="commandInput" 
                       placeholder="Type command here or use voice..."
                       onkeypress="handleKeyPress(event)">
                <button class="send-button" onclick="sendTextCommand()">EXECUTE</button>
            </div>

            <!-- Response display -->
            <div class="response-container" id="responseContainer">
                <div class="response-header">JARVIS RESPONSE</div>
                <div class="response-text" id="responseText"></div>
            </div>
        </div>

            <div class="response-container" id="responseContainer">
                <div class="response-text" id="responseText"></div>
            </div>
        </div>

        <script>
            let commandCount = 0;
            let startTime = Date.now();

            // Initialize the interface when page loads
            document.addEventListener('DOMContentLoaded', function() {
                initializeInterface();
                populateSystemGrid();
                
                // Update time every second to keep it current
                setInterval(updateSystemReadouts, 1000);
                
                // Simulate system activity with periodic updates
                setInterval(simulateSystemActivity, 2000);
            });

            function initializeInterface() {
                updateStatus('JARVIS READY');
                updateVoiceStatus('TEXT INPUT READY');
                updateReadoutValue('voiceStatus', 'ONLINE');
                updateReadoutValue('speechStatus', 'TEXT MODE');
                updateReadoutValue('apiStatus', 'CONNECTED');
                updateReadoutValue('commandCount', '0');
                
                console.log('Arc Reactor Interface Online - JARVIS Systems Activated');
                
                // Focus on text input
                document.getElementById('commandInput').focus();
                
                setTimeout(() => {
                    showSystemMessage('Interface ready. Type commands below.');
                }, 1000);
            }

            function updateStatus(message) {
                document.getElementById('statusText').textContent = message;
            }

            function updateVoiceStatus(message) {
                document.getElementById('voiceStatusText').textContent = message;
            }

            function updateReadoutValue(elementId, value) {
                const element = document.getElementById(elementId);
                if (element) {
                    element.textContent = value;
                }
            }

            function updateSystemReadouts() {
                // Update uptime
                const uptime = Math.floor((Date.now() - startTime) / 1000);
                const hours = Math.floor(uptime / 3600).toString().padStart(2, '0');
                const minutes = Math.floor((uptime % 3600) / 60).toString().padStart(2, '0');
                const seconds = (uptime % 60).toString().padStart(2, '0');
                updateReadoutValue('uptime', `${hours}:${minutes}:${seconds}`);
            }

            function updateReactorState(state) {
                const reactorCore = document.getElementById('reactorCore');
                const energySegments = document.getElementById('energySegments');
                const statusIcon = document.getElementById('statusIcon');
                
                // Reset classes
                reactorCore.className = 'reactor-core';
                energySegments.className = 'energy-segments';
                statusIcon.className = 'status-icon';
                
                if (state === 'processing') {
                    reactorCore.classList.add('processing');
                    energySegments.classList.add('processing');
                    statusIcon.classList.add('processing');
                }
            }

            function toggleListening() {
                // Just focus on text input instead of attempting voice
                const textInput = document.getElementById('commandInput');
                textInput.focus();
                showSystemMessage('Use text input below to send commands');
            }

            function resetInterface() {
                updateReactorState('default');
                updateStatus('JARVIS READY');
                updateVoiceStatus('TEXT INPUT READY');
                updateReadoutValue('speechStatus', 'TEXT MODE');
            }

            async function sendCommand(commandText) {
                const command = commandText || document.getElementById('commandInput').value.trim();
                
                if (!command) {
                    showSystemMessage('Please enter a command');
                    document.getElementById('commandInput').focus();
                    return;
                }

                updateReactorState('processing');
                updateStatus('PROCESSING COMMAND');
                updateVoiceStatus('ANALYZING...');
                updateReadoutValue('apiStatus', 'TRANSMITTING');
                
                try {
                    const startTime = performance.now();
                    
                    const response = await fetch('/command', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            command: command,
                            source: 'arc_reactor_interface'
                        })
                    });
                    
                    const processingTime = Math.round(performance.now() - startTime);
                    
                    if (!response.ok) {
                        throw new Error(`Server error ${response.status}: ${response.statusText}`);
                    }
                    
                    const data = await response.json();
                    
                    // Update command count
                    commandCount++;
                    updateReadoutValue('commandCount', commandCount.toString());
                    
                    // Display the response
                    const responseContainer = document.getElementById('responseContainer');
                    const responseText = document.getElementById('responseText');
                    
                    if (data.success) {
                        responseText.innerHTML = `
                            <strong>Command:</strong> "${command}"<br>
                            <strong>Response:</strong> ${data.response}<br>
                            <strong>Time:</strong> ${processingTime}ms
                        `;
                        updateStatus('COMMAND EXECUTED');
                        updateVoiceStatus('OPERATION COMPLETE');
                        updateReadoutValue('apiStatus', 'SUCCESS');
                        
                        // Clear the input field
                        document.getElementById('commandInput').value = '';
                    } else {
                        responseText.innerHTML = `
                            <strong>Command:</strong> "${command}"<br>
                            <strong>Error:</strong> ${data.response || 'Unknown error'}<br>
                            <strong>Time:</strong> ${processingTime}ms
                        `;
                        updateStatus('EXECUTION FAILED');
                        updateVoiceStatus('COMMAND ERROR');
                        updateReadoutValue('apiStatus', 'FAILED');
                    }
                    
                    responseContainer.style.display = 'block';
                    
                    // Auto-hide response after 10 seconds
                    setTimeout(() => {
                        responseContainer.style.display = 'none';
                    }, 10000);
                    
                } catch (error) {
                    const responseContainer = document.getElementById('responseContainer');
                    const responseText = document.getElementById('responseText');
                    
                    responseText.innerHTML = `
                        <strong>Command:</strong> "${command}"<br>
                        <strong>Error:</strong> ${error.message}<br>
                        <strong>Status:</strong> Connection Failed
                    `;
                    responseContainer.style.display = 'block';
                    updateStatus('CONNECTION FAILED');
                    updateVoiceStatus('NETWORK ERROR');
                    updateReadoutValue('apiStatus', 'DISCONNECTED');
                    
                    setTimeout(() => {
                        responseContainer.style.display = 'none';
                    }, 10000);
                }
                
                // Reset interface
                setTimeout(() => {
                    resetInterface();
                    updateReadoutValue('apiStatus', 'CONNECTED');
                    document.getElementById('commandInput').focus();
                }, 2000);
            }

            function sendTextCommand() {
                sendCommand();
            }

            function handleKeyPress(event) {
                if (event.key === 'Enter') {
                    event.preventDefault();
                    sendTextCommand();
                }
            }

            // Create the system grid with realistic technical labels
            function populateSystemGrid() {
                const systemGrid = document.getElementById('systemGrid');
                const gridLabels = [
                    'PWR', 'SYS', 'NAV', 'COM', 'WPN', 'SHD',
                    'THR', 'STB', 'GYR', 'ALT', 'VEL', 'TMP',
                    'O2', 'CO2', 'H2O', 'FUL', 'BAT', 'GEN',
                    'RAD', 'MAG', 'GRV', 'IRT', 'OPT', 'AUD'
                ];
                
                gridLabels.forEach(label => {
                    const cell = document.createElement('div');
                    cell.className = 'grid-cell';
                    cell.textContent = label;
                    
                    if (Math.random() > 0.7) {
                        cell.style.background = 'rgba(255, 153, 0, 0.2)';
                        cell.style.color = '#ffcc00';
                    }
                    
                    systemGrid.appendChild(cell);
                });
            }

            function simulateSystemActivity() {
                const gridCells = document.querySelectorAll('.grid-cell');
                gridCells.forEach(cell => {
                    if (Math.random() > 0.95) {
                        cell.style.background = 'rgba(0, 255, 170, 0.4)';
                        cell.style.boxShadow = '0 0 10px #00ffaa';
                        
                        setTimeout(() => {
                            cell.style.background = 'rgba(0, 170, 255, 0.1)';
                            cell.style.boxShadow = 'none';
                        }, 500);
                    }
                });
            }

            function showSystemMessage(message) {
                console.log('JARVIS:', message);
                
                const notification = document.createElement('div');
                notification.style.cssText = `
                    position: fixed;
                    top: 100px;
                    left: 50%;
                    transform: translateX(-50%);
                    background: rgba(0, 170, 255, 0.9);
                    color: white;
                    padding: 10px 20px;
                    border-radius: 5px;
                    font-size: 12px;
                    font-family: 'Courier New', monospace;
                    z-index: 1000;
                    backdrop-filter: blur(10px);
                    border: 1px solid #00aaff;
                `;
                notification.textContent = message;
                document.body.appendChild(notification);
                
                setTimeout(() => {
                    if (document.body.contains(notification)) {
                        document.body.removeChild(notification);
                    }
                }, 3000);
            }
        </script>
    </body>
    </html>
    """
    return html_content

@app.get("/health")
@app.head("/health")
async def health_check():
    """Health check endpoint - returns 200 OK for deployment health checks."""
    return {"status": "healthy", "service": "voice-assistant-api", "version": "1.0.0", "ready": True}

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
                
        elif any(phrase in command for phrase in ["joke", "tell me a joke", "funny"]):
            jokes = [
                "Why don't scientists trust atoms? Because they make up everything!",
                "I told my wife she was drawing her eyebrows too high. She looked surprised.",
                "Why did the scarecrow win an award? He was outstanding in his field!",
                "I'm reading a book about anti-gravity. It's impossible to put down!",
                "Why don't eggs tell jokes? They'd crack each other up!"
            ]
            import random
            response = random.choice(jokes)
            
        elif any(phrase in command for phrase in ["system", "status", "diagnostics"]):
            response = "All systems operational. Arc reactor at optimal efficiency. No errors detected."
            
        elif any(phrase in command for phrase in ["shutdown", "power off", "turn off"]):
            response = "I cannot shut down core systems. Voice interface will remain active for your safety."
            
        elif any(phrase in command for phrase in ["who are you", "what are you", "introduce yourself"]):
            response = "I am JARVIS, your advanced AI assistant. I'm here to help with various tasks and answer your questions."
            
        elif any(phrase in command for phrase in ["thank you", "thanks", "appreciate"]):
            response = "You're welcome! I'm always here to help whenever you need assistance."
            
        elif any(phrase in command for phrase in ["good morning", "good afternoon", "good evening"]):
            hour = datetime.now().hour
            if hour < 12:
                response = "Good morning! I hope you have a productive day ahead."
            elif hour < 17:
                response = "Good afternoon! How may I assist you today?"
            else:
                response = "Good evening! What can I help you with this evening?"
                
        elif any(phrase in command for phrase in ["help", "what can you do", "commands"]):
            response = """I can help you with:
• Time and date queries
• Simple math calculations  
• Basic greetings and conversation
• System status information
• Tell jokes and have casual conversations
• Weather and news (requires API configuration)
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
    import os
    
    # Get port from environment (Cloud Run sets PORT automatically)
    port = int(os.environ.get("PORT", 5000))
    
    logger.info(f"Starting Voice Assistant API server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)