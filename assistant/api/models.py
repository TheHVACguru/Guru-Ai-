"""
Pydantic models for API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# Request Models
class CommandRequest(BaseModel):
    """Request model for voice commands."""
    command: str = Field(..., description="The voice command to process")
    source: Optional[str] = Field("api", description="Source of the command")

class VoiceTestRequest(BaseModel):
    """Request model for voice testing."""
    text: str = Field(..., description="Text to speak")
    voice_index: Optional[int] = Field(None, description="Voice index to use")

class EmailRequest(BaseModel):
    """Request model for sending emails."""
    to: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body")
    cc: Optional[str] = Field(None, description="CC email address")
    bcc: Optional[str] = Field(None, description="BCC email address")

class CalendarEventRequest(BaseModel):
    """Request model for creating calendar events."""
    title: str = Field(..., description="Event title")
    start_time: datetime = Field(..., description="Event start time")
    end_time: datetime = Field(..., description="Event end time")
    description: Optional[str] = Field("", description="Event description")
    location: Optional[str] = Field("", description="Event location")
    attendees: Optional[List[str]] = Field([], description="List of attendee emails")

class SmartHomeRequest(BaseModel):
    """Request model for smart home control."""
    device_type: str = Field(..., description="Type of device (lights, tv, roku)")
    action: str = Field(..., description="Action to perform")
    device_id: Optional[str] = Field(None, description="Specific device ID")
    parameters: Optional[Dict[str, Any]] = Field({}, description="Additional parameters")

# Response Models
class CommandResponse(BaseModel):
    """Response model for voice commands."""
    success: bool = Field(..., description="Whether the command was successful")
    response: str = Field(..., description="Response message")
    command: str = Field(..., description="Original command")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)

class StatusResponse(BaseModel):
    """Response model for system status."""
    status: str = Field(..., description="System status")
    wake_word: str = Field(..., description="Current wake word")
    voice_recognition: bool = Field(..., description="Voice recognition status")
    speech_synthesis: bool = Field(..., description="Speech synthesis status")
    api_server: bool = Field(..., description="API server status")
    openai_available: bool = Field(..., description="OpenAI availability")
    weather_available: bool = Field(..., description="Weather service availability")
    news_available: bool = Field(..., description="News service availability")
    gmail_available: bool = Field(..., description="Gmail service availability")
    calendar_available: bool = Field(..., description="Calendar service availability")
    smart_home_enabled: bool = Field(..., description="Smart home features enabled")
    face_recognition_enabled: bool = Field(..., description="Face recognition enabled")
    camera_available: bool = Field(..., description="Camera availability")
    audio_available: bool = Field(..., description="Audio devices availability")
    uptime_seconds: int = Field(..., description="System uptime in seconds")
    version: str = Field(..., description="System version")

class WeatherResponse(BaseModel):
    """Response model for weather information."""
    location: str = Field(..., description="Location name")
    temperature: float = Field(..., description="Temperature in Celsius")
    description: str = Field(..., description="Weather description")
    humidity: int = Field(..., description="Humidity percentage")
    wind_speed: float = Field(..., description="Wind speed")
    formatted_message: str = Field(..., description="Formatted weather message")

class StockResponse(BaseModel):
    """Response model for stock information."""
    symbol: str = Field(..., description="Stock symbol")
    name: str = Field(..., description="Company name")
    current_price: float = Field(..., description="Current stock price")
    change: float = Field(..., description="Price change")
    change_percent: float = Field(..., description="Percentage change")
    formatted_message: str = Field(..., description="Formatted stock message")

class NewsResponse(BaseModel):
    """Response model for news information."""
    articles: List[Dict[str, Any]] = Field(..., description="List of news articles")
    count: int = Field(..., description="Number of articles")
    category: str = Field(..., description="News category")
    formatted_message: str = Field(..., description="Formatted news message")

class DeviceInfo(BaseModel):
    """Response model for device information."""
    type: str = Field(..., description="Device type")
    devices: Dict[str, List[Dict[str, Any]]] = Field(..., description="Available devices")
    current_input: Optional[int] = Field(None, description="Current input device index")
    current_output: Optional[int] = Field(None, description="Current output device index")

class VoiceInfo(BaseModel):
    """Response model for voice information."""
    voices: List[Dict[str, Any]] = Field(..., description="Available voices")
    current_voice: Optional[str] = Field(None, description="Current voice name")
    voice_rate: int = Field(..., description="Current speech rate")
    voice_volume: float = Field(..., description="Current voice volume")

class CameraInfo(BaseModel):
    """Response model for camera information."""
    available_cameras: List[Dict[str, Any]] = Field(..., description="Available cameras")
    current_camera: int = Field(..., description="Current camera index")
    face_recognition_enabled: bool = Field(..., description="Face recognition status")
    known_faces_count: int = Field(..., description="Number of known faces")

class ErrorResponse(BaseModel):
    """Response model for errors."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Smart Home Models
class LightControl(BaseModel):
    """Model for light control parameters."""
    action: str = Field(..., description="Action: on, off, toggle, brightness, color")
    brightness: Optional[int] = Field(None, description="Brightness level (0-255)")
    color: Optional[str] = Field(None, description="Color name or RGB values")
    device_ip: Optional[str] = Field(None, description="Specific device IP")

class TVControl(BaseModel):
    """Model for TV control parameters."""
    action: str = Field(..., description="Action: on, off, volume_up, volume_down, mute, channel, app")
    volume: Optional[int] = Field(None, description="Volume level")
    channel: Optional[str] = Field(None, description="Channel number or name")
    app: Optional[str] = Field(None, description="App name to launch")

class RokuControl(BaseModel):
    """Model for Roku control parameters."""
    action: str = Field(..., description="Action: home, back, up, down, left, right, select, play, pause")
    app: Optional[str] = Field(None, description="App name to launch")

# Analytics Models
class UsageStats(BaseModel):
    """Model for usage statistics."""
    total_commands: int = Field(..., description="Total commands processed")
    successful_commands: int = Field(..., description="Successful commands")
    failed_commands: int = Field(..., description="Failed commands")
    most_used_features: List[str] = Field(..., description="Most used features")
    average_response_time: float = Field(..., description="Average response time in seconds")

class SystemMetrics(BaseModel):
    """Model for system metrics."""
    cpu_usage: float = Field(..., description="CPU usage percentage")
    memory_usage: float = Field(..., description="Memory usage percentage")
    disk_usage: float = Field(..., description="Disk usage percentage")
    network_status: bool = Field(..., description="Network connectivity status")
    active_connections: int = Field(..., description="Active API connections")
