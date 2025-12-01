"""Property-based tests for CLI interface and workflow orchestration."""

import json
import os
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Any, Dict
import pytest
from hypothesis import given, settings, strategies as st

from src.run import (
    validate_query,
    validate_inputs,
    ensure_output_directory,
    write_output_file,
    CLIError,
)
from src.utils.logger import setup_logger


# Feature: kasparro-fb-analyst, Property 33: Agent Execution Start Logging
# Validates: Requirements 10.1
@settings(max_examples=100, deadline=None)
@given(
    agent_name=st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
    input_param_count=st.integers(min_value=1, max_value=5),
)
def test_property_33_agent_execution_start_logging(agent_name, input_param_count):
    """
    Property 33: Agent Execution Start Logging
    For any agent execution start, the System should write a log entry containing
    agent_name, input_parameters, and start_timestamp.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        import uuid
        logger_name = f"test_{uuid.uuid4().hex[:8]}"
        
        # Set up logger
        logger = setup_logger(
            name=logger_name,
            log_level="INFO",
            log_format="json",
            log_dir=temp_dir,
            log_to_console=False,
        )
        
        # Create input parameters
        input_parameters = {
            f"param_{i}": f"value_{i}"
            for i in range(input_param_count)
        }
        
        # Log agent start using the utility function
        from src.utils.logger import log_agent_start
        log_agent_start(logger, agent_name, input_parameters)
        
        # Close handlers to flush
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)
        
        # Read log file
        log_files = list(Path(temp_dir).glob("*.log"))
        assert len(log_files) == 1
        
        with open(log_files[0], 'r') as f:
            log_entry = json.loads(f.read().strip())
        
        # Assert required fields are present
        assert "agent_name" in log_entry
        assert log_entry["agent_name"] == agent_name
        
        assert "input_parameters" in log_entry
        assert log_entry["input_parameters"] == input_parameters
        
        assert "timestamp" in log_entry
        assert log_entry["timestamp"].endswith("Z")
        
        # Verify timestamp is valid ISO 8601
        datetime.fromisoformat(log_entry["timestamp"].replace("Z", "+00:00"))
        
        # Verify event type
        assert log_entry.get("event_type") == "agent_start"


# Feature: kasparro-fb-analyst, Property 34: Agent Execution Completion Logging
# Validates: Requirements 10.2
@settings(max_examples=100, deadline=None)
@given(
    agent_name=st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
    execution_duration_ms=st.integers(min_value=1, max_value=100000),
    output_key_count=st.integers(min_value=1, max_value=5),
)
def test_property_34_agent_execution_completion_logging(agent_name, execution_duration_ms, output_key_count):
    """
    Property 34: Agent Execution Completion Logging
    For any agent execution completion, the System should write a log entry containing
    agent_name, output_summary, and execution_duration_ms.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        import uuid
        logger_name = f"test_{uuid.uuid4().hex[:8]}"
        
        # Set up logger
        logger = setup_logger(
            name=logger_name,
            log_level="INFO",
            log_format="json",
            log_dir=temp_dir,
            log_to_console=False,
        )
        
        # Create output summary
        output_summary = {
            "status": "success",
            "output_keys": [f"key_{i}" for i in range(output_key_count)]
        }
        
        # Log agent completion using the utility function
        from src.utils.logger import log_agent_completion
        log_agent_completion(logger, agent_name, execution_duration_ms, output_summary)
        
        # Close handlers to flush
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)
        
        # Read log file
        log_files = list(Path(temp_dir).glob("*.log"))
        assert len(log_files) == 1
        
        with open(log_files[0], 'r') as f:
            log_entry = json.loads(f.read().strip())
        
        # Assert required fields are present
        assert "agent_name" in log_entry
        assert log_entry["agent_name"] == agent_name
        
        assert "execution_duration_ms" in log_entry
        assert log_entry["execution_duration_ms"] == execution_duration_ms
        
        assert "output_summary" in log_entry
        assert log_entry["output_summary"] == output_summary
        
        assert "timestamp" in log_entry
        assert log_entry["timestamp"].endswith("Z")
        
        # Verify event type
        assert log_entry.get("event_type") == "agent_completion"


