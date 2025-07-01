"""
Open Source Voice Assistant
A comprehensive voice-activated natural language UI.
"""

__version__ = "1.0.0"
__author__ = "Open Source Community"
__license__ = "MIT"

from assistant.config import Config
from assistant.core.wake_word import WakeWordDetector
from assistant.core.listener import VoiceListener
from assistant.core.speaker import VoiceSpeaker

__all__ = [
    "Config",
    "WakeWordDetector", 
    "VoiceListener",
    "VoiceSpeaker"
]
