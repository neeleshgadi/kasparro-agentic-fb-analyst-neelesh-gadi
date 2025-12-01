"""
Property-based tests for Creative Generator Agent.

These tests verify that the Creative Generator correctly identifies low-CTR campaigns,
generates creative variations, and produces valid recommendations.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from datetime import datetime
import json
import pandas as pd
import tempfile
import os

from src.agents.creative_generator import CreativeGeneratorAgent
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
def valid_dataset_with_low_ctr(draw):
    """Generate a valid dataset with some low-CTR campaigns."""
    num_rows = draw(st.integers(min_value=50, max_value=200))
    num_campaigns = draw(st.integers(min_value=3, max_value=8))
    
    # Generate data
    data = {
        "campaign_name": [f"Campaign_{i % num_campaigns}" for i in range(num_rows)],
        "date": [f"2024-01-{(i % 28) + 1:02d}" for i in range(num_rows)],
        "spend": [draw(st.floats(min_value=10, max_value=1000)) for _ in range(num_rows)],
        "impressions": [draw(st.integers(min_value=1000, max_value=10000)) for _ in range(num_rows)],
        "revenue": [draw(st.floats(min_value=5, max_value=2000)) for _ in range(num_rows)],
        "purchases": [draw(st.integers(min_value=0, max_value=50)) for _ in range(num_rows)],
        "creative_type": [draw(st.sampled_from(["image", "video", "carousel"])) for _ in range(num_rows)],
        "creative_message": [f"Message {i % 10}" for i in range(num_rows)],
        "audience_type": [f"audience_{i % 3}" for i in range(num_rows)],
        "platform": [draw(st.sampled_from(["Facebook", "Instagram"])) for _ in range(num_rows)],
    }
    
    # Generate clicks - ensure some campaigns have low CTR
    clicks = []
    for i in range(num_rows):
        campaign_idx = i % num_campaigns
        impressions = data["impressions"][i]
        
        # Make first half of campaigns have low CTR
        if campaign_idx < num_campaigns // 2:
            # Low CTR: 0.005 to 0.009
            ctr = draw(st.floats(min_value=0.005, max_value=0.009))
        else:
            # Normal/high CTR: 0.012 to 0.025
            ctr = draw(st.floats(min_value=0.012, max_value=0.025))
        
        clicks.append(int(impressions * ctr))
    
    data["clicks"] = clicks
    
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
def valid_data_summary_with_low_ctr(draw, df):
    """Generate a valid data summary with low-CTR campaigns."""
    # Calculate overall metrics
    total_spend = df["spend"].sum()
    total_revenue = df["revenue"].sum()
    total_impressions = df["impressions"].sum()
    total_clicks = df["clicks"].sum()
    
    overall_roas = total_revenue / total_spend if total_spend > 0 else 0
    overall_ctr = total_clicks / total_impressions if total_impressions > 0 else 0
    
    # Generate campaign segmentation
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
    
    # Generate creative type segmentation
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
                "week_over_week_change": 0.0,
                "month_over_month_change": 0.0,
            },
            "ctr_trend": {
                "direction": "stable",
                "week_over_week_change": 0.0,
                "month_over_month_change": 0.0,
            }
        },
        "segmentation": {
            "by_campaign": campaigns,
            "by_creative_type": creative_segments,
            "by_audience_type": [],
            "by_platform": [],
        },
        "data_quality_issues": []
    }


@st.composite
def valid_creative_generator_input(draw):
    """Generate valid input for Creative Generator Agent."""
    # Generate dataset with low-CTR campaigns
    dataset_path, df = draw(valid_dataset_with_low_ctr())
    
    # Generate data summary based on dataset
    data_summary = draw(valid_data_summary_with_low_ctr(df))
    
    # Use threshold that will catch low-CTR campaigns
    low_ctr_threshold = draw(st.floats(min_value=0.01, max_value=0.012))
    
    return {
        "data_summary": data_summary,
        "dataset_path": dataset_path,
        "low_ctr_threshold": low_ctr_threshold,
        "config": SIMPLE_CONFIG
    }, dataset_path


# Feature: kasparro-fb-analyst, Property 19: Creative Variation Minimum Count
# Validates: Requirements 6.2

@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(input_data_tuple=valid_creative_generator_input())
def test_property_creative_variation_minimum_count(input_data_tuple):
    """
    Property 19: Creative Variation Minimum Count
    
    For any low-CTR campaign, the Creative Generator should produce
    at least three distinct creative variations.
    """
    input_data, dataset_path = input_data_tuple
    
    try:
        # Create creative generator agent
        agent = CreativeGeneratorAgent(input_data["config"])
        
        # Execute agent
        result = agent.execute(input_data)
        
        # Should have recommendations field
        assert "recommendations" in result
        recommendations = result["recommendations"]
        
        # Each recommendation should have at least 3 new creatives
        for recommendation in recommendations:
            assert "new_creatives" in recommendation, "Recommendation should have new_creatives"
            new_creatives = recommendation["new_creatives"]
            
            assert isinstance(new_creatives, list), "new_creatives should be a list"
            assert len(new_creatives) >= 3, \
                f"Expected at least 3 creative variations, got {len(new_creatives)} for campaign {recommendation.get('campaign', 'unknown')}"
            
            # Creatives should be distinct (different creative_id)
            creative_ids = [c["creative_id"] for c in new_creatives]
            assert len(creative_ids) == len(set(creative_ids)), \
                "Creative variations should have distinct IDs"
    
    finally:
        # Clean up temp file
        if os.path.exists(dataset_path):
            os.unlink(dataset_path)


@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(input_data_tuple=valid_creative_generator_input())
def test_property_creative_variations_are_distinct(input_data_tuple):
    """
    Property 19: Creative Variation Minimum Count
    
    Creative variations should be distinct (different messages or types).
    """
    input_data, dataset_path = input_data_tuple
    
    try:
        agent = CreativeGeneratorAgent(input_data["config"])
        result = agent.execute(input_data)
        
        recommendations = result["recommendations"]
        
        for recommendation in recommendations:
            new_creatives = recommendation["new_creatives"]
            
            # Check that creative messages are distinct
            messages = [c["creative_message"] for c in new_creatives]
            # At least some messages should be different
            assert len(set(messages)) >= 2, \
                "Creative variations should have diverse messages"
            
            # Check that we have variety in creative types
            types = [c["creative_type"] for c in new_creatives]
            # Should have at least 2 different types among the variations
            assert len(set(types)) >= 2, \
                "Creative variations should include different creative types"
    
    finally:
        if os.path.exists(dataset_path):
            os.unlink(dataset_path)


# Feature: kasparro-fb-analyst, Property 20: Creative Schema Completeness
# Validates: Requirements 6.3

@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(input_data_tuple=valid_creative_generator_input())
def test_property_creative_schema_completeness(input_data_tuple):
    """
    Property 20: Creative Schema Completeness
    
    For any generated creative recommendation, the output should include
    all required fields: creative_message, creative_type, audience_type,
    rationale, and confidence_score.
    """
    input_data, dataset_path = input_data_tuple
    
    try:
        agent = CreativeGeneratorAgent(input_data["config"])
        result = agent.execute(input_data)
        
        recommendations = result["recommendations"]
        
        # Check each creative variation has all required fields
        for recommendation in recommendations:
            new_creatives = recommendation["new_creatives"]
            
            for creative in new_creatives:
                # Check required fields
                assert "creative_message" in creative, "Creative should have creative_message"
                assert "creative_type" in creative, "Creative should have creative_type"
                assert "audience_type" in creative, "Creative should have audience_type"
                assert "rationale" in creative, "Creative should have rationale"
                assert "confidence_score" in creative, "Creative should have confidence_score"
                
                # Check field types
                assert isinstance(creative["creative_message"], str), "creative_message should be string"
                assert isinstance(creative["creative_type"], str), "creative_type should be string"
                assert isinstance(creative["audience_type"], str), "audience_type should be string"
                assert isinstance(creative["rationale"], str), "rationale should be string"
                assert isinstance(creative["confidence_score"], (int, float)), "confidence_score should be numeric"
                
                # Check field values
                assert len(creative["creative_message"]) > 0, "creative_message should not be empty"
                assert len(creative["creative_type"]) > 0, "creative_type should not be empty"
                assert len(creative["audience_type"]) > 0, "audience_type should not be empty"
                assert len(creative["rationale"]) > 0, "rationale should not be empty"
                assert 0 <= creative["confidence_score"] <= 1, \
                    f"confidence_score should be between 0 and 1, got {creative['confidence_score']}"
    
    finally:
        if os.path.exists(dataset_path):
            os.unlink(dataset_path)


@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(input_data_tuple=valid_creative_generator_input())
def test_property_creative_fields_non_empty(input_data_tuple):
    """
    Property 20: Creative Schema Completeness
    
    All required string fields should be non-empty and meaningful.
    """
    input_data, dataset_path = input_data_tuple
    
    try:
        agent = CreativeGeneratorAgent(input_data["config"])
        result = agent.execute(input_data)
        
        recommendations = result["recommendations"]
        
        for recommendation in recommendations:
            new_creatives = recommendation["new_creatives"]
            
            for creative in new_creatives:
                # Messages should be meaningful (not just whitespace)
                assert creative["creative_message"].strip() != "", \
                    "creative_message should not be empty or whitespace"
                
                # Rationale should be meaningful
                assert creative["rationale"].strip() != "", \
                    "rationale should not be empty or whitespace"
                assert len(creative["rationale"]) > 10, \
                    "rationale should be descriptive (>10 chars)"
    
    finally:
        if os.path.exists(dataset_path):
            os.unlink(dataset_path)


# Feature: kasparro-fb-analyst, Property 21: Creative Output Serialization Round-Trip
# Validates: Requirements 6.4

@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(input_data_tuple=valid_creative_generator_input())
def test_property_creative_output_serialization_round_trip(input_data_tuple):
    """
    Property 21: Creative Output Serialization Round-Trip
    
    For any creative recommendations output, writing to creatives.json
    and reading back should produce valid JSON that deserializes to an
    equivalent data structure.
    """
    input_data, dataset_path = input_data_tuple
    
    try:
        agent = CreativeGeneratorAgent(input_data["config"])
        result = agent.execute(input_data)
        
        # Serialize to JSON
        json_str = json.dumps(result)
        
        # Deserialize from JSON
        deserialized = json.loads(json_str)
        
        # Should have recommendations
        assert "recommendations" in deserialized
        recommendations = deserialized["recommendations"]
        
        # Each recommendation should have required fields
        for recommendation in recommendations:
            assert "campaign" in recommendation, "Should have campaign"
            assert "current_ctr" in recommendation, "Should have current_ctr"
            assert "new_creatives" in recommendation, "Should have new_creatives"
            
            # Each creative should have required fields
            for creative in recommendation["new_creatives"]:
                assert "creative_message" in creative
                assert "creative_type" in creative
                assert "audience_type" in creative
                assert "rationale" in creative
                assert "confidence_score" in creative
                
                # Types should be preserved
                assert isinstance(creative["creative_message"], str)
                assert isinstance(creative["confidence_score"], (int, float))
        
        # Key fields should match original
        assert deserialized["agent_name"] == result["agent_name"]
        assert len(deserialized["recommendations"]) == len(result["recommendations"])
    
    finally:
        if os.path.exists(dataset_path):
            os.unlink(dataset_path)


@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(input_data_tuple=valid_creative_generator_input())
def test_property_creative_json_structure_valid(input_data_tuple):
    """
    Property 21: Creative Output Serialization Round-Trip
    
    The JSON structure should be valid and contain all required top-level fields.
    """
    input_data, dataset_path = input_data_tuple
    
    try:
        agent = CreativeGeneratorAgent(input_data["config"])
        result = agent.execute(input_data)
        
        # Should be JSON serializable
        try:
            json_str = json.dumps(result)
            deserialized = json.loads(json_str)
        except (TypeError, ValueError) as e:
            pytest.fail(f"Result should be JSON serializable: {e}")
        
        # Should have required top-level fields
        assert "agent_name" in deserialized
        assert "timestamp" in deserialized
        assert "execution_duration_ms" in deserialized
        assert "recommendations" in deserialized
        assert "reasoning" in deserialized
        
        # Reasoning should have required sections
        reasoning = deserialized["reasoning"]
        assert "think" in reasoning
        assert "analyze" in reasoning
        assert "conclude" in reasoning
    
    finally:
        if os.path.exists(dataset_path):
            os.unlink(dataset_path)