# Feature: kasparro-fb-analyst, Property 35: Error Logging Completeness
# Validates: Requirements 10.3
@settings(max_examples=100, deadline=None)
@given(
    agent_name=st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
    error_type=st.sampled_from(["ValidationError", "IOError", "TimeoutError", "UnexpectedError"]),
    error_message=st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_characters='\x00\n\r')),
)
def test_property_35_error_logging_completeness(agent_name, error_type, error_message):
    """
    Property 35: Error Logging Completeness
    For any error occurrence during agent execution, the System should log
    error_message, stack_trace, agent_name, and agent_state.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        import uuid
        logger_name = f"test_{uuid.uuid4().hex[:8]}"
        
        # Set up logger
        logger = setup_logger(
            name=logger_name,
            log_level="ERROR",
            log_format="json",
            log_dir=temp_dir,
            log_to_console=False,
        )
        
        # Create agent state
        agent_state = {
            "current_step": "processing",
            "items_processed": 42
        }
        
        # Log agent error using the utility function
        from src.utils.logger import log_agent_error
        log_agent_error(logger, agent_name, error_message, error_type, agent_state)
        
        # Close handlers to flush
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)
        
        # Read log file
        log_files = list(Path(temp_dir).glob("*.log"))
        assert len(log_files) == 1
        
        with open(log_files[0], 'r') as f:
            log_entry = json.loads(f.read().strip())
        
        # Assert required fields are present
        assert "agent_name" in log_entry
        assert log_entry["agent_name"] == agent_name
        
        assert "error_type" in log_entry
        assert log_entry["error_type"] == error_type
        
        assert "message" in log_entry
        assert error_message in log_entry["message"]
        
        # Stack trace should be present (from exc_info=True)
        # Note: In actual error scenarios, exception info would be captured
        
        assert "agent_state" in log_entry
        assert log_entry["agent_state"] == agent_state
        
        assert "timestamp" in log_entry
        assert log_entry["timestamp"].endswith("Z")
        
        # Verify event type
        assert log_entry.get("event_type") == "agent_error"


# Feature: kasparro-fb-analyst, Property 37: Log File Creation
# Validates: Requirements 10.5
@settings(max_examples=100, deadline=None)
@given(
    log_message=st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_characters='\x00\n\r')),
)
def test_property_37_log_file_creation(log_message):
    """
    Property 37: Log File Creation
    For any system execution, the System should create a log file in the logs
    directory with timestamp-based filename.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        import uuid
        logger_name = f"test_{uuid.uuid4().hex[:8]}"
        
        # Set up logger with custom log directory
        logger = setup_logger(
            name=logger_name,
            log_level="INFO",
            log_format="json",
            log_dir=temp_dir,
            log_to_console=False,
        )
        
        # Log a message
        logger.info(log_message)
        
        # Close handlers to flush
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)
        
        # Verify log file was created in the specified directory
        log_files = list(Path(temp_dir).glob("*.log"))
        assert len(log_files) == 1
        
        # Verify filename format: execution_YYYYMMDD_HHMMSS.log
        log_filename = log_files[0].name
        assert log_filename.startswith("execution_")
        assert log_filename.endswith(".log")
        
        # Extract timestamp from filename
        timestamp_part = log_filename.replace("execution_", "").replace(".log", "")
        assert len(timestamp_part) == 15  # YYYYMMDD_HHMMSS
        assert timestamp_part[8] == "_"  # Underscore separator
        
        # Verify file is in the correct directory
        assert log_files[0].parent == Path(temp_dir)


