"""
Open Source Voice Assistant
A comprehensive voice-activated natural language UI.
"""

__version__ = "1.0.0"
__author__ = "Open Source Community"
__license__ = "MIT"

from assistant.config import Config

# Try to import voice components conditionally
try:
    from assistant.core.wake_word import WakeWordDetector
    WAKE_WORD_AVAILABLE = True
except ImportError:
    WakeWordDetector = None
    WAKE_WORD_AVAILABLE = False

try:
    from assistant.core.listener import VoiceListener
    VOICE_LISTENER_AVAILABLE = True
except ImportError:
    VoiceListener = None
    VOICE_LISTENER_AVAILABLE = False

try:
    from assistant.core.speaker import VoiceSpeaker
    VOICE_SPEAKER_AVAILABLE = True
except ImportError:
    VoiceSpeaker = None
    VOICE_SPEAKER_AVAILABLE = False

__all__ = [
    "Config",
    "WakeWordDetector", 
    "VoiceListener",
    "VoiceSpeaker",
    "WAKE_WORD_AVAILABLE",
    "VOICE_LISTENER_AVAILABLE", 
    "VOICE_SPEAKER_AVAILABLE"
]
