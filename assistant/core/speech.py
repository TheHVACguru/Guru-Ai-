"""
Speech recognition and synthesis utilities.
"""

import asyncio
import io
import threading
from typing import Optional, List, Dict, Any
import speech_recognition as sr
import pyttsx3
import pyaudio
import wave
from assistant.utils.logger import setup_logger

logger = setup_logger(__name__)

class SpeechRecognizer:
    """Speech recognition using Google Speech API with offline fallback."""
    
    def __init__(self, config):
        """Initialize speech recognizer."""
        self.config = config
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone(device_index=config.microphone_index)
        
        # Adjust for ambient noise
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                logger.info("Microphone calibrated for ambient noise")
        except Exception as e:
            logger.warning(f"Could not calibrate microphone: {e}")
    
    async def listen_and_recognize(self, timeout: Optional[float] = None, phrase_limit: Optional[float] = None) -> Optional[str]:
        """Listen for speech and return recognized text."""
        try:
            timeout = timeout or self.config.listener_timeout
            phrase_limit = phrase_limit or self.config.listener_phrase_limit
            
            # Listen for audio
            with self.microphone as source:
                logger.debug("Listening for speech...")
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout, 
                    phrase_time_limit=phrase_limit
                )
            
            # Recognize speech in a thread to avoid blocking
            def recognize():
                try:
                    # Try Google Speech Recognition first
                    try:
                        text = self.recognizer.recognize_google(audio, language=self.config.language)
                        logger.debug(f"Google Speech Recognition: {text}")
                        return text
                    except sr.RequestError:
                        logger.warning("Google Speech Recognition unavailable, trying offline")
                        
                    # Fallback to offline recognition
                    try:
                        text = self.recognizer.recognize_sphinx(audio)
                        logger.debug(f"Sphinx Recognition: {text}")
                        return text
                    except sr.RequestError:
                        logger.error("Offline speech recognition also unavailable")
                        return None
                        
                except sr.UnknownValueError:
                    logger.debug("Could not understand audio")
                    return None
                except Exception as e:
                    logger.error(f"Speech recognition error: {e}")
                    return None
            
            # Run recognition in thread pool
            loop = asyncio.get_event_loop()
            text = await loop.run_in_executor(None, recognize)
            
            return text
            
        except sr.WaitTimeoutError:
            logger.debug("Listening timeout")
            return None
        except Exception as e:
            logger.error(f"Error in speech recognition: {e}")
            return None

class SpeechSynthesizer:
    """Text-to-speech synthesis."""
    
    def __init__(self, config):
        """Initialize speech synthesizer."""
        self.config = config
        self.engine = pyttsx3.init()
        self._setup_voice()
        
    def _setup_voice(self):
        """Setup voice properties."""
        try:
            voices = self.engine.getProperty('voices')
            
            # Set voice by name if specified
            if self.config.voice_name:
                for voice in voices:
                    if self.config.voice_name.lower() in voice.name.lower():
                        self.engine.setProperty('voice', voice.id)
                        logger.info(f"Voice set to: {voice.name}")
                        break
                else:
                    logger.warning(f"Voice '{self.config.voice_name}' not found, using default")
            
            # Set speech rate
            self.engine.setProperty('rate', self.config.voice_rate)
            
            # Set volume
            self.engine.setProperty('volume', self.config.voice_volume)
            
            logger.info("Speech synthesizer configured")
            
        except Exception as e:
            logger.error(f"Error setting up voice: {e}")
    
    async def speak(self, text: str) -> bool:
        """Speak the given text."""
        try:
            if not text or not text.strip():
                return False
                
            logger.debug(f"Speaking: {text}")
            
            # Run TTS in thread to avoid blocking
            def speak_sync():
                try:
                    self.engine.say(text)
                    self.engine.runAndWait()
                    return True
                except Exception as e:
                    logger.error(f"Error in speech synthesis: {e}")
                    return False
            
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(None, speak_sync)
            
            return success
            
        except Exception as e:
            logger.error(f"Error in speak method: {e}")
            return False
    
    def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get list of available voices."""
        try:
            voices = self.engine.getProperty('voices')
            voice_list = []
            
            for voice in voices:
                voice_info = {
                    'id': voice.id,
                    'name': voice.name,
                    'languages': getattr(voice, 'languages', []),
                    'gender': getattr(voice, 'gender', 'unknown'),
                    'age': getattr(voice, 'age', 'unknown')
                }
                voice_list.append(voice_info)
            
            return voice_list
            
        except Exception as e:
            logger.error(f"Error getting available voices: {e}")
            return []
    
    def set_voice_by_index(self, index: int) -> bool:
        """Set voice by index."""
        try:
            voices = self.engine.getProperty('voices')
            if 0 <= index < len(voices):
                self.engine.setProperty('voice', voices[index].id)
                logger.info(f"Voice set to: {voices[index].name}")
                return True
            else:
                logger.error(f"Voice index {index} out of range")
                return False
        except Exception as e:
            logger.error(f"Error setting voice by index: {e}")
            return False
    
    def cleanup(self):
        """Clean up resources."""
        try:
            if hasattr(self.engine, 'stop'):
                self.engine.stop()
        except Exception as e:
            logger.error(f"Error cleaning up speech synthesizer: {e}")
