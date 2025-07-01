"""
OpenAI integration for natural language processing and AI responses.
"""

import json
import os
from typing import Optional, Dict, Any, List
from openai import OpenAI
from assistant.utils.logger import setup_logger

logger = setup_logger(__name__)

class OpenAIClient:
    """OpenAI client for AI-powered responses and natural language processing."""
    
    def __init__(self, config):
        """Initialize OpenAI client."""
        self.config = config
        self.client = None
        
        if config.openai_api_key:
            try:
                self.client = OpenAI(api_key=config.openai_api_key)
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
        else:
            logger.warning("OpenAI API key not provided - AI features disabled")
    
    async def process_unrecognized_command(self, command: str, context: Optional[Dict] = None) -> str:
        """Process unrecognized commands using GPT."""
        if not self.client:
            return "I'm sorry, I don't understand that command and AI processing is not available."
        
        try:
            # Build context for the AI
            system_prompt = """You are a helpful voice assistant. The user has given you a command that wasn't recognized by the system's built-in commands. 

Your role is to:
1. Try to understand what the user wants
2. Provide a helpful response
3. If it's a request you can fulfill with information, provide that information
4. If it's something that requires system actions you can't perform, politely explain the limitation
5. Keep responses conversational and concise (under 100 words)
6. If asked about capabilities, mention you can help with information, conversations, and explanations

Available system capabilities include:
- Weather information
- Time and date
- Basic calculations  
- General knowledge questions
- System controls (volume, brightness)
- Smart home device control
- Email and calendar management
- News and stock information"""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": command}
            ]
            
            # Add context if provided
            if context:
                context_str = f"Additional context: {json.dumps(context)}"
                messages.append({"role": "assistant", "content": context_str})
            
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # do not change this unless explicitly requested by the user
            response = self.client.chat.completions.create(
                model=self.config.openai_model,
                messages=messages,
                max_tokens=self.config.openai_max_tokens,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error processing command with OpenAI: {e}")
            return "I encountered an error while processing your request. Please try again."
    
    async def analyze_intent(self, command: str) -> Dict[str, Any]:
        """Analyze user intent from command."""
        if not self.client:
            return {"intent": "unknown", "confidence": 0.0, "entities": []}
        
        try:
            prompt = f"""Analyze the following voice command and extract the intent and entities.
            
Command: "{command}"

Respond with JSON in this format:
{{
    "intent": "intent_name",
    "confidence": 0.95,
    "entities": [
        {{"type": "entity_type", "value": "entity_value", "confidence": 0.9}}
    ],
    "action": "suggested_action"
}}

Common intents include: weather, time, email, calendar, music, smart_home, information, calculation, system_control, news, stocks"""

            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # do not change this unless explicitly requested by the user
            response = self.client.chat.completions.create(
                model=self.config.openai_model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_tokens=200
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing intent: {e}")
            return {"intent": "unknown", "confidence": 0.0, "entities": []}
    
    async def generate_response(self, prompt: str, context: Optional[str] = None) -> str:
        """Generate a general response to a prompt."""
        if not self.client:
            return "AI response generation is not available."
        
        try:
            messages = [{"role": "user", "content": prompt}]
            
            if context:
                messages.insert(0, {"role": "system", "content": context})
            
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # do not change this unless explicitly requested by the user
            response = self.client.chat.completions.create(
                model=self.config.openai_model,
                messages=messages,
                max_tokens=self.config.openai_max_tokens,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I encountered an error while generating a response."
    
    async def summarize_text(self, text: str, max_length: int = 100) -> str:
        """Summarize long text."""
        if not self.client:
            return text[:max_length] + "..." if len(text) > max_length else text
        
        try:
            prompt = f"Please summarize the following text concisely in about {max_length} words:\n\n{text}"
            
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # do not change this unless explicitly requested by the user
            response = self.client.chat.completions.create(
                model=self.config.openai_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_length + 50
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error summarizing text: {e}")
            return text[:max_length] + "..." if len(text) > max_length else text
    
    def is_available(self) -> bool:
        """Check if OpenAI client is available."""
        return self.client is not None
