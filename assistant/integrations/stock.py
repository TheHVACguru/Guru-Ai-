"""
Stock market information integration using Yahoo Finance.
"""

import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import yfinance as yf
from assistant.utils.logger import setup_logger

logger = setup_logger(__name__)

class StockClient:
    """Stock market client using Yahoo Finance."""
    
    def __init__(self, config):
        """Initialize stock client."""
        self.config = config
        self.default_stocks = config.default_stocks
    
    async def get_stock_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current stock price for a symbol."""
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            
            def fetch_stock_data():
                ticker = yf.Ticker(symbol.upper())
                info = ticker.info
                history = ticker.history(period="1d")
                
                if history.empty:
                    return None
                
                current_price = history['Close'].iloc[-1]
                previous_close = info.get('previousClose', current_price)
                change = current_price - previous_close
                change_percent = (change / previous_close) * 100 if previous_close else 0
                
                return {
                    'symbol': symbol.upper(),
                    'name': info.get('longName', symbol.upper()),
                    'current_price': round(current_price, 2),
                    'previous_close': round(previous_close, 2),
                    'change': round(change, 2),
                    'change_percent': round(change_percent, 2),
                    'volume': info.get('volume', 0),
                    'market_cap': info.get('marketCap', 0),
                    'pe_ratio': info.get('trailingPE', 0),
                    'day_high': round(history['High'].iloc[-1], 2),
                    'day_low': round(history['Low'].iloc[-1], 2),
                    'currency': info.get('currency', 'USD'),
                    'exchange': info.get('exchange', 'Unknown')
                }
            
            stock_data = await loop.run_in_executor(None, fetch_stock_data)
            
            if stock_data:
                logger.info(f"Stock data retrieved for {symbol}")
            else:
                logger.warning(f"No stock data found for {symbol}")
            
            return stock_data
            
        except Exception as e:
            logger.error(f"Error getting stock price for {symbol}: {e}")
            return None
    
    async def get_multiple_stocks(self, symbols: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get stock data for multiple symbols."""
        symbols = symbols or self.default_stocks
        
        if not symbols:
            return []
        
        stock_list = []
        
        # Fetch data for each symbol
        for symbol in symbols:
            stock_data = await self.get_stock_price(symbol)
            if stock_data:
                stock_list.append(stock_data)
        
        return stock_list
    
    async def get_stock_news(self, symbol: str, count: int = 5) -> List[Dict[str, Any]]:
        """Get recent news for a stock symbol."""
        try:
            loop = asyncio.get_event_loop()
            
            def fetch_news():
                ticker = yf.Ticker(symbol.upper())
                news = ticker.news
                
                news_list = []
                for item in news[:count]:
                    news_info = {
                        'title': item.get('title', ''),
                        'publisher': item.get('publisher', ''),
                        'link': item.get('link', ''),
                        'publish_time': datetime.fromtimestamp(
                            item.get('providerPublishTime', 0)
                        ).strftime('%Y-%m-%d %H:%M:%S') if item.get('providerPublishTime') else '',
                        'type': item.get('type', 'article')
                    }
                    news_list.append(news_info)
                
                return news_list
            
            news_data = await loop.run_in_executor(None, fetch_news)
            logger.info(f"News data retrieved for {symbol}")
            return news_data
            
        except Exception as e:
            logger.error(f"Error getting stock news for {symbol}: {e}")
            return []
    
    async def get_market_summary(self) -> Dict[str, Any]:
        """Get overall market summary."""
        try:
            # Get data for major indices
            indices = {
                '^GSPC': 'S&P 500',
                '^DJI': 'Dow Jones',
                '^IXIC': 'NASDAQ',
                '^VIX': 'VIX'
            }
            
            market_data = {}
            
            for symbol, name in indices.items():
                stock_data = await self.get_stock_price(symbol)
                if stock_data:
                    market_data[name] = {
                        'price': stock_data['current_price'],
                        'change': stock_data['change'],
                        'change_percent': stock_data['change_percent']
                    }
            
            logger.info("Market summary retrieved")
            return market_data
            
        except Exception as e:
            logger.error(f"Error getting market summary: {e}")
            return {}
    
    async def create_watchlist_alert(self, symbol: str, target_price: float, 
                                   alert_type: str = "above") -> bool:
        """Create a price alert for a stock (simplified implementation)."""
        try:
            current_data = await self.get_stock_price(symbol)
            if not current_data:
                return False
            
            current_price = current_data['current_price']
            
            # Simple alert logic (in a real implementation, this would be stored and checked periodically)
            if alert_type == "above" and current_price >= target_price:
                logger.info(f"Alert: {symbol} is above ${target_price} (current: ${current_price})")
                return True
            elif alert_type == "below" and current_price <= target_price:
                logger.info(f"Alert: {symbol} is below ${target_price} (current: ${current_price})")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error creating watchlist alert: {e}")
            return False
    
    def format_stock_message(self, stock_data: Dict[str, Any]) -> str:
        """Format stock data into a spoken message."""
        if not stock_data:
            return "I couldn't get the stock information."
        
        symbol = stock_data['symbol']
        name = stock_data['name']
        price = stock_data['current_price']
        change = stock_data['change']
        change_percent = stock_data['change_percent']
        
        direction = "up" if change >= 0 else "down"
        abs_change = abs(change)
        abs_change_percent = abs(change_percent)
        
        message = (
            f"{name} ({symbol}) is trading at ${price}, "
            f"{direction} ${abs_change:.2f} or {abs_change_percent:.2f}% "
            f"from the previous close."
        )
        
        return message
    
    def format_portfolio_message(self, stocks: List[Dict[str, Any]]) -> str:
        """Format multiple stocks into a portfolio summary."""
        if not stocks:
            return "I couldn't get portfolio information."
        
        total_gainers = sum(1 for stock in stocks if stock['change'] >= 0)
        total_losers = len(stocks) - total_gainers
        
        message = f"Portfolio summary: {total_gainers} stocks are up, {total_losers} are down. "
        
        # Add top performer and worst performer
        if stocks:
            best_performer = max(stocks, key=lambda x: x['change_percent'])
            worst_performer = min(stocks, key=lambda x: x['change_percent'])
            
            message += (
                f"Best performer is {best_performer['symbol']} "
                f"up {best_performer['change_percent']:.2f}%. "
                f"Worst performer is {worst_performer['symbol']} "
                f"down {abs(worst_performer['change_percent']):.2f}%."
            )
        
        return message
    
    def is_available(self) -> bool:
        """Check if stock service is available."""
        return True  # Yahoo Finance doesn't require API key
