"""
News integration using NewsAPI.
"""

import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import aiohttp
from assistant.utils.logger import setup_logger

logger = setup_logger(__name__)

class NewsClient:
    """News client using NewsAPI."""
    
    BASE_URL = "https://newsapi.org/v2"
    
    def __init__(self, config):
        """Initialize news client."""
        self.config = config
        self.api_key = config.news_api_key
        self.default_sources = config.news_sources
        
        if not self.api_key:
            logger.warning("News API key not provided - news features disabled")
    
    async def get_top_headlines(self, country: str = "us", category: Optional[str] = None, 
                               count: int = 5) -> List[Dict[str, Any]]:
        """Get top headlines."""
        if not self.api_key:
            return []
        
        try:
            url = f"{self.BASE_URL}/top-headlines"
            params = {
                'apiKey': self.api_key,
                'country': country,
                'pageSize': count
            }
            
            if category:
                params['category'] = category
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        articles = data.get('articles', [])
                        
                        news_list = []
                        for article in articles:
                            if article['title'] and article['title'] != '[Removed]':
                                news_info = {
                                    'title': article['title'],
                                    'description': article.get('description', ''),
                                    'source': article['source']['name'],
                                    'author': article.get('author', 'Unknown'),
                                    'url': article.get('url', ''),
                                    'published_at': article.get('publishedAt', ''),
                                    'url_to_image': article.get('urlToImage', '')
                                }
                                news_list.append(news_info)
                        
                        logger.info(f"Retrieved {len(news_list)} top headlines")
                        return news_list
                    else:
                        logger.error(f"News API error: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error getting top headlines: {e}")
            return []
    
    async def get_news_by_sources(self, sources: Optional[List[str]] = None, 
                                 count: int = 10) -> List[Dict[str, Any]]:
        """Get news from specific sources."""
        if not self.api_key:
            return []
        
        sources = sources or self.default_sources
        if not sources:
            return await self.get_top_headlines(count=count)
        
        try:
            url = f"{self.BASE_URL}/everything"
            params = {
                'apiKey': self.api_key,
                'sources': ','.join(sources),
                'sortBy': 'publishedAt',
                'pageSize': count
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        articles = data.get('articles', [])
                        
                        news_list = []
                        for article in articles:
                            if article['title'] and article['title'] != '[Removed]':
                                news_info = {
                                    'title': article['title'],
                                    'description': article.get('description', ''),
                                    'source': article['source']['name'],
                                    'author': article.get('author', 'Unknown'),
                                    'url': article.get('url', ''),
                                    'published_at': article.get('publishedAt', ''),
                                    'url_to_image': article.get('urlToImage', '')
                                }
                                news_list.append(news_info)
                        
                        logger.info(f"Retrieved {len(news_list)} news articles from sources")
                        return news_list
                    else:
                        logger.error(f"News API error: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error getting news by sources: {e}")
            return []
    
    async def search_news(self, query: str, count: int = 10, 
                         from_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Search news articles by query."""
        if not self.api_key:
            return []
        
        try:
            url = f"{self.BASE_URL}/everything"
            params = {
                'apiKey': self.api_key,
                'q': query,
                'sortBy': 'publishedAt',
                'pageSize': count,
                'language': 'en'
            }
            
            if from_date:
                params['from'] = from_date.strftime('%Y-%m-%d')
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        articles = data.get('articles', [])
                        
                        news_list = []
                        for article in articles:
                            if article['title'] and article['title'] != '[Removed]':
                                news_info = {
                                    'title': article['title'],
                                    'description': article.get('description', ''),
                                    'source': article['source']['name'],
                                    'author': article.get('author', 'Unknown'),
                                    'url': article.get('url', ''),
                                    'published_at': article.get('publishedAt', ''),
                                    'url_to_image': article.get('urlToImage', '')
                                }
                                news_list.append(news_info)
                        
                        logger.info(f"Found {len(news_list)} news articles for query: {query}")
                        return news_list
                    else:
                        logger.error(f"News API error: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error searching news: {e}")
            return []
    
    async def get_news_by_category(self, category: str, count: int = 5) -> List[Dict[str, Any]]:
        """Get news by category."""
        valid_categories = ['business', 'entertainment', 'general', 'health', 
                          'science', 'sports', 'technology']
        
        if category.lower() not in valid_categories:
            logger.warning(f"Invalid category: {category}")
            category = 'general'
        
        return await self.get_top_headlines(category=category.lower(), count=count)
    
    async def get_available_sources(self, country: str = "us", 
                                   language: str = "en") -> List[Dict[str, Any]]:
        """Get available news sources."""
        if not self.api_key:
            return []
        
        try:
            url = f"{self.BASE_URL}/sources"
            params = {
                'apiKey': self.api_key,
                'country': country,
                'language': language
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        sources = data.get('sources', [])
                        
                        source_list = []
                        for source in sources:
                            source_info = {
                                'id': source['id'],
                                'name': source['name'],
                                'description': source.get('description', ''),
                                'url': source.get('url', ''),
                                'category': source.get('category', ''),
                                'language': source.get('language', ''),
                                'country': source.get('country', '')
                            }
                            source_list.append(source_info)
                        
                        logger.info(f"Retrieved {len(source_list)} news sources")
                        return source_list
                    else:
                        logger.error(f"News API error: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error getting news sources: {e}")
            return []
    
    def format_news_headlines(self, articles: List[Dict[str, Any]], count: int = 3) -> str:
        """Format news articles into a spoken message."""
        if not articles:
            return "I couldn't get the latest news."
        
        headlines = articles[:count]
        
        if len(headlines) == 1:
            message = f"Here's the top headline: {headlines[0]['title']}"
        else:
            message = "Here are the top headlines: "
            for i, article in enumerate(headlines, 1):
                message += f"{i}. {article['title']}. "
        
        return message
    
    def format_news_summary(self, articles: List[Dict[str, Any]]) -> str:
        """Format news articles into a summary."""
        if not articles:
            return "No news available."
        
        sources = set(article['source'] for article in articles)
        
        message = (
            f"I found {len(articles)} recent articles "
            f"from {len(sources)} sources including "
            f"{', '.join(list(sources)[:3])}."
        )
        
        if len(sources) > 3:
            message += f" and {len(sources) - 3} others."
        
        return message
    
    def is_available(self) -> bool:
        """Check if news service is available."""
        return bool(self.api_key)
