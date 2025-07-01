"""
API routes for Voice Assistant.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from typing import Optional, List
import asyncio
import os
from pathlib import Path

from assistant.api.models import (
    CommandRequest, CommandResponse, StatusResponse,
    VoiceTestRequest, DeviceInfo, WeatherResponse,
    StockResponse, NewsResponse, EmailRequest
)
from assistant.commands.processor import CommandProcessor
from assistant.core.speaker import VoiceSpeaker
from assistant.core.listener import VoiceListener
from assistant.devices.camera import CameraDevice
from assistant.devices.audio import AudioDevice
from assistant.integrations.weather import WeatherClient
from assistant.integrations.stock import StockClient
from assistant.integrations.news import NewsClient
from assistant.integrations.gmail import GmailClient
from assistant.integrations.calendar import CalendarClient
from assistant.utils.logger import setup_logger

logger = setup_logger(__name__)

def create_router(config) -> APIRouter:
    """Create API router with all endpoints."""
    
    router = APIRouter()
    
    # Initialize components
    voice_speaker = VoiceSpeaker(config)
    voice_listener = VoiceListener(config)
    command_processor = CommandProcessor(config, voice_speaker)
    camera_device = CameraDevice(config)
    audio_device = AudioDevice(config)
    weather_client = WeatherClient(config)
    stock_client = StockClient(config)
    news_client = NewsClient(config)
    gmail_client = GmailClient(config)
    calendar_client = CalendarClient(config)
    
    # System Status Endpoints
    @router.get("/status", response_model=StatusResponse)
    async def get_status():
        """Get system status."""
        try:
            return StatusResponse(
                status="online",
                wake_word=config.wake_word,
                voice_recognition=True,
                speech_synthesis=True,
                api_server=True,
                openai_available=bool(config.openai_api_key),
                weather_available=weather_client.is_available(),
                news_available=news_client.is_available(),
                gmail_available=gmail_client.is_available(),
                calendar_available=calendar_client.is_available(),
                smart_home_enabled=config.enable_smart_home,
                face_recognition_enabled=config.enable_face_recognition,
                camera_available=camera_device.is_available(),
                audio_available=audio_device.is_available(),
                uptime_seconds=0,  # TODO: Implement uptime tracking
                version="1.0.0"
            )
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            raise HTTPException(status_code=500, detail="Failed to get status")
    
    # Voice Command Endpoints
    @router.post("/command", response_model=CommandResponse)
    async def process_command(request: CommandRequest):
        """Process a voice command."""
        try:
            response = await command_processor.process(request.command)
            
            return CommandResponse(
                success=True,
                response=response or "Command processed successfully",
                command=request.command
            )
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            return CommandResponse(
                success=False,
                response=f"Error processing command: {str(e)}",
                command=request.command
            )
    
    @router.post("/speak")
    async def speak_text(request: VoiceTestRequest):
        """Make the assistant speak text."""
        try:
            success = await voice_speaker.speak(request.text)
            
            if success:
                return {"success": True, "message": "Text spoken successfully"}
            else:
                raise HTTPException(status_code=500, detail="Failed to speak text")
        except Exception as e:
            logger.error(f"Error speaking text: {e}")
            raise HTTPException(status_code=500, detail="Failed to speak text")
    
    @router.get("/listen")
    async def listen_for_command():
        """Listen for a voice command."""
        try:
            command = await voice_listener.listen()
            
            if command:
                return {"success": True, "command": command}
            else:
                return {"success": False, "command": None, "message": "No command heard"}
        except Exception as e:
            logger.error(f"Error listening for command: {e}")
            raise HTTPException(status_code=500, detail="Failed to listen for command")
    
    # Device Information Endpoints
    @router.get("/devices/audio", response_model=DeviceInfo)
    async def get_audio_devices():
        """Get available audio devices."""
        try:
            devices = audio_device.get_audio_devices()
            return DeviceInfo(
                type="audio",
                devices=devices,
                current_input=config.microphone_index,
                current_output=config.speaker_index
            )
        except Exception as e:
            logger.error(f"Error getting audio devices: {e}")
            raise HTTPException(status_code=500, detail="Failed to get audio devices")
    
    @router.get("/devices/camera")
    async def get_camera_devices():
        """Get available camera devices."""
        try:
            cameras = camera_device.get_available_cameras()
            camera_info = camera_device.get_camera_info()
            
            return {
                "available_cameras": cameras,
                "current_camera": config.camera_index,
                "camera_info": camera_info
            }
        except Exception as e:
            logger.error(f"Error getting camera devices: {e}")
            raise HTTPException(status_code=500, detail="Failed to get camera devices")
    
    @router.post("/devices/test-microphone")
    async def test_microphone(device_index: Optional[int] = None):
        """Test microphone functionality."""
        try:
            result = audio_device.test_microphone(device_index=device_index)
            return result
        except Exception as e:
            logger.error(f"Error testing microphone: {e}")
            raise HTTPException(status_code=500, detail="Failed to test microphone")
    
    # Weather Endpoints
    @router.get("/weather", response_model=WeatherResponse)
    async def get_weather(location: Optional[str] = None):
        """Get current weather information."""
        try:
            weather_data = await weather_client.get_current_weather(location)
            
            if weather_data:
                return WeatherResponse(
                    location=weather_data['location'],
                    temperature=weather_data['temperature'],
                    description=weather_data['description'],
                    humidity=weather_data['humidity'],
                    wind_speed=weather_data['wind_speed'],
                    formatted_message=weather_client.format_weather_message(weather_data)
                )
            else:
                raise HTTPException(status_code=404, detail="Weather data not available")
        except Exception as e:
            logger.error(f"Error getting weather: {e}")
            raise HTTPException(status_code=500, detail="Failed to get weather")
    
    @router.get("/weather/forecast")
    async def get_weather_forecast(location: Optional[str] = None, days: int = 5):
        """Get weather forecast."""
        try:
            forecast_data = await weather_client.get_forecast(location, days)
            
            if forecast_data:
                return {"forecast": forecast_data, "location": location or config.default_location}
            else:
                raise HTTPException(status_code=404, detail="Forecast data not available")
        except Exception as e:
            logger.error(f"Error getting forecast: {e}")
            raise HTTPException(status_code=500, detail="Failed to get forecast")
    
    # Stock Endpoints
    @router.get("/stocks/{symbol}", response_model=StockResponse)
    async def get_stock_price(symbol: str):
        """Get stock price for a symbol."""
        try:
            stock_data = await stock_client.get_stock_price(symbol)
            
            if stock_data:
                return StockResponse(
                    symbol=stock_data['symbol'],
                    name=stock_data['name'],
                    current_price=stock_data['current_price'],
                    change=stock_data['change'],
                    change_percent=stock_data['change_percent'],
                    formatted_message=stock_client.format_stock_message(stock_data)
                )
            else:
                raise HTTPException(status_code=404, detail="Stock data not available")
        except Exception as e:
            logger.error(f"Error getting stock data: {e}")
            raise HTTPException(status_code=500, detail="Failed to get stock data")
    
    @router.get("/stocks")
    async def get_portfolio():
        """Get portfolio summary."""
        try:
            stocks = await stock_client.get_multiple_stocks()
            return {
                "stocks": stocks,
                "summary": stock_client.format_portfolio_message(stocks)
            }
        except Exception as e:
            logger.error(f"Error getting portfolio: {e}")
            raise HTTPException(status_code=500, detail="Failed to get portfolio")
    
    # News Endpoints
    @router.get("/news", response_model=NewsResponse)
    async def get_news(category: Optional[str] = None, count: int = 5):
        """Get latest news headlines."""
        try:
            if category:
                articles = await news_client.get_news_by_category(category, count)
            else:
                articles = await news_client.get_top_headlines(count=count)
            
            return NewsResponse(
                articles=articles,
                count=len(articles),
                category=category or "general",
                formatted_message=news_client.format_news_headlines(articles)
            )
        except Exception as e:
            logger.error(f"Error getting news: {e}")
            raise HTTPException(status_code=500, detail="Failed to get news")
    
    @router.get("/news/search")
    async def search_news(query: str, count: int = 10):
        """Search news articles."""
        try:
            articles = await news_client.search_news(query, count)
            return {
                "articles": articles,
                "query": query,
                "count": len(articles),
                "summary": news_client.format_news_summary(articles)
            }
        except Exception as e:
            logger.error(f"Error searching news: {e}")
            raise HTTPException(status_code=500, detail="Failed to search news")
    
    # Email Endpoints
    @router.post("/email/send")
    async def send_email(request: EmailRequest):
        """Send an email."""
        try:
            success = await gmail_client.send_email(
                to=request.to,
                subject=request.subject,
                body=request.body,
                cc=request.cc,
                bcc=request.bcc
            )
            
            if success:
                return {"success": True, "message": "Email sent successfully"}
            else:
                raise HTTPException(status_code=500, detail="Failed to send email")
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            raise HTTPException(status_code=500, detail="Failed to send email")
    
    @router.get("/email/recent")
    async def get_recent_emails(count: int = 10):
        """Get recent emails."""
        try:
            emails = await gmail_client.get_recent_emails(count)
            return {"emails": emails, "count": len(emails)}
        except Exception as e:
            logger.error(f"Error getting recent emails: {e}")
            raise HTTPException(status_code=500, detail="Failed to get recent emails")
    
    # Calendar Endpoints
    @router.get("/calendar/events")
    async def get_calendar_events(count: int = 10):
        """Get upcoming calendar events."""
        try:
            events = await calendar_client.get_upcoming_events(count)
            return {
                "events": events,
                "count": len(events),
                "summary": calendar_client.format_events_message(events)
            }
        except Exception as e:
            logger.error(f"Error getting calendar events: {e}")
            raise HTTPException(status_code=500, detail="Failed to get calendar events")
    
    # Camera Endpoints
    @router.post("/camera/photo")
    async def take_photo(filename: Optional[str] = None):
        """Take a photo with the camera."""
        try:
            photo_path = camera_device.take_photo(filename)
            
            if photo_path:
                return {"success": True, "photo_path": photo_path}
            else:
                raise HTTPException(status_code=500, detail="Failed to take photo")
        except Exception as e:
            logger.error(f"Error taking photo: {e}")
            raise HTTPException(status_code=500, detail="Failed to take photo")
    
    @router.get("/camera/stream")
    async def camera_stream():
        """Stream camera feed."""
        try:
            if not camera_device.is_available():
                raise HTTPException(status_code=404, detail="Camera not available")
            
            def generate_frames():
                for frame_bytes in camera_device.stream_camera():
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            return StreamingResponse(
                generate_frames(),
                media_type="multipart/x-mixed-replace; boundary=frame"
            )
        except Exception as e:
            logger.error(f"Error streaming camera: {e}")
            raise HTTPException(status_code=500, detail="Failed to stream camera")
    
    # File Upload Endpoints
    @router.post("/upload")
    async def upload_file(file: UploadFile = File(...), description: str = Form("")):
        """Upload a file."""
        try:
            # Create uploads directory
            uploads_dir = Path("data/uploads")
            uploads_dir.mkdir(parents=True, exist_ok=True)
            
            # Save file
            file_path = uploads_dir / file.filename
            
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            logger.info(f"File uploaded: {file_path}")
            
            return {
                "success": True,
                "filename": file.filename,
                "file_path": str(file_path),
                "size": len(content),
                "description": description
            }
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            raise HTTPException(status_code=500, detail="Failed to upload file")
    
    # Configuration Endpoints
    @router.get("/config")
    async def get_config():
        """Get current configuration (non-sensitive data only)."""
        try:
            return config.to_dict()
        except Exception as e:
            logger.error(f"Error getting config: {e}")
            raise HTTPException(status_code=500, detail="Failed to get configuration")
    
    return router
