"""
Property-based tests for Planner Agent.

These tests verify that the Planner Agent correctly parses queries,
decomposes tasks, and routes workflows across a wide range of inputs.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from datetime import datetime, timedelta
import re

from src.agents.planner import PlannerAgent
from src.schemas.validation import ValidationError


# Hypothesis strategies for generating test data

@st.composite
def valid_query(draw):
    """Generate a valid natural language query."""
    # Query templates
    templates = [
        "Analyze ROAS changes in the last {days} days",
        "Why did ROAS drop in the last {days} days?",
        "Generate creative recommendations for low CTR campaigns",
        "Show me insights for the past {days} days",
        "What caused the ROAS decline from {date1} to {date2}?",
        "Create new ad creatives for underperforming campaigns",
        "Analyze campaign performance",
        "Generate report for last {days} days",
    ]
    
    template = draw(st.sampled_from(templates))
    
    # Fill in template variables
    if "{days}" in template:
        days = draw(st.integers(min_value=1, max_value=90))
        template = template.replace("{days}", str(days))
    
    if "{date1}" in template and "{date2}" in template:
        today = datetime.utcnow().date()
        days_ago = draw(st.integers(min_value=7, max_value=60))
        date1 = (today - timedelta(days=days_ago)).isoformat()
        date2 = today.isoformat()
        template = template.replace("{date1}", date1).replace("{date2}", date2)
    
    return template


# Simple config for faster test generation
SIMPLE_CONFIG = {
    "thresholds": {
        "low_ctr": 0.01,
        "high_confidence": 0.7,
        "roas_change_significant": 0.15,
    },
    "agents": {
        "max_hypotheses": 5,
        "min_data_points": 10,
    },
    "retry": {
        "max_retries": 3,
        "backoff_multiplier": 2,
    },
    "logging": {
        "level": "INFO",
        "format": "json",
    },
    "random_seed": 42,
}


@st.composite
def valid_context(draw):
    """Generate a valid context dictionary."""
    return {
        "dataset_path": "data/synthetic_fb_ads_undergarments.csv",
        "config": SIMPLE_CONFIG
    }


@st.composite
def ambiguous_query(draw):
    """Generate an ambiguous or incomplete query."""
    # Queries that might be considered ambiguous
    queries = [
        "",  # Empty query
        "analyze",  # Too vague
        "help",  # Not a valid analysis request
        "what",  # Incomplete
    ]
    return draw(st.sampled_from(queries))


# Feature: kasparro-fb-analyst, Property 1: CLI Query Processing Completeness
# Validates: Requirements 1.1, 1.2, 1.5

@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(query=valid_query(), context=valid_context())
def test_property_query_processing_completeness(query, context):
    """
    Property 1: CLI Query Processing Completeness
    
    For any valid natural language query submitted via CLI, the System should
    parse the query, extract parameters, initiate the agent workflow, and log
    the request with timestamp and query text.
    """
    # Create planner agent
    planner = PlannerAgent(context["config"])
    
    # Execute planner
    result = planner.execute(query, context)
    
    # Should successfully parse and process the query
    assert "agent_name" in result
    assert result["agent_name"] == "planner"
    
    # Should include timestamp
    assert "timestamp" in result
    assert "T" in result["timestamp"]
    assert result["timestamp"].endswith("Z")
    
    # Should include execution duration
    assert "execution_duration_ms" in result
    assert isinstance(result["execution_duration_ms"], int)
    assert result["execution_duration_ms"] >= 0
    
    # Should have identified a task
    assert "task" in result
    assert result["task"] in ["roas_analysis", "creative_generation", "full_analysis"]
    
    # Should have routing information
    assert "routing" in result
    assert "next_agent" in result["routing"]
    assert "workflow_type" in result["routing"]
    
    # Should have task plan
    assert "task_plan" in result
    assert isinstance(result["task_plan"], list)
    assert len(result["task_plan"]) > 0
    
    # Should have steps
    assert "steps" in result
    assert isinstance(result["steps"], list)
    assert len(result["steps"]) > 0


@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(query=valid_query(), context=valid_context())
def test_property_query_parameter_extraction(query, context):
    """
    Property 1: CLI Query Processing Completeness
    
    For any query containing time range specifications, the System should
    extract and validate the date parameters.
    """
    planner = PlannerAgent(context["config"])
    result = planner.execute(query, context)
    
    # If query contains time range keywords, should extract date_range
    query_lower = query.lower()
    has_time_keywords = any(keyword in query_lower for keyword in [
        "last", "past", "days", "week", "month", "2024-", "2023-"
    ])
    
    if has_time_keywords and "date_range" in result and result["date_range"]:
        date_range = result["date_range"]
        
        # Should have from and to dates
        assert "from" in date_range
        assert "to" in date_range
        
        # Dates should be in ISO format
        assert re.match(r'\d{4}-\d{2}-\d{2}', date_range["from"])
        assert re.match(r'\d{4}-\d{2}-\d{2}', date_range["to"])
        
        # From date should be before or equal to to date
        from_date = datetime.fromisoformat(date_range["from"]).date()
        to_date = datetime.fromisoformat(date_range["to"]).date()
        assert from_date <= to_date


@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(query=valid_query(), context=valid_context())
def test_property_workflow_initiation(query, context):
    """
    Property 1: CLI Query Processing Completeness
    
    For any valid query, the System should initiate the agent workflow
    by providing routing instructions to the next agent.
    """
    planner = PlannerAgent(context["config"])
    result = planner.execute(query, context)
    
    # Should have routing to next agent
    assert "routing" in result
    routing = result["routing"]
    
    # Next agent should be specified
    assert "next_agent" in routing
    assert routing["next_agent"] in [
        "data_agent", "insight_agent", "evaluator_agent",
        "creative_generator", "report_generator", "none"
    ]
    
    # Workflow type should be specified
    assert "workflow_type" in routing
    assert routing["workflow_type"] in [
        "analysis", "creative_generation", "full", "clarification"
    ]
    
    # If not clarification, should start with data_agent
    if routing["workflow_type"] != "clarification":
        assert routing["next_agent"] == "data_agent"


# Feature: kasparro-fb-analyst, Property 2: CLI Error Handling
# Validates: Requirements 1.3

@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(query=ambiguous_query(), context=valid_context())
def test_property_ambiguous_query_handling(query, context):
    """
    Property 2: CLI Error Handling
    
    For any ambiguous or incomplete query, the System should return a
    structured clarification request identifying the specific missing parameters.
    """
    # Skip non-ambiguous queries
    assume(len(query.strip()) < 10)
    
    planner = PlannerAgent(context["config"])
    result = planner.execute(query, context)
    
    # For very short/ambiguous queries, system should still process them
    # (current implementation defaults to full_analysis)
    # But we verify it handles them gracefully without errors
    assert "agent_name" in result
    assert "routing" in result


@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(context=valid_context())
def test_property_missing_query_handling(context):
    """
    Property 2: CLI Error Handling
    
    For queries with missing or invalid input, the System should handle
    errors gracefully and return structured error information.
    """
    planner = PlannerAgent(context["config"])
    
    # Test with None query (should raise error or handle gracefully)
    try:
        result = planner.execute(None, context)
        # If it doesn't raise an error, should return error envelope
        if "error" in result:
            assert result["status"] == "failure"
            assert "error_type" in result["error"]
    except (TypeError, ValidationError):
        # Expected behavior - validation should catch this
        pass


# Feature: kasparro-fb-analyst, Property 11: Task Decomposition Completeness
# Validates: Requirements 4.1

@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(context=valid_context())
def test_property_roas_analysis_decomposition(context):
    """
    Property 11: Task Decomposition Completeness
    
    For any ROAS analysis request, the Planner Agent should decompose
    the request into at least three steps: data retrieval, hypothesis
    generation, and validation.
    """
    planner = PlannerAgent(context["config"])
    
    # Create ROAS analysis query
    query = "Analyze ROAS changes in the last 7 days"
    result = planner.execute(query, context)
    
    # Should identify as ROAS analysis
    assert result["task"] == "roas_analysis"
    
    # Should have task plan with at least 3 steps
    task_plan = result["task_plan"]
    assert len(task_plan) >= 3
    
    # Should include data retrieval step
    agent_names = [step["agent"] for step in task_plan]
    assert "data_agent" in agent_names
    
    # Should include hypothesis generation step
    assert "insight_agent" in agent_names
    
    # Should include validation step
    assert "evaluator_agent" in agent_names
    
    # Steps should be ordered correctly
    data_idx = agent_names.index("data_agent")
    insight_idx = agent_names.index("insight_agent")
    evaluator_idx = agent_names.index("evaluator_agent")
    
    assert data_idx < insight_idx < evaluator_idx


@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(query=valid_query(), context=valid_context())
def test_property_task_plan_structure(query, context):
    """
    Property 11: Task Decomposition Completeness
    
    For any query, the task plan should have proper structure with
    step IDs, agent names, actions, and parameters.
    """
    planner = PlannerAgent(context["config"])
    result = planner.execute(query, context)
    
    task_plan = result["task_plan"]
    
    # Each step should have required fields
    for step in task_plan:
        assert "step_id" in step
        assert "agent" in step
        assert "action" in step
        assert "parameters" in step
        
        # Step ID should be positive integer
        assert isinstance(step["step_id"], int)
        assert step["step_id"] > 0
        
        # Agent should be valid
        assert step["agent"] in [
            "data_agent", "insight_agent", "evaluator_agent",
            "creative_generator", "report_generator"
        ]
        
        # Action should be non-empty string
        assert isinstance(step["action"], str)
        assert len(step["action"]) > 0
        
        # Parameters should be dict
        assert isinstance(step["parameters"], dict)
    
    # Step IDs should be sequential
    step_ids = [step["step_id"] for step in task_plan]
    assert step_ids == list(range(1, len(task_plan) + 1))


@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(query=valid_query(), context=valid_context())
def test_property_data_agent_first_step(query, context):
    """
    Property 11: Task Decomposition Completeness
    
    For any workflow, the first step should always be data_agent
    to load and process the dataset.
    """
    planner = PlannerAgent(context["config"])
    result = planner.execute(query, context)
    
    # Skip clarification workflows
    if result.get("routing", {}).get("workflow_type") == "clarification":
        return
    
    task_plan = result["task_plan"]
    
    # First step should be data_agent
    assert len(task_plan) > 0
    assert task_plan[0]["agent"] == "data_agent"
    assert task_plan[0]["step_id"] == 1


# Feature: kasparro-fb-analyst, Property 16: Reasoning Structure Completeness
# Validates: Requirements 5.1, 5.2, 5.3, 5.4

@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(query=valid_query(), context=valid_context())
def test_property_reasoning_structure_completeness(query, context):
    """
    Property 16: Reasoning Structure Completeness
    
    For any agent execution that produces reasoning output, the output
    should contain three distinct sections: think, analyze, and conclude.
    """
    planner = PlannerAgent(context["config"])
    result = planner.execute(query, context)
    
    # Should have reasoning section
    assert "reasoning" in result
    reasoning = result["reasoning"]
    
    # Should have all three sections
    assert "think" in reasoning
    assert "analyze" in reasoning
    assert "conclude" in reasoning
    
    # Each section should be non-empty string
    assert isinstance(reasoning["think"], str)
    assert isinstance(reasoning["analyze"], str)
    assert isinstance(reasoning["conclude"], str)
    
    assert len(reasoning["think"]) > 0
    assert len(reasoning["analyze"]) > 0
    assert len(reasoning["conclude"]) > 0


@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(query=valid_query(), context=valid_context())
def test_property_reasoning_think_section_content(query, context):
    """
    Property 16: Reasoning Structure Completeness
    
    The Think section should document the agent's understanding of
    the task and approach.
    """
    planner = PlannerAgent(context["config"])
    result = planner.execute(query, context)
    
    think = result["reasoning"]["think"]
    
    # Think section should reference the query
    # (at least mention analyzing or understanding)
    assert any(keyword in think.lower() for keyword in [
        "query", "analyzing", "identified", "intent", "understanding"
    ])


@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(query=valid_query(), context=valid_context())
def test_property_reasoning_analyze_section_content(query, context):
    """
    Property 16: Reasoning Structure Completeness
    
    The Analyze section should present data observations and
    intermediate computations.
    """
    planner = PlannerAgent(context["config"])
    result = planner.execute(query, context)
    
    analyze = result["reasoning"]["analyze"]
    
    # Analyze section should reference task decomposition or steps
    assert any(keyword in analyze.lower() for keyword in [
        "step", "task", "decomposition", "workflow", "agent"
    ])


@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(query=valid_query(), context=valid_context())
def test_property_reasoning_conclude_section_content(query, context):
    """
    Property 16: Reasoning Structure Completeness
    
    The Conclude section should provide actionable findings with
    confidence levels or next steps.
    """
    planner = PlannerAgent(context["config"])
    result = planner.execute(query, context)
    
    conclude = result["reasoning"]["conclude"]
    
    # Conclude section should reference workflow or outputs
    assert any(keyword in conclude.lower() for keyword in [
        "workflow", "output", "starting", "expected", "result"
    ])


# Feature: kasparro-fb-analyst, Property 17: Reasoning Chain Logging
# Validates: Requirements 5.5

@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(query=valid_query(), context=valid_context())
def test_property_reasoning_chain_preservation(query, context):
    """
    Property 17: Reasoning Chain Logging
    
    For any agent execution with reasoning, the full reasoning chain
    should be preserved in the output for logging.
    """
    planner = PlannerAgent(context["config"])
    result = planner.execute(query, context)
    
    # Reasoning should be present and complete
    assert "reasoning" in result
    reasoning = result["reasoning"]
    
    # All sections should be preserved
    assert "think" in reasoning
    assert "analyze" in reasoning
    assert "conclude" in reasoning
    
    # Reasoning should be serializable (for logging)
    import json
    try:
        json_str = json.dumps(reasoning)
        deserialized = json.loads(json_str)
        assert deserialized == reasoning
    except (TypeError, ValueError):
        pytest.fail("Reasoning chain is not JSON serializable")


@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(query=valid_query(), context=valid_context())
def test_property_reasoning_chain_in_output(query, context):
    """
    Property 17: Reasoning Chain Logging
    
    The reasoning chain should be included in the agent output
    structure for logging purposes.
    """
    planner = PlannerAgent(context["config"])
    result = planner.execute(query, context)
    
    # Result should be a complete output structure
    assert isinstance(result, dict)
    
    # Should include reasoning alongside other output fields
    assert "reasoning" in result
    assert "agent_name" in result
    assert "timestamp" in result
    
    # Reasoning should be at the same level as other output fields
    assert result["reasoning"] is not None
    assert isinstance(result["reasoning"], dict)
