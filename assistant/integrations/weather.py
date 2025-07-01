"""
Weather information integration using OpenWeatherMap API.
"""

import asyncio
from typing import Optional, Dict, Any, List
import aiohttp
from assistant.utils.logger import setup_logger

logger = setup_logger(__name__)

class WeatherClient:
    """Weather client using OpenWeatherMap API."""
    
    BASE_URL = "https://api.openweathermap.org/data/2.5"
    
    def __init__(self, config):
        """Initialize weather client."""
        self.config = config
        self.api_key = config.weather_api_key
        
        if not self.api_key:
            logger.warning("Weather API key not provided - weather features disabled")
    
    async def get_current_weather(self, location: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get current weather for a location."""
        if not self.api_key:
            return None
        
        location = location or self.config.default_location
        
        try:
            url = f"{self.BASE_URL}/weather"
            params = {
                'q': location,
                'appid': self.api_key,
                'units': 'metric'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        weather_info = {
                            'location': data['name'],
                            'country': data['sys']['country'],
                            'temperature': data['main']['temp'],
                            'feels_like': data['main']['feels_like'],
                            'humidity': data['main']['humidity'],
                            'pressure': data['main']['pressure'],
                            'description': data['weather'][0]['description'].title(),
                            'wind_speed': data['wind']['speed'],
                            'wind_direction': data['wind'].get('deg', 0),
                            'visibility': data.get('visibility', 0) / 1000,  # Convert to km
                            'timestamp': data['dt']
                        }
                        
                        logger.info(f"Weather data retrieved for {location}")
                        return weather_info
                    else:
                        logger.error(f"Weather API error: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error getting weather data: {e}")
            return None
    
    async def get_forecast(self, location: Optional[str] = None, days: int = 5) -> Optional[List[Dict[str, Any]]]:
        """Get weather forecast for a location."""
        if not self.api_key:
            return None
        
        location = location or self.config.default_location
        
        try:
            url = f"{self.BASE_URL}/forecast"
            params = {
                'q': location,
                'appid': self.api_key,
                'units': 'metric',
                'cnt': days * 8  # 8 forecasts per day (every 3 hours)
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        forecast_list = []
                        for item in data['list']:
                            forecast_info = {
                                'datetime': item['dt_txt'],
                                'temperature': item['main']['temp'],
                                'feels_like': item['main']['feels_like'],
                                'humidity': item['main']['humidity'],
                                'description': item['weather'][0]['description'].title(),
                                'wind_speed': item['wind']['speed'],
                                'precipitation': item.get('rain', {}).get('3h', 0)
                            }
                            forecast_list.append(forecast_info)
                        
                        logger.info(f"Forecast data retrieved for {location}")
                        return forecast_list
                    else:
                        logger.error(f"Weather API error: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error getting forecast data: {e}")
            return None
    
    async def get_weather_alerts(self, location: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """Get weather alerts for a location."""
        if not self.api_key:
            return None
        
        # Note: Weather alerts require One Call API which needs lat/lon
        # First get coordinates from location
        coords = await self._get_coordinates(location)
        if not coords:
            return None
        
        try:
            url = "https://api.openweathermap.org/data/3.0/onecall"
            params = {
                'lat': coords['lat'],
                'lon': coords['lon'],
                'appid': self.api_key,
                'exclude': 'minutely,hourly,daily'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        alerts = data.get('alerts', [])
                        alert_list = []
                        
                        for alert in alerts:
                            alert_info = {
                                'sender': alert.get('sender_name', 'Unknown'),
                                'event': alert.get('event', 'Weather Alert'),
                                'description': alert.get('description', ''),
                                'start': alert.get('start', 0),
                                'end': alert.get('end', 0),
                                'tags': alert.get('tags', [])
                            }
                            alert_list.append(alert_info)
                        
                        logger.info(f"Weather alerts retrieved for {location}")
                        return alert_list
                    else:
                        logger.error(f"Weather alerts API error: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error getting weather alerts: {e}")
            return None
    
    async def _get_coordinates(self, location: Optional[str] = None) -> Optional[Dict[str, float]]:
        """Get coordinates for a location using geocoding API."""
        location = location or self.config.default_location
        
        try:
            url = "http://api.openweathermap.org/geo/1.0/direct"
            params = {
                'q': location,
                'limit': 1,
                'appid': self.api_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data:
                            return {
                                'lat': data[0]['lat'],
                                'lon': data[0]['lon']
                            }
                        
        except Exception as e:
            logger.error(f"Error getting coordinates: {e}")
        
        return None
    
    def format_weather_message(self, weather_data: Dict[str, Any]) -> str:
        """Format weather data into a spoken message."""
        if not weather_data:
            return "I couldn't get the weather information."
        
        temp = round(weather_data['temperature'])
        feels_like = round(weather_data['feels_like'])
        
        message = (
            f"The current weather in {weather_data['location']} is "
            f"{temp} degrees Celsius, feeling like {feels_like} degrees. "
            f"It's {weather_data['description']} with {weather_data['humidity']}% humidity "
            f"and wind speed of {weather_data['wind_speed']} meters per second."
        )
        
        return message
    
    def is_available(self) -> bool:
        """Check if weather service is available."""
        return bool(self.api_key)
