"""
Gmail integration for sending and reading emails.
"""

import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List, Dict, Any
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from assistant.utils.logger import setup_logger

logger = setup_logger(__name__)

class GmailClient:
    """Gmail client for email operations."""
    
    SCOPES = ['https://www.googleapis.com/auth/gmail.send', 
              'https://www.googleapis.com/auth/gmail.readonly']
    
    def __init__(self, config):
        """Initialize Gmail client."""
        self.config = config
        self.service = None
        self.credentials = None
        
        if config.google_credentials_path and os.path.exists(config.google_credentials_path):
            self._authenticate()
        else:
            logger.warning("Google credentials not found - Gmail features disabled")
    
    def _authenticate(self):
        """Authenticate with Google Gmail API."""
        try:
            creds = None
            token_path = "token_gmail.json"
            
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
            self.service = build('gmail', 'v1', credentials=creds)
            logger.info("Gmail client authenticated successfully")
            
        except Exception as e:
            logger.error(f"Failed to authenticate Gmail client: {e}")
    
    async def send_email(self, to: str, subject: str, body: str, 
                        cc: Optional[str] = None, bcc: Optional[str] = None) -> bool:
        """Send an email."""
        if not self.service:
            logger.error("Gmail service not available")
            return False
        
        try:
            # Create message
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject
            
            if cc:
                message['cc'] = cc
            if bcc:
                message['bcc'] = bcc
            
            # Add body
            message.attach(MIMEText(body, 'plain'))
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            # Send message
            send_message = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            logger.info(f"Email sent successfully: {send_message['id']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    async def get_recent_emails(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent emails."""
        if not self.service:
            logger.error("Gmail service not available")
            return []
        
        try:
            # Get message list
            results = self.service.users().messages().list(
                userId='me',
                maxResults=count
            ).execute()
            
            messages = results.get('messages', [])
            email_list = []
            
            for message in messages:
                # Get message details
                msg = self.service.users().messages().get(
                    userId='me',
                    id=message['id']
                ).execute()
                
                # Extract email information
                headers = msg['payload'].get('headers', [])
                email_info = {
                    'id': message['id'],
                    'snippet': msg.get('snippet', ''),
                    'date': None,
                    'from': None,
                    'subject': None
                }
                
                for header in headers:
                    name = header['name'].lower()
                    if name == 'date':
                        email_info['date'] = header['value']
                    elif name == 'from':
                        email_info['from'] = header['value']
                    elif name == 'subject':
                        email_info['subject'] = header['value']
                
                email_list.append(email_info)
            
            logger.info(f"Retrieved {len(email_list)} recent emails")
            return email_list
            
        except Exception as e:
            logger.error(f"Failed to get recent emails: {e}")
            return []
    
    async def search_emails(self, query: str, count: int = 10) -> List[Dict[str, Any]]:
        """Search emails by query."""
        if not self.service:
            logger.error("Gmail service not available")
            return []
        
        try:
            # Search messages
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=count
            ).execute()
            
            messages = results.get('messages', [])
            email_list = []
            
            for message in messages:
                # Get message details
                msg = self.service.users().messages().get(
                    userId='me',
                    id=message['id']
                ).execute()
                
                # Extract email information
                headers = msg['payload'].get('headers', [])
                email_info = {
                    'id': message['id'],
                    'snippet': msg.get('snippet', ''),
                    'date': None,
                    'from': None,
                    'subject': None
                }
                
                for header in headers:
                    name = header['name'].lower()
                    if name == 'date':
                        email_info['date'] = header['value']
                    elif name == 'from':
                        email_info['from'] = header['value']
                    elif name == 'subject':
                        email_info['subject'] = header['value']
                
                email_list.append(email_info)
            
            logger.info(f"Found {len(email_list)} emails matching query: {query}")
            return email_list
            
        except Exception as e:
            logger.error(f"Failed to search emails: {e}")
            return []
    
    def is_available(self) -> bool:
        """Check if Gmail service is available."""
        return self.service is not None