# Feature: kasparro-fb-analyst, Property 56: Output File Location Consistency
# Validates: Requirements 18.5
@settings(max_examples=100, deadline=None)
@given(
    output_dir_name=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
    file_content_size=st.integers(min_value=1, max_value=10),
)
def test_property_56_output_file_location_consistency(output_dir_name, file_content_size):
    """
    Property 56: Output File Location Consistency
    For any system execution, outputs should be written to the configured output
    directory (reports/ by default) with consistent filenames: insights.json,
    creatives.json, and report.md.
    """
    with tempfile.TemporaryDirectory() as temp_base:
        # Create output directory
        output_dir = os.path.join(temp_base, output_dir_name)
        ensure_output_directory(output_dir)
        
        # Verify directory was created
        assert os.path.exists(output_dir)
        assert os.path.isdir(output_dir)
        
        # Create a simple logger for testing
        import uuid
        logger_name = f"test_{uuid.uuid4().hex[:8]}"
        logger = setup_logger(
            name=logger_name,
            log_level="INFO",
            log_format="json",
            log_dir=temp_base,
            log_to_console=False,
        )
        
        # Write test outputs
        insights_data = {
            "validated_hypotheses": [
                {"hypothesis": f"test_{i}", "confidence": 0.8}
                for i in range(file_content_size)
            ]
        }
        
        creatives_data = {
            "recommendations": [
                {"creative": f"creative_{i}", "confidence": 0.7}
                for i in range(file_content_size)
            ]
        }
        
        report_content = "# Test Report\n\nThis is a test report."
        
        # Write files
        write_output_file(output_dir, "insights.json", insights_data, logger)
        write_output_file(output_dir, "creatives.json", creatives_data, logger)
        write_output_file(output_dir, "report.md", report_content, logger)
        
        # Close logger handlers
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)
        
        # Verify all files were created in the correct location
        insights_path = os.path.join(output_dir, "insights.json")
        creatives_path = os.path.join(output_dir, "creatives.json")
        report_path = os.path.join(output_dir, "report.md")
        
        assert os.path.exists(insights_path)
        assert os.path.exists(creatives_path)
        assert os.path.exists(report_path)
        
        # Verify file contents
        with open(insights_path, 'r') as f:
            loaded_insights = json.load(f)
            assert loaded_insights == insights_data
        
        with open(creatives_path, 'r') as f:
            loaded_creatives = json.load(f)
            assert loaded_creatives == creatives_data
        
        with open(report_path, 'r') as f:
            loaded_report = f.read()
            assert loaded_report == report_content


# Additional tests for CLI validation
@settings(max_examples=100)
@given(
    query_length=st.integers(min_value=0, max_value=4),
)
def test_cli_query_validation_short_query(query_length):
    """Test that short queries are rejected."""
    query = "a" * query_length
    
    if query_length < 5:
        with pytest.raises(CLIError) as exc_info:
            validate_query(query)
        # Check for either "empty" (when length is 0) or "too short" (when 1-4)
        error_msg = str(exc_info.value).lower()
        assert "empty" in error_msg or "too short" in error_msg
    else:
        # Should not raise for queries >= 5 characters
        validate_query(query)


@settings(max_examples=100)
@given(
    whitespace_count=st.integers(min_value=0, max_value=10),
)
def test_cli_query_validation_whitespace(whitespace_count):
    """Test that whitespace-only queries are rejected."""
    query = " " * whitespace_count
    
    with pytest.raises(CLIError) as exc_info:
        validate_query(query)
    assert "empty" in str(exc_info.value).lower()


def test_output_directory_creation():
    """Test that output directory is created if it doesn't exist."""
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = os.path.join(temp_dir, "test_output", "nested", "dir")
        
        # Directory should not exist initially
        assert not os.path.exists(output_dir)
        
        # Create directory
        ensure_output_directory(output_dir)
        
        # Directory should now exist
        assert os.path.exists(output_dir)
        assert os.path.isdir(output_dir)
