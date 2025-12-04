import logging
import os
from datetime import datetime
from typing import Optional

class AppLogger:
    """
    Centralized logging utility for the Compliance Agent.
    Provides file and console logging with structured formatting.
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not AppLogger._initialized:
            self.setup_logging()
            AppLogger._initialized = True
    
    def setup_logging(self):
        """Initialize logging configuration."""
        # Create logs directory
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger("ComplianceAgent")
        self.logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            return
        
        # File handler
        log_file = os.path.join(log_dir, f"app_{datetime.now().strftime('%Y%m%d')}.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Activity log for UI display
        self.activity_log = []
        self.max_activity_items = 50
    
    def log_activity(self, level: str, message: str, details: Optional[str] = None):
        """
        Log an activity and store it for UI display.
        
        Args:
            level: Log level (INFO, WARNING, ERROR, SUCCESS)
            message: Main message
            details: Optional detailed information
        """
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # Add to activity log
        activity_item = {
            "timestamp": timestamp,
            "level": level,
            "message": message,
            "details": details
        }
        self.activity_log.insert(0, activity_item)  # Most recent first
        
        # Keep only last N items
        if len(self.activity_log) > self.max_activity_items:
            self.activity_log = self.activity_log[:self.max_activity_items]
        
        # Log to file/console
        log_method = getattr(self.logger, level.lower() if level != "SUCCESS" else "info")
        full_message = f"{message} | {details}" if details else message
        log_method(full_message)
    
    def info(self, message: str, details: Optional[str] = None):
        """Log info level message."""
        self.log_activity("INFO", message, details)
    
    def success(self, message: str, details: Optional[str] = None):
        """Log success message."""
        self.log_activity("SUCCESS", message, details)
    
    def warning(self, message: str, details: Optional[str] = None):
        """Log warning level message."""
        self.log_activity("WARNING", message, details)
    
    def error(self, message: str, details: Optional[str] = None):
        """Log error level message."""
        self.log_activity("ERROR", message, details)
    
    def get_recent_activities(self, limit: int = 10):
        """Get recent activity log items for UI display."""
        return self.activity_log[:limit]
    
    def clear_activities(self):
        """Clear activity log."""
        self.activity_log = []

# Singleton instance
logger = AppLogger()
