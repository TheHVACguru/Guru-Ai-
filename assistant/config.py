"""
Configuration management for the Voice Assistant.
"""

import os
from pathlib import Path
from typing import Optional, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for Voice Assistant."""
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        
        # Core Settings
        self.wake_word: str = os.getenv("WAKE_WORD", "assistant")
        self.sensitivity: float = float(os.getenv("SENSITIVITY", "0.5"))
        self.language: str = os.getenv("LANGUAGE", "en-US")
        self.timezone: str = os.getenv("TIMEZONE", "UTC")
        
        # Voice Settings
        self.voice_name: Optional[str] = os.getenv("VOICE_NAME")
        self.voice_rate: int = int(os.getenv("VOICE_RATE", "200"))
        self.voice_pitch: int = int(os.getenv("VOICE_PITCH", "50"))
        self.voice_volume: float = float(os.getenv("VOICE_VOLUME", "0.8"))
        
        # Audio Settings
        self.microphone_index: Optional[int] = self._get_int_env("MICROPHONE_INDEX")
        self.speaker_index: Optional[int] = self._get_int_env("SPEAKER_INDEX")
        self.sample_rate: int = int(os.getenv("SAMPLE_RATE", "16000"))
        self.chunk_size: int = int(os.getenv("CHUNK_SIZE", "1024"))
        
        # Listener Settings
        self.listener_timeout: float = float(os.getenv("LISTENER_TIMEOUT", "5.0"))
        self.listener_phrase_limit: float = float(os.getenv("LISTENER_PHRASE_LIMIT", "10.0"))
        self.speech_timeout: float = float(os.getenv("SPEECH_TIMEOUT", "15.0"))
        
        # API Settings
        self.enable_api: bool = self._get_bool_env("ENABLE_API", True)
        self.api_host: str = os.getenv("API_HOST", "0.0.0.0")
        self.api_port: int = int(os.getenv("API_PORT", "8000"))
        self.api_token: str = os.getenv("API_TOKEN", "default_token_change_me")
        self.cors_origins: List[str] = self._get_list_env("CORS_ORIGINS", ["*"])
        
        # Web UI Settings
        self.enable_web_ui: bool = self._get_bool_env("ENABLE_WEB_UI", True)
        self.web_ui_port: int = int(os.getenv("WEB_UI_PORT", "5000"))
        
        # OpenAI Settings
        self.openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
        self.openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o")
        self.openai_max_tokens: int = int(os.getenv("OPENAI_MAX_TOKENS", "500"))
        
        # Google Services
        self.google_credentials_path: Optional[str] = os.getenv("GOOGLE_CREDENTIALS_PATH")
        self.gmail_user: str = os.getenv("GMAIL_USER", "")
        
        # Weather Settings
        self.weather_api_key: str = os.getenv("WEATHER_API_KEY", "")
        self.default_location: str = os.getenv("DEFAULT_LOCATION", "New York, NY")
        
        # Stock Settings
        self.stock_api_key: str = os.getenv("STOCK_API_KEY", "")
        self.default_stocks: List[str] = self._get_list_env("DEFAULT_STOCKS", ["AAPL", "GOOGL", "MSFT"])
        
        # News Settings
        self.news_api_key: str = os.getenv("NEWS_API_KEY", "")
        self.news_sources: List[str] = self._get_list_env("NEWS_SOURCES", ["bbc-news", "cnn", "reuters"])
        
        # Telegram Settings
        self.telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")
        
        # Smart Home Settings
        self.enable_smart_home: bool = self._get_bool_env("ENABLE_SMART_HOME", False)
        self.magic_home_devices: List[str] = self._get_list_env("MAGIC_HOME_DEVICES", [])
        self.lg_tv_ip: str = os.getenv("LG_TV_IP", "")
        self.roku_ip: str = os.getenv("ROKU_IP", "")
        
        # Camera Settings
        self.enable_face_recognition: bool = self._get_bool_env("ENABLE_FACE_RECOGNITION", False)
        self.camera_index: int = int(os.getenv("CAMERA_INDEX", "0"))
        self.face_recognition_tolerance: float = float(os.getenv("FACE_RECOGNITION_TOLERANCE", "0.6"))
        
        # Security Settings
        self.encryption_key: str = os.getenv("ENCRYPTION_KEY", "default_key_change_me")
        self.jwt_secret: str = os.getenv("JWT_SECRET", "default_jwt_secret_change_me")
        self.jwt_expiry_hours: int = int(os.getenv("JWT_EXPIRY_HOURS", "24"))
        
        # Logging Settings
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
        self.log_file: str = os.getenv("LOG_FILE", "assistant.log")
        self.max_log_size: int = int(os.getenv("MAX_LOG_SIZE", "10485760"))  # 10MB
        
        # Performance Settings
        self.max_workers: int = int(os.getenv("MAX_WORKERS", "4"))
        self.request_timeout: float = float(os.getenv("REQUEST_TIMEOUT", "30.0"))
        self.enable_caching: bool = self._get_bool_env("ENABLE_CACHING", True)
        
        # Development Settings
        self.debug_mode: bool = self._get_bool_env("DEBUG_MODE", False)
        self.enable_profiling: bool = self._get_bool_env("ENABLE_PROFILING", False)
        
    def _get_bool_env(self, key: str, default: bool = False) -> bool:
        """Get boolean environment variable."""
        value = os.getenv(key, str(default)).lower()
        return value in ("true", "1", "yes", "on")
    
    def _get_int_env(self, key: str, default: Optional[int] = None) -> Optional[int]:
        """Get integer environment variable."""
        value = os.getenv(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            return default
    
    def _get_list_env(self, key: str, default: List[str] = None) -> List[str]:
        """Get list environment variable (comma-separated)."""
        if default is None:
            default = []
        value = os.getenv(key)
        if not value:
            return default
        return [item.strip() for item in value.split(",") if item.strip()]
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of warnings."""
        warnings = []
        
        # Check required API keys
        if not self.openai_api_key:
            warnings.append("OpenAI API key not set - AI features will be disabled")
        
        if not self.weather_api_key:
            warnings.append("Weather API key not set - weather features will be disabled")
        
        if not self.news_api_key:
            warnings.append("News API key not set - news features will be disabled")
        
        # Check security settings
        if self.api_token == "default_token_change_me":
            warnings.append("Default API token in use - please change for security")
        
        if self.jwt_secret == "default_jwt_secret_change_me":
            warnings.append("Default JWT secret in use - please change for security")
        
        # Check file paths
        if self.google_credentials_path and not Path(self.google_credentials_path).exists():
            warnings.append(f"Google credentials file not found: {self.google_credentials_path}")
        
        return warnings
    
    def to_dict(self) -> dict:
        """Convert configuration to dictionary (excluding sensitive data)."""
        return {
            "wake_word": self.wake_word,
            "language": self.language,
            "timezone": self.timezone,
            "voice_rate": self.voice_rate,
            "enable_api": self.enable_api,
            "api_host": self.api_host,
            "api_port": self.api_port,
            "enable_web_ui": self.enable_web_ui,
            "enable_smart_home": self.enable_smart_home,
            "enable_face_recognition": self.enable_face_recognition,
            "debug_mode": self.debug_mode
        }
