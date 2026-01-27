"""Structured JSON logging setup."""
import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs JSON logs."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
        }
        
        # Add extra fields if available
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data)


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Configure and return a JSON logger."""
    logger = logging.getLogger("webhook_api")
    logger.setLevel(log_level.upper())
    
    # Remove existing handlers
    logger.handlers = []
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
    
    return logger


# Global logger instance
logger = logging.getLogger("webhook_api")
