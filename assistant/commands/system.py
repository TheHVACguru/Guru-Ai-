"""
System control commands for Voice Assistant.
"""

import asyncio
import platform
import subprocess
import psutil
from datetime import datetime
from typing import Optional
from assistant.utils.logger import setup_logger

logger = setup_logger(__name__)

class SystemCommands:
    """System control command handlers."""
    
    def __init__(self, config, voice_speaker):
        """Initialize system commands."""
        self.config = config
        self.voice_speaker = voice_speaker
        self.os_type = platform.system().lower()
        
    async def get_time(self, command: str) -> str:
        """Get current time."""
        try:
            now = datetime.now()
            time_str = now.strftime("%I:%M %p")
            
            # Remove leading zero from hour
            if time_str.startswith("0"):
                time_str = time_str[1:]
            
            response = f"The current time is {time_str}"
            logger.info(f"Time requested: {time_str}")
            return response
            
        except Exception as e:
            logger.error(f"Error getting time: {e}")
            return "I couldn't get the current time."
    
    async def get_date(self, command: str) -> str:
        """Get current date."""
        try:
            now = datetime.now()
            date_str = now.strftime("%A, %B %d, %Y")
            
            response = f"Today is {date_str}"
            logger.info(f"Date requested: {date_str}")
            return response
            
        except Exception as e:
            logger.error(f"Error getting date: {e}")
            return "I couldn't get the current date."
    
    async def control_volume(self, command: str) -> str:
        """Control system volume."""
        try:
            if "up" in command or "increase" in command or "raise" in command:
                success = await self._change_volume("up")
                return "Volume increased" if success else "Couldn't increase volume"
            elif "down" in command or "decrease" in command or "lower" in command:
                success = await self._change_volume("down")
                return "Volume decreased" if success else "Couldn't decrease volume"
            elif "mute" in command:
                success = await self._change_volume("mute")
                return "Volume muted" if success else "Couldn't mute volume"
            elif "unmute" in command:
                success = await self._change_volume("unmute")
                return "Volume unmuted" if success else "Couldn't unmute volume"
            else:
                return "I can increase, decrease, mute, or unmute the volume."
                
        except Exception as e:
            logger.error(f"Error controlling volume: {e}")
            return "I couldn't control the volume."
    
    async def _change_volume(self, action: str) -> bool:
        """Change system volume based on OS."""
        try:
            if self.os_type == "darwin":  # macOS
                if action == "up":
                    subprocess.run(["osascript", "-e", "set volume output volume (output volume of (get volume settings) + 10)"])
                elif action == "down":
                    subprocess.run(["osascript", "-e", "set volume output volume (output volume of (get volume settings) - 10)"])
                elif action == "mute":
                    subprocess.run(["osascript", "-e", "set volume with output muted"])
                elif action == "unmute":
                    subprocess.run(["osascript", "-e", "set volume without output muted"])
                
            elif self.os_type == "windows":  # Windows
                if action == "up":
                    # Use nircmd or similar tool if available
                    try:
                        subprocess.run(["nircmd.exe", "changesysvolume", "6553"])
                    except FileNotFoundError:
                        logger.warning("nircmd not found, volume control not available on Windows")
                        return False
                elif action == "down":
                    try:
                        subprocess.run(["nircmd.exe", "changesysvolume", "-6553"])
                    except FileNotFoundError:
                        return False
                elif action == "mute":
                    try:
                        subprocess.run(["nircmd.exe", "mutesysvolume", "1"])
                    except FileNotFoundError:
                        return False
                elif action == "unmute":
                    try:
                        subprocess.run(["nircmd.exe", "mutesysvolume", "0"])
                    except FileNotFoundError:
                        return False
                        
            elif self.os_type == "linux":  # Linux
                if action == "up":
                    subprocess.run(["amixer", "-D", "pulse", "sset", "Master", "5%+"])
                elif action == "down":
                    subprocess.run(["amixer", "-D", "pulse", "sset", "Master", "5%-"])
                elif action == "mute":
                    subprocess.run(["amixer", "-D", "pulse", "sset", "Master", "mute"])
                elif action == "unmute":
                    subprocess.run(["amixer", "-D", "pulse", "sset", "Master", "unmute"])
            
            return True
            
        except Exception as e:
            logger.error(f"Error changing volume: {e}")
            return False
    
    async def control_brightness(self, command: str) -> str:
        """Control screen brightness."""
        try:
            if "up" in command or "increase" in command or "brighten" in command:
                success = await self._change_brightness("up")
                return "Brightness increased" if success else "Couldn't increase brightness"
            elif "down" in command or "decrease" in command or "dim" in command:
                success = await self._change_brightness("down")
                return "Brightness decreased" if success else "Couldn't decrease brightness"
            else:
                return "I can increase or decrease the screen brightness."
                
        except Exception as e:
            logger.error(f"Error controlling brightness: {e}")
            return "I couldn't control the brightness."
    
    async def _change_brightness(self, action: str) -> bool:
        """Change screen brightness based on OS."""
        try:
            if self.os_type == "darwin":  # macOS
                if action == "up":
                    subprocess.run(["osascript", "-e", "tell application \"System Events\" to key code 144"])
                elif action == "down":
                    subprocess.run(["osascript", "-e", "tell application \"System Events\" to key code 145"])
                    
            elif self.os_type == "windows":  # Windows
                # Windows brightness control is more complex and may require WMI
                logger.warning("Brightness control not implemented for Windows")
                return False
                
            elif self.os_type == "linux":  # Linux
                try:
                    if action == "up":
                        subprocess.run(["xbacklight", "-inc", "10"])
                    elif action == "down":
                        subprocess.run(["xbacklight", "-dec", "10"])
                except FileNotFoundError:
                    logger.warning("xbacklight not found, brightness control not available")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error changing brightness: {e}")
            return False
    
    async def get_system_info(self, command: str) -> str:
        """Get system information."""
        try:
            # Get basic system info
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            response = (
                f"System status: CPU usage is {cpu_percent:.1f}%, "
                f"memory usage is {memory.percent:.1f}%, "
                f"and disk usage is {disk.percent:.1f}%."
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return "I couldn't get the system information."
    
    async def shutdown_system(self, command: str) -> str:
        """Shutdown the system."""
        try:
            # Ask for confirmation
            confirmation = "Are you sure you want to shutdown the system? This will close all applications."
            await self.voice_speaker.speak(confirmation)
            
            # In a real implementation, you'd want to add a confirmation mechanism
            logger.warning("System shutdown requested but not executed (safety)")
            
            return "System shutdown cancelled for safety. Use your system's normal shutdown procedure."
            
        except Exception as e:
            logger.error(f"Error shutting down system: {e}")
            return "I couldn't shutdown the system."
    
    async def restart_system(self, command: str) -> str:
        """Restart the system."""
        try:
            # Ask for confirmation
            confirmation = "Are you sure you want to restart the system? This will close all applications."
            await self.voice_speaker.speak(confirmation)
            
            # In a real implementation, you'd want to add a confirmation mechanism
            logger.warning("System restart requested but not executed (safety)")
            
            return "System restart cancelled for safety. Use your system's normal restart procedure."
            
        except Exception as e:
            logger.error(f"Error restarting system: {e}")
            return "I couldn't restart the system."
    
    async def open_application(self, command: str) -> str:
        """Open an application."""
        try:
            # Extract application name from command
            app_name = None
            
            if "notepad" in command:
                app_name = "notepad" if self.os_type == "windows" else "TextEdit" if self.os_type == "darwin" else "gedit"
            elif "calculator" in command:
                app_name = "calc" if self.os_type == "windows" else "Calculator" if self.os_type == "darwin" else "gnome-calculator"
            elif "browser" in command or "chrome" in command:
                app_name = "chrome" if self.os_type == "windows" else "Google Chrome" if self.os_type == "darwin" else "google-chrome"
            elif "terminal" in command:
                app_name = "cmd" if self.os_type == "windows" else "Terminal" if self.os_type == "darwin" else "gnome-terminal"
            
            if app_name:
                if self.os_type == "windows":
                    subprocess.Popen([app_name])
                elif self.os_type == "darwin":
                    subprocess.Popen(["open", "-a", app_name])
                elif self.os_type == "linux":
                    subprocess.Popen([app_name])
                
                return f"Opening {app_name}"
            else:
                return "I couldn't identify which application to open."
                
        except Exception as e:
            logger.error(f"Error opening application: {e}")
            return "I couldn't open that application."
    
    async def lock_system(self, command: str) -> str:
        """Lock the system."""
        try:
            if self.os_type == "windows":
                subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
            elif self.os_type == "darwin":
                subprocess.run(["/System/Library/CoreServices/Menu Extras/User.menu/Contents/Resources/CGSession", "-suspend"])
            elif self.os_type == "linux":
                subprocess.run(["gnome-screensaver-command", "--lock"])
            
            return "System locked"
            
        except Exception as e:
            logger.error(f"Error locking system: {e}")
            return "I couldn't lock the system."
    
    async def get_battery_status(self, command: str) -> str:
        """Get battery status."""
        try:
            battery = psutil.sensors_battery()
            
            if battery is None:
                return "This device doesn't have a battery or battery information is not available."
            
            percent = battery.percent
            plugged = battery.power_plugged
            
            if plugged:
                status = "charging" if percent < 100 else "fully charged"
            else:
                status = "not charging"
            
            response = f"Battery is at {percent:.0f}% and {status}."
            
            if not plugged and percent < 20:
                response += " Battery is running low."
            
            return response
            
        except Exception as e:
            logger.error(f"Error getting battery status: {e}")
            return "I couldn't get the battery status."
