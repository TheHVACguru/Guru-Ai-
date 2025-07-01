"""
Logging utilities for Voice Assistant.
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

def setup_logger(name: str, level: Optional[str] = None, log_file: Optional[str] = None) -> logging.Logger:
    """Setup logger with console and file handlers."""
    
    # Get log level from environment or use INFO as default
    log_level = level or os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level, logging.INFO)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(numeric_level)
    
    # Avoid duplicate handlers if logger already exists
    if logger.handlers:
        return logger
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    if log_file or os.getenv("LOG_FILE"):
        log_file = log_file or os.getenv("LOG_FILE", "assistant.log")
        
        # Create logs directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Get max log size from environment
        max_bytes = int(os.getenv("MAX_LOG_SIZE", "10485760"))  # 10MB default
        backup_count = int(os.getenv("LOG_BACKUP_COUNT", "5"))
        
        # Rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """Get an existing logger or create a new one."""
    return logging.getLogger(name)

def set_log_level(level: str) -> None:
    """Set log level for all existing loggers."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Set root logger level
    logging.getLogger().setLevel(numeric_level)
    
    # Set level for all existing loggers
    for logger_name in logging.Logger.manager.loggerDict:
        logger = logging.getLogger(logger_name)
        logger.setLevel(numeric_level)
        
        # Update handler levels
        for handler in logger.handlers:
            handler.setLevel(numeric_level)

class ContextLogger:
    """Logger with additional context information."""
    
    def __init__(self, logger: logging.Logger, context: dict = None):
        """Initialize context logger."""
        self.logger = logger
        self.context = context or {}
    
    def _format_message(self, message: str) -> str:
        """Format message with context."""
        if self.context:
            context_str = " | ".join(f"{k}={v}" for k, v in self.context.items())
            return f"[{context_str}] {message}"
        return message
    
    def debug(self, message: str, *args, **kwargs):
        """Log debug message with context."""
        self.logger.debug(self._format_message(message), *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """Log info message with context."""
        self.logger.info(self._format_message(message), *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """Log warning message with context."""
        self.logger.warning(self._format_message(message), *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """Log error message with context."""
        self.logger.error(self._format_message(message), *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """Log critical message with context."""
        self.logger.critical(self._format_message(message), *args, **kwargs)
    
    def exception(self, message: str, *args, **kwargs):
        """Log exception with context."""
        self.logger.exception(self._format_message(message), *args, **kwargs)

def create_context_logger(name: str, context: dict = None) -> ContextLogger:
    """Create a context logger."""
    logger = setup_logger(name)
    return ContextLogger(logger, context)

class LogTimer:
    """Context manager for timing operations with logging."""
    
    def __init__(self, logger: logging.Logger, operation: str, level: int = logging.INFO):
        """Initialize log timer."""
        self.logger = logger
        self.operation = operation
        self.level = level
        self.start_time = None
    
    def __enter__(self):
        """Start timing."""
        self.start_time = datetime.now()
        self.logger.log(self.level, f"Starting {self.operation}...")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End timing and log duration."""
        if self.start_time:
            duration = datetime.now() - self.start_time
            duration_ms = duration.total_seconds() * 1000
            
            if exc_type is None:
                self.logger.log(self.level, f"Completed {self.operation} in {duration_ms:.2f}ms")
            else:
                self.logger.error(f"Failed {self.operation} after {duration_ms:.2f}ms: {exc_val}")

def log_function_call(logger: logging.Logger, level: int = logging.DEBUG):
    """Decorator to log function calls."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            func_name = func.__name__
            logger.log(level, f"Calling {func_name} with args={args}, kwargs={kwargs}")
            
            try:
                result = func(*args, **kwargs)
                logger.log(level, f"{func_name} completed successfully")
                return result
            except Exception as e:
                logger.error(f"{func_name} failed with error: {e}")
                raise
        
        return wrapper
    return decorator

# Performance logging utilities
class PerformanceLogger:
    """Logger for performance metrics."""
    
    def __init__(self, name: str = "performance"):
        """Initialize performance logger."""
        self.logger = setup_logger(f"assistant.performance.{name}")
    
    def log_response_time(self, operation: str, duration_ms: float, success: bool = True):
        """Log response time for an operation."""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"RESPONSE_TIME | {operation} | {duration_ms:.2f}ms | {status}")
    
    def log_resource_usage(self, cpu_percent: float, memory_mb: float, operation: str = ""):
        """Log resource usage."""
        self.logger.info(f"RESOURCE_USAGE | {operation} | CPU: {cpu_percent:.1f}% | Memory: {memory_mb:.1f}MB")
    
    def log_api_call(self, service: str, endpoint: str, duration_ms: float, status_code: int):
        """Log API call metrics."""
        self.logger.info(f"API_CALL | {service} | {endpoint} | {duration_ms:.2f}ms | {status_code}")

# Error tracking utilities
class ErrorTracker:
    """Track and log errors with context."""
    
    def __init__(self, name: str = "errors"):
        """Initialize error tracker."""
        self.logger = setup_logger(f"assistant.errors.{name}")
        self.error_counts = {}
    
    def track_error(self, error_type: str, error_message: str, context: dict = None):
        """Track an error occurrence."""
        # Count errors
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        # Log error with context
        context_str = ""
        if context:
            context_str = " | " + " | ".join(f"{k}={v}" for k, v in context.items())
        
        self.logger.error(f"ERROR_TRACKED | {error_type} | {error_message} | Count: {self.error_counts[error_type]}{context_str}")
    
    def get_error_summary(self) -> dict:
        """Get summary of tracked errors."""
        return self.error_counts.copy()

# Global logger instances
_main_logger = None
_performance_logger = None
_error_tracker = None

def get_main_logger() -> logging.Logger:
    """Get the main application logger."""
    global _main_logger
    if _main_logger is None:
        _main_logger = setup_logger("assistant.main")
    return _main_logger

def get_performance_logger() -> PerformanceLogger:
    """Get the performance logger."""
    global _performance_logger
    if _performance_logger is None:
        _performance_logger = PerformanceLogger()
    return _performance_logger

def get_error_tracker() -> ErrorTracker:
    """Get the error tracker."""
    global _error_tracker
    if _error_tracker is None:
        _error_tracker = ErrorTracker()
    return _error_tracker
