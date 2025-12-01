"""
Property-based tests for Insight Agent.

These tests verify that the Insight Agent correctly generates hypotheses,
assigns confidence scores, and incorporates trend data.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from datetime import datetime
import json

from src.agents.insight_agent import InsightAgent
from src.schemas.validation import ValidationError


# Hypothesis strategies for generating test data

SIMPLE_CONFIG = {
    "thresholds": {
        "low_ctr": 0.01,
        "high_confidence": 0.7,
        "roas_change_significant": 0.15,
        "trend_stable_threshold": 0.05,
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
        "log_dir": "logs",
    },
    "random_seed": 42,
}


@st.composite
def valid_data_summary(draw):
    """Generate a valid data summary from Data Agent."""
    # Generate metrics
    overall_roas = draw(st.floats(min_value=0.5, max_value=5.0))
    overall_ctr = draw(st.floats(min_value=0.001, max_value=0.05))
    
    # Generate trends
    roas_wow_change = draw(st.floats(min_value=-50, max_value=50))
    roas_mom_change = draw(st.floats(min_value=-50, max_value=50))
    ctr_wow_change = draw(st.floats(min_value=-50, max_value=50))
    ctr_mom_change = draw(st.floats(min_value=-50, max_value=50))
    
    # Determine trend directions
    roas_avg_change = (abs(roas_wow_change) + abs(roas_mom_change)) / 2
    if roas_avg_change > 5:
        roas_direction = "increasing" if roas_wow_change > 0 or roas_mom_change > 0 else "decreasing"
    else:
        roas_direction = "stable"
    
    ctr_avg_change = (abs(ctr_wow_change) + abs(ctr_mom_change)) / 2
    if ctr_avg_change > 5:
        ctr_direction = "increasing" if ctr_wow_change > 0 or ctr_mom_change > 0 else "decreasing"
    else:
        ctr_direction = "stable"
    
    # Generate segmentation data
    num_campaigns = draw(st.integers(min_value=1, max_value=10))
    campaigns = []
    for i in range(num_campaigns):
        campaign_roas = draw(st.floats(min_value=0.1, max_value=6.0))
        campaign_ctr = draw(st.floats(min_value=0.0001, max_value=0.08))
        campaigns.append({
            "campaign_name": f"Campaign_{i}",
            "spend": draw(st.floats(min_value=100, max_value=10000)),
            "revenue": draw(st.floats(min_value=50, max_value=20000)),
            "roas": campaign_roas,
            "impressions": draw(st.integers(min_value=1000, max_value=100000)),
            "clicks": draw(st.integers(min_value=10, max_value=5000)),
            "ctr": campaign_ctr,
        })
    
    # Generate creative type segmentation
    creative_types = ["image", "video", "carousel"]
    creative_segments = []
    for creative_type in creative_types:
        creative_segments.append({
            "creative_type": creative_type,
            "spend": draw(st.floats(min_value=100, max_value=5000)),
            "revenue": draw(st.floats(min_value=50, max_value=10000)),
            "roas": draw(st.floats(min_value=0.5, max_value=5.0)),
            "impressions": draw(st.integers(min_value=1000, max_value=50000)),
            "clicks": draw(st.integers(min_value=10, max_value=2000)),
            "ctr": draw(st.floats(min_value=0.001, max_value=0.05)),
        })
    
    # Generate audience segmentation
    num_audiences = draw(st.integers(min_value=1, max_value=5))
    audiences = []
    for i in range(num_audiences):
        audiences.append({
            "audience_type": f"audience_{i}",
            "spend": draw(st.floats(min_value=100, max_value=5000)),
            "revenue": draw(st.floats(min_value=50, max_value=10000)),
            "roas": draw(st.floats(min_value=0.5, max_value=5.0)),
            "impressions": draw(st.integers(min_value=1000, max_value=50000)),
            "clicks": draw(st.integers(min_value=10, max_value=2000)),
            "ctr": draw(st.floats(min_value=0.001, max_value=0.05)),
        })
    
    # Generate platform segmentation
    platforms = ["Facebook", "Instagram"]
    platform_segments = []
    for platform in platforms:
        platform_segments.append({
            "platform": platform,
            "spend": draw(st.floats(min_value=100, max_value=5000)),
            "revenue": draw(st.floats(min_value=50, max_value=10000)),
            "roas": draw(st.floats(min_value=0.5, max_value=5.0)),
            "impressions": draw(st.integers(min_value=1000, max_value=50000)),
            "clicks": draw(st.integers(min_value=10, max_value=2000)),
            "ctr": draw(st.floats(min_value=0.001, max_value=0.05)),
        })
    
    return {
        "dataset_summary": {
            "total_rows": draw(st.integers(min_value=100, max_value=10000)),
            "date_range": {
                "start": "2024-01-01",
                "end": "2024-01-31"
            },
            "total_spend": draw(st.floats(min_value=1000, max_value=100000)),
            "total_revenue": draw(st.floats(min_value=500, max_value=200000)),
            "campaigns_count": num_campaigns,
            "data_quality": {
                "missing_values": {},
                "invalid_rows": 0
            }
        },
        "metrics": {
            "overall_roas": overall_roas,
            "overall_ctr": overall_ctr,
            "avg_cpc": draw(st.floats(min_value=0.1, max_value=5.0)),
            "conversion_rate": draw(st.floats(min_value=0.001, max_value=0.1)),
        },
        "trends": {
            "roas_trend": {
                "direction": roas_direction,
                "week_over_week_change": roas_wow_change,
                "month_over_month_change": roas_mom_change,
            },
            "ctr_trend": {
                "direction": ctr_direction,
                "week_over_week_change": ctr_wow_change,
                "month_over_month_change": ctr_mom_change,
            }
        },
        "segmentation": {
            "by_campaign": campaigns,
            "by_creative_type": creative_segments,
            "by_audience_type": audiences,
            "by_platform": platform_segments,
        },
        "data_quality_issues": []
    }


@st.composite
def valid_insight_input(draw):
    """Generate valid input for Insight Agent."""
    data_summary = draw(valid_data_summary())
    focus_metric = draw(st.sampled_from(["roas", "ctr", "cvr"]))
    
    return {
        "data_summary": data_summary,
        "focus_metric": focus_metric,
        "time_period": {
            "start": "2024-01-01",
            "end": "2024-01-31"
        },
        "config": SIMPLE_CONFIG
    }


# Feature: kasparro-fb-analyst, Property 12: Hypothesis Generation Minimum Count
# Validates: Requirements 4.2

@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(input_data=valid_insight_input())
def test_property_hypothesis_generation_minimum_count(input_data):
    """
    Property 12: Hypothesis Generation Minimum Count
    
    For any Insight Agent execution with sufficient data, the output
    should contain at least three distinct hypotheses.
    """
    # Create insight agent
    agent = InsightAgent(input_data["config"])
    
    # Execute agent
    result = agent.execute(input_data)
    
    # Should have hypotheses field
    assert "hypotheses" in result
    hypotheses = result["hypotheses"]
    
    # Should have at least 3 hypotheses
    assert isinstance(hypotheses, list)
    assert len(hypotheses) >= 3, f"Expected at least 3 hypotheses, got {len(hypotheses)}"
    
    # Each hypothesis should have required fields
    for hypothesis in hypotheses:
        assert "hypothesis_id" in hypothesis
        assert "hypothesis_text" in hypothesis
        assert "category" in hypothesis
        assert "confidence_score" in hypothesis
        
        # Hypothesis ID should be unique
        assert isinstance(hypothesis["hypothesis_id"], str)
        assert len(hypothesis["hypothesis_id"]) > 0
        
        # Hypothesis text should be non-empty
        assert isinstance(hypothesis["hypothesis_text"], str)
        assert len(hypothesis["hypothesis_text"]) > 0
        
        # Category should be valid
        assert hypothesis["category"] in ["creative", "audience", "platform", "budget", "seasonality"]
    
    # Hypothesis IDs should be unique
    hypothesis_ids = [h["hypothesis_id"] for h in hypotheses]
    assert len(hypothesis_ids) == len(set(hypothesis_ids)), "Hypothesis IDs should be unique"


@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(input_data=valid_insight_input())
def test_property_hypothesis_distinctness(input_data):
    """
    Property 12: Hypothesis Generation Minimum Count
    
    The hypotheses should be distinct (not duplicates).
    """
    agent = InsightAgent(input_data["config"])
    result = agent.execute(input_data)
    
    hypotheses = result["hypotheses"]
    
    # Hypothesis texts should be distinct
    hypothesis_texts = [h["hypothesis_text"] for h in hypotheses]
    assert len(hypothesis_texts) == len(set(hypothesis_texts)), "Hypotheses should be distinct"


@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(input_data=valid_insight_input())
def test_property_hypothesis_max_count(input_data):
    """
    Property 12: Hypothesis Generation Minimum Count
    
    The number of hypotheses should not exceed max_hypotheses configuration.
    """
    agent = InsightAgent(input_data["config"])
    result = agent.execute(input_data)
    
    hypotheses = result["hypotheses"]
    max_hypotheses = input_data["config"]["agents"]["max_hypotheses"]
    
    # Should not exceed max_hypotheses
    assert len(hypotheses) <= max_hypotheses, f"Expected at most {max_hypotheses} hypotheses, got {len(hypotheses)}"


# Feature: kasparro-fb-analyst, Property 13: Confidence Score Bounds
# Validates: Requirements 4.3, 6.5, 14.1, 14.3

@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(input_data=valid_insight_input())
def test_property_confidence_score_bounds(input_data):
    """
    Property 13: Confidence Score Bounds
    
    For any hypothesis, insight, or creative recommendation, the
    confidence_score field should be between 0.0 and 1.0 inclusive.
    """
    agent = InsightAgent(input_data["config"])
    result = agent.execute(input_data)
    
    hypotheses = result["hypotheses"]
    
    # Check each hypothesis confidence score
    for hypothesis in hypotheses:
        assert "confidence_score" in hypothesis
        confidence = hypothesis["confidence_score"]
        
        # Should be a number
        assert isinstance(confidence, (int, float)), f"Confidence score should be numeric, got {type(confidence)}"
        
        # Should be between 0 and 1
        assert 0.0 <= confidence <= 1.0, f"Confidence score {confidence} is out of bounds [0.0, 1.0]"


@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(input_data=valid_insight_input())
def test_property_all_confidence_scores_valid(input_data):
    """
    Property 13: Confidence Score Bounds
    
    All confidence scores in the output should be valid (between 0 and 1).
    """
    agent = InsightAgent(input_data["config"])
    result = agent.execute(input_data)
    
    # Extract all confidence scores from hypotheses
    confidence_scores = [h["confidence_score"] for h in result["hypotheses"]]
    
    # All should be valid
    assert all(0.0 <= score <= 1.0 for score in confidence_scores), \
        f"Some confidence scores are out of bounds: {confidence_scores}"
    
    # All should be numeric
    assert all(isinstance(score, (int, float)) for score in confidence_scores), \
        "All confidence scores should be numeric"


@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(input_data=valid_insight_input())
def test_property_confidence_score_not_nan(input_data):
    """
    Property 13: Confidence Score Bounds
    
    Confidence scores should not be NaN or infinite.
    """
    import math
    
    agent = InsightAgent(input_data["config"])
    result = agent.execute(input_data)
    
    confidence_scores = [h["confidence_score"] for h in result["hypotheses"]]
    
    # None should be NaN or infinite
    for score in confidence_scores:
        assert not math.isnan(score), f"Confidence score is NaN"
        assert not math.isinf(score), f"Confidence score is infinite"


# Feature: kasparro-fb-analyst, Property 55: Trend Incorporation in Hypotheses
# Validates: Requirements 17.5

@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(input_data=valid_insight_input())
def test_property_trend_incorporation_in_hypotheses(input_data):
    """
    Property 55: Trend Incorporation in Hypotheses
    
    For any Insight Agent execution with trend data available, at least
    one hypothesis should reference trend information.
    """
    agent = InsightAgent(input_data["config"])
    result = agent.execute(input_data)
    
    hypotheses = result["hypotheses"]
    trends = input_data["data_summary"].get("trends", {})
    
    # If trends are available and show significant changes, at least one hypothesis should reference them
    if trends and (trends.get("roas_trend") or trends.get("ctr_trend")):
        # Check if trends show significant changes (>5% in either direction)
        roas_trend = trends.get("roas_trend", {})
        ctr_trend = trends.get("ctr_trend", {})
        
        roas_wow = abs(roas_trend.get("week_over_week_change", 0))
        roas_mom = abs(roas_trend.get("month_over_month_change", 0))
        ctr_wow = abs(ctr_trend.get("week_over_week_change", 0))
        ctr_mom = abs(ctr_trend.get("month_over_month_change", 0))
        
        has_significant_trend = (roas_wow > 5 or roas_mom > 5 or ctr_wow > 5 or ctr_mom > 5)
        
        # Only check for trend references if there are significant trends
        if has_significant_trend:
            # Check if any hypothesis references trend data
            trend_referenced = False
            
            for hypothesis in hypotheses:
                # Check evidence_used field
                evidence = hypothesis.get("evidence_used", [])
                if any("trend" in str(e).lower() for e in evidence):
                    trend_referenced = True
                    break
                
                # Check hypothesis text
                hypothesis_text = hypothesis.get("hypothesis_text", "").lower()
                if any(keyword in hypothesis_text for keyword in ["trend", "wow", "mom", "week-over-week", "month-over-month"]):
                    trend_referenced = True
                    break
                
                # Check supporting observations
                observations = hypothesis.get("supporting_observations", [])
                if any(any(keyword in str(obs).lower() for keyword in ["trend", "wow", "mom", "week-over-week", "month-over-month"]) for obs in observations):
                    trend_referenced = True
                    break
            
            assert trend_referenced, "At least one hypothesis should reference trend data when significant trends are available"


@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(input_data=valid_insight_input())
def test_property_trend_data_in_evidence(input_data):
    """
    Property 55: Trend Incorporation in Hypotheses
    
    When trends are available, hypotheses that reference trends should
    include trend-related evidence.
    """
    agent = InsightAgent(input_data["config"])
    result = agent.execute(input_data)
    
    hypotheses = result["hypotheses"]
    trends = input_data["data_summary"].get("trends", {})
    
    # If trends are available
    if trends and (trends.get("roas_trend") or trends.get("ctr_trend")):
        # Find hypotheses that mention trends
        for hypothesis in hypotheses:
            hypothesis_text = hypothesis.get("hypothesis_text", "").lower()
            
            # If hypothesis mentions trends
            if any(keyword in hypothesis_text for keyword in ["trend", "wow", "mom", "week-over-week", "month-over-month"]):
                # Should have trend-related evidence
                evidence = hypothesis.get("evidence_used", [])
                assert any("trend" in str(e).lower() or "change" in str(e).lower() for e in evidence), \
                    f"Hypothesis mentioning trends should include trend-related evidence: {hypothesis_text}"


@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(input_data=valid_insight_input())
def test_property_hypothesis_structure_completeness(input_data):
    """
    Verify that all hypotheses have complete structure with all required fields.
    """
    agent = InsightAgent(input_data["config"])
    result = agent.execute(input_data)
    
    hypotheses = result["hypotheses"]
    
    # Each hypothesis should have all required fields
    required_fields = [
        "hypothesis_id",
        "hypothesis_text",
        "category",
        "confidence_score"
    ]
    
    for hypothesis in hypotheses:
        for field in required_fields:
            assert field in hypothesis, f"Hypothesis missing required field: {field}"
        
        # Optional but expected fields
        assert "supporting_observations" in hypothesis or "evidence_used" in hypothesis, \
            "Hypothesis should have supporting_observations or evidence_used"
        
        # Testable field should be present
        if "testable" in hypothesis:
            assert isinstance(hypothesis["testable"], bool)
        
        # Validation approach should be present
        if "validation_approach" in hypothesis:
            assert isinstance(hypothesis["validation_approach"], str)
            assert len(hypothesis["validation_approach"]) > 0


@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(input_data=valid_insight_input())
def test_property_reasoning_structure_completeness(input_data):
    """
    Verify that the reasoning structure is complete with think, analyze, conclude.
    """
    agent = InsightAgent(input_data["config"])
    result = agent.execute(input_data)
    
    # Should have reasoning
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
@given(input_data=valid_insight_input())
def test_property_output_serialization(input_data):
    """
    Verify that the output can be serialized to JSON and back.
    """
    agent = InsightAgent(input_data["config"])
    result = agent.execute(input_data)
    
    # Should be JSON serializable
    try:
        json_str = json.dumps(result)
        deserialized = json.loads(json_str)
        
        # Key fields should be preserved
        assert deserialized["agent_name"] == result["agent_name"]
        assert len(deserialized["hypotheses"]) == len(result["hypotheses"])
        assert deserialized["reasoning"] == result["reasoning"]
    except (TypeError, ValueError) as e:
        pytest.fail(f"Output is not JSON serializable: {e}")
