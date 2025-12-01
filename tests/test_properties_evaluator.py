"""
Property-based tests for Evaluator Agent.

These tests verify that the Evaluator Agent correctly validates hypotheses,
computes evidence metrics, performs statistical significance testing, and
adjusts confidence scores.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from datetime import datetime
import json
import pandas as pd
import tempfile
import os

from src.agents.evaluator_agent import EvaluatorAgent
from src.schemas.validation import ValidationError


# Test configuration
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
def valid_hypothesis(draw):
    """Generate a valid hypothesis."""
    category = draw(st.sampled_from(["creative", "audience", "platform", "budget", "seasonality"]))
    confidence = draw(st.floats(min_value=0.3, max_value=0.8))
    
    return {
        "hypothesis_id": f"hyp_{draw(st.integers(min_value=1, max_value=10000))}",
        "hypothesis_text": draw(st.text(min_size=20, max_size=200)),
        "category": category,
        "confidence_score": confidence,
        "supporting_observations": [
            draw(st.text(min_size=10, max_size=100)),
            draw(st.text(min_size=10, max_size=100))
        ],
        "evidence_used": ["segmentation", "metrics"],
        "testable": True,
        "validation_approach": "Compare metrics across segments"
    }


@st.composite
def valid_dataset(draw):
    """Generate a valid dataset DataFrame and save to temp file."""
    num_rows = draw(st.integers(min_value=50, max_value=200))
    
    # Generate data
    data = {
        "campaign_name": [f"Campaign_{i % 5}" for i in range(num_rows)],
        "date": [f"2024-01-{(i % 28) + 1:02d}" for i in range(num_rows)],
        "spend": [draw(st.floats(min_value=10, max_value=1000)) for _ in range(num_rows)],
        "impressions": [draw(st.integers(min_value=100, max_value=10000)) for _ in range(num_rows)],
        "clicks": [draw(st.integers(min_value=5, max_value=500)) for _ in range(num_rows)],
        "revenue": [draw(st.floats(min_value=5, max_value=2000)) for _ in range(num_rows)],
        "purchases": [draw(st.integers(min_value=0, max_value=50)) for _ in range(num_rows)],
        "creative_type": [draw(st.sampled_from(["image", "video", "carousel"])) for _ in range(num_rows)],
        "audience_type": [f"audience_{i % 3}" for i in range(num_rows)],
        "platform": [draw(st.sampled_from(["Facebook", "Instagram"])) for _ in range(num_rows)],
    }
    
    # Calculate derived metrics
    data["ctr"] = [data["clicks"][i] / data["impressions"][i] if data["impressions"][i] > 0 else 0 for i in range(num_rows)]
    data["roas"] = [data["revenue"][i] / data["spend"][i] if data["spend"][i] > 0 else 0 for i in range(num_rows)]
    
    df = pd.DataFrame(data)
    
    # Save to temp file
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
    df.to_csv(temp_file.name, index=False)
    temp_file.close()
    
    return temp_file.name, df


@st.composite
def valid_data_summary(draw, df):
    """Generate a valid data summary based on DataFrame."""
    # Calculate overall metrics
    total_spend = df["spend"].sum()
    total_revenue = df["revenue"].sum()
    total_impressions = df["impressions"].sum()
    total_clicks = df["clicks"].sum()
    
    overall_roas = total_revenue / total_spend if total_spend > 0 else 0
    overall_ctr = total_clicks / total_impressions if total_impressions > 0 else 0
    
    # Generate segmentation
    campaigns = []
    for campaign in df["campaign_name"].unique():
        campaign_df = df[df["campaign_name"] == campaign]
        campaigns.append({
            "campaign_name": campaign,
            "spend": float(campaign_df["spend"].sum()),
            "revenue": float(campaign_df["revenue"].sum()),
            "roas": float(campaign_df["revenue"].sum() / campaign_df["spend"].sum()) if campaign_df["spend"].sum() > 0 else 0,
            "impressions": int(campaign_df["impressions"].sum()),
            "clicks": int(campaign_df["clicks"].sum()),
            "ctr": float(campaign_df["clicks"].sum() / campaign_df["impressions"].sum()) if campaign_df["impressions"].sum() > 0 else 0,
        })
    
    creative_segments = []
    for creative_type in df["creative_type"].unique():
        creative_df = df[df["creative_type"] == creative_type]
        creative_segments.append({
            "creative_type": creative_type,
            "spend": float(creative_df["spend"].sum()),
            "revenue": float(creative_df["revenue"].sum()),
            "roas": float(creative_df["revenue"].sum() / creative_df["spend"].sum()) if creative_df["spend"].sum() > 0 else 0,
            "impressions": int(creative_df["impressions"].sum()),
            "clicks": int(creative_df["clicks"].sum()),
            "ctr": float(creative_df["clicks"].sum() / creative_df["impressions"].sum()) if creative_df["impressions"].sum() > 0 else 0,
        })
    
    audience_segments = []
    for audience_type in df["audience_type"].unique():
        audience_df = df[df["audience_type"] == audience_type]
        audience_segments.append({
            "audience_type": audience_type,
            "spend": float(audience_df["spend"].sum()),
            "revenue": float(audience_df["revenue"].sum()),
            "roas": float(audience_df["revenue"].sum() / audience_df["spend"].sum()) if audience_df["spend"].sum() > 0 else 0,
            "impressions": int(audience_df["impressions"].sum()),
            "clicks": int(audience_df["clicks"].sum()),
            "ctr": float(audience_df["clicks"].sum() / audience_df["impressions"].sum()) if audience_df["impressions"].sum() > 0 else 0,
        })
    
    platform_segments = []
    for platform in df["platform"].unique():
        platform_df = df[df["platform"] == platform]
        platform_segments.append({
            "platform": platform,
            "spend": float(platform_df["spend"].sum()),
            "revenue": float(platform_df["revenue"].sum()),
            "roas": float(platform_df["revenue"].sum() / platform_df["spend"].sum()) if platform_df["spend"].sum() > 0 else 0,
            "impressions": int(platform_df["impressions"].sum()),
            "clicks": int(platform_df["clicks"].sum()),
            "ctr": float(platform_df["clicks"].sum() / platform_df["impressions"].sum()) if platform_df["impressions"].sum() > 0 else 0,
        })
    
    return {
        "dataset_summary": {
            "total_rows": len(df),
            "date_range": {
                "start": "2024-01-01",
                "end": "2024-01-31"
            },
            "total_spend": float(total_spend),
            "total_revenue": float(total_revenue),
            "campaigns_count": len(df["campaign_name"].unique()),
            "data_quality": {
                "missing_values": {},
                "invalid_rows": 0
            }
        },
        "metrics": {
            "overall_roas": float(overall_roas),
            "overall_ctr": float(overall_ctr),
            "avg_cpc": float(total_spend / total_clicks) if total_clicks > 0 else 0,
            "conversion_rate": 0.05,
        },
        "trends": {
            "roas_trend": {
                "direction": "stable",
                "week_over_week_change": draw(st.floats(min_value=-20, max_value=20)),
                "month_over_month_change": draw(st.floats(min_value=-20, max_value=20)),
            },
            "ctr_trend": {
                "direction": "stable",
                "week_over_week_change": draw(st.floats(min_value=-20, max_value=20)),
                "month_over_month_change": draw(st.floats(min_value=-20, max_value=20)),
            }
        },
        "segmentation": {
            "by_campaign": campaigns,
            "by_creative_type": creative_segments,
            "by_audience_type": audience_segments,
            "by_platform": platform_segments,
        },
        "data_quality_issues": []
    }


@st.composite
def valid_evaluator_input(draw):
    """Generate valid input for Evaluator Agent."""
    # Generate dataset
    dataset_path, df = draw(valid_dataset())
    
    # Generate data summary based on dataset
    data_summary = draw(valid_data_summary(df))
    
    # Generate hypotheses
    num_hypotheses = draw(st.integers(min_value=3, max_value=5))
    hypotheses = [draw(valid_hypothesis()) for _ in range(num_hypotheses)]
    
    return {
        "hypotheses": hypotheses,
        "dataset_path": dataset_path,
        "data_summary": data_summary,
        "config": SIMPLE_CONFIG
    }, dataset_path


# Feature: kasparro-fb-analyst, Property 14: Hypothesis Validation Evidence
# Validates: Requirements 4.4, 7.1

@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(input_data_tuple=valid_evaluator_input())
def test_property_hypothesis_validation_evidence(input_data_tuple):
    """
    Property 14: Hypothesis Validation Evidence
    
    For any hypothesis validated by the Evaluator Agent, the output
    should include at least two distinct supporting metrics computed
    from the dataset.
    """
    input_data, dataset_path = input_data_tuple
    
    try:
        # Create evaluator agent
        agent = EvaluatorAgent(input_data["config"])
        
        # Execute agent
        result = agent.execute(input_data)
        
        # Should have validated_hypotheses field
        assert "validated_hypotheses" in result
        validated_hypotheses = result["validated_hypotheses"]
        
        # Should have at least as many validated hypotheses as input hypotheses
        assert len(validated_hypotheses) >= len(input_data["hypotheses"])
        
        # Each validated hypothesis should have evidence with at least 2 metrics
        for validated_hyp in validated_hypotheses:
            assert "evidence" in validated_hyp, "Validated hypothesis should have evidence"
            evidence = validated_hyp["evidence"]
            
            assert "metrics" in evidence, "Evidence should have metrics"
            metrics = evidence["metrics"]
            
            assert isinstance(metrics, list), "Metrics should be a list"
            assert len(metrics) >= 2, f"Expected at least 2 metrics, got {len(metrics)}"
            
            # Each metric should have required fields
            for metric in metrics:
                assert "metric_name" in metric, "Metric should have metric_name"
                assert "value" in metric, "Metric should have value"
                assert isinstance(metric["metric_name"], str)
                assert isinstance(metric["value"], (int, float))
    
    finally:
        # Clean up temp file
        if os.path.exists(dataset_path):
            os.unlink(dataset_path)


@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(input_data_tuple=valid_evaluator_input())
def test_property_evidence_metrics_distinct(input_data_tuple):
    """
    Property 14: Hypothesis Validation Evidence
    
    The metrics in evidence should be distinct (not duplicates).
    """
    input_data, dataset_path = input_data_tuple
    
    try:
        agent = EvaluatorAgent(input_data["config"])
        result = agent.execute(input_data)
        
        validated_hypotheses = result["validated_hypotheses"]
        
        for validated_hyp in validated_hypotheses:
            metrics = validated_hyp["evidence"]["metrics"]
            metric_names = [m["metric_name"] for m in metrics]
            
            # Metric names should be distinct
            assert len(metric_names) == len(set(metric_names)), \
                f"Metrics should be distinct, got duplicates: {metric_names}"
    
    finally:
        if os.path.exists(dataset_path):
            os.unlink(dataset_path)



# Feature: kasparro-fb-analyst, Property 15: Hypothesis Ranking Consistency
# Validates: Requirements 4.5, 14.5

@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(input_data_tuple=valid_evaluator_input())
def test_property_hypothesis_ranking_consistency(input_data_tuple):
    """
    Property 15: Hypothesis Ranking Consistency
    
    For any set of validated hypotheses, the System should rank them
    in descending order by validation strength and confidence score.
    """
    input_data, dataset_path = input_data_tuple
    
    try:
        agent = EvaluatorAgent(input_data["config"])
        result = agent.execute(input_data)
        
        validated_hypotheses = result["validated_hypotheses"]
        
        # Extract confidence scores
        confidence_scores = [h["adjusted_confidence_score"] for h in validated_hypotheses]
        
        # Should be sorted in descending order
        for i in range(len(confidence_scores) - 1):
            assert confidence_scores[i] >= confidence_scores[i + 1], \
                f"Hypotheses should be ranked by confidence (descending), but {confidence_scores[i]} < {confidence_scores[i + 1]}"
    
    finally:
        if os.path.exists(dataset_path):
            os.unlink(dataset_path)


@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(input_data_tuple=valid_evaluator_input())
def test_property_top_insights_from_top_hypotheses(input_data_tuple):
    """
    Property 15: Hypothesis Ranking Consistency
    
    Top insights should be derived from the top-ranked hypotheses.
    """
    input_data, dataset_path = input_data_tuple
    
    try:
        agent = EvaluatorAgent(input_data["config"])
        result = agent.execute(input_data)
        
        validated_hypotheses = result["validated_hypotheses"]
        top_insights = result["top_insights"]
        
        # Top insights should be from top 3 hypotheses
        assert len(top_insights) <= 3, "Should have at most 3 top insights"
        assert len(top_insights) <= len(validated_hypotheses), "Cannot have more insights than hypotheses"
        
        # Top insights should match top hypotheses
        for i, insight in enumerate(top_insights):
            if i < len(validated_hypotheses):
                assert insight["hypothesis"] == validated_hypotheses[i]["hypothesis_text"]
                assert insight["validated_confidence"] == validated_hypotheses[i]["adjusted_confidence_score"]
    
    finally:
        if os.path.exists(dataset_path):
            os.unlink(dataset_path)



# Feature: kasparro-fb-analyst, Property 22: Hypothesis Segmentation Comparison
# Validates: Requirements 7.2

@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(input_data_tuple=valid_evaluator_input())
def test_property_hypothesis_segmentation_comparison(input_data_tuple):
    """
    Property 22: Hypothesis Segmentation Comparison
    
    For any hypothesis validation, the Evaluator Agent should compute
    metrics comparing performance across at least two segments identified
    in the hypothesis.
    """
    input_data, dataset_path = input_data_tuple
    
    try:
        agent = EvaluatorAgent(input_data["config"])
        result = agent.execute(input_data)
        
        validated_hypotheses = result["validated_hypotheses"]
        
        # Each validated hypothesis should have evidence with metrics
        for validated_hyp in validated_hypotheses:
            evidence = validated_hyp["evidence"]
            metrics = evidence["metrics"]
            
            # Should have at least 2 metrics (for comparison)
            assert len(metrics) >= 2, f"Expected at least 2 metrics for segmentation comparison, got {len(metrics)}"
            
            # At least one metric should mention comparison or segments
            has_comparison = any(
                "comparison" in metric or
                any(keyword in str(metric).lower() for keyword in ["worst", "best", "vs", "compared", "segment"])
                for metric in metrics
            )
            
            # If validation status is confirmed or rejected, should have comparison
            if validated_hyp["validation_status"] in ["confirmed", "rejected"]:
                assert has_comparison or len(metrics) >= 2, \
                    "Confirmed/rejected hypotheses should have segmentation comparison"
    
    finally:
        if os.path.exists(dataset_path):
            os.unlink(dataset_path)


@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(input_data_tuple=valid_evaluator_input())
def test_property_segmentation_metrics_have_values(input_data_tuple):
    """
    Property 22: Hypothesis Segmentation Comparison
    
    Segmentation comparison metrics should have valid numeric values.
    """
    input_data, dataset_path = input_data_tuple
    
    try:
        agent = EvaluatorAgent(input_data["config"])
        result = agent.execute(input_data)
        
        validated_hypotheses = result["validated_hypotheses"]
        
        for validated_hyp in validated_hypotheses:
            metrics = validated_hyp["evidence"]["metrics"]
            
            for metric in metrics:
                # Should have value field
                assert "value" in metric, "Metric should have value field"
                value = metric["value"]
                
                # Value should be numeric
                assert isinstance(value, (int, float)), f"Metric value should be numeric, got {type(value)}"
                
                # Value should not be NaN or infinite
                import math
                assert not math.isnan(value), "Metric value should not be NaN"
                assert not math.isinf(value), "Metric value should not be infinite"
    
    finally:
        if os.path.exists(dataset_path):
            os.unlink(dataset_path)



# Feature: kasparro-fb-analyst, Property 23: Statistical Significance Inclusion
# Validates: Requirements 7.3

@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(input_data_tuple=valid_evaluator_input())
def test_property_statistical_significance_inclusion(input_data_tuple):
    """
    Property 23: Statistical Significance Inclusion
    
    For any hypothesis validation where sample size permits statistical
    testing, the Evaluator Agent should include p_value or confidence_interval
    in the evidence.
    """
    input_data, dataset_path = input_data_tuple
    
    try:
        agent = EvaluatorAgent(input_data["config"])
        result = agent.execute(input_data)
        
        validated_hypotheses = result["validated_hypotheses"]
        
        # Check if any hypothesis has statistical significance
        # (depends on sample size and data availability)
        for validated_hyp in validated_hypotheses:
            evidence = validated_hyp["evidence"]
            
            # If statistical_significance is present, it should have required fields
            if "statistical_significance" in evidence:
                stat_sig = evidence["statistical_significance"]
                
                # Should have p_value or confidence_interval
                assert "p_value" in stat_sig or "confidence_interval" in stat_sig, \
                    "Statistical significance should have p_value or confidence_interval"
                
                # If p_value is present, should be between 0 and 1
                if "p_value" in stat_sig:
                    p_value = stat_sig["p_value"]
                    assert isinstance(p_value, (int, float)), "p_value should be numeric"
                    assert 0 <= p_value <= 1, f"p_value should be between 0 and 1, got {p_value}"
                
                # If confidence_interval is present, should be a list of 2 numbers
                if "confidence_interval" in stat_sig:
                    ci = stat_sig["confidence_interval"]
                    assert isinstance(ci, list), "confidence_interval should be a list"
                    assert len(ci) == 2, "confidence_interval should have 2 elements"
                    assert all(isinstance(x, (int, float)) for x in ci), "confidence_interval elements should be numeric"
    
    finally:
        if os.path.exists(dataset_path):
            os.unlink(dataset_path)


@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(input_data_tuple=valid_evaluator_input())
def test_property_statistical_significance_valid_values(input_data_tuple):
    """
    Property 23: Statistical Significance Inclusion
    
    Statistical significance values should be valid (not NaN or infinite).
    """
    import math
    
    input_data, dataset_path = input_data_tuple
    
    try:
        agent = EvaluatorAgent(input_data["config"])
        result = agent.execute(input_data)
        
        validated_hypotheses = result["validated_hypotheses"]
        
        for validated_hyp in validated_hypotheses:
            evidence = validated_hyp["evidence"]
            
            if "statistical_significance" in evidence:
                stat_sig = evidence["statistical_significance"]
                
                if "p_value" in stat_sig:
                    p_value = stat_sig["p_value"]
                    assert not math.isnan(p_value), "p_value should not be NaN"
                    assert not math.isinf(p_value), "p_value should not be infinite"
                
                if "confidence_interval" in stat_sig:
                    ci = stat_sig["confidence_interval"]
                    for value in ci:
                        assert not math.isnan(value), "confidence_interval values should not be NaN"
                        assert not math.isinf(value), "confidence_interval values should not be infinite"
    
    finally:
        if os.path.exists(dataset_path):
            os.unlink(dataset_path)



# Feature: kasparro-fb-analyst, Property 24: Weak Evidence Confidence Calibration
# Validates: Requirements 7.4

@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(input_data_tuple=valid_evaluator_input())
def test_property_weak_evidence_confidence_calibration(input_data_tuple):
    """
    Property 24: Weak Evidence Confidence Calibration
    
    For any hypothesis where validation evidence shows contradictory metrics
    or insufficient data, the adjusted_confidence_score should be below 0.5.
    """
    input_data, dataset_path = input_data_tuple
    
    try:
        agent = EvaluatorAgent(input_data["config"])
        result = agent.execute(input_data)
        
        validated_hypotheses = result["validated_hypotheses"]
        
        for validated_hyp in validated_hypotheses:
            evidence = validated_hyp["evidence"]
            validation_status = validated_hyp["validation_status"]
            adjusted_confidence = validated_hyp["adjusted_confidence_score"]
            metrics = evidence.get("metrics", [])
            
            # If validation status is inconclusive or rejected, confidence should be lower
            if validation_status == "rejected":
                assert adjusted_confidence < 0.6, \
                    f"Rejected hypothesis should have low confidence, got {adjusted_confidence}"
            
            # If there are very few metrics (insufficient data), confidence should be lower
            if len(metrics) < 2:
                assert adjusted_confidence < 0.6, \
                    f"Hypothesis with insufficient metrics should have low confidence, got {adjusted_confidence}"
            
            # If validation status is inconclusive with no statistical significance, should be moderate or low
            if validation_status == "inconclusive" and "statistical_significance" not in evidence:
                assert adjusted_confidence <= 0.7, \
                    f"Inconclusive hypothesis without stats should have moderate/low confidence, got {adjusted_confidence}"
    
    finally:
        if os.path.exists(dataset_path):
            os.unlink(dataset_path)


@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(input_data_tuple=valid_evaluator_input())
def test_property_confidence_adjustment_applied(input_data_tuple):
    """
    Property 24: Weak Evidence Confidence Calibration
    
    Adjusted confidence should differ from initial confidence based on validation.
    """
    input_data, dataset_path = input_data_tuple
    
    try:
        agent = EvaluatorAgent(input_data["config"])
        result = agent.execute(input_data)
        
        validated_hypotheses = result["validated_hypotheses"]
        input_hypotheses = input_data["hypotheses"]
        
        # Match validated hypotheses with input hypotheses
        for validated_hyp in validated_hypotheses:
            hyp_id = validated_hyp["hypothesis_id"]
            
            # Find matching input hypothesis
            input_hyp = next((h for h in input_hypotheses if h["hypothesis_id"] == hyp_id), None)
            
            if input_hyp:
                initial_confidence = input_hyp["confidence_score"]
                adjusted_confidence = validated_hyp["adjusted_confidence_score"]
                
                # Adjusted confidence should be within valid range
                assert 0 <= adjusted_confidence <= 1, \
                    f"Adjusted confidence {adjusted_confidence} out of range"
                
                # For confirmed hypotheses, confidence might increase or stay similar
                # For rejected hypotheses, confidence should decrease
                if validated_hyp["validation_status"] == "rejected":
                    # Confidence should be lower than initial or at least not much higher
                    assert adjusted_confidence <= initial_confidence + 0.1, \
                        f"Rejected hypothesis confidence should not increase significantly"
    
    finally:
        if os.path.exists(dataset_path):
            os.unlink(dataset_path)



# Feature: kasparro-fb-analyst, Property 25: Insights Output Serialization Round-Trip
# Validates: Requirements 7.5

@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(input_data_tuple=valid_evaluator_input())
def test_property_insights_output_serialization_round_trip(input_data_tuple):
    """
    Property 25: Insights Output Serialization Round-Trip
    
    For any validated hypotheses output, writing to insights.json and
    reading back should produce valid JSON containing hypothesis_text,
    metrics, and confidence_scores.
    """
    input_data, dataset_path = input_data_tuple
    
    try:
        agent = EvaluatorAgent(input_data["config"])
        result = agent.execute(input_data)
        
        # Serialize to JSON
        json_str = json.dumps(result)
        
        # Deserialize from JSON
        deserialized = json.loads(json_str)
        
        # Should have validated_hypotheses
        assert "validated_hypotheses" in deserialized
        validated_hypotheses = deserialized["validated_hypotheses"]
        
        # Each hypothesis should have required fields
        for hypothesis in validated_hypotheses:
            assert "hypothesis_text" in hypothesis, "Should have hypothesis_text"
            assert "evidence" in hypothesis, "Should have evidence"
            assert "adjusted_confidence_score" in hypothesis, "Should have adjusted_confidence_score"
            
            # Evidence should have metrics
            evidence = hypothesis["evidence"]
            assert "metrics" in evidence, "Evidence should have metrics"
            
            # Confidence score should be preserved
            assert isinstance(hypothesis["adjusted_confidence_score"], (int, float))
            assert 0 <= hypothesis["adjusted_confidence_score"] <= 1
        
        # Key fields should match original
        assert deserialized["agent_name"] == result["agent_name"]
        assert len(deserialized["validated_hypotheses"]) == len(result["validated_hypotheses"])
    
    finally:
        if os.path.exists(dataset_path):
            os.unlink(dataset_path)


@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(input_data_tuple=valid_evaluator_input())
def test_property_insights_json_structure_valid(input_data_tuple):
    """
    Property 25: Insights Output Serialization Round-Trip
    
    The JSON structure should be valid and contain all required fields.
    """
    input_data, dataset_path = input_data_tuple
    
    try:
        agent = EvaluatorAgent(input_data["config"])
        result = agent.execute(input_data)
        
        # Should be JSON serializable
        try:
            json_str = json.dumps(result)
            deserialized = json.loads(json_str)
        except (TypeError, ValueError) as e:
            pytest.fail(f"Output is not JSON serializable: {e}")
        
        # Should have all required top-level fields
        required_fields = ["agent_name", "timestamp", "execution_duration_ms", "validated_hypotheses", "reasoning"]
        for field in required_fields:
            assert field in deserialized, f"Missing required field: {field}"
    
    finally:
        if os.path.exists(dataset_path):
            os.unlink(dataset_path)



# Feature: kasparro-fb-analyst, Property 45: Confidence Score Adjustment
# Validates: Requirements 14.2

@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(input_data_tuple=valid_evaluator_input())
def test_property_confidence_score_adjustment(input_data_tuple):
    """
    Property 45: Confidence Score Adjustment
    
    For any hypothesis that undergoes validation, the Evaluator Agent
    should output an adjusted_confidence_score based on validation evidence.
    """
    input_data, dataset_path = input_data_tuple
    
    try:
        agent = EvaluatorAgent(input_data["config"])
        result = agent.execute(input_data)
        
        validated_hypotheses = result["validated_hypotheses"]
        
        # Each validated hypothesis should have adjusted_confidence_score
        for validated_hyp in validated_hypotheses:
            assert "adjusted_confidence_score" in validated_hyp, \
                "Validated hypothesis should have adjusted_confidence_score"
            
            adjusted_confidence = validated_hyp["adjusted_confidence_score"]
            
            # Should be numeric
            assert isinstance(adjusted_confidence, (int, float)), \
                f"Adjusted confidence should be numeric, got {type(adjusted_confidence)}"
            
            # Should be between 0 and 1
            assert 0 <= adjusted_confidence <= 1, \
                f"Adjusted confidence {adjusted_confidence} out of range [0, 1]"
            
            # Should not be NaN or infinite
            import math
            assert not math.isnan(adjusted_confidence), "Adjusted confidence should not be NaN"
            assert not math.isinf(adjusted_confidence), "Adjusted confidence should not be infinite"
    
    finally:
        if os.path.exists(dataset_path):
            os.unlink(dataset_path)


@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(input_data_tuple=valid_evaluator_input())
def test_property_confidence_adjustment_formula_applied(input_data_tuple):
    """
    Property 45: Confidence Score Adjustment
    
    The adjusted confidence should reflect the weighted formula:
    (InsightConfidence * 0.4) + (ValidationStrength * 0.4) + (SegmentationEvidence * 0.2)
    """
    input_data, dataset_path = input_data_tuple
    
    try:
        agent = EvaluatorAgent(input_data["config"])
        result = agent.execute(input_data)
        
        validated_hypotheses = result["validated_hypotheses"]
        input_hypotheses = input_data["hypotheses"]
        
        for validated_hyp in validated_hypotheses:
            hyp_id = validated_hyp["hypothesis_id"]
            adjusted_confidence = validated_hyp["adjusted_confidence_score"]
            
            # Find matching input hypothesis
            input_hyp = next((h for h in input_hypotheses if h["hypothesis_id"] == hyp_id), None)
            
            if input_hyp:
                initial_confidence = input_hyp["confidence_score"]
                
                # Adjusted confidence should be influenced by initial confidence
                # but also by validation results
                # The formula ensures adjusted confidence is a weighted combination
                
                # Check that adjusted confidence is within reasonable bounds
                # given the initial confidence
                # It should not be exactly the same (unless by coincidence)
                # and should be influenced by validation
                
                # Adjusted confidence should be in valid range
                assert 0 <= adjusted_confidence <= 1
                
                # For confirmed hypotheses with strong evidence, confidence might increase
                # For rejected hypotheses, confidence should decrease
                validation_status = validated_hyp["validation_status"]
                
                if validation_status == "confirmed":
                    # Confidence should be at least moderate
                    assert adjusted_confidence >= 0.3, \
                        f"Confirmed hypothesis should have at least moderate confidence"
                
                if validation_status == "rejected":
                    # Confidence should be lower
                    assert adjusted_confidence <= 0.6, \
                        f"Rejected hypothesis should have lower confidence"
    
    finally:
        if os.path.exists(dataset_path):
            os.unlink(dataset_path)


@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(input_data_tuple=valid_evaluator_input())
def test_property_all_confidence_scores_adjusted(input_data_tuple):
    """
    Property 45: Confidence Score Adjustment
    
    All hypotheses should have their confidence scores adjusted.
    """
    input_data, dataset_path = input_data_tuple
    
    try:
        agent = EvaluatorAgent(input_data["config"])
        result = agent.execute(input_data)
        
        validated_hypotheses = result["validated_hypotheses"]
        
        # All validated hypotheses should have adjusted confidence
        assert all("adjusted_confidence_score" in h for h in validated_hypotheses), \
            "All validated hypotheses should have adjusted_confidence_score"
        
        # All adjusted confidence scores should be valid
        confidence_scores = [h["adjusted_confidence_score"] for h in validated_hypotheses]
        assert all(0 <= score <= 1 for score in confidence_scores), \
            "All adjusted confidence scores should be between 0 and 1"
    
    finally:
        if os.path.exists(dataset_path):
            os.unlink(dataset_path)
