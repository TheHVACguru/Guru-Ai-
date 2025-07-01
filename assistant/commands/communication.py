"""
Communication commands for Voice Assistant.
"""

import asyncio
import re
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from assistant.integrations.gmail import GmailClient
from assistant.integrations.calendar import CalendarClient
from assistant.integrations.telegram_bot import TelegramBot
from assistant.utils.logger import setup_logger

logger = setup_logger(__name__)

class CommunicationCommands:
    """Communication command handlers for email, calendar, and messaging."""
    
    def __init__(self, config, voice_speaker):
        """Initialize communication commands."""
        self.config = config
        self.voice_speaker = voice_speaker
        self.gmail_client = GmailClient(config)
        self.calendar_client = CalendarClient(config)
        self.telegram_bot = TelegramBot(config)
        self.reminders = []  # Simple in-memory reminders storage
        
    async def send_email(self, command: str) -> str:
        """Send an email based on voice command."""
        try:
            if not self.gmail_client.is_available():
                return "Email service is not available. Please check your Gmail configuration."
            
            # Extract email components from command
            email_info = self._parse_email_command(command)
            
            if not email_info.get('recipient'):
                return "I need to know who to send the email to. Please specify a recipient."
            
            if not email_info.get('subject') and not email_info.get('body'):
                return "I need either a subject or message content for the email."
            
            # Use defaults for missing information
            subject = email_info.get('subject', 'Message from Voice Assistant')
            body = email_info.get('body', 'This email was sent via voice command.')
            recipient = email_info['recipient']
            
            success = await self.gmail_client.send_email(
                to=recipient,
                subject=subject,
                body=body
            )
            
            if success:
                return f"Email sent to {recipient} successfully."
            else:
                return "I couldn't send the email. Please check the recipient address and try again."
                
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return "I encountered an error while sending the email."
    
    def _parse_email_command(self, command: str) -> Dict[str, str]:
        """Parse email command to extract recipient, subject, and body."""
        email_info = {}
        
        # Look for email patterns
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, command)
        if emails:
            email_info['recipient'] = emails[0]
        
        # Look for subject patterns
        subject_patterns = [
            r'subject\s+(.+?)(?:\s+saying|\s+message|\s+body|$)',
            r'with\s+subject\s+(.+?)(?:\s+saying|\s+message|\s+body|$)',
            r'titled\s+(.+?)(?:\s+saying|\s+message|\s+body|$)'
        ]
        
        for pattern in subject_patterns:
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                email_info['subject'] = match.group(1).strip()
                break
        
        # Look for body/message patterns
        body_patterns = [
            r'saying\s+(.+)$',
            r'message\s+(.+)$',
            r'body\s+(.+)$',
            r'tell\s+them\s+(.+)$'
        ]
        
        for pattern in body_patterns:
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                email_info['body'] = match.group(1).strip()
                break
        
        # Look for recipient names (common names)
        if 'recipient' not in email_info:
            # Try to extract names
            name_pattern = r'to\s+([A-Za-z\s]+?)(?:\s+saying|\s+with|\s+about|$)'
            match = re.search(name_pattern, command, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # This would need a contact lookup in a real implementation
                email_info['recipient'] = f"{name.lower().replace(' ', '.')}@example.com"
        
        return email_info
    
    async def check_email(self, command: str) -> str:
        """Check recent emails."""
        try:
            if not self.gmail_client.is_available():
                return "Email service is not available."
            
            # Extract count from command
            count = self._extract_email_count(command)
            
            emails = await self.gmail_client.get_recent_emails(count)
            
            if not emails:
                return "You have no recent emails."
            
            if len(emails) == 1:
                email = emails[0]
                return f"You have 1 email from {email.get('from', 'Unknown')} with subject '{email.get('subject', 'No subject')}'"
            else:
                response = f"You have {len(emails)} recent emails. "
                for i, email in enumerate(emails[:3], 1):
                    sender = email.get('from', 'Unknown')
                    subject = email.get('subject', 'No subject')
                    response += f"{i}. From {sender}: {subject}. "
                
                if len(emails) > 3:
                    response += f"And {len(emails) - 3} more emails."
                
                return response
                
        except Exception as e:
            logger.error(f"Error checking email: {e}")
            return "I encountered an error while checking your emails."
    
    def _extract_email_count(self, command: str) -> int:
        """Extract number of emails to check from command."""
        numbers = re.findall(r'\d+', command)
        if numbers:
            return min(int(numbers[0]), 20)  # Limit to 20 emails
        
        if "last" in command or "recent" in command:
            return 5
        
        return 10  # Default
    
    async def manage_calendar(self, command: str) -> str:
        """Manage calendar events."""
        try:
            if not self.calendar_client.is_available():
                return "Calendar service is not available. Please check your Google Calendar configuration."
            
            if "check" in command or "what" in command or "schedule" in command:
                return await self._check_calendar(command)
            elif "create" in command or "add" in command or "schedule" in command:
                return await self._create_calendar_event(command)
            else:
                return await self._check_calendar(command)
                
        except Exception as e:
            logger.error(f"Error managing calendar: {e}")
            return "I encountered an error while accessing your calendar."
    
    async def _check_calendar(self, command: str) -> str:
        """Check upcoming calendar events."""
        try:
            # Extract time period
            count = self._extract_calendar_count(command)
            
            events = await self.calendar_client.get_upcoming_events(count)
            
            if not events:
                return "You have no upcoming events."
            
            return self.calendar_client.format_events_message(events, min(count, 3))
            
        except Exception as e:
            logger.error(f"Error checking calendar: {e}")
            return "I couldn't check your calendar."
    
    async def _create_calendar_event(self, command: str) -> str:
        """Create a new calendar event."""
        try:
            event_info = self._parse_calendar_command(command)
            
            if not event_info.get('title'):
                return "I need a title for the calendar event."
            
            if not event_info.get('start_time'):
                return "I need to know when the event should start."
            
            # Set default end time if not provided
            start_time = event_info['start_time']
            end_time = event_info.get('end_time', start_time + timedelta(hours=1))
            
            event_id = await self.calendar_client.create_event(
                title=event_info['title'],
                start_time=start_time,
                end_time=end_time,
                description=event_info.get('description', ''),
                location=event_info.get('location', '')
            )
            
            if event_id:
                return f"Calendar event '{event_info['title']}' created successfully."
            else:
                return "I couldn't create the calendar event."
                
        except Exception as e:
            logger.error(f"Error creating calendar event: {e}")
            return "I encountered an error while creating the calendar event."
    
    def _parse_calendar_command(self, command: str) -> Dict[str, Any]:
        """Parse calendar command to extract event details."""
        event_info = {}
        
        # Extract title
        title_patterns = [
            r'(?:create|add|schedule)\s+(?:a\s+)?(?:meeting|event|appointment)\s+(?:called\s+|titled\s+|named\s+)?(.+?)(?:\s+at|\s+on|\s+for|$)',
            r'(?:meeting|event|appointment)\s+(.+?)(?:\s+at|\s+on|\s+for|$)'
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                event_info['title'] = match.group(1).strip()
                break
        
        # Extract time information (simplified parsing)
        time_info = self._parse_time_from_command(command)
        if time_info:
            event_info.update(time_info)
        
        return event_info
    
    def _parse_time_from_command(self, command: str) -> Dict[str, datetime]:
        """Parse time information from command."""
        now = datetime.now()
        time_info = {}
        
        # Simple time parsing patterns
        if "tomorrow" in command:
            if "morning" in command:
                time_info['start_time'] = now.replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=1)
            elif "afternoon" in command:
                time_info['start_time'] = now.replace(hour=14, minute=0, second=0, microsecond=0) + timedelta(days=1)
            elif "evening" in command:
                time_info['start_time'] = now.replace(hour=18, minute=0, second=0, microsecond=0) + timedelta(days=1)
            else:
                time_info['start_time'] = now.replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=1)
        
        elif "next week" in command:
            time_info['start_time'] = now.replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=7)
        
        elif "today" in command or "this" in command:
            if "morning" in command:
                time_info['start_time'] = now.replace(hour=9, minute=0, second=0, microsecond=0)
            elif "afternoon" in command:
                time_info['start_time'] = now.replace(hour=14, minute=0, second=0, microsecond=0)
            elif "evening" in command:
                time_info['start_time'] = now.replace(hour=18, minute=0, second=0, microsecond=0)
            else:
                # Default to next hour
                time_info['start_time'] = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        
        # Look for specific times (simplified)
        time_pattern = r'(?:at\s+)?(\d{1,2})(?::(\d{2}))?\s*(am|pm)?'
        match = re.search(time_pattern, command, re.IGNORECASE)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else 0
            ampm = match.group(3)
            
            if ampm and ampm.lower() == 'pm' and hour != 12:
                hour += 12
            elif ampm and ampm.lower() == 'am' and hour == 12:
                hour = 0
            
            start_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # If time is in the past, schedule for tomorrow
            if start_time <= now:
                start_time += timedelta(days=1)
            
            time_info['start_time'] = start_time
        
        return time_info
    
    def _extract_calendar_count(self, command: str) -> int:
        """Extract number of events to show from command."""
        if "today" in command:
            return 5
        elif "week" in command:
            return 10
        elif "month" in command:
            return 20
        
        numbers = re.findall(r'\d+', command)
        if numbers:
            return min(int(numbers[0]), 20)
        
        return 5  # Default
    
    async def set_reminder(self, command: str) -> str:
        """Set a reminder."""
        try:
            reminder_info = self._parse_reminder_command(command)
            
            if not reminder_info.get('message'):
                return "I need to know what to remind you about."
            
            if not reminder_info.get('time'):
                return "I need to know when to remind you."
            
            # Store reminder (in a real implementation, this would use a database)
            reminder = {
                'message': reminder_info['message'],
                'time': reminder_info['time'],
                'created': datetime.now()
            }
            
            self.reminders.append(reminder)
            
            time_str = reminder_info['time'].strftime("%A at %I:%M %p")
            return f"I'll remind you about '{reminder_info['message']}' on {time_str}."
            
        except Exception as e:
            logger.error(f"Error setting reminder: {e}")
            return "I encountered an error while setting the reminder."
    
    def _parse_reminder_command(self, command: str) -> Dict[str, Any]:
        """Parse reminder command to extract message and time."""
        reminder_info = {}
        
        # Extract reminder message
        message_patterns = [
            r'remind me to (.+?)(?:\s+at|\s+on|\s+in|$)',
            r'reminder to (.+?)(?:\s+at|\s+on|\s+in|$)',
            r'remind me about (.+?)(?:\s+at|\s+on|\s+in|$)'
        ]
        
        for pattern in message_patterns:
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                reminder_info['message'] = match.group(1).strip()
                break
        
        # Extract time (simplified parsing)
        time_info = self._parse_time_from_command(command)
        if time_info and 'start_time' in time_info:
            reminder_info['time'] = time_info['start_time']
        else:
            # Default to 1 hour from now
            reminder_info['time'] = datetime.now() + timedelta(hours=1)
        
        return reminder_info
    
    async def check_reminders(self, command: str) -> str:
        """Check upcoming reminders."""
        try:
            if not self.reminders:
                return "You have no active reminders."
            
            # Get reminders for the next 24 hours
            now = datetime.now()
            upcoming = [r for r in self.reminders if r['time'] > now and r['time'] <= now + timedelta(days=1)]
            
            if not upcoming:
                return "You have no reminders for the next 24 hours."
            
            if len(upcoming) == 1:
                reminder = upcoming[0]
                time_str = reminder['time'].strftime("%I:%M %p")
                return f"You have 1 reminder: '{reminder['message']}' at {time_str}."
            else:
                response = f"You have {len(upcoming)} upcoming reminders: "
                for i, reminder in enumerate(upcoming[:3], 1):
                    time_str = reminder['time'].strftime("%I:%M %p")
                    response += f"{i}. '{reminder['message']}' at {time_str}. "
                
                if len(upcoming) > 3:
                    response += f"And {len(upcoming) - 3} more."
                
                return response
                
        except Exception as e:
            logger.error(f"Error checking reminders: {e}")
            return "I encountered an error while checking your reminders."
    
    async def send_telegram_message(self, command: str) -> str:
        """Send a message via Telegram."""
        try:
            if not self.telegram_bot.is_available():
                return "Telegram bot is not configured."
            
            # Extract message from command
            message = self._extract_telegram_message(command)
            
            if not message:
                return "I need to know what message to send."
            
            success = await self.telegram_bot.send_message(message)
            
            if success:
                return "Telegram message sent successfully."
            else:
                return "I couldn't send the Telegram message."
                
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            return "I encountered an error while sending the Telegram message."
    
    def _extract_telegram_message(self, command: str) -> Optional[str]:
        """Extract message content from Telegram command."""
        patterns = [
            r'send telegram (?:message )?saying (.+)$',
            r'telegram (.+)$',
            r'send message (.+)$'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    async def check_messages(self, command: str) -> str:
        """Check for new messages (placeholder for future implementation)."""
        return "Message checking is not implemented yet. I can help you send emails, manage calendar events, and set reminders."
