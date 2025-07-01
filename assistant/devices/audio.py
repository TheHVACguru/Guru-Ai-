"""
Audio device management for microphone and speaker operations.
"""

import pyaudio
import sounddevice as sd
import numpy as np
import wave
import threading
import time
from typing import Optional, List, Dict, Any, Callable
from assistant.utils.logger import setup_logger

logger = setup_logger(__name__)

class AudioDevice:
    """Audio device manager for microphone and speaker operations."""
    
    def __init__(self, config):
        """Initialize audio device manager."""
        self.config = config
        self.pa = pyaudio.PyAudio()
        self.recording_stream = None
        self.playback_stream = None
        self.is_recording = False
        self.is_playing = False
        
        # Audio settings
        self.sample_rate = config.sample_rate
        self.chunk_size = config.chunk_size
        self.channels = 1  # Mono for voice
        self.format = pyaudio.paInt16
        
        logger.info("Audio device manager initialized")
    
    def get_audio_devices(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get available audio input and output devices."""
        try:
            devices = {
                'input': [],
                'output': []
            }
            
            device_count = self.pa.get_device_count()
            
            for i in range(device_count):
                device_info = self.pa.get_device_info_by_index(i)
                
                device_data = {
                    'index': i,
                    'name': device_info['name'],
                    'channels': device_info['maxInputChannels'] if device_info['maxInputChannels'] > 0 else device_info['maxOutputChannels'],
                    'sample_rate': int(device_info['defaultSampleRate']),
                    'api': self.pa.get_host_api_info_by_index(device_info['hostApi'])['name']
                }
                
                # Input device
                if device_info['maxInputChannels'] > 0:
                    device_data['type'] = 'input'
                    device_data['channels'] = device_info['maxInputChannels']
                    devices['input'].append(device_data.copy())
                
                # Output device
                if device_info['maxOutputChannels'] > 0:
                    device_data['type'] = 'output'
                    device_data['channels'] = device_info['maxOutputChannels']
                    devices['output'].append(device_data.copy())
            
            logger.info(f"Found {len(devices['input'])} input and {len(devices['output'])} output devices")
            return devices
            
        except Exception as e:
            logger.error(f"Error getting audio devices: {e}")
            return {'input': [], 'output': []}
    
    def test_microphone(self, device_index: Optional[int] = None, duration: float = 3.0) -> Dict[str, Any]:
        """Test microphone by recording for a specified duration."""
        try:
            device_index = device_index or self.config.microphone_index
            
            # Record audio
            audio_data = self.record_audio(duration=duration, device_index=device_index)
            
            if audio_data is None:
                return {
                    'success': False,
                    'error': 'Failed to record audio',
                    'volume_level': 0.0,
                    'duration': 0.0
                }
            
            # Calculate volume level
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            volume_level = np.sqrt(np.mean(audio_array**2))
            max_volume = np.max(np.abs(audio_array))
            
            # Normalize volume level (0.0 to 1.0)
            normalized_volume = min(volume_level / 32767.0, 1.0)
            
            result = {
                'success': True,
                'duration': duration,
                'volume_level': normalized_volume,
                'max_volume': max_volume / 32767.0,
                'sample_rate': self.sample_rate,
                'channels': self.channels
            }
            
            logger.info(f"Microphone test completed: volume={normalized_volume:.3f}")
            return result
            
        except Exception as e:
            logger.error(f"Error testing microphone: {e}")
            return {
                'success': False,
                'error': str(e),
                'volume_level': 0.0,
                'duration': 0.0
            }
    
    def record_audio(self, duration: float, device_index: Optional[int] = None, 
                    filename: Optional[str] = None) -> Optional[bytes]:
        """Record audio for a specified duration."""
        try:
            device_index = device_index or self.config.microphone_index
            
            # Configure stream
            stream = self.pa.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=self.chunk_size
            )
            
            logger.info(f"Recording audio for {duration} seconds...")
            
            frames = []
            frames_to_record = int(self.sample_rate / self.chunk_size * duration)
            
            for _ in range(frames_to_record):
                data = stream.read(self.chunk_size)
                frames.append(data)
            
            stream.stop_stream()
            stream.close()
            
            # Combine all frames
            audio_data = b''.join(frames)
            
            # Save to file if filename provided
            if filename:
                self.save_audio(audio_data, filename)
            
            logger.info(f"Audio recording completed: {len(audio_data)} bytes")
            return audio_data
            
        except Exception as e:
            logger.error(f"Error recording audio: {e}")
            return None
    
    def play_audio(self, audio_data: bytes, device_index: Optional[int] = None) -> bool:
        """Play audio data."""
        try:
            device_index = device_index or self.config.speaker_index
            
            # Configure stream
            stream = self.pa.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                output=True,
                output_device_index=device_index,
                frames_per_buffer=self.chunk_size
            )
            
            logger.info("Playing audio...")
            
            # Play audio in chunks
            for i in range(0, len(audio_data), self.chunk_size * 2):  # 2 bytes per sample
                chunk = audio_data[i:i + self.chunk_size * 2]
                stream.write(chunk)
            
            stream.stop_stream()
            stream.close()
            
            logger.info("Audio playback completed")
            return True
            
        except Exception as e:
            logger.error(f"Error playing audio: {e}")
            return False
    
    def save_audio(self, audio_data: bytes, filename: str) -> bool:
        """Save audio data to WAV file."""
        try:
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.pa.get_sample_size(self.format))
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_data)
            
            logger.info(f"Audio saved to: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving audio: {e}")
            return False
    
    def load_audio(self, filename: str) -> Optional[bytes]:
        """Load audio data from WAV file."""
        try:
            with wave.open(filename, 'rb') as wf:
                audio_data = wf.readframes(wf.getnframes())
            
            logger.info(f"Audio loaded from: {filename}")
            return audio_data
            
        except Exception as e:
            logger.error(f"Error loading audio: {e}")
            return None
    
    def start_real_time_monitoring(self, callback: Callable[[np.ndarray], None], 
                                  device_index: Optional[int] = None) -> bool:
        """Start real-time audio monitoring with callback."""
        try:
            device_index = device_index or self.config.microphone_index
            
            def audio_callback(indata, frames, time, status):
                if status:
                    logger.warning(f"Audio callback status: {status}")
                
                # Convert to numpy array and call user callback
                audio_array = indata[:, 0] if indata.ndim > 1 else indata
                callback(audio_array)
            
            # Start stream
            self.monitoring_stream = sd.InputStream(
                device=device_index,
                channels=1,
                samplerate=self.sample_rate,
                blocksize=self.chunk_size,
                callback=audio_callback
            )
            
            self.monitoring_stream.start()
            logger.info("Real-time audio monitoring started")
            return True
            
        except Exception as e:
            logger.error(f"Error starting audio monitoring: {e}")
            return False
    
    def stop_real_time_monitoring(self):
        """Stop real-time audio monitoring."""
        try:
            if hasattr(self, 'monitoring_stream') and self.monitoring_stream:
                self.monitoring_stream.stop()
                self.monitoring_stream.close()
                delattr(self, 'monitoring_stream')
                logger.info("Real-time audio monitoring stopped")
        except Exception as e:
            logger.error(f"Error stopping audio monitoring: {e}")
    
    def get_volume_level(self, device_index: Optional[int] = None, duration: float = 0.1) -> float:
        """Get current microphone volume level."""
        try:
            device_index = device_index or self.config.microphone_index
            
            # Record brief audio sample
            stream = self.pa.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=self.chunk_size
            )
            
            frames_to_read = int(self.sample_rate * duration / self.chunk_size)
            audio_data = b''
            
            for _ in range(frames_to_read):
                data = stream.read(self.chunk_size)
                audio_data += data
            
            stream.stop_stream()
            stream.close()
            
            # Calculate RMS volume
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            rms = np.sqrt(np.mean(audio_array**2))
            
            # Normalize to 0.0-1.0 range
            normalized_volume = min(rms / 32767.0, 1.0)
            
            return normalized_volume
            
        except Exception as e:
            logger.error(f"Error getting volume level: {e}")
            return 0.0
    
    def calibrate_microphone(self, device_index: Optional[int] = None, 
                           duration: float = 2.0) -> Dict[str, float]:
        """Calibrate microphone to determine ambient noise level."""
        try:
            device_index = device_index or self.config.microphone_index
            
            logger.info(f"Calibrating microphone for {duration} seconds...")
            
            # Record ambient noise
            audio_data = self.record_audio(duration=duration, device_index=device_index)
            
            if audio_data is None:
                return {'ambient_level': 0.0, 'recommended_threshold': 0.1}
            
            # Analyze audio
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Calculate statistics
            rms = np.sqrt(np.mean(audio_array**2))
            max_amplitude = np.max(np.abs(audio_array))
            
            # Normalize
            ambient_level = rms / 32767.0
            max_level = max_amplitude / 32767.0
            
            # Recommend threshold (ambient + margin)
            recommended_threshold = min(ambient_level * 3.0, 0.1)
            
            calibration_data = {
                'ambient_level': ambient_level,
                'max_level': max_level,
                'recommended_threshold': recommended_threshold,
                'sample_rate': self.sample_rate,
                'duration': duration
            }
            
            logger.info(f"Microphone calibration complete: ambient={ambient_level:.4f}")
            return calibration_data
            
        except Exception as e:
            logger.error(f"Error calibrating microphone: {e}")
            return {'ambient_level': 0.0, 'recommended_threshold': 0.1}
    
    def get_default_devices(self) -> Dict[str, Optional[int]]:
        """Get default input and output device indices."""
        try:
            default_input = self.pa.get_default_input_device_info()
            default_output = self.pa.get_default_output_device_info()
            
            return {
                'input': default_input['index'] if default_input else None,
                'output': default_output['index'] if default_output else None
            }
            
        except Exception as e:
            logger.error(f"Error getting default devices: {e}")
            return {'input': None, 'output': None}
    
    def cleanup(self):
        """Clean up audio resources."""
        try:
            # Stop any active streams
            if hasattr(self, 'monitoring_stream'):
                self.stop_real_time_monitoring()
            
            if self.recording_stream:
                self.recording_stream.stop_stream()
                self.recording_stream.close()
            
            if self.playback_stream:
                self.playback_stream.stop_stream()
                self.playback_stream.close()
            
            # Terminate PyAudio
            self.pa.terminate()
            
            logger.info("Audio device cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during audio cleanup: {e}")
    
    def is_available(self) -> bool:
        """Check if audio devices are available."""
        devices = self.get_audio_devices()
        return len(devices['input']) > 0 and len(devices['output']) > 0
