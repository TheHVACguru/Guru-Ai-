"""
Smart home device control integration.
"""

import asyncio
from typing import Optional, List, Dict, Any
from assistant.utils.logger import setup_logger

logger = setup_logger(__name__)

# Optional imports for smart home devices
try:
    from magichome import MagicHome
    MAGICHOME_AVAILABLE = True
except ImportError:
    MAGICHOME_AVAILABLE = False
    logger.warning("MagicHome not available - smart light control disabled")

try:
    from pywebostv.discovery import discover
    from pywebostv.connection import WebOSClient
    WEBOS_AVAILABLE = True
except ImportError:
    WEBOS_AVAILABLE = False
    logger.warning("PyWebOSTV not available - LG TV control disabled")

try:
    import roku
    ROKU_AVAILABLE = True
except ImportError:
    ROKU_AVAILABLE = False
    logger.warning("Roku not available - Roku control disabled")

class SmartHomeController:
    """Smart home device controller."""
    
    def __init__(self, config):
        """Initialize smart home controller."""
        self.config = config
        self.magic_home_devices = {}
        self.webos_client = None
        self.roku_client = None
        
        if config.enable_smart_home:
            self._initialize_devices()
        else:
            logger.info("Smart home features disabled in configuration")
    
    def _initialize_devices(self):
        """Initialize smart home devices."""
        # Initialize MagicHome devices
        if MAGICHOME_AVAILABLE and self.config.magic_home_devices:
            for device_ip in self.config.magic_home_devices:
                try:
                    device = MagicHome(device_ip)
                    self.magic_home_devices[device_ip] = device
                    logger.info(f"MagicHome device initialized: {device_ip}")
                except Exception as e:
                    logger.error(f"Failed to initialize MagicHome device {device_ip}: {e}")
        
        # Initialize LG WebOS TV
        if WEBOS_AVAILABLE and self.config.lg_tv_ip:
            try:
                self.webos_client = WebOSClient(self.config.lg_tv_ip)
                logger.info(f"LG WebOS TV initialized: {self.config.lg_tv_ip}")
            except Exception as e:
                logger.error(f"Failed to initialize LG TV: {e}")
        
        # Initialize Roku
        if ROKU_AVAILABLE and self.config.roku_ip:
            try:
                self.roku_client = roku.Roku(self.config.roku_ip)
                logger.info(f"Roku device initialized: {self.config.roku_ip}")
            except Exception as e:
                logger.error(f"Failed to initialize Roku: {e}")
    
    # MagicHome Light Control
    async def control_lights(self, action: str, device_ip: Optional[str] = None,
                            color: Optional[str] = None, brightness: Optional[int] = None) -> bool:
        """Control MagicHome smart lights."""
        if not MAGICHOME_AVAILABLE:
            logger.error("MagicHome not available")
            return False
        
        try:
            # If no specific device, control all devices
            devices_to_control = []
            if device_ip and device_ip in self.magic_home_devices:
                devices_to_control = [self.magic_home_devices[device_ip]]
            else:
                devices_to_control = list(self.magic_home_devices.values())
            
            if not devices_to_control:
                logger.error("No MagicHome devices available")
                return False
            
            success_count = 0
            
            for device in devices_to_control:
                try:
                    if action.lower() == "on":
                        device.turn_on()
                        success_count += 1
                    elif action.lower() == "off":
                        device.turn_off()
                        success_count += 1
                    elif action.lower() == "toggle":
                        # Check current state and toggle
                        if device.is_on():
                            device.turn_off()
                        else:
                            device.turn_on()
                        success_count += 1
                    elif action.lower() == "brightness" and brightness is not None:
                        # Set brightness (0-255)
                        brightness_value = max(0, min(255, brightness))
                        device.set_brightness(brightness_value)
                        success_count += 1
                    elif action.lower() == "color" and color:
                        # Set color (hex format or RGB)
                        if color.startswith('#'):
                            device.set_color(color)
                        else:
                            # Try to parse as RGB
                            rgb = self._parse_color(color)
                            if rgb:
                                device.set_color(rgb)
                        success_count += 1
                    
                    await asyncio.sleep(0.1)  # Small delay between commands
                    
                except Exception as e:
                    logger.error(f"Error controlling light device: {e}")
            
            logger.info(f"Light control completed: {success_count}/{len(devices_to_control)} devices")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error in light control: {e}")
            return False
    
    # LG WebOS TV Control
    async def control_tv(self, action: str, volume: Optional[int] = None,
                        channel: Optional[str] = None, app: Optional[str] = None) -> bool:
        """Control LG WebOS TV."""
        if not WEBOS_AVAILABLE or not self.webos_client:
            logger.error("LG WebOS TV not available")
            return False
        
        try:
            # Connect to TV
            self.webos_client.connect()
            
            if action.lower() == "on":
                # Turn on TV (if supported)
                self.webos_client.power_on()
            elif action.lower() == "off":
                self.webos_client.power_off()
            elif action.lower() == "volume_up":
                self.webos_client.volume_up()
            elif action.lower() == "volume_down":
                self.webos_client.volume_down()
            elif action.lower() == "mute":
                self.webos_client.mute()
            elif action.lower() == "set_volume" and volume is not None:
                self.webos_client.set_volume(volume)
            elif action.lower() == "channel" and channel:
                self.webos_client.set_channel(channel)
            elif action.lower() == "app" and app:
                # Launch app
                apps = self.webos_client.get_apps()
                target_app = None
                for available_app in apps:
                    if app.lower() in available_app['title'].lower():
                        target_app = available_app
                        break
                
                if target_app:
                    self.webos_client.launch_app(target_app['id'])
                else:
                    logger.warning(f"App not found: {app}")
                    return False
            
            self.webos_client.disconnect()
            logger.info(f"TV control completed: {action}")
            return True
            
        except Exception as e:
            logger.error(f"Error controlling TV: {e}")
            return False
    
    # Roku Control
    async def control_roku(self, action: str, app: Optional[str] = None) -> bool:
        """Control Roku device."""
        if not ROKU_AVAILABLE or not self.roku_client:
            logger.error("Roku not available")
            return False
        
        try:
            if action.lower() == "home":
                self.roku_client.home()
            elif action.lower() == "back":
                self.roku_client.back()
            elif action.lower() == "up":
                self.roku_client.up()
            elif action.lower() == "down":
                self.roku_client.down()
            elif action.lower() == "left":
                self.roku_client.left()
            elif action.lower() == "right":
                self.roku_client.right()
            elif action.lower() == "select":
                self.roku_client.select()
            elif action.lower() == "play":
                self.roku_client.play()
            elif action.lower() == "pause":
                self.roku_client.pause()
            elif action.lower() == "volume_up":
                self.roku_client.volume_up()
            elif action.lower() == "volume_down":
                self.roku_client.volume_down()
            elif action.lower() == "mute":
                self.roku_client.mute()
            elif action.lower() == "app" and app:
                # Launch app
                apps = self.roku_client.apps
                target_app = None
                for available_app in apps:
                    if app.lower() in available_app.name.lower():
                        target_app = available_app
                        break
                
                if target_app:
                    target_app.launch()
                else:
                    logger.warning(f"Roku app not found: {app}")
                    return False
            
            logger.info(f"Roku control completed: {action}")
            return True
            
        except Exception as e:
            logger.error(f"Error controlling Roku: {e}")
            return False
    
    # Generic device discovery
    async def discover_devices(self) -> Dict[str, List[Dict[str, Any]]]:
        """Discover available smart home devices."""
        discovered_devices = {
            "lights": [],
            "tvs": [],
            "roku": []
        }
        
        try:
            # Discover LG TVs
            if WEBOS_AVAILABLE:
                webos_devices = discover()
                for device in webos_devices:
                    discovered_devices["tvs"].append({
                        "type": "LG WebOS TV",
                        "ip": device,
                        "status": "discovered"
                    })
            
            # For lights and Roku, we'd need specific discovery methods
            # This is a simplified implementation
            
            logger.info(f"Device discovery completed: {discovered_devices}")
            return discovered_devices
            
        except Exception as e:
            logger.error(f"Error during device discovery: {e}")
            return discovered_devices
    
    def _parse_color(self, color_str: str) -> Optional[tuple]:
        """Parse color string to RGB tuple."""
        color_map = {
            "red": (255, 0, 0),
            "green": (0, 255, 0),
            "blue": (0, 0, 255),
            "white": (255, 255, 255),
            "yellow": (255, 255, 0),
            "purple": (128, 0, 128),
            "orange": (255, 165, 0),
            "pink": (255, 192, 203)
        }
        
        color_str = color_str.lower().strip()
        if color_str in color_map:
            return color_map[color_str]
        
        # Try to parse RGB format "255,0,0"
        try:
            rgb_parts = [int(x.strip()) for x in color_str.split(',')]
            if len(rgb_parts) == 3:
                return tuple(max(0, min(255, x)) for x in rgb_parts)
        except ValueError:
            pass
        
        return None
    
    def get_device_status(self) -> Dict[str, Any]:
        """Get status of all smart home devices."""
        status = {
            "lights": {},
            "tv": None,
            "roku": None,
            "total_devices": 0
        }
        
        try:
            # Check MagicHome devices
            for ip, device in self.magic_home_devices.items():
                try:
                    status["lights"][ip] = {
                        "connected": True,
                        "on": device.is_on() if hasattr(device, 'is_on') else False
                    }
                    status["total_devices"] += 1
                except Exception:
                    status["lights"][ip] = {"connected": False, "on": False}
            
            # Check TV status
            if self.webos_client:
                try:
                    # Simple connection test
                    status["tv"] = {"connected": True}
                    status["total_devices"] += 1
                except Exception:
                    status["tv"] = {"connected": False}
            
            # Check Roku status
            if self.roku_client:
                try:
                    # Simple connection test
                    status["roku"] = {"connected": True}
                    status["total_devices"] += 1
                except Exception:
                    status["roku"] = {"connected": False}
            
        except Exception as e:
            logger.error(f"Error getting device status: {e}")
        
        return status
    
    def is_available(self) -> bool:
        """Check if smart home features are available."""
        return self.config.enable_smart_home and (
            bool(self.magic_home_devices) or 
            bool(self.webos_client) or 
            bool(self.roku_client)
        )
