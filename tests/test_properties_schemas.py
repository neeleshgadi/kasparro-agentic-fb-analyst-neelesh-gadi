"""
Property-based tests for schema validation.

These tests verify that schema validation works correctly across
a wide range of inputs using property-based testing with Hypothesis.
"""

import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime
import json

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
)

from src.schemas.validation import (
    ValidationError,
    validate_schema,
    validate_agent_input,
    validate_agent_output,
    validate_envelope,
    serialize_to_json,
    deserialize_from_json,
    validate_confidence_score,
    create_success_envelope,
    create_error_envelope,
)


# Hypothesis strategies for generating test data

@st.composite
def valid_envelope(draw):
    """Generate a valid communication envelope."""
    return {
        "agent_name": draw(st.text(min_size=1, max_size=50)),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "status": draw(st.sampled_from(["success", "failure", "partial"])),
        "execution_duration_ms": draw(st.integers(min_value=0, max_value=100000))
    }


@st.composite
def invalid_envelope(draw):
    """Generate an invalid communication envelope (missing required fields)."""
    # Create envelope with missing required fields
    envelope = {}
    
    # Randomly include/exclude required fields
    if draw(st.booleans()):
        envelope["agent_name"] = draw(st.text(min_size=1, max_size=50))
    
    if draw(st.booleans()):
        envelope["timestamp"] = datetime.utcnow().isoformat() + "Z"
    
    # Ensure at least one required field is missing
    if "agent_name" in envelope and "timestamp" in envelope:
        # Remove one randomly
        if draw(st.booleans()):
            del envelope["agent_name"]
        else:
            del envelope["timestamp"]
    
    return envelope


@st.composite
def valid_planner_input(draw):
    """Generate valid planner input."""
    return {
        "query": draw(st.text(min_size=1, max_size=200)),
        "context": {
            "dataset_path": draw(st.text(min_size=1, max_size=100)),
            "config": draw(st.dictionaries(st.text(min_size=1), st.integers()))
        }
    }


@st.composite
def valid_data_agent_input(draw):
    """Generate valid data agent input."""
    return {
        "dataset_path": draw(st.text(min_size=1, max_size=100)),
        "config": draw(st.dictionaries(st.text(min_size=1), st.integers()))
    }


@st.composite
def valid_confidence_score(draw):
    """Generate a valid confidence score between 0 and 1."""
    return draw(st.floats(min_value=0.0, max_value=1.0))


@st.composite
def invalid_confidence_score(draw):
    """Generate an invalid confidence score (outside 0-1 range)."""
    return draw(st.one_of(
        st.floats(min_value=-100.0, max_value=-0.01),
        st.floats(min_value=1.01, max_value=100.0)
    ))


# Feature: kasparro-fb-analyst, Property 3: Schema Validation on Agent Communication
# Validates: Requirements 2.1, 2.2, 2.3

@settings(max_examples=100)
@given(envelope=valid_envelope())
def test_property_valid_envelope_passes_validation(envelope):
    """
    Property 3: Schema Validation on Agent Communication
    
    For any valid communication envelope, validation should succeed.
    """
    # Valid envelopes should pass validation
    is_valid, error = validate_schema(envelope, ENVELOPE_SCHEMA, "test_envelope")
    assert is_valid is True
    assert error is None


@settings(max_examples=100)
@given(envelope=invalid_envelope())
def test_property_invalid_envelope_fails_validation(envelope):
    """
    Property 3: Schema Validation on Agent Communication
    
    For any invalid communication envelope (missing required fields),
    validation should fail with a ValidationError.
    """
    # Invalid envelopes should raise ValidationError
    with pytest.raises(ValidationError) as exc_info:
        validate_schema(envelope, ENVELOPE_SCHEMA, "test_envelope")
    
    # Error should contain details
    assert exc_info.value.details is not None
    assert "schema_name" in exc_info.value.details


@settings(max_examples=100)
@given(planner_input=valid_planner_input())
def test_property_valid_planner_input_passes_validation(planner_input):
    """
    Property 3: Schema Validation on Agent Communication
    
    For any valid planner input, validation should succeed.
    """
    is_valid = validate_agent_input(planner_input, PLANNER_INPUT_SCHEMA, "planner")
    assert is_valid is True


@settings(max_examples=100)
@given(data_input=valid_data_agent_input())
def test_property_valid_data_agent_input_passes_validation(data_input):
    """
    Property 3: Schema Validation on Agent Communication
    
    For any valid data agent input, validation should succeed.
    """
    is_valid = validate_agent_input(data_input, DATA_AGENT_INPUT_SCHEMA, "data_agent")
    assert is_valid is True


@settings(max_examples=100)
@given(score=valid_confidence_score())
def test_property_valid_confidence_scores_pass_validation(score):
    """
    Property 3: Schema Validation on Agent Communication
    
    For any confidence score between 0.0 and 1.0, validation should succeed.
    """
    is_valid = validate_confidence_score(score)
    assert is_valid is True


@settings(max_examples=100)
@given(score=invalid_confidence_score())
def test_property_invalid_confidence_scores_fail_validation(score):
    """
    Property 3: Schema Validation on Agent Communication
    
    For any confidence score outside the range [0.0, 1.0],
    validation should fail with a ValidationError.
    """
    with pytest.raises(ValidationError) as exc_info:
        validate_confidence_score(score)
    
    # Error should indicate the score is out of bounds
    assert "between 0.0 and 1.0" in exc_info.value.message


