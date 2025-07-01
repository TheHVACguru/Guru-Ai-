"""
Helper utilities for Voice Assistant.
"""

import os
import re
import json
import hashlib
import secrets
import asyncio
import functools
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Callable
from urllib.parse import urlparse
import aiohttp
import requests

def sanitize_filename(filename: str) -> str:
    """Sanitize a filename by removing invalid characters."""
    # Remove invalid characters for most file systems
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip(' .')
    
    # Limit length
    if len(sanitized) > 255:
        name, ext = os.path.splitext(sanitized)
        max_name_length = 255 - len(ext)
        sanitized = name[:max_name_length] + ext
    
    # Ensure it's not empty
    if not sanitized:
        sanitized = "unnamed_file"
    
    return sanitized

def safe_json_loads(json_string: str, default: Any = None) -> Any:
    """Safely load JSON string with default fallback."""
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError):
        return default

def safe_json_dumps(obj: Any, default: str = "{}") -> str:
    """Safely dump object to JSON string with default fallback."""
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except (TypeError, ValueError):
        return default

def generate_secure_token(length: int = 32) -> str:
    """Generate a secure random token."""
    return secrets.token_urlsafe(length)

def hash_string(text: str, algorithm: str = "sha256") -> str:
    """Hash a string using specified algorithm."""
    hasher = hashlib.new(algorithm)
    hasher.update(text.encode('utf-8'))
    return hasher.hexdigest()

def validate_email(email: str) -> bool:
    """Validate email address format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_url(url: str) -> bool:
    """Validate URL format."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

def format_duration(seconds: float) -> str:
    """Format duration in seconds to human readable string."""
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} minutes"
    else:
        hours = seconds / 3600
        return f"{hours:.1f} hours"

def format_bytes(bytes_count: int) -> str:
    """Format bytes to human readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_count < 1024.0:
            return f"{bytes_count:.1f} {unit}"
        bytes_count /= 1024.0
    return f"{bytes_count:.1f} PB"

def extract_numbers(text: str) -> List[float]:
    """Extract all numbers from text."""
    pattern = r'-?\d+\.?\d*'
    matches = re.findall(pattern, text)
    return [float(match) for match in matches if match]

def extract_urls(text: str) -> List[str]:
    """Extract all URLs from text."""
    pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    return re.findall(pattern, text)

def extract_email_addresses(text: str) -> List[str]:
    """Extract all email addresses from text."""
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.findall(pattern, text)

def clean_text(text: str) -> str:
    """Clean text by removing extra whitespace and special characters."""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text

def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to maximum length with suffix."""
    if len(text) <= max_length:
        return text
    
    truncated = text[:max_length - len(suffix)]
    return truncated + suffix

def parse_time_string(time_str: str) -> Optional[datetime]:
    """Parse various time string formats to datetime."""
    time_str = time_str.strip().lower()
    now = datetime.now()
    
    # Relative time patterns
    if "now" in time_str:
        return now
    elif "minute" in time_str:
        minutes = extract_numbers(time_str)
        if minutes:
            return now + timedelta(minutes=minutes[0])
    elif "hour" in time_str:
        hours = extract_numbers(time_str)
        if hours:
            return now + timedelta(hours=hours[0])
    elif "day" in time_str:
        days = extract_numbers(time_str)
        if days:
            return now + timedelta(days=days[0])
    elif "tomorrow" in time_str:
        return now + timedelta(days=1)
    elif "next week" in time_str:
        return now + timedelta(weeks=1)
    
    # Absolute time patterns (simplified)
    time_patterns = [
        "%H:%M",
        "%I:%M %p",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %I:%M %p",
        "%m/%d/%Y %H:%M",
        "%m/%d/%Y %I:%M %p"
    ]
    
    for pattern in time_patterns:
        try:
            return datetime.strptime(time_str, pattern)
        except ValueError:
            continue
    
    return None

def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Decorator to retry function on failure."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    
            raise last_exception
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        import time
                        time.sleep(current_delay)
                        current_delay *= backoff
            
            raise last_exception
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator

