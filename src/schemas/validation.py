"""
Schema validation functions for agent communication.

This module provides validation functions using jsonschema to ensure
all agent inputs and outputs conform to their defined schemas.
"""

import json
from typing import Any, Dict, Optional, Tuple
from jsonschema import validate, ValidationError as JsonSchemaValidationError, Draft7Validator
from datetime import datetime


class ValidationError(Exception):
    """Custom validation error for schema validation failures."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


def validate_schema(data: Dict[str, Any], schema: Dict[str, Any], schema_name: str = "unknown") -> Tuple[bool, Optional[str]]:
    """
    Validate data against a JSON schema.
    
    Args:
        data: The data to validate
        schema: The JSON schema to validate against
        schema_name: Name of the schema for error reporting
        
    Returns:
        Tuple of (is_valid, error_message)
        
    Raises:
        ValidationError: If validation fails with structured error details
    """
    try:
        validate(instance=data, schema=schema)
        return True, None
    except JsonSchemaValidationError as e:
        error_msg = f"Schema validation failed for {schema_name}: {e.message}"
        error_details = {
            "schema_name": schema_name,
            "validation_error": e.message,
            "failed_path": list(e.path) if e.path else [],
            "schema_path": list(e.schema_path) if e.schema_path else []
        }
        raise ValidationError(error_msg, error_details)


def validate_agent_input(data: Dict[str, Any], schema: Dict[str, Any], agent_name: str) -> bool:
    """
    Validate agent input data against schema.
    
    Args:
        data: Input data to validate
        schema: JSON schema for the agent input
        agent_name: Name of the agent for error reporting
        
    Returns:
        True if validation succeeds
        
    Raises:
        ValidationError: If validation fails
    """
    schema_name = f"{agent_name}_input"
    return validate_schema(data, schema, schema_name)[0]


def validate_agent_output(data: Dict[str, Any], schema: Dict[str, Any], agent_name: str) -> bool:
    """
    Validate agent output data against schema.
    
    Args:
        data: Output data to validate
        schema: JSON schema for the agent output
        agent_name: Name of the agent for error reporting
        
    Returns:
        True if validation succeeds
        
    Raises:
        ValidationError: If validation fails
    """
    schema_name = f"{agent_name}_output"
    return validate_schema(data, schema, schema_name)[0]


def validate_envelope(data: Dict[str, Any], envelope_schema: Dict[str, Any]) -> bool:
    """
    Validate communication envelope structure.
    
    Args:
        data: Envelope data to validate
        envelope_schema: JSON schema for the envelope
        
    Returns:
        True if validation succeeds
        
    Raises:
        ValidationError: If validation fails
    """
    return validate_schema(data, envelope_schema, "communication_envelope")[0]


def create_error_envelope(
    agent_name: str,
    error_type: str,
    error_message: str,
    error_details: Optional[Dict[str, Any]] = None,
    stack_trace: Optional[str] = None,
    execution_duration_ms: Optional[int] = None
) -> Dict[str, Any]:
    """
    Create a standardized error envelope.
    
    Args:
        agent_name: Name of the agent that encountered the error
        error_type: Type of error (ValidationError, IOError, etc.)
        error_message: Human-readable error message
        error_details: Additional error context
        stack_trace: Stack trace if available
        execution_duration_ms: Execution duration in milliseconds (optional)
        
    Returns:
        Error envelope dictionary
    """
    envelope = {
        "agent_name": agent_name,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "status": "failure",
        "error": {
            "error_type": error_type,
            "error_message": error_message
        }
    }
    
    if execution_duration_ms is not None:
        envelope["execution_duration_ms"] = execution_duration_ms
    
    if error_details:
        envelope["error"]["error_details"] = error_details
    
    if stack_trace:
        envelope["error"]["stack_trace"] = stack_trace
    
    return envelope


def create_success_envelope(
    agent_name: str,
    execution_duration_ms: int,
    payload: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a standardized success envelope.
    
    Args:
        agent_name: Name of the agent
        execution_duration_ms: Execution time in milliseconds
        payload: Agent-specific output data
        
    Returns:
        Success envelope dictionary
    """
    envelope = {
        "agent_name": agent_name,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "execution_duration_ms": execution_duration_ms,
        "status": "success"
    }
    
    if payload:
        envelope.update(payload)
    
    return envelope


def serialize_to_json(data: Dict[str, Any]) -> str:
    """
    Serialize data to JSON string.
    
    Args:
        data: Data to serialize
        
    Returns:
        JSON string
        
    Raises:
        ValidationError: If serialization fails
    """
    try:
        return json.dumps(data, indent=2, ensure_ascii=False)
    except (TypeError, ValueError) as e:
        raise ValidationError(f"JSON serialization failed: {str(e)}", {"original_error": str(e)})


def deserialize_from_json(json_str: str) -> Dict[str, Any]:
    """
    Deserialize JSON string to dictionary.
    
    Args:
        json_str: JSON string to deserialize
        
    Returns:
        Deserialized dictionary
        
    Raises:
        ValidationError: If deserialization fails
    """
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValidationError(f"JSON deserialization failed: {str(e)}", {"original_error": str(e)})


def validate_confidence_score(score: float, field_name: str = "confidence_score") -> bool:
    """
    Validate that a confidence score is between 0 and 1.
    
    Args:
        score: Confidence score to validate
        field_name: Name of the field for error reporting
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If score is out of bounds
    """
    if not isinstance(score, (int, float)):
        raise ValidationError(
            f"{field_name} must be a number",
            {"field": field_name, "value": score, "type": type(score).__name__}
        )
    
    if not (0.0 <= score <= 1.0):
        raise ValidationError(
            f"{field_name} must be between 0.0 and 1.0",
            {"field": field_name, "value": score, "min": 0.0, "max": 1.0}
        )
    
    return True


def validate_required_fields(data: Dict[str, Any], required_fields: list, context: str = "data") -> bool:
    """
    Validate that all required fields are present in data.
    
    Args:
        data: Data dictionary to check
        required_fields: List of required field names
        context: Context description for error reporting
        
    Returns:
        True if all fields present
        
    Raises:
        ValidationError: If any required fields are missing
    """
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        raise ValidationError(
            f"Missing required fields in {context}",
            {"missing_fields": missing_fields, "required_fields": required_fields}
        )
    
    return True


def validate_iso8601_timestamp(timestamp: str, field_name: str = "timestamp") -> bool:
    """
    Validate that a timestamp is in ISO 8601 format.
    
    Args:
        timestamp: Timestamp string to validate
        field_name: Name of the field for error reporting
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If timestamp format is invalid
    """
    try:
        # Try to parse the timestamp
        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return True
    except (ValueError, AttributeError) as e:
        raise ValidationError(
            f"{field_name} must be in ISO 8601 format",
            {"field": field_name, "value": timestamp, "error": str(e)}
        )