# Feature: kasparro-fb-analyst, Property 5: JSON Serialization Round-Trip
# Validates: Requirements 2.4

@settings(max_examples=100)
@given(envelope=valid_envelope())
def test_property_json_serialization_round_trip_envelope(envelope):
    """
    Property 5: JSON Serialization Round-Trip
    
    For any valid envelope, serializing to JSON and deserializing
    should produce an equivalent structure.
    """
    # Serialize to JSON
    json_str = serialize_to_json(envelope)
    
    # Deserialize back
    deserialized = deserialize_from_json(json_str)
    
    # Should be equivalent
    assert deserialized == envelope
    
    # Verify it's still valid
    is_valid, _ = validate_schema(deserialized, ENVELOPE_SCHEMA, "test_envelope")
    assert is_valid is True


@settings(max_examples=100)
@given(planner_input=valid_planner_input())
def test_property_json_serialization_round_trip_planner_input(planner_input):
    """
    Property 5: JSON Serialization Round-Trip
    
    For any valid planner input, serializing to JSON and deserializing
    should produce an equivalent structure.
    """
    # Serialize to JSON
    json_str = serialize_to_json(planner_input)
    
    # Deserialize back
    deserialized = deserialize_from_json(json_str)
    
    # Should be equivalent
    assert deserialized == planner_input
    
    # Verify it's still valid
    is_valid = validate_agent_input(deserialized, PLANNER_INPUT_SCHEMA, "planner")
    assert is_valid is True


@settings(max_examples=100)
@given(
    agent_name=st.text(min_size=1, max_size=50),
    duration=st.integers(min_value=0, max_value=100000)
)
def test_property_json_serialization_round_trip_success_envelope(agent_name, duration):
    """
    Property 5: JSON Serialization Round-Trip
    
    For any success envelope created by the system, serializing to JSON
    and deserializing should produce an equivalent structure.
    """
    # Create success envelope
    envelope = create_success_envelope(agent_name, duration)
    
    # Serialize to JSON
    json_str = serialize_to_json(envelope)
    
    # Deserialize back
    deserialized = deserialize_from_json(json_str)
    
    # Should be equivalent
    assert deserialized["agent_name"] == agent_name
    assert deserialized["execution_duration_ms"] == duration
    assert deserialized["status"] == "success"


# Feature: kasparro-fb-analyst, Property 4: Agent Output Envelope Consistency
# Validates: Requirements 2.5

@settings(max_examples=100)
@given(
    agent_name=st.text(min_size=1, max_size=50),
    duration=st.integers(min_value=0, max_value=100000)
)
def test_property_success_envelope_contains_required_metadata(agent_name, duration):
    """
    Property 4: Agent Output Envelope Consistency
    
    For any agent execution completion, the output should include
    metadata fields for agent_name, timestamp, and execution_duration_ms.
    """
    envelope = create_success_envelope(agent_name, duration)
    
    # Verify all required metadata fields are present
    assert "agent_name" in envelope
    assert "timestamp" in envelope
    assert "execution_duration_ms" in envelope
    assert "status" in envelope
    
    # Verify values
    assert envelope["agent_name"] == agent_name
    assert envelope["execution_duration_ms"] == duration
    assert envelope["status"] == "success"
    
    # Verify timestamp is ISO 8601 format
    assert "T" in envelope["timestamp"]
    assert envelope["timestamp"].endswith("Z")


@settings(max_examples=100)
@given(
    agent_name=st.text(min_size=1, max_size=50),
    error_type=st.sampled_from(["ValidationError", "IOError", "TimeoutError", "UnexpectedError"]),
    error_message=st.text(min_size=1, max_size=200)
)
def test_property_error_envelope_contains_required_metadata(agent_name, error_type, error_message):
    """
    Property 4: Agent Output Envelope Consistency
    
    For any agent execution failure, the output should include
    metadata fields for agent_name, timestamp, and status.
    """
    envelope = create_error_envelope(agent_name, error_type, error_message)
    
    # Verify all required metadata fields are present
    assert "agent_name" in envelope
    assert "timestamp" in envelope
    assert "status" in envelope
    assert "error" in envelope
    
    # Verify values
    assert envelope["agent_name"] == agent_name
    assert envelope["status"] == "failure"
    assert envelope["error"]["error_type"] == error_type
    assert envelope["error"]["error_message"] == error_message
    
    # Verify timestamp is ISO 8601 format
    assert "T" in envelope["timestamp"]
    assert envelope["timestamp"].endswith("Z")


@settings(max_examples=100)
@given(
    agent_name=st.text(min_size=1, max_size=50),
    duration=st.integers(min_value=0, max_value=100000),
    payload=st.dictionaries(
        st.text(min_size=1, max_size=20),
        st.one_of(st.integers(), st.floats(allow_nan=False, allow_infinity=False), st.text(), st.booleans())
    )
)
def test_property_envelope_with_payload_preserves_metadata(agent_name, duration, payload):
    """
    Property 4: Agent Output Envelope Consistency
    
    For any agent output with additional payload data, the required
    metadata fields should still be present and correctly formatted.
    """
    envelope = create_success_envelope(agent_name, duration, payload)
    
    # Verify required metadata is present
    assert "agent_name" in envelope
    assert "timestamp" in envelope
    assert "execution_duration_ms" in envelope
    assert "status" in envelope
    
    # Verify payload data is also present
    for key, value in payload.items():
        assert key in envelope
        assert envelope[key] == value
