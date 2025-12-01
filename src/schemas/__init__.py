"""
Schemas package for Kasparro multi-agent system.

This package contains JSON schemas and validation functions for all agent communication.
"""

from src.schemas.agent_io import (
    ENVELOPE_SCHEMA,
    PLANNER_INPUT_SCHEMA,
    PLANNER_OUTPUT_SCHEMA,
    DATA_AGENT_INPUT_SCHEMA,
    DATA_AGENT_OUTPUT_SCHEMA,
    INSIGHT_AGENT_INPUT_SCHEMA,
    INSIGHT_AGENT_OUTPUT_SCHEMA,
    EVALUATOR_INPUT_SCHEMA,
    EVALUATOR_OUTPUT_SCHEMA,
    CREATIVE_GENERATOR_INPUT_SCHEMA,
    CREATIVE_GENERATOR_OUTPUT_SCHEMA,
    REPORT_GENERATOR_INPUT_SCHEMA,
)

from src.schemas.validation import (
    ValidationError,
    validate_schema,
    validate_agent_input,
    validate_agent_output,
    validate_envelope,
    create_error_envelope,
    create_success_envelope,
    serialize_to_json,
    deserialize_from_json,
    validate_confidence_score,
    validate_required_fields,
    validate_iso8601_timestamp,
)

__all__ = [
    # Schemas
    "ENVELOPE_SCHEMA",
    "PLANNER_INPUT_SCHEMA",
    "PLANNER_OUTPUT_SCHEMA",
    "DATA_AGENT_INPUT_SCHEMA",
    "DATA_AGENT_OUTPUT_SCHEMA",
    "INSIGHT_AGENT_INPUT_SCHEMA",
    "INSIGHT_AGENT_OUTPUT_SCHEMA",
    "EVALUATOR_INPUT_SCHEMA",
    "EVALUATOR_OUTPUT_SCHEMA",
    "CREATIVE_GENERATOR_INPUT_SCHEMA",
    "CREATIVE_GENERATOR_OUTPUT_SCHEMA",
    "REPORT_GENERATOR_INPUT_SCHEMA",
    # Validation functions
    "ValidationError",
    "validate_schema",
    "validate_agent_input",
    "validate_agent_output",
    "validate_envelope",
    "create_error_envelope",
    "create_success_envelope",
    "serialize_to_json",
    "deserialize_from_json",
    "validate_confidence_score",
    "validate_required_fields",
    "validate_iso8601_timestamp",
]
