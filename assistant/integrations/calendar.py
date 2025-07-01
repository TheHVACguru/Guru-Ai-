"""
Calendar integration using Google Calendar API.
"""

import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from assistant.utils.logger import setup_logger

logger = setup_logger(__name__)

class CalendarClient:
    """Google Calendar client for calendar operations."""
    
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    def __init__(self, config):
        """Initialize calendar client."""
        self.config = config
        self.service = None
        self.credentials = None
        
        if config.google_credentials_path and os.path.exists(config.google_credentials_path):
            self._authenticate()
        else:
            logger.warning("Google credentials not found - calendar features disabled")
    
    def _authenticate(self):
        """Authenticate with Google Calendar API."""
        try:
            creds = None
            token_path = "token_calendar.json"
            
            # Load existing token
            if os.path.exists(token_path):
                creds = Credentials.from_authorized_user_file(token_path, self.SCOPES)
            
            # If no valid credentials, get new ones
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = Flow.from_client_secrets_file(
                        self.config.google_credentials_path, self.SCOPES)
                    flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
                    
                    auth_url, _ = flow.authorization_url(prompt='consent')
                    logger.info(f"Please visit this URL to authorize the application: {auth_url}")
                    
                    code = input("Enter the authorization code: ")
                    flow.fetch_token(code=code)
                    creds = flow.credentials
                
                # Save credentials for next run
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())
            
            self.credentials = creds
            self.service = build('calendar', 'v3', credentials=creds)
            logger.info("Calendar client authenticated successfully")
            
        except Exception as e:
            logger.error(f"Failed to authenticate calendar client: {e}")
    
    async def get_upcoming_events(self, count: int = 10, 
                                 calendar_id: str = 'primary') -> List[Dict[str, Any]]:
        """Get upcoming calendar events."""
        if not self.service:
            logger.error("Calendar service not available")
            return []
        
        try:
            # Get current time in RFC3339 format
            now = datetime.utcnow().isoformat() + 'Z'
            
            # Call the Calendar API
            events_result = self.service.events().list(
                calendarId=calendar_id,
                timeMin=now,
                maxResults=count,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            event_list = []
            
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                
                event_info = {
                    'id': event['id'],
                    'summary': event.get('summary', 'No Title'),
                    'description': event.get('description', ''),
                    'start': start,
                    'end': end,
                    'location': event.get('location', ''),
                    'attendees': [attendee.get('email', '') 
                                for attendee in event.get('attendees', [])],
                    'creator': event.get('creator', {}).get('email', ''),
                    'html_link': event.get('htmlLink', '')
                }
                event_list.append(event_info)
            
            logger.info(f"Retrieved {len(event_list)} upcoming events")
            return event_list
            
        except Exception as e:
            logger.error(f"Error getting upcoming events: {e}")
            return []
    
    async def create_event(self, title: str, start_time: datetime, 
                          end_time: datetime, description: str = '',
                          location: str = '', attendees: List[str] = None,
                          calendar_id: str = 'primary') -> Optional[str]:
        """Create a new calendar event."""
        if not self.service:
            logger.error("Calendar service not available")
            return None
        
        try:
            event = {
                'summary': title,
                'description': description,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': self.config.timezone,
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': self.config.timezone,
                }
            }
            
            if location:
                event['location'] = location
            
            if attendees:
                event['attendees'] = [{'email': email} for email in attendees]
            
            # Create the event
            created_event = self.service.events().insert(
                calendarId=calendar_id,
                body=event
            ).execute()
            
            event_id = created_event['id']
            logger.info(f"Event created successfully: {event_id}")
            return event_id
            
        except Exception as e:
            logger.error(f"Error creating event: {e}")
            return None
    
    async def update_event(self, event_id: str, title: Optional[str] = None,
                          start_time: Optional[datetime] = None,
                          end_time: Optional[datetime] = None,
                          description: Optional[str] = None,
                          location: Optional[str] = None,
                          calendar_id: str = 'primary') -> bool:
        """Update an existing calendar event."""
        if not self.service:
            logger.error("Calendar service not available")
            return False
        
        try:
            # Get existing event
            event = self.service.events().get(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            
            # Update fields if provided
            if title is not None:
                event['summary'] = title
            if description is not None:
                event['description'] = description
            if location is not None:
                event['location'] = location
            if start_time is not None:
                event['start'] = {
                    'dateTime': start_time.isoformat(),
                    'timeZone': self.config.timezone,
                }
            if end_time is not None:
                event['end'] = {
                    'dateTime': end_time.isoformat(),
                    'timeZone': self.config.timezone,
                }
            
            # Update the event
            updated_event = self.service.events().update(
                calendarId=calendar_id,
                eventId=event_id,
                body=event
            ).execute()
            
            logger.info(f"Event updated successfully: {event_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating event: {e}")
            return False
    
    async def delete_event(self, event_id: str, calendar_id: str = 'primary') -> bool:
        """Delete a calendar event."""
        if not self.service:
            logger.error("Calendar service not available")
            return False
        
        try:
            self.service.events().delete(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            
            logger.info(f"Event deleted successfully: {event_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting event: {e}")
            return False
    
    async def search_events(self, query: str, count: int = 10,
                           calendar_id: str = 'primary') -> List[Dict[str, Any]]:
        """Search for events by query."""
        if not self.service:
            logger.error("Calendar service not available")
            return []
        
        try:
            # Get current time in RFC3339 format
            now = datetime.utcnow().isoformat() + 'Z'
            
            # Search events
            events_result = self.service.events().list(
                calendarId=calendar_id,
                timeMin=now,
                maxResults=count,
                singleEvents=True,
                orderBy='startTime',
                q=query
            ).execute()
            
            events = events_result.get('items', [])
            event_list = []
            
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                
                event_info = {
                    'id': event['id'],
                    'summary': event.get('summary', 'No Title'),
                    'description': event.get('description', ''),
                    'start': start,
                    'end': end,
                    'location': event.get('location', ''),
                    'attendees': [attendee.get('email', '') 
                                for attendee in event.get('attendees', [])],
                    'creator': event.get('creator', {}).get('email', ''),
                    'html_link': event.get('htmlLink', '')
                }
                event_list.append(event_info)
            
            logger.info(f"Found {len(event_list)} events matching query: {query}")
            return event_list
            
        except Exception as e:
            logger.error(f"Error searching events: {e}")
            return []
    
    def format_events_message(self, events: List[Dict[str, Any]], count: int = 3) -> str:
        """Format events into a spoken message."""
        if not events:
            return "You have no upcoming events."
        
        upcoming_events = events[:count]
        
        if len(upcoming_events) == 1:
            event = upcoming_events[0]
            start_time = self._parse_datetime(event['start'])
            message = f"You have one upcoming event: {event['summary']} "
            if start_time:
                message += f"on {start_time.strftime('%A, %B %d at %I:%M %p')}"
        else:
            message = f"You have {len(events)} upcoming events. "
            message += "The next few are: "
            
            for i, event in enumerate(upcoming_events, 1):
                start_time = self._parse_datetime(event['start'])
                time_str = start_time.strftime('%A at %I:%M %p') if start_time else 'unknown time'
                message += f"{i}. {event['summary']} on {time_str}. "
        
        return message
    
    def _parse_datetime(self, datetime_str: str) -> Optional[datetime]:
        """Parse datetime string from Calendar API."""
        try:
            # Handle both date and datetime formats
            if 'T' in datetime_str:
                # DateTime format
                dt_str = datetime_str.split('.')[0]  # Remove microseconds if present
                dt_str = dt_str.replace('Z', '+00:00')  # Replace Z with timezone
                if '+' in dt_str or dt_str.endswith('Z'):
                    return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
                else:
                    return datetime.fromisoformat(dt_str)
            else:
                # Date format
                return datetime.strptime(datetime_str, '%Y-%m-%d')
        except Exception as e:
            logger.error(f"Error parsing datetime: {e}")
            return None
    
    def is_available(self) -> bool:
        """Check if calendar service is available."""
        return self.service is not None