def rate_limit(calls_per_second: float):
    """Decorator to rate limit function calls."""
    min_interval = 1.0 / calls_per_second
    last_called = [0.0]
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            current_time = asyncio.get_event_loop().time()
            elapsed = current_time - last_called[0]
            
            if elapsed < min_interval:
                await asyncio.sleep(min_interval - elapsed)
            
            last_called[0] = asyncio.get_event_loop().time()
            return await func(*args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            import time
            current_time = time.time()
            elapsed = current_time - last_called[0]
            
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
            
            last_called[0] = time.time()
            return func(*args, **kwargs)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator

async def download_file(url: str, file_path: str, chunk_size: int = 8192) -> bool:
    """Download file from URL asynchronously."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    with open(file_path, 'wb') as file:
                        async for chunk in response.content.iter_chunked(chunk_size):
                            file.write(chunk)
                    return True
                else:
                    return False
    except Exception:
        return False

def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensure directory exists, create if it doesn't."""
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory

def read_file_safely(file_path: Union[str, Path], encoding: str = 'utf-8') -> Optional[str]:
    """Safely read file content."""
    try:
        with open(file_path, 'r', encoding=encoding) as file:
            return file.read()
    except Exception:
        return None

def write_file_safely(file_path: Union[str, Path], content: str, encoding: str = 'utf-8') -> bool:
    """Safely write content to file."""
    try:
        # Ensure directory exists
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding=encoding) as file:
            file.write(content)
        return True
    except Exception:
        return False

def get_file_size(file_path: Union[str, Path]) -> Optional[int]:
    """Get file size in bytes."""
    try:
        return Path(file_path).stat().st_size
    except Exception:
        return None

def get_file_age(file_path: Union[str, Path]) -> Optional[timedelta]:
    """Get file age as timedelta."""
    try:
        file_time = datetime.fromtimestamp(Path(file_path).stat().st_mtime)
        return datetime.now() - file_time
    except Exception:
        return None

class CircularBuffer:
    """Simple circular buffer for storing recent items."""
    
    def __init__(self, capacity: int):
        """Initialize circular buffer."""
        self.capacity = capacity
        self.buffer = []
        self.index = 0
    
    def append(self, item: Any) -> None:
        """Add item to buffer."""
        if len(self.buffer) < self.capacity:
            self.buffer.append(item)
        else:
            self.buffer[self.index] = item
            self.index = (self.index + 1) % self.capacity
    
    def get_all(self) -> List[Any]:
        """Get all items in order."""
        if len(self.buffer) < self.capacity:
            return self.buffer.copy()
        else:
            return self.buffer[self.index:] + self.buffer[:self.index]
    
    def get_last(self, n: int) -> List[Any]:
        """Get last n items."""
        all_items = self.get_all()
        return all_items[-n:] if n <= len(all_items) else all_items
    
    def clear(self) -> None:
        """Clear the buffer."""
        self.buffer.clear()
        self.index = 0

class RateLimiter:
    """Rate limiter using token bucket algorithm."""
    
    def __init__(self, capacity: int, refill_rate: float):
        """Initialize rate limiter."""
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = datetime.now()
    
    def acquire(self, tokens: int = 1) -> bool:
        """Try to acquire tokens."""
        now = datetime.now()
        elapsed = (now - self.last_refill).total_seconds()
        
        # Refill tokens
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        
        return False

def merge_dicts(*dicts: Dict) -> Dict:
    """Merge multiple dictionaries, later ones override earlier ones."""
    result = {}
    for d in dicts:
        if d:
            result.update(d)
    return result

def deep_merge_dicts(dict1: Dict, dict2: Dict) -> Dict:
    """Deep merge two dictionaries."""
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result

def flatten_dict(d: Dict, parent_key: str = '', sep: str = '.') -> Dict:
    """Flatten a nested dictionary."""
    items = []
    
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    
    return dict(items)

def is_port_open(host: str, port: int, timeout: float = 3.0) -> bool:
    """Check if a port is open on a host."""
    import socket
    
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, socket.error):
        return False

def get_local_ip() -> Optional[str]:
    """Get local IP address."""
    import socket
    
    try:
        # Connect to a remote server to determine local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return None

def command_line_args_to_dict(args: List[str]) -> Dict[str, Union[str, bool]]:
    """Convert command line arguments to dictionary."""
    result = {}
    i = 0
    
    while i < len(args):
        arg = args[i]
        
        if arg.startswith('--'):
            key = arg[2:]
            if i + 1 < len(args) and not args[i + 1].startswith('-'):
                # Has value
                result[key] = args[i + 1]
                i += 2
            else:
                # Boolean flag
                result[key] = True
                i += 1
        elif arg.startswith('-'):
            key = arg[1:]
            if i + 1 < len(args) and not args[i + 1].startswith('-'):
                # Has value
                result[key] = args[i + 1]
                i += 2
            else:
                # Boolean flag
                result[key] = True
                i += 1
        else:
            i += 1
    
    return result
