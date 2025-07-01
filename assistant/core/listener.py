"""
Voice listener for processing user commands.
"""

import asyncio
from typing import Optional
from assistant.core.speech import SpeechRecognizer
from assistant.utils.logger import setup_logger

logger = setup_logger(__name__)

class VoiceListener:
    """Voice listener for processing user commands."""
    
    def __init__(self, config):
        """Initialize voice listener."""
        self.config = config
        self.speech_recognizer = SpeechRecognizer(config)
        
    async def listen(self, timeout: Optional[float] = None) -> Optional[str]:
        """Listen for user command and return recognized text."""
        try:
            timeout = timeout or self.config.listener_timeout
            
            logger.debug("Listening for command...")
            command = await self.speech_recognizer.listen_and_recognize(
                timeout=timeout,
                phrase_limit=self.config.listener_phrase_limit
            )
            
            if command:
                command = command.strip()
                logger.info(f"Command recognized: {command}")
                return command
            else:
                logger.debug("No command recognized")
                return None
                
        except Exception as e:
            logger.error(f"Error in voice listener: {e}")
            return None
    
    def cleanup(self):
        """Clean up resources."""
        # SpeechRecognizer doesn't need explicit cleanup
        pass
