"""
Telegram bot integration for remote control.
"""

import asyncio
import os
from typing import Optional, Dict, Any
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from assistant.utils.logger import setup_logger

logger = setup_logger(__name__)

class TelegramBot:
    """Telegram bot for remote control of the assistant."""
    
    def __init__(self, config, command_processor=None):
        """Initialize Telegram bot."""
        self.config = config
        self.command_processor = command_processor
        self.bot_token = config.telegram_bot_token
        self.chat_id = config.telegram_chat_id
        self.application = None
        self.bot = None
        
        if not self.bot_token:
            logger.warning("Telegram bot token not provided - Telegram features disabled")
            return
        
        self._setup_bot()
    
    def _setup_bot(self):
        """Setup Telegram bot application."""
        try:
            self.application = Application.builder().token(self.bot_token).build()
            self.bot = Bot(self.bot_token)
            
            # Add command handlers
            self.application.add_handler(CommandHandler("start", self._start_command))
            self.application.add_handler(CommandHandler("help", self._help_command))
            self.application.add_handler(CommandHandler("status", self._status_command))
            self.application.add_handler(CommandHandler("speak", self._speak_command))
            self.application.add_handler(CommandHandler("weather", self._weather_command))
            self.application.add_handler(CommandHandler("stocks", self._stocks_command))
            self.application.add_handler(CommandHandler("news", self._news_command))
            
            # Add message handler for general commands
            self.application.add_handler(
                MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message)
            )
            
            logger.info("Telegram bot setup completed")
            
        except Exception as e:
            logger.error(f"Failed to setup Telegram bot: {e}")
    
    async def start_bot(self):
        """Start the Telegram bot."""
        if not self.application:
            logger.error("Telegram bot not initialized")
            return
        
        try:
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            logger.info("Telegram bot started successfully")
            
            # Send startup message
            if self.chat_id:
                await self.send_message("🤖 Voice Assistant is now online and ready for commands!")
            
        except Exception as e:
            logger.error(f"Failed to start Telegram bot: {e}")
    
    async def stop_bot(self):
        """Stop the Telegram bot."""
        if self.application:
            try:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
                logger.info("Telegram bot stopped")
            except Exception as e:
                logger.error(f"Error stopping Telegram bot: {e}")
    
    async def send_message(self, text: str, chat_id: Optional[str] = None) -> bool:
        """Send a message via Telegram."""
        if not self.bot:
            logger.error("Telegram bot not available")
            return False
        
        try:
            target_chat_id = chat_id or self.chat_id
            if not target_chat_id:
                logger.error("No chat ID provided")
                return False
            
            await self.bot.send_message(chat_id=target_chat_id, text=text)
            logger.debug(f"Message sent to Telegram: {text[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
    
    async def send_file(self, file_path: str, caption: str = "", 
                       chat_id: Optional[str] = None) -> bool:
        """Send a file via Telegram."""
        if not self.bot:
            logger.error("Telegram bot not available")
            return False
        
        try:
            target_chat_id = chat_id or self.chat_id
            if not target_chat_id:
                logger.error("No chat ID provided")
                return False
            
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return False
            
            with open(file_path, 'rb') as file:
                await self.bot.send_document(
                    chat_id=target_chat_id,
                    document=file,
                    caption=caption
                )
            
            logger.info(f"File sent to Telegram: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send file via Telegram: {e}")
            return False
    
    # Command handlers
    async def _start_command(self, update: Update, context) -> None:
        """Handle /start command."""
        welcome_message = (
            "🤖 Welcome to Voice Assistant!\n\n"
            "Available commands:\n"
            "/help - Show help message\n"
            "/status - Check assistant status\n"
            "/speak <text> - Make assistant speak\n"
            "/weather - Get weather information\n"
            "/stocks - Get stock information\n"
            "/news - Get latest news\n\n"
            "You can also send any text message and I'll process it as a voice command!"
        )
        await update.message.reply_text(welcome_message)
    
    async def _help_command(self, update: Update, context) -> None:
        """Handle /help command."""
        help_message = (
            "🔧 Voice Assistant Commands:\n\n"
            "📱 Telegram Commands:\n"
            "/start - Welcome message\n"
            "/help - This help message\n"
            "/status - System status\n"
            "/speak <text> - Text-to-speech\n"
            "/weather [location] - Weather info\n"
            "/stocks [symbol] - Stock prices\n"
            "/news [category] - Latest news\n\n"
            "🎤 Voice Commands (send as text):\n"
            "• What's the weather?\n"
            "• Tell me the news\n"
            "• What time is it?\n"
            "• Send an email\n"
            "• Control smart home devices\n"
            "• Play music\n"
            "• Set a reminder\n\n"
            "Just type your command and I'll process it!"
        )
        await update.message.reply_text(help_message)
    
    async def _status_command(self, update: Update, context) -> None:
        """Handle /status command."""
        status_message = (
            "🟢 Voice Assistant Status:\n\n"
            f"• Wake Word: {self.config.wake_word}\n"
            f"• API Server: {'Running' if self.config.enable_api else 'Disabled'}\n"
            f"• OpenAI: {'Available' if self.config.openai_api_key else 'Not configured'}\n"
            f"• Weather API: {'Available' if self.config.weather_api_key else 'Not configured'}\n"
            f"• News API: {'Available' if self.config.news_api_key else 'Not configured'}\n"
            f"• Smart Home: {'Enabled' if self.config.enable_smart_home else 'Disabled'}\n"
            f"• Face Recognition: {'Enabled' if self.config.enable_face_recognition else 'Disabled'}\n"
        )
        await update.message.reply_text(status_message)
    
    async def _speak_command(self, update: Update, context) -> None:
        """Handle /speak command."""
        if not context.args:
            await update.message.reply_text("Please provide text to speak: /speak Hello world")
            return
        
        text = " ".join(context.args)
        
        if self.command_processor and hasattr(self.command_processor, 'voice_speaker'):
            success = await self.command_processor.voice_speaker.speak(text)
            if success:
                await update.message.reply_text(f"🔊 Speaking: {text}")
            else:
                await update.message.reply_text("❌ Failed to speak the text")
        else:
            await update.message.reply_text("❌ Speech synthesis not available")
    
    async def _weather_command(self, update: Update, context) -> None:
        """Handle /weather command."""
        location = " ".join(context.args) if context.args else None
        
        if self.command_processor:
            response = await self.command_processor.process_weather_command(location)
            await update.message.reply_text(f"🌤️ {response}")
        else:
            await update.message.reply_text("❌ Weather service not available")
    
    async def _stocks_command(self, update: Update, context) -> None:
        """Handle /stocks command."""
        symbol = context.args[0] if context.args else None
        
        if self.command_processor:
            response = await self.command_processor.process_stock_command(symbol)
            await update.message.reply_text(f"📈 {response}")
        else:
            await update.message.reply_text("❌ Stock service not available")
    
    async def _news_command(self, update: Update, context) -> None:
        """Handle /news command."""
        category = context.args[0] if context.args else None
        
        if self.command_processor:
            response = await self.command_processor.process_news_command(category)
            await update.message.reply_text(f"📰 {response}")
        else:
            await update.message.reply_text("❌ News service not available")
    
    async def _handle_message(self, update: Update, context) -> None:
        """Handle general text messages as voice commands."""
        command = update.message.text
        
        # Log the command from Telegram
        logger.info(f"Telegram command received: {command}")
        
        if self.command_processor:
            try:
                # Process the command
                response = await self.command_processor.process(command, source="telegram")
                
                # Send response back to Telegram
                if response:
                    await update.message.reply_text(f"🤖 {response}")
                else:
                    await update.message.reply_text("✅ Command processed")
                    
            except Exception as e:
                logger.error(f"Error processing Telegram command: {e}")
                await update.message.reply_text("❌ Error processing command")
        else:
            await update.message.reply_text("❌ Command processor not available")
    
    def is_available(self) -> bool:
        """Check if Telegram bot is available."""
        return bool(self.bot_token)
