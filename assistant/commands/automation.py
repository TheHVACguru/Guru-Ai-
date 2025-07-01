"""
Automation commands for Voice Assistant.
"""

import asyncio
import re
from typing import Optional, Dict, Any, List
from assistant.devices.smart_home import SmartHomeController
from assistant.utils.logger import setup_logger

logger = setup_logger(__name__)

class AutomationCommands:
    """Automation command handlers for smart home and system automation."""
    
    def __init__(self, config, voice_speaker):
        """Initialize automation commands."""
        self.config = config
        self.voice_speaker = voice_speaker
        self.smart_home = SmartHomeController(config)
        
    async def control_lights(self, command: str) -> str:
        """Control smart lights."""
        try:
            if not self.smart_home.is_available():
                return "Smart home features are not configured."
            
            # Parse light control command
            light_command = self._parse_light_command(command)
            
            if not light_command:
                return "I didn't understand the light command. Try saying 'turn lights on' or 'turn lights off'."
            
            success = await self.smart_home.control_lights(
                action=light_command['action'],
                device_ip=light_command.get('device_ip'),
                color=light_command.get('color'),
                brightness=light_command.get('brightness')
            )
            
            if success:
                action_text = self._format_light_action(light_command)
                return f"Lights {action_text}"
            else:
                return "I couldn't control the lights. Please check your smart home configuration."
                
        except Exception as e:
            logger.error(f"Error controlling lights: {e}")
            return "I encountered an error while controlling the lights."
    
    def _parse_light_command(self, command: str) -> Optional[Dict[str, Any]]:
        """Parse light control command."""
        light_command = {}
        
        # Determine action
        if "on" in command or "turn on" in command:
            light_command['action'] = "on"
        elif "off" in command or "turn off" in command:
            light_command['action'] = "off"
        elif "toggle" in command:
            light_command['action'] = "toggle"
        elif "dim" in command or "brightness" in command:
            light_command['action'] = "brightness"
            # Extract brightness level
            numbers = re.findall(r'\d+', command)
            if numbers:
                # Convert percentage to 0-255 scale
                brightness_percent = min(int(numbers[0]), 100)
                light_command['brightness'] = int((brightness_percent / 100) * 255)
            else:
                light_command['brightness'] = 127  # Default to 50%
        elif "color" in command or "colour" in command:
            light_command['action'] = "color"
            color = self._extract_color(command)
            if color:
                light_command['color'] = color
        else:
            return None
        
        # Extract specific device if mentioned
        if "bedroom" in command:
            light_command['device_name'] = "bedroom"
        elif "living room" in command:
            light_command['device_name'] = "living_room"
        elif "kitchen" in command:
            light_command['device_name'] = "kitchen"
        
        return light_command
    
    def _extract_color(self, command: str) -> Optional[str]:
        """Extract color from command."""
        colors = {
            "red": "red",
            "green": "green",
            "blue": "blue",
            "white": "white",
            "yellow": "yellow",
            "purple": "purple",
            "orange": "orange",
            "pink": "pink",
            "cyan": "cyan",
            "magenta": "magenta"
        }
        
        command_lower = command.lower()
        for color_name, color_value in colors.items():
            if color_name in command_lower:
                return color_value
        
        return None
    
    def _format_light_action(self, light_command: Dict[str, Any]) -> str:
        """Format light action for response."""
        action = light_command['action']
        
        if action == "on":
            return "turned on"
        elif action == "off":
            return "turned off"
        elif action == "toggle":
            return "toggled"
        elif action == "brightness":
            brightness = light_command.get('brightness', 127)
            percentage = int((brightness / 255) * 100)
            return f"set to {percentage}% brightness"
        elif action == "color":
            color = light_command.get('color', 'unknown')
            return f"changed to {color}"
        
        return action
    
    async def control_tv(self, command: str) -> str:
        """Control smart TV."""
        try:
            if not self.smart_home.is_available():
                return "Smart home features are not configured."
            
            # Parse TV control command
            tv_command = self._parse_tv_command(command)
            
            if not tv_command:
                return "I didn't understand the TV command. Try saying 'turn TV on' or 'change channel'."
            
            success = await self.smart_home.control_tv(
                action=tv_command['action'],
                volume=tv_command.get('volume'),
                channel=tv_command.get('channel'),
                app=tv_command.get('app')
            )
            
            if success:
                action_text = self._format_tv_action(tv_command)
                return f"TV {action_text}"
            else:
                return "I couldn't control the TV. Please check your smart home configuration."
                
        except Exception as e:
            logger.error(f"Error controlling TV: {e}")
            return "I encountered an error while controlling the TV."
    
    def _parse_tv_command(self, command: str) -> Optional[Dict[str, Any]]:
        """Parse TV control command."""
        tv_command = {}
        
        # Determine action
        if "on" in command or "turn on" in command:
            tv_command['action'] = "on"
        elif "off" in command or "turn off" in command:
            tv_command['action'] = "off"
        elif "volume up" in command or "louder" in command:
            tv_command['action'] = "volume_up"
        elif "volume down" in command or "quieter" in command:
            tv_command['action'] = "volume_down"
        elif "mute" in command:
            tv_command['action'] = "mute"
        elif "unmute" in command:
            tv_command['action'] = "unmute"
        elif "channel" in command:
            tv_command['action'] = "channel"
            # Extract channel number or name
            numbers = re.findall(r'\d+', command)
            if numbers:
                tv_command['channel'] = numbers[0]
            else:
                # Look for channel names
                if "news" in command:
                    tv_command['channel'] = "news"
                elif "sports" in command:
                    tv_command['channel'] = "sports"
        elif "volume" in command and "set" in command:
            tv_command['action'] = "set_volume"
            numbers = re.findall(r'\d+', command)
            if numbers:
                tv_command['volume'] = min(int(numbers[0]), 100)
        elif any(app in command for app in ["netflix", "youtube", "hulu", "prime", "disney"]):
            tv_command['action'] = "app"
            if "netflix" in command:
                tv_command['app'] = "netflix"
            elif "youtube" in command:
                tv_command['app'] = "youtube"
            elif "hulu" in command:
                tv_command['app'] = "hulu"
            elif "prime" in command:
                tv_command['app'] = "prime video"
            elif "disney" in command:
                tv_command['app'] = "disney plus"
        else:
            return None
        
        return tv_command
    
    def _format_tv_action(self, tv_command: Dict[str, Any]) -> str:
        """Format TV action for response."""
        action = tv_command['action']
        
        if action == "on":
            return "turned on"
        elif action == "off":
            return "turned off"
        elif action == "volume_up":
            return "volume increased"
        elif action == "volume_down":
            return "volume decreased"
        elif action == "mute":
            return "muted"
        elif action == "unmute":
            return "unmuted"
        elif action == "channel":
            channel = tv_command.get('channel', 'unknown')
            return f"changed to channel {channel}"
        elif action == "set_volume":
            volume = tv_command.get('volume', 50)
            return f"volume set to {volume}%"
        elif action == "app":
            app = tv_command.get('app', 'unknown')
            return f"opened {app}"
        
        return action
    
    async def control_roku(self, command: str) -> str:
        """Control Roku device."""
        try:
            if not self.smart_home.is_available():
                return "Smart home features are not configured."
            
            # Parse Roku control command
            roku_command = self._parse_roku_command(command)
            
            if not roku_command:
                return "I didn't understand the Roku command. Try saying 'Roku home' or 'Roku play'."
            
            success = await self.smart_home.control_roku(
                action=roku_command['action'],
                app=roku_command.get('app')
            )
            
            if success:
                action_text = self._format_roku_action(roku_command)
                return f"Roku {action_text}"
            else:
                return "I couldn't control the Roku. Please check your configuration."
                
        except Exception as e:
            logger.error(f"Error controlling Roku: {e}")
            return "I encountered an error while controlling the Roku."
    
    def _parse_roku_command(self, command: str) -> Optional[Dict[str, Any]]:
        """Parse Roku control command."""
        roku_command = {}
        
        # Determine action
        if "home" in command:
            roku_command['action'] = "home"
        elif "back" in command:
            roku_command['action'] = "back"
        elif "up" in command:
            roku_command['action'] = "up"
        elif "down" in command:
            roku_command['action'] = "down"
        elif "left" in command:
            roku_command['action'] = "left"
        elif "right" in command:
            roku_command['action'] = "right"
        elif "select" in command or "ok" in command:
            roku_command['action'] = "select"
        elif "play" in command:
            roku_command['action'] = "play"
        elif "pause" in command:
            roku_command['action'] = "pause"
        elif any(app in command for app in ["netflix", "youtube", "hulu", "disney"]):
            roku_command['action'] = "app"
            if "netflix" in command:
                roku_command['app'] = "netflix"
            elif "youtube" in command:
                roku_command['app'] = "youtube"
            elif "hulu" in command:
                roku_command['app'] = "hulu"
            elif "disney" in command:
                roku_command['app'] = "disney plus"
        else:
            return None
        
        return roku_command
    
    def _format_roku_action(self, roku_command: Dict[str, Any]) -> str:
        """Format Roku action for response."""
        action = roku_command['action']
        
        if action == "app":
            app = roku_command.get('app', 'unknown')
            return f"opened {app}"
        else:
            return f"{action} pressed"
    
    async def control_smart_home(self, command: str) -> str:
        """General smart home control."""
        try:
            if not self.smart_home.is_available():
                return "Smart home features are not configured."
            
            # Check what type of device is being referenced
            if "light" in command or "lamp" in command:
                return await self.control_lights(command)
            elif "tv" in command or "television" in command:
                return await self.control_tv(command)
            elif "roku" in command:
                return await self.control_roku(command)
            else:
                # Get device status
                status = self.smart_home.get_device_status()
                
                device_count = status['total_devices']
                if device_count == 0:
                    return "No smart home devices are currently configured."
                
                response = f"Smart home status: {device_count} devices connected. "
                
                # Report on lights
                if status['lights']:
                    light_count = len(status['lights'])
                    response += f"{light_count} smart lights available. "
                
                # Report on TV
                if status['tv']:
                    response += "Smart TV connected. "
                
                # Report on Roku
                if status['roku']:
                    response += "Roku device connected. "
                
                response += "You can control lights, TV, and Roku with voice commands."
                
                return response
                
        except Exception as e:
            logger.error(f"Error with smart home control: {e}")
            return "I encountered an error with smart home control."
    
    async def discover_devices(self, command: str) -> str:
        """Discover available smart home devices."""
        try:
            if not self.config.enable_smart_home:
                return "Smart home features are disabled. Enable them in the configuration."
            
            discovered = await self.smart_home.discover_devices()
            
            total_devices = sum(len(devices) for devices in discovered.values())
            
            if total_devices == 0:
                return "No smart home devices were discovered on the network."
            
            response = f"Discovered {total_devices} smart home devices: "
            
            if discovered['lights']:
                response += f"{len(discovered['lights'])} lights, "
            
            if discovered['tvs']:
                response += f"{len(discovered['tvs'])} TVs, "
            
            if discovered['roku']:
                response += f"{len(discovered['roku'])} Roku devices, "
            
            response = response.rstrip(', ') + ". You can now control these devices with voice commands."
            
            return response
            
        except Exception as e:
            logger.error(f"Error discovering devices: {e}")
            return "I encountered an error while discovering smart home devices."
    
    async def create_automation(self, command: str) -> str:
        """Create simple automation rules."""
        try:
            # Parse automation command
            automation = self._parse_automation_command(command)
            
            if not automation:
                return "I didn't understand the automation command. Try saying 'turn on lights when I get home'."
            
            # This would be stored in a database in a real implementation
            automation_id = len(getattr(self, '_automations', [])) + 1
            
            if not hasattr(self, '_automations'):
                self._automations = []
            
            automation['id'] = automation_id
            self._automations.append(automation)
            
            return f"Automation created: {automation['description']}"
            
        except Exception as e:
            logger.error(f"Error creating automation: {e}")
            return "I encountered an error while creating the automation."
    
    def _parse_automation_command(self, command: str) -> Optional[Dict[str, Any]]:
        """Parse automation command."""
        automation = {}
        
        # Simple automation patterns
        if "when" in command and "turn on" in command:
            automation['trigger'] = "time_based"  # Simplified
            automation['action'] = "turn_on_lights"
            automation['description'] = "Turn on lights based on trigger"
        elif "if" in command and "then" in command:
            automation['trigger'] = "conditional"
            automation['action'] = "smart_action"
            automation['description'] = "Conditional automation"
        else:
            return None
        
        return automation
    
    async def list_automations(self, command: str) -> str:
        """List active automations."""
        try:
            if not hasattr(self, '_automations') or not self._automations:
                return "No automations are currently active."
            
            response = f"You have {len(self._automations)} active automations: "
            
            for automation in self._automations:
                response += f"ID {automation['id']}: {automation['description']}. "
            
            return response
            
        except Exception as e:
            logger.error(f"Error listing automations: {e}")
            return "I encountered an error while listing automations."
    
    async def enable_scene(self, command: str) -> str:
        """Enable a predefined scene."""
        try:
            scene_name = self._extract_scene_name(command)
            
            if not scene_name:
                return "Please specify a scene name like 'movie time' or 'bedtime'."
            
            success = await self._activate_scene(scene_name)
            
            if success:
                return f"Scene '{scene_name}' activated."
            else:
                return f"I couldn't activate the '{scene_name}' scene."
                
        except Exception as e:
            logger.error(f"Error enabling scene: {e}")
            return "I encountered an error while enabling the scene."
    
    def _extract_scene_name(self, command: str) -> Optional[str]:
        """Extract scene name from command."""
        scenes = {
            "movie": "movie time",
            "bedtime": "bedtime",
            "morning": "morning",
            "evening": "evening",
            "party": "party",
            "romantic": "romantic",
            "work": "work",
            "relax": "relax"
        }
        
        command_lower = command.lower()
        for keyword, scene_name in scenes.items():
            if keyword in command_lower:
                return scene_name
        
        return None
    
    async def _activate_scene(self, scene_name: str) -> bool:
        """Activate a predefined scene."""
        try:
            # Define scene actions
            scenes = {
                "movie time": {
                    "lights": {"action": "dim", "brightness": 51},  # 20% brightness
                    "tv": {"action": "on"}
                },
                "bedtime": {
                    "lights": {"action": "off"},
                    "tv": {"action": "off"}
                },
                "morning": {
                    "lights": {"action": "on", "brightness": 255},  # Full brightness
                },
                "evening": {
                    "lights": {"action": "on", "brightness": 127},  # 50% brightness
                },
                "party": {
                    "lights": {"action": "color", "color": "rainbow"},
                },
                "romantic": {
                    "lights": {"action": "color", "color": "red", "brightness": 76},  # 30% red
                },
                "work": {
                    "lights": {"action": "on", "brightness": 204},  # 80% brightness
                },
                "relax": {
                    "lights": {"action": "color", "color": "blue", "brightness": 102},  # 40% blue
                }
            }
            
            if scene_name not in scenes:
                return False
            
            scene_actions = scenes[scene_name]
            success_count = 0
            
            # Execute light actions
            if "lights" in scene_actions:
                light_action = scene_actions["lights"]
                success = await self.smart_home.control_lights(**light_action)
                if success:
                    success_count += 1
            
            # Execute TV actions
            if "tv" in scene_actions:
                tv_action = scene_actions["tv"]
                success = await self.smart_home.control_tv(**tv_action)
                if success:
                    success_count += 1
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error activating scene: {e}")
            return False
    
    async def schedule_automation(self, command: str) -> str:
        """Schedule an automation for later."""
        return "Automation scheduling is not implemented yet. You can create basic automations and scenes."
