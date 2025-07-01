"""
Media control commands for Voice Assistant.
"""

import asyncio
import subprocess
import webbrowser
from pathlib import Path
from typing import Optional
from assistant.devices.camera import CameraDevice
from assistant.utils.logger import setup_logger

logger = setup_logger(__name__)

class MediaCommands:
    """Media control command handlers."""
    
    def __init__(self, config, voice_speaker):
        """Initialize media commands."""
        self.config = config
        self.voice_speaker = voice_speaker
        self.camera_device = CameraDevice(config)
        
    async def control_music(self, command: str) -> str:
        """Control music playback."""
        try:
            if "play" in command:
                # Extract song/artist name if provided
                if "spotify" in command:
                    return await self._control_spotify(command)
                elif "youtube" in command:
                    return await self._play_youtube_music(command)
                else:
                    return await self._control_system_music("play")
                    
            elif "stop" in command:
                return await self._control_system_music("stop")
                
            elif "pause" in command:
                return await self._control_system_music("pause")
                
            elif "next" in command or "skip" in command:
                return await self._control_system_music("next")
                
            elif "previous" in command or "back" in command:
                return await self._control_system_music("previous")
                
            elif "volume up" in command:
                return await self._control_system_music("volume_up")
                
            elif "volume down" in command:
                return await self._control_system_music("volume_down")
                
            else:
                return "I can play, pause, stop music, or control volume. Try saying 'play music' or 'pause music'."
                
        except Exception as e:
            logger.error(f"Error controlling music: {e}")
            return "I couldn't control the music."
    
    async def _control_system_music(self, action: str) -> str:
        """Control system music player."""
        try:
            import platform
            os_type = platform.system().lower()
            
            if os_type == "darwin":  # macOS
                if action == "play":
                    subprocess.run(["osascript", "-e", "tell application \"Music\" to play"])
                    return "Playing music"
                elif action == "pause":
                    subprocess.run(["osascript", "-e", "tell application \"Music\" to pause"])
                    return "Music paused"
                elif action == "stop":
                    subprocess.run(["osascript", "-e", "tell application \"Music\" to stop"])
                    return "Music stopped"
                elif action == "next":
                    subprocess.run(["osascript", "-e", "tell application \"Music\" to next track"])
                    return "Playing next track"
                elif action == "previous":
                    subprocess.run(["osascript", "-e", "tell application \"Music\" to previous track"])
                    return "Playing previous track"
                    
            elif os_type == "windows":  # Windows
                # Windows media control is more complex, would need specific implementation
                return "Music control on Windows requires specific media player integration."
                
            elif os_type == "linux":  # Linux
                try:
                    if action == "play":
                        subprocess.run(["playerctl", "play"])
                        return "Playing music"
                    elif action == "pause":
                        subprocess.run(["playerctl", "pause"])
                        return "Music paused"
                    elif action == "stop":
                        subprocess.run(["playerctl", "stop"])
                        return "Music stopped"
                    elif action == "next":
                        subprocess.run(["playerctl", "next"])
                        return "Playing next track"
                    elif action == "previous":
                        subprocess.run(["playerctl", "previous"])
                        return "Playing previous track"
                except FileNotFoundError:
                    return "playerctl not found. Please install it for music control on Linux."
            
            return f"Music {action} command sent"
            
        except Exception as e:
            logger.error(f"Error in system music control: {e}")
            return f"Couldn't {action} music"
    
    async def _control_spotify(self, command: str) -> str:
        """Control Spotify specifically."""
        try:
            # Extract song/artist from command
            song_query = self._extract_music_query(command)
            
            if song_query:
                # Open Spotify with search
                spotify_url = f"spotify:search:{song_query.replace(' ', '%20')}"
                webbrowser.open(spotify_url)
                return f"Searching for '{song_query}' on Spotify"
            else:
                # Just open Spotify
                webbrowser.open("spotify:")
                return "Opening Spotify"
                
        except Exception as e:
            logger.error(f"Error controlling Spotify: {e}")
            return "I couldn't control Spotify."
    
    async def _play_youtube_music(self, command: str) -> str:
        """Play music on YouTube."""
        try:
            song_query = self._extract_music_query(command)
            
            if song_query:
                # Search YouTube for the song
                youtube_url = f"https://www.youtube.com/results?search_query={song_query.replace(' ', '+')}"
                webbrowser.open(youtube_url)
                return f"Searching for '{song_query}' on YouTube"
            else:
                webbrowser.open("https://music.youtube.com")
                return "Opening YouTube Music"
                
        except Exception as e:
            logger.error(f"Error playing YouTube music: {e}")
            return "I couldn't play music on YouTube."
    
    def _extract_music_query(self, command: str) -> Optional[str]:
        """Extract song/artist from command."""
        # Remove command words
        remove_words = ["play", "spotify", "youtube", "music", "song", "on"]
        words = command.split()
        
        # Filter out command words
        query_words = [word for word in words if word.lower() not in remove_words]
        
        if query_words:
            return " ".join(query_words)
        
        return None
    
    async def control_video(self, command: str) -> str:
        """Control video playback."""
        try:
            if "netflix" in command:
                webbrowser.open("https://netflix.com")
                return "Opening Netflix"
                
            elif "youtube" in command:
                video_query = self._extract_video_query(command)
                if video_query:
                    youtube_url = f"https://www.youtube.com/results?search_query={video_query.replace(' ', '+')}"
                    webbrowser.open(youtube_url)
                    return f"Searching for '{video_query}' on YouTube"
                else:
                    webbrowser.open("https://youtube.com")
                    return "Opening YouTube"
                    
            elif "prime" in command or "amazon" in command:
                webbrowser.open("https://www.amazon.com/gp/video/storefront")
                return "Opening Amazon Prime Video"
                
            elif "hulu" in command:
                webbrowser.open("https://hulu.com")
                return "Opening Hulu"
                
            else:
                return "I can open Netflix, YouTube, Amazon Prime, or Hulu. Which would you like?"
                
        except Exception as e:
            logger.error(f"Error controlling video: {e}")
            return "I couldn't control video playback."
    
    def _extract_video_query(self, command: str) -> Optional[str]:
        """Extract video search query from command."""
        remove_words = ["watch", "play", "youtube", "video", "show", "movie", "on"]
        words = command.split()
        
        query_words = [word for word in words if word.lower() not in remove_words]
        
        if query_words:
            return " ".join(query_words)
        
        return None
    
    async def take_photo(self, command: str) -> str:
        """Take a photo with the camera."""
        try:
            if not self.camera_device.is_available():
                return "Camera is not available on this device."
            
            # Extract filename if provided
            filename = None
            if "save as" in command or "name" in command:
                # Simple filename extraction
                words = command.split()
                for i, word in enumerate(words):
                    if word.lower() in ["as", "name"] and i + 1 < len(words):
                        filename = words[i + 1] + ".jpg"
                        break
            
            photo_path = self.camera_device.take_photo(filename)
            
            if photo_path:
                return f"Photo taken and saved as {Path(photo_path).name}"
            else:
                return "I couldn't take a photo."
                
        except Exception as e:
            logger.error(f"Error taking photo: {e}")
            return "I couldn't take a photo."
    
    async def record_video(self, command: str) -> str:
        """Record a video (simplified implementation)."""
        try:
            # This would require more complex video recording implementation
            return "Video recording is not implemented yet. I can take photos instead."
            
        except Exception as e:
            logger.error(f"Error recording video: {e}")
            return "I couldn't record a video."
    
    async def control_screen_recording(self, command: str) -> str:
        """Control screen recording."""
        try:
            import platform
            os_type = platform.system().lower()
            
            if "start" in command or "begin" in command:
                if os_type == "darwin":  # macOS
                    # macOS has built-in screen recording
                    subprocess.Popen(["screencapture", "-v", f"screen_recording_{int(asyncio.get_event_loop().time())}.mov"])
                    return "Started screen recording"
                else:
                    return "Screen recording is not implemented for this operating system."
                    
            elif "stop" in command or "end" in command:
                return "Screen recording stopped. (Note: You may need to stop manually)"
                
            else:
                return "I can start or stop screen recording. Try saying 'start screen recording'."
                
        except Exception as e:
            logger.error(f"Error controlling screen recording: {e}")
            return "I couldn't control screen recording."
    
    async def adjust_media_volume(self, command: str) -> str:
        """Adjust media-specific volume."""
        try:
            if "up" in command or "increase" in command:
                return await self._control_system_music("volume_up")
            elif "down" in command or "decrease" in command:
                return await self._control_system_music("volume_down")
            else:
                return "I can increase or decrease media volume."
                
        except Exception as e:
            logger.error(f"Error adjusting media volume: {e}")
            return "I couldn't adjust the media volume."
    
    async def open_media_app(self, command: str) -> str:
        """Open specific media applications."""
        try:
            import platform
            os_type = platform.system().lower()
            
            if "music" in command or "itunes" in command:
                if os_type == "darwin":
                    subprocess.Popen(["open", "-a", "Music"])
                    return "Opening Music app"
                elif os_type == "windows":
                    # Try to open Windows Media Player or default music app
                    subprocess.Popen(["start", "ms-windows-store://pdp/?ProductId=9wzdncrfj3pt"], shell=True)
                    return "Opening Music app"
                    
            elif "photos" in command:
                if os_type == "darwin":
                    subprocess.Popen(["open", "-a", "Photos"])
                    return "Opening Photos app"
                elif os_type == "windows":
                    subprocess.Popen(["start", "ms-photos:"], shell=True)
                    return "Opening Photos app"
                    
            elif "video" in command or "movies" in command:
                if os_type == "darwin":
                    subprocess.Popen(["open", "-a", "QuickTime Player"])
                    return "Opening QuickTime Player"
                elif os_type == "windows":
                    subprocess.Popen(["start", "ms-windows-store://pdp/?ProductId=9wzdncrfj3pt"], shell=True)
                    return "Opening Movies & TV app"
                    
            else:
                return "I can open Music, Photos, or Video apps. Which would you like?"
                
        except Exception as e:
            logger.error(f"Error opening media app: {e}")
            return "I couldn't open that media app."
