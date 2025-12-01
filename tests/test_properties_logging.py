"""Property-based tests for logging functionality."""

import json
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path
import pytest
from hypothesis import given, settings, strategies as st

from src.utils.logger import (
    setup_logger,
    log_agent_start,
    log_agent_completion,
    log_agent_error,
    JSONFormatter,
)


# Feature: kasparro-fb-analyst, Property 36: Log Format Consistency
# Validates: Requirements 10.4
@settings(max_examples=100, deadline=None)
@given(
    agent_name=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
    log_level=st.sampled_from(["INFO", "WARNING", "ERROR"]),
    message=st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_characters='\x00\n\r')),
)
def test_property_36_log_format_consistency(agent_name, log_level, message):
    """
    Property 36: Log Format Consistency
    For any log entry written by the System, the entry should be valid JSON
    with consistent field names and ISO 8601 timestamps.
    """
    # Create temporary log directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Use unique logger name to avoid conflicts
        import uuid
        logger_name = f"test_{uuid.uuid4().hex[:8]}"
        
        # Set up logger with JSON format
        logger = setup_logger(
            name=logger_name,
            log_level=log_level,
            log_format="json",
            log_dir=temp_dir,
            log_to_console=False,
        )
        
        # Log a message
        logger.log(getattr(logging, log_level), message, extra={"agent_name": agent_name})
        
        # Close handlers to flush
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)
        
        # Find the log file
        log_files = list(Path(temp_dir).glob("*.log"))
        assert len(log_files) == 1
        
        # Read and parse log entry
        with open(log_files[0], 'r') as f:
            log_content = f.read().strip()
        
        # Parse as JSON - should not raise exception
        log_entry = json.loads(log_content)
        
        # Assert required fields are present
        assert "timestamp" in log_entry
        assert "level" in log_entry
        assert "logger" in log_entry
        assert "message" in log_entry
        
        # Assert timestamp is ISO 8601 format
        timestamp_str = log_entry["timestamp"]
        assert timestamp_str.endswith("Z")  # UTC indicator
        # Parse to validate ISO 8601 format
        datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        
        # Assert level matches
        assert log_entry["level"] == log_level
        
        # Assert message is preserved
        assert log_entry["message"] == message
        
        # Assert agent_name is included
        assert log_entry["agent_name"] == agent_name


@settings(max_examples=100, deadline=None)
@given(
    agent_name=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
    execution_duration_ms=st.integers(min_value=0, max_value=100000),
)
def test_log_agent_completion_format(agent_name, execution_duration_ms):
    """Test that agent completion logs have consistent format."""
    with tempfile.TemporaryDirectory() as temp_dir:
        import uuid
        logger_name = f"test_{uuid.uuid4().hex[:8]}"
        
        logger = setup_logger(
            name=logger_name,
            log_level="INFO",
            log_format="json",
            log_dir=temp_dir,
            log_to_console=False,
        )
        
        # Log agent completion
        log_agent_completion(
            logger=logger,
            agent_name=agent_name,
            execution_duration_ms=execution_duration_ms,
            output_summary={"status": "success"},
        )
        
        # Close handlers
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)
        
        # Read log file
        log_files = list(Path(temp_dir).glob("*.log"))
        with open(log_files[0], 'r') as f:
            log_entry = json.loads(f.read().strip())
        
        # Verify format
        assert log_entry["agent_name"] == agent_name
        assert log_entry["execution_duration_ms"] == execution_duration_ms
        assert log_entry["event_type"] == "agent_completion"
        assert "timestamp" in log_entry
        assert log_entry["timestamp"].endswith("Z")


@settings(max_examples=100, deadline=None)
@given(
    agent_name=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
    error_type=st.sampled_from(["ValidationError", "IOError", "TimeoutError", "UnexpectedError"]),
    error_message=st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_characters='\x00\n\r')),
)
def test_log_agent_error_format(agent_name, error_type, error_message):
    """Test that agent error logs have consistent format."""
    with tempfile.TemporaryDirectory() as temp_dir:
        import uuid
        logger_name = f"test_{uuid.uuid4().hex[:8]}"
        
        logger = setup_logger(
            name=logger_name,
            log_level="ERROR",
            log_format="json",
            log_dir=temp_dir,
            log_to_console=False,
        )
        
        # Log agent error
        log_agent_error(
            logger=logger,
            agent_name=agent_name,
            error_message=error_message,
            error_type=error_type,
            agent_state={"current_step": "validation"},
        )
        
        # Close handlers
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)
        
        # Read log file
        log_files = list(Path(temp_dir).glob("*.log"))
        with open(log_files[0], 'r') as f:
            log_entry = json.loads(f.read().strip())
        
        # Verify format
        assert log_entry["agent_name"] == agent_name
        assert log_entry["error_type"] == error_type
        assert log_entry["event_type"] == "agent_error"
        assert error_message in log_entry["message"]
        assert "timestamp" in log_entry
        assert log_entry["timestamp"].endswith("Z")


def test_log_file_creation():
    """Test that log files are created in the correct directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        import uuid
        logger_name = f"test_{uuid.uuid4().hex[:8]}"
        
        logger = setup_logger(
            name=logger_name,
            log_level="INFO",
            log_format="json",
            log_dir=temp_dir,
            log_to_console=False,
        )
        
        logger.info("Test message")
        
        # Close handlers to release file locks
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)
        
        # Verify log file was created
        log_files = list(Path(temp_dir).glob("execution_*.log"))
        assert len(log_files) == 1
        
        # Verify filename format
        log_filename = log_files[0].name
        assert log_filename.startswith("execution_")
        assert log_filename.endswith(".log")
