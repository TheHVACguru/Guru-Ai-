"""
Main command processor for Voice Assistant.
"""

import re
import asyncio
from typing import Optional, Dict, Any
from assistant.commands.system import SystemCommands
from assistant.commands.media import MediaCommands
from assistant.commands.information import InformationCommands
from assistant.commands.communication import CommunicationCommands
from assistant.commands.automation import AutomationCommands
from assistant.integrations.openai_client import OpenAIClient
from assistant.utils.logger import setup_logger

logger = setup_logger(__name__)

class CommandProcessor:
    """Main command processor that routes commands to appropriate handlers."""
    
    def __init__(self, config, voice_speaker):
        """Initialize command processor."""
        self.config = config
        self.voice_speaker = voice_speaker
        
        # Initialize command handlers
        self.system_commands = SystemCommands(config, voice_speaker)
        self.media_commands = MediaCommands(config, voice_speaker)
        self.information_commands = InformationCommands(config, voice_speaker)
        self.communication_commands = CommunicationCommands(config, voice_speaker)
        self.automation_commands = AutomationCommands(config, voice_speaker)
        
        # Initialize OpenAI client for unrecognized commands
        self.openai_client = OpenAIClient(config)
        
        # Command patterns for routing
        self.command_patterns = self._setup_command_patterns()
        
        logger.info("Command processor initialized")
    
    def _setup_command_patterns(self) -> Dict[str, Dict]:
        """Setup command patterns for routing."""
        return {
            # System commands
            'time': {
                'patterns': [r'\b(what|tell me|current)\s*(time|clock)\b', r'\btime\s*is\s*it\b'],
                'handler': self.system_commands.get_time
            },
            'date': {
                'patterns': [r'\b(what|tell me|current)\s*(date|day)\b', r'\bdate\s*is\s*it\b', r'\btoday.*date\b'],
                'handler': self.system_commands.get_date
            },
            'volume': {
                'patterns': [r'\b(volume|sound)\s*(up|down|mute|unmute)\b', r'\b(increase|decrease|raise|lower)\s*(volume|sound)\b'],
                'handler': self.system_commands.control_volume
            },
            'brightness': {
                'patterns': [r'\b(brightness|screen)\s*(up|down|increase|decrease)\b', r'\b(brighten|dim)\s*(screen|display)\b'],
                'handler': self.system_commands.control_brightness
            },
            'shutdown': {
                'patterns': [r'\b(shutdown|power off|turn off)\b.*\b(computer|system|machine)\b'],
                'handler': self.system_commands.shutdown_system
            },
            'restart': {
                'patterns': [r'\b(restart|reboot)\b.*\b(computer|system|machine)\b'],
                'handler': self.system_commands.restart_system
            },
            
            # Information commands
            'weather': {
                'patterns': [r'\b(weather|temperature|forecast)\b', r'\bhow.*hot|cold.*outside\b'],
                'handler': self.information_commands.get_weather
            },
            'news': {
                'patterns': [r'\b(news|headlines|latest news)\b', r'\bwhat.*happening\b'],
                'handler': self.information_commands.get_news
            },
            'stocks': {
                'patterns': [r'\b(stock|stocks|share|shares)\s*(price|prices)\b', r'\bmarket.*doing\b'],
                'handler': self.information_commands.get_stocks
            },
            'calculate': {
                'patterns': [r'\b(calculate|compute|math|solve)\b', r'\bwhat.*\d+.*[\+\-\*\/].*\d+\b'],
                'handler': self.information_commands.calculate
            },
            'search': {
                'patterns': [r'\b(search|look up|find|google)\b', r'\bwhat.*is.*\b'],
                'handler': self.information_commands.search_web
            },
            
            # Communication commands
            'email': {
                'patterns': [r'\b(send|write|compose)\s*(email|mail)\b', r'\bemail.*to\b'],
                'handler': self.communication_commands.send_email
            },
            'calendar': {
                'patterns': [r'\b(calendar|schedule|appointment|meeting)\b', r'\bwhat.*schedule\b'],
                'handler': self.communication_commands.manage_calendar
            },
            'reminder': {
                'patterns': [r'\b(remind|reminder|alert)\b', r'\bset.*reminder\b'],
                'handler': self.communication_commands.set_reminder
            },
            
            # Media commands
            'music': {
                'patterns': [r'\b(play|stop|pause|music|song|spotify|youtube)\b', r'\bvolume\s*(up|down)\b'],
                'handler': self.media_commands.control_music
            },
            'video': {
                'patterns': [r'\b(video|movie|netflix|youtube|watch)\b'],
                'handler': self.media_commands.control_video
            },
            'camera': {
                'patterns': [r'\b(photo|picture|camera|take.*picture)\b', r'\bsmile|cheese\b'],
                'handler': self.media_commands.take_photo
            },
            
            # Smart home commands
            'lights': {
                'patterns': [r'\b(light|lights|lamp|bulb)\s*(on|off|dim|bright)\b', r'\bturn.*light\b'],
                'handler': self.automation_commands.control_lights
            },
            'tv': {
                'patterns': [r'\b(tv|television)\s*(on|off|channel|volume)\b', r'\bturn.*tv\b'],
                'handler': self.automation_commands.control_tv
            },
            'smart_home': {
                'patterns': [r'\b(smart home|home automation|iot)\b'],
                'handler': self.automation_commands.control_smart_home
            },
            
            # General assistant commands
            'help': {
                'patterns': [r'\b(help|what can you do|commands|capabilities)\b'],
                'handler': self._show_help
            },
            'greeting': {
                'patterns': [r'\b(hello|hi|hey|good morning|good afternoon|good evening)\b'],
                'handler': self._handle_greeting
            },
            'goodbye': {
                'patterns': [r'\b(goodbye|bye|see you|talk to you later)\b'],
                'handler': self._handle_goodbye
            }
        }
    
    async def process(self, command: str, source: str = "voice") -> Optional[str]:
        """Process a voice command and return response."""
        try:
            if not command or not command.strip():
                return "I didn't hear a command. Please try again."
            
            command = command.strip().lower()
            logger.info(f"Processing command: {command} (source: {source})")
            
            # Find matching command pattern
            matched_handler = None
            matched_command_type = None
            
            for command_type, command_info in self.command_patterns.items():
                for pattern in command_info['patterns']:
                    if re.search(pattern, command, re.IGNORECASE):
                        matched_handler = command_info['handler']
                        matched_command_type = command_type
                        break
                
                if matched_handler:
                    break
            
            # Process the command
            if matched_handler:
                logger.info(f"Matched command type: {matched_command_type}")
                response = await matched_handler(command)
                
                # Speak the response if it came from voice
                if source == "voice" and response:
                    await self.voice_speaker.speak(response)
                
                return response
            else:
                # Use OpenAI for unrecognized commands
                logger.info("No pattern matched, using OpenAI")
                response = await self._handle_unrecognized_command(command)
                
                if source == "voice" and response:
                    await self.voice_speaker.speak(response)
                
                return response
                
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            error_response = "I encountered an error while processing your command. Please try again."
            
            if source == "voice":
                await self.voice_speaker.speak(error_response)
            
            return error_response
    
    async def _handle_unrecognized_command(self, command: str) -> str:
        """Handle unrecognized commands using OpenAI."""
        try:
            if self.openai_client.is_available():
                response = await self.openai_client.process_unrecognized_command(command)
                logger.info("OpenAI processed unrecognized command")
                return response
            else:
                # Fallback responses for common unrecognized patterns
                fallback_responses = [
                    "I'm not sure how to help with that. Try asking about weather, news, time, or system controls.",
                    "That's not something I can do right now. I can help with weather, time, calculations, and basic system controls.",
                    "I don't understand that command. You can ask me about the weather, news, time, or to control system settings."
                ]
                
                import random
                return random.choice(fallback_responses)
                
        except Exception as e:
            logger.error(f"Error handling unrecognized command: {e}")
            return "I'm not sure what you want me to do. Please try rephrasing your request."
    
    async def _show_help(self, command: str) -> str:
        """Show available commands."""
        help_text = """
        I can help you with the following:
        
        System Control:
        - What time is it?
        - What's the date?
        - Turn volume up/down
        - Increase/decrease brightness
        
        Information:
        - What's the weather?
        - Tell me the news
        - Check stock prices
        - Calculate math problems
        
        Communication:
        - Send an email
        - Check my calendar
        - Set a reminder
        
        Entertainment:
        - Play music
        - Take a photo
        - Control TV
        
        Smart Home:
        - Turn lights on/off
        - Control smart devices
        
        Just speak naturally and I'll try to help!
        """
        
        return help_text.strip()
    
    async def _handle_greeting(self, command: str) -> str:
        """Handle greeting commands."""
        greetings = [
            "Hello! How can I help you today?",
            "Hi there! What can I do for you?",
            "Good to hear from you! How can I assist?",
            "Hello! I'm here to help. What do you need?"
        ]
        
        import random
        return random.choice(greetings)
    
    async def _handle_goodbye(self, command: str) -> str:
        """Handle goodbye commands."""
        goodbyes = [
            "Goodbye! Have a great day!",
            "See you later! Take care!",
            "Bye! Let me know if you need anything else.",
            "Talk to you soon! Have a wonderful day!"
        ]
        
        import random
        return random.choice(goodbyes)
    
    # Helper methods for specific integrations
    async def process_weather_command(self, location: Optional[str] = None) -> str:
        """Process weather command via API."""
        return await self.information_commands.get_weather(f"weather in {location}" if location else "weather")
    
    async def process_stock_command(self, symbol: Optional[str] = None) -> str:
        """Process stock command via API."""
        return await self.information_commands.get_stocks(f"stock price {symbol}" if symbol else "stock prices")
    
    async def process_news_command(self, category: Optional[str] = None) -> str:
        """Process news command via API."""
        return await self.information_commands.get_news(f"news {category}" if category else "news")
