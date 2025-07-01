"""
Information retrieval commands for Voice Assistant.
"""

import asyncio
import re
import math
import webbrowser
from typing import Optional
from assistant.integrations.weather import WeatherClient
from assistant.integrations.stock import StockClient
from assistant.integrations.news import NewsClient
from assistant.integrations.openai_client import OpenAIClient
from assistant.utils.logger import setup_logger

logger = setup_logger(__name__)

class InformationCommands:
    """Information retrieval command handlers."""
    
    def __init__(self, config, voice_speaker):
        """Initialize information commands."""
        self.config = config
        self.voice_speaker = voice_speaker
        self.weather_client = WeatherClient(config)
        self.stock_client = StockClient(config)
        self.news_client = NewsClient(config)
        self.openai_client = OpenAIClient(config)
        
    async def get_weather(self, command: str) -> str:
        """Get weather information."""
        try:
            if not self.weather_client.is_available():
                return "Weather service is not available. Please check your API key configuration."
            
            # Extract location from command
            location = self._extract_location(command)
            
            weather_data = await self.weather_client.get_current_weather(location)
            
            if weather_data:
                return self.weather_client.format_weather_message(weather_data)
            else:
                location_text = f" for {location}" if location else ""
                return f"I couldn't get the weather information{location_text}. Please try again later."
                
        except Exception as e:
            logger.error(f"Error getting weather: {e}")
            return "I encountered an error while getting the weather information."
    
    def _extract_location(self, command: str) -> Optional[str]:
        """Extract location from weather command."""
        # Remove common weather words
        weather_words = ["weather", "temperature", "forecast", "what's", "how's", "the", "in", "for", "at"]
        words = command.split()
        
        # Find location words
        location_words = []
        start_collecting = False
        
        for word in words:
            word_clean = word.lower().strip(".,!?")
            
            if word_clean in ["in", "for", "at"]:
                start_collecting = True
                continue
            
            if start_collecting and word_clean not in weather_words:
                location_words.append(word)
        
        if location_words:
            return " ".join(location_words)
        
        return None
    
    async def get_forecast(self, command: str) -> str:
        """Get weather forecast."""
        try:
            if not self.weather_client.is_available():
                return "Weather service is not available."
            
            location = self._extract_location(command)
            days = self._extract_forecast_days(command)
            
            forecast_data = await self.weather_client.get_forecast(location, days)
            
            if forecast_data:
                # Format forecast for voice
                location_text = location or self.config.default_location
                response = f"Here's the {days}-day forecast for {location_text}: "
                
                # Group by days and summarize
                daily_forecasts = {}
                for item in forecast_data[:days*2]:  # Take first few items
                    date = item['datetime'].split()[0]
                    if date not in daily_forecasts:
                        daily_forecasts[date] = item
                
                for i, (date, forecast) in enumerate(daily_forecasts.items()):
                    if i < 3:  # Limit to 3 days for voice response
                        temp = round(forecast['temperature'])
                        desc = forecast['description']
                        response += f"Day {i+1}: {temp} degrees, {desc}. "
                
                return response
            else:
                return "I couldn't get the forecast information."
                
        except Exception as e:
            logger.error(f"Error getting forecast: {e}")
            return "I encountered an error while getting the forecast."
    
    def _extract_forecast_days(self, command: str) -> int:
        """Extract number of days for forecast."""
        # Look for numbers in the command
        numbers = re.findall(r'\d+', command)
        if numbers:
            days = int(numbers[0])
            return min(days, 7)  # Limit to 7 days
        
        # Check for text indicators
        if "tomorrow" in command:
            return 1
        elif "week" in command:
            return 7
        
        return 3  # Default to 3 days
    
    async def get_news(self, command: str) -> str:
        """Get news headlines."""
        try:
            if not self.news_client.is_available():
                return "News service is not available. Please check your API key configuration."
            
            # Extract category from command
            category = self._extract_news_category(command)
            
            if category:
                articles = await self.news_client.get_news_by_category(category, 3)
            else:
                articles = await self.news_client.get_top_headlines(count=3)
            
            if articles:
                return self.news_client.format_news_headlines(articles, 3)
            else:
                return "I couldn't get the latest news. Please try again later."
                
        except Exception as e:
            logger.error(f"Error getting news: {e}")
            return "I encountered an error while getting the news."
    
    def _extract_news_category(self, command: str) -> Optional[str]:
        """Extract news category from command."""
        categories = {
            "business": ["business", "finance", "financial", "economy", "economic"],
            "technology": ["technology", "tech", "computer", "software", "gadget"],
            "sports": ["sports", "sport", "football", "basketball", "soccer", "baseball"],
            "health": ["health", "medical", "medicine", "healthcare"],
            "science": ["science", "scientific", "research"],
            "entertainment": ["entertainment", "celebrity", "movie", "music", "hollywood"]
        }
        
        command_lower = command.lower()
        
        for category, keywords in categories.items():
            if any(keyword in command_lower for keyword in keywords):
                return category
        
        return None
    
    async def get_stocks(self, command: str) -> str:
        """Get stock information."""
        try:
            # Extract stock symbol from command
            symbol = self._extract_stock_symbol(command)
            
            if symbol:
                stock_data = await self.stock_client.get_stock_price(symbol)
                if stock_data:
                    return self.stock_client.format_stock_message(stock_data)
                else:
                    return f"I couldn't find stock information for {symbol}."
            else:
                # Get portfolio summary
                stocks = await self.stock_client.get_multiple_stocks()
                if stocks:
                    return self.stock_client.format_portfolio_message(stocks)
                else:
                    return "I couldn't get stock information. Please try specifying a stock symbol."
                    
        except Exception as e:
            logger.error(f"Error getting stocks: {e}")
            return "I encountered an error while getting stock information."
    
    def _extract_stock_symbol(self, command: str) -> Optional[str]:
        """Extract stock symbol from command."""
        # Common stock symbols and company names
        stock_mapping = {
            "apple": "AAPL",
            "microsoft": "MSFT",
            "google": "GOOGL",
            "amazon": "AMZN",
            "tesla": "TSLA",
            "facebook": "META",
            "meta": "META",
            "netflix": "NFLX",
            "nvidia": "NVDA",
            "intel": "INTC"
        }
        
        command_lower = command.lower()
        
        # Check for company names
        for company, symbol in stock_mapping.items():
            if company in command_lower:
                return symbol
        
        # Look for potential stock symbols (2-5 uppercase letters)
        words = command.upper().split()
        for word in words:
            if len(word) >= 2 and len(word) <= 5 and word.isalpha():
                # Could be a stock symbol
                return word
        
        return None
    
    async def calculate(self, command: str) -> str:
        """Perform mathematical calculations."""
        try:
            # Extract mathematical expression from command
            expression = self._extract_math_expression(command)
            
            if not expression:
                return "I couldn't find a mathematical expression to calculate."
            
            # Evaluate the expression safely
            result = self._safe_eval(expression)
            
            if result is not None:
                return f"The answer is {result}"
            else:
                return "I couldn't calculate that expression."
                
        except Exception as e:
            logger.error(f"Error calculating: {e}")
            return "I encountered an error while calculating."
    
    def _extract_math_expression(self, command: str) -> Optional[str]:
        """Extract mathematical expression from command."""
        # Remove common words
        remove_words = ["calculate", "compute", "what", "is", "equals", "plus", "minus", "times", "divided", "by"]
        
        # Replace word operators with symbols
        replacements = {
            "plus": "+",
            "add": "+",
            "minus": "-",
            "subtract": "-",
            "times": "*",
            "multiply": "*",
            "multiplied": "*",
            "divided": "/",
            "divide": "/",
            "power": "**",
            "squared": "**2",
            "cubed": "**3"
        }
        
        expression = command.lower()
        
        # Apply replacements
        for word, symbol in replacements.items():
            expression = expression.replace(word, symbol)
        
        # Remove common words
        for word in remove_words:
            expression = expression.replace(word, "")
        
        # Clean up the expression
        expression = re.sub(r'[^0-9+\-*/().\s]', '', expression)
        expression = expression.strip()
        
        if expression:
            return expression
        
        # Try to find numbers and operators
        math_pattern = r'[\d+\-*/().\s]+'
        matches = re.findall(math_pattern, command)
        
        if matches:
            return matches[0].strip()
        
        return None
    
    def _safe_eval(self, expression: str) -> Optional[float]:
        """Safely evaluate mathematical expression."""
        try:
            # Only allow basic mathematical operations
            allowed_chars = set('0123456789+-*/(). ')
            if not all(c in allowed_chars for c in expression):
                return None
            
            # Replace ** with ^ for power (but eval uses **)
            expression = expression.replace('^', '**')
            
            # Add math functions
            safe_dict = {
                "__builtins__": {},
                "abs": abs,
                "round": round,
                "pow": pow,
                "sqrt": math.sqrt,
                "sin": math.sin,
                "cos": math.cos,
                "tan": math.tan,
                "log": math.log,
                "pi": math.pi,
                "e": math.e
            }
            
            result = eval(expression, safe_dict)
            
            # Round to reasonable precision
            if isinstance(result, float):
                if result.is_integer():
                    return int(result)
                else:
                    return round(result, 6)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in safe_eval: {e}")
            return None
    
    async def search_web(self, command: str) -> str:
        """Search the web for information."""
        try:
            # Extract search query
            query = self._extract_search_query(command)
            
            if not query:
                return "What would you like me to search for?"
            
            # Use OpenAI to answer if available
            if self.openai_client.is_available():
                response = await self.openai_client.generate_response(
                    f"Please provide a brief answer to: {query}",
                    "You are a helpful assistant. Provide concise, accurate information."
                )
                
                # Also open web search as backup
                search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
                webbrowser.open(search_url)
                
                return response + " I've also opened a web search for more information."
            else:
                # Just open web search
                search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
                webbrowser.open(search_url)
                
                return f"I've opened a web search for '{query}'"
                
        except Exception as e:
            logger.error(f"Error searching web: {e}")
            return "I encountered an error while searching."
    
    def _extract_search_query(self, command: str) -> Optional[str]:
        """Extract search query from command."""
        # Remove command words
        remove_words = ["search", "look", "up", "find", "google", "what", "is", "are", "tell", "me", "about"]
        
        words = command.split()
        query_words = []
        
        for word in words:
            if word.lower() not in remove_words:
                query_words.append(word)
        
        if query_words:
            return " ".join(query_words)
        
        return None
    
    async def get_definition(self, command: str) -> str:
        """Get definition of a word."""
        try:
            # Extract word to define
            word = self._extract_word_to_define(command)
            
            if not word:
                return "What word would you like me to define?"
            
            if self.openai_client.is_available():
                response = await self.openai_client.generate_response(
                    f"Define the word '{word}' clearly and concisely.",
                    "You are a dictionary. Provide clear, accurate definitions."
                )
                return response
            else:
                # Open dictionary search
                dict_url = f"https://www.merriam-webster.com/dictionary/{word}"
                webbrowser.open(dict_url)
                return f"I've opened the dictionary definition for '{word}'"
                
        except Exception as e:
            logger.error(f"Error getting definition: {e}")
            return "I encountered an error while getting the definition."
    
    def _extract_word_to_define(self, command: str) -> Optional[str]:
        """Extract word to define from command."""
        # Look for patterns like "define [word]" or "what is [word]"
        patterns = [
            r"define\s+(\w+)",
            r"what\s+is\s+(\w+)",
            r"meaning\s+of\s+(\w+)",
            r"definition\s+of\s+(\w+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    async def get_fact(self, command: str) -> str:
        """Get an interesting fact."""
        try:
            if self.openai_client.is_available():
                response = await self.openai_client.generate_response(
                    "Tell me an interesting and educational fact.",
                    "You are an educational assistant. Share fascinating, true facts."
                )
                return response
            else:
                facts = [
                    "The human brain contains approximately 86 billion neurons.",
                    "Octopuses have three hearts and blue blood.",
                    "A group of flamingos is called a flamboyance.",
                    "Honey never spoils. Archaeologists have found 3000-year-old honey that's still edible.",
                    "The Great Wall of China isn't visible from space with the naked eye."
                ]
                
                import random
                return random.choice(facts)
                
        except Exception as e:
            logger.error(f"Error getting fact: {e}")
            return "I encountered an error while getting a fact."
