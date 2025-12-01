"""Structured JSON logging with ISO 8601 timestamps for Kasparro system."""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs logs as JSON with ISO 8601 timestamps."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON-formatted log string
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields from record
        if hasattr(record, "agent_name"):
            log_data["agent_name"] = record.agent_name
        
        if hasattr(record, "execution_duration_ms"):
            log_data["execution_duration_ms"] = record.execution_duration_ms
        
        if hasattr(record, "error_type"):
            log_data["error_type"] = record.error_type
        
        # Add any other custom attributes
        for key, value in record.__dict__.items():
            if key not in ["name", "msg", "args", "created", "filename", "funcName",
                          "levelname", "levelno", "lineno", "module", "msecs",
                          "message", "pathname", "process", "processName",
                          "relativeCreated", "thread", "threadName", "exc_info",
                          "exc_text", "stack_info", "agent_name", "execution_duration_ms",
                          "error_type"]:
                if not key.startswith("_"):
                    log_data[key] = value
        
        return json.dumps(log_data)


class TextFormatter(logging.Formatter):
    """Custom formatter for human-readable text logs."""
    
    def __init__(self):
        super().__init__(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S"
        )
    
    def formatTime(self, record: logging.LogRecord, datefmt: Optional[str] = None) -> str:
        """Format timestamp as ISO 8601.
        
        Args:
            record: Log record
            datefmt: Date format string
            
        Returns:
            Formatted timestamp
        """
        ct = datetime.fromtimestamp(record.created)
        if datefmt:
            s = ct.strftime(datefmt)
        else:
            s = ct.isoformat()
        return s


def setup_logger(
    name: str,
    log_level: str = "INFO",
    log_format: str = "json",
    log_dir: str = "logs",
    log_to_console: bool = True,
) -> logging.Logger:
    """Set up a logger with specified configuration.
    
    Args:
        name: Logger name
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_format: Format type ('json' or 'text')
        log_dir: Directory for log files
        log_to_console: Whether to also log to console
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create log directory if it doesn't exist
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # Create file handler with timestamp-based filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"execution_{timestamp}.log")
    file_handler = logging.FileHandler(log_file)
    
    # Set formatter based on format type
    if log_format.lower() == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()
    
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Add console handler if requested
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger


def log_agent_start(
    logger: logging.Logger,
    agent_name: str,
    input_parameters: Dict[str, Any],
) -> None:
    """Log agent execution start.
    
    Args:
        logger: Logger instance
        agent_name: Name of the agent
        input_parameters: Agent input parameters
    """
    logger.info(
        f"Agent {agent_name} starting execution",
        extra={
            "agent_name": agent_name,
            "input_parameters": input_parameters,
            "event_type": "agent_start",
        }
    )


def log_agent_completion(
    logger: logging.Logger,
    agent_name: str,
    execution_duration_ms: int,
    output_summary: Optional[Dict[str, Any]] = None,
) -> None:
    """Log agent execution completion.
    
    Args:
        logger: Logger instance
        agent_name: Name of the agent
        execution_duration_ms: Execution duration in milliseconds
        output_summary: Summary of agent output
    """
    extra = {
        "agent_name": agent_name,
        "execution_duration_ms": execution_duration_ms,
        "event_type": "agent_completion",
    }
    
    if output_summary:
        extra["output_summary"] = output_summary
    
    logger.info(
        f"Agent {agent_name} completed execution in {execution_duration_ms}ms",
        extra=extra
    )


def log_agent_error(
    logger: logging.Logger,
    agent_name: str,
    error_message: str,
    error_type: str,
    agent_state: Optional[Dict[str, Any]] = None,
) -> None:
    """Log agent execution error.
    
    Args:
        logger: Logger instance
        agent_name: Name of the agent
        error_message: Error message
        error_type: Type of error
        agent_state: Current agent state
    """
    extra = {
        "agent_name": agent_name,
        "error_type": error_type,
        "event_type": "agent_error",
    }
    
    if agent_state:
        extra["agent_state"] = agent_state
    
    logger.error(
        f"Agent {agent_name} error: {error_message}",
        extra=extra,
        exc_info=True
    )


def create_logger_from_config(config: Dict[str, Any], name: str = "kasparro") -> logging.Logger:
    """Create logger from configuration dictionary.
    
    Args:
        config: Configuration dictionary
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    logging_config = config.get("logging", {})
    
    return setup_logger(
        name=name,
        log_level=logging_config.get("level", "INFO"),
        log_format=logging_config.get("format", "json"),
        log_dir=logging_config.get("log_dir", "logs"),
        log_to_console=True,
    )
