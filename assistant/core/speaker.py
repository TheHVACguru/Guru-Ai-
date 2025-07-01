"""
Voice speaker for providing audio responses.
"""

import asyncio
from typing import List, Dict, Any
from assistant.core.speech import SpeechSynthesizer
from assistant.utils.logger import setup_logger

logger = setup_logger(__name__)

class VoiceSpeaker:
    """Voice speaker for providing audio responses."""
    
    def __init__(self, config):
        """Initialize voice speaker."""
        self.config = config
        self.speech_synthesizer = SpeechSynthesizer(config)
        
    async def speak(self, text: str) -> bool:
        """Speak the given text."""
        try:
            if not text or not text.strip():
                logger.warning("Empty text provided to speaker")
                return False
                
            logger.debug(f"Speaking: {text}")
            success = await self.speech_synthesizer.speak(text)
            
            if success:
                logger.debug("Speech completed successfully")
            else:
                logger.warning("Speech synthesis failed")
                
            return success
            
        except Exception as e:
            logger.error(f"Error in voice speaker: {e}")
            return False
    
    def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get list of available voices."""
        return self.speech_synthesizer.get_available_voices()
    
    def set_voice_by_index(self, index: int) -> bool:
        """Set voice by index."""
        return self.speech_synthesizer.set_voice_by_index(index)
    
    async def speak_voices_demo(self):
        """Demonstrate all available voices."""
        voices = self.get_available_voices()
        
        for i, voice in enumerate(voices):
            self.set_voice_by_index(i)
            await self.speak(f"This is voice {i + 1}, {voice['name']}")
            await asyncio.sleep(1)  # Pause between demonstrations
    
    def cleanup(self):
        """Clean up resources."""
        if self.speech_synthesizer:
            self.speech_synthesizer.cleanup()
