#!/usr/bin/env python3
"""
Open Source Voice Assistant
A comprehensive voice-activated natural language UI with smart home control,
AI integration, and extensive automation capabilities.
"""

import asyncio
import os
import sys
import threading
import time
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from assistant.config import Config
from assistant.api.app import create_app
from assistant.utils.logger import setup_logger

# Voice components will be imported conditionally when needed
WakeWordDetector = None
VoiceListener = None
VoiceSpeaker = None
CommandProcessor = None

# Initialize logger
logger = setup_logger(__name__)

class VoiceAssistant:
    """Main Voice Assistant application."""
    
    def __init__(self):
        """Initialize the voice assistant."""
        self.config = Config()
        self.wake_word_detector = None
        self.voice_listener = None
        self.voice_speaker = None
        self.command_processor = None
        self.api_server = None
        self.running = False
        
    async def initialize(self):
        """Initialize all components."""
        try:
            logger.info("Initializing Voice Assistant...")
            
            # Check system permissions
            if not check_permissions():
                logger.error("Insufficient permissions. Please check system requirements.")
                return False
                
            # Initialize components
            self.wake_word_detector = WakeWordDetector(self.config)
            self.voice_listener = VoiceListener(self.config)
            self.voice_speaker = VoiceSpeaker(self.config)
            self.command_processor = CommandProcessor(self.config, self.voice_speaker)
            
            # Initialize API server if enabled
            if self.config.enable_api:
                self.api_server = create_app(self.config)
                
            logger.info("Voice Assistant initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Voice Assistant: {e}")
            return False
    
    async def start_api_server(self):
        """Start the API server in a separate thread."""
        if self.api_server:
            import uvicorn
            def run_server():
                uvicorn.run(
                    self.api_server,
                    host=self.config.api_host,
                    port=self.config.api_port,
                    log_level="info"
                )
            
            api_thread = threading.Thread(target=run_server, daemon=True)
            api_thread.start()
            logger.info(f"API server started on {self.config.api_host}:{self.config.api_port}")
    
    async def listen_for_wake_word(self):
        """Listen for wake word continuously."""
        logger.info(f"Listening for wake word: '{self.config.wake_word}'")
        
        while self.running:
            try:
                if await self.wake_word_detector.listen():
                    logger.info("Wake word detected!")
                    await self.voice_speaker.speak("Yes?")
                    
                    # Listen for command
                    command = await self.voice_listener.listen()
                    if command:
                        logger.info(f"Command received: {command}")
                        await self.command_processor.process(command)
                    else:
                        await self.voice_speaker.speak("I didn't hear anything. Please try again.")
                        
            except KeyboardInterrupt:
                logger.info("Shutdown requested by user")
                break
            except Exception as e:
                logger.error(f"Error in wake word loop: {e}")
                await asyncio.sleep(1)
    
    async def start(self):
        """Start the voice assistant."""
        if not await self.initialize():
            return
            
        self.running = True
        
        # Start API server if enabled
        if self.config.enable_api:
            await self.start_api_server()
        
        # Welcome message
        await self.voice_speaker.speak(
            f"Voice Assistant is now active. Say '{self.config.wake_word}' to get started."
        )
        
        # Start main listening loop
        try:
            await self.listen_for_wake_word()
        except KeyboardInterrupt:
            logger.info("Shutdown requested")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Shutdown the voice assistant."""
        logger.info("Shutting down Voice Assistant...")
        self.running = False
        
        if self.voice_speaker:
            await self.voice_speaker.speak("Goodbye!")
        
        # Cleanup components
        if self.wake_word_detector:
            self.wake_word_detector.cleanup()
        if self.voice_listener:
            self.voice_listener.cleanup()
        if self.voice_speaker:
            self.voice_speaker.cleanup()
            
        logger.info("Voice Assistant shutdown complete")

async def main():
    """Main entry point."""
    try:
        assistant = VoiceAssistant()
        await assistant.start()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Handle command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] in ["--help", "-h"]:
            print("""
Voice Assistant - Open Source Voice Activated Natural Language UI

Usage:
    python main.py                 Start the voice assistant
    python main.py --help          Show this help message
    python main.py --install       Install dependencies
    python main.py --setup         Run setup wizard
    python main.py --api-only      Start API server only
    
Environment Variables:
    See .env.example for configuration options
    
For more information, visit: https://github.com/your-repo/voice-assistant
            """)
            sys.exit(0)
        elif sys.argv[1] == "--install":
            from scripts.install import run_install
            run_install()
            sys.exit(0)
        elif sys.argv[1] == "--setup":
            from scripts.setup import run_setup
            run_setup()
            sys.exit(0)
        elif sys.argv[1] == "--api-only":
            # Start API server only
            from assistant.api.app import create_app
            from assistant.config import Config
            import uvicorn
            
            config = Config()
            app = create_app(config)
            uvicorn.run(app, host="0.0.0.0", port=5000)
            sys.exit(0)
    
    # Start the assistant
    asyncio.run(main())
