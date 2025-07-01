"""
Wake word detection using Porcupine.
"""

import asyncio
import struct
import threading
from typing import Optional
from assistant.utils.logger import setup_logger

# Try to import audio dependencies
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False

try:
    import pvporcupine
    PORCUPINE_AVAILABLE = True
except ImportError:
    PORCUPINE_AVAILABLE = False

logger = setup_logger(__name__)

class WakeWordDetector:
    """Wake word detector using Porcupine."""
    
    def __init__(self, config):
        """Initialize wake word detector."""
        self.config = config
        self.porcupine = None
        self.audio_stream = None
        self.pa = None
        self.running = False
        self.available = PYAUDIO_AVAILABLE and PORCUPINE_AVAILABLE
        
        if self.available:
            self._setup_porcupine()
        else:
            logger.warning("Wake word detection disabled: missing audio dependencies (pyaudio or pvporcupine)")
        
    def _setup_porcupine(self):
        """Setup Porcupine wake word detection."""
        if not self.available:
            return
            
        try:
            # Get available wake word models
            keywords = ["alexa", "bumblebee", "computer", "hey google", "hey siri", "jarvis", "picovoice", "porcupine", "terminator"]
            
            # Use the configured wake word if available, otherwise default
            keyword = self.config.wake_word.lower()
            if keyword not in keywords:
                logger.warning(f"Wake word '{keyword}' not available in built-in models. Using 'porcupine'")
                keyword = "porcupine"
            
            # Note: pvporcupine requires an access key for some versions
            # For now, we'll use a basic setup without key
            self.porcupine = pvporcupine.create(
                keywords=[keyword]
            )
            
            self.pa = pyaudio.PyAudio()
            
            logger.info(f"Wake word detector initialized with keyword: '{keyword}'")
            
        except Exception as e:
            logger.error(f"Failed to initialize wake word detector: {e}")
            self.available = False
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Audio callback for wake word detection."""
        if not self.available or not PYAUDIO_AVAILABLE:
            return (None, None)
            
        try:
            if self.porcupine is None:
                return (None, pyaudio.paComplete)
                
            pcm = struct.unpack_from("h" * self.porcupine.frame_length, in_data)
            keyword_index = self.porcupine.process(pcm)
            
            if keyword_index >= 0:
                logger.debug("Wake word detected!")
                # Set a flag or trigger an event here
                self._wake_word_detected = True
                
        except Exception as e:
            logger.error(f"Error in audio callback: {e}")
            
        return (in_data, pyaudio.paContinue)
    
    async def listen(self) -> bool:
        """Listen for wake word. Returns True when detected."""
        if not self.available or not self.porcupine:
            logger.warning("Wake word detector not available or not initialized")
            return False
            
        try:
            self._wake_word_detected = False
            
            # Open audio stream
            self.audio_stream = self.pa.open(
                rate=self.porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.porcupine.frame_length,
                input_device_index=self.config.microphone_index,
                stream_callback=self._audio_callback
            )
            
            self.audio_stream.start_stream()
            self.running = True
            
            # Wait for wake word detection
            while self.running and not self._wake_word_detected:
                await asyncio.sleep(0.1)
            
            # Clean up stream
            if self.audio_stream:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
                self.audio_stream = None
            
            return self._wake_word_detected
            
        except Exception as e:
            logger.error(f"Error in wake word detection: {e}")
            return False
    
    def stop(self):
        """Stop wake word detection."""
        self.running = False
        
        if self.audio_stream:
            try:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
            except Exception as e:
                logger.error(f"Error stopping audio stream: {e}")
            finally:
                self.audio_stream = None
    
    def cleanup(self):
        """Clean up resources."""
        self.stop()
        
        if self.porcupine:
            try:
                self.porcupine.delete()
            except Exception as e:
                logger.error(f"Error cleaning up Porcupine: {e}")
            finally:
                self.porcupine = None
        
        if self.pa:
            try:
                self.pa.terminate()
            except Exception as e:
                logger.error(f"Error terminating PyAudio: {e}")
            finally:
                self.pa = None
