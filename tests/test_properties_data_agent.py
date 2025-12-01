"""
Property-based tests for Data Agent.

These tests validate correctness properties for the Data Agent using Hypothesis.
"""

import pytest
import pandas as pd
import tempfile
import os
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime, timedelta

from src.agents.data_agent import DataAgent
from src.schemas.validation import ValidationError
from src.utils.config_loader import ConfigLoader


# Test configuration
TEST_CONFIG = {
    "thresholds": {
        "low_ctr": 0.01,
        "trend_stable_threshold": 0.05,
    },
    "logging": {
        "level": "ERROR",
        "format": "json",
        "log_dir": "logs",
    },
    "data_quality": {
        "date_format": "%Y-%m-%d",
        "required_fields": [
            "campaign_name",
            "date",
            "spend",
            "impressions",
            "clicks",
            "revenue",
        ],
    },
}


# Hypothesis strategies for generating test data
@st.composite
def valid_dataset_row(draw):
    """Generate a valid dataset row."""
    base_date = datetime(2024, 1, 1)
    days_offset = draw(st.integers(min_value=0, max_value=60))
    
    impressions = draw(st.integers(min_value=100, max_value=100000))
    clicks = draw(st.integers(min_value=0, max_value=impressions))
    spend = draw(st.floats(min_value=10.0, max_value=10000.0))
    revenue = draw(st.floats(min_value=0.0, max_value=50000.0))
    
    return {
        "campaign_name": draw(st.sampled_from(["Campaign_A", "Campaign_B", "Campaign_C"])),
        "date": (base_date + timedelta(days=days_offset)).strftime("%Y-%m-%d"),
        "spend": round(spend, 2),
        "impressions": impressions,
        "clicks": clicks,
        "revenue": round(revenue, 2),
        "adset_name": draw(st.sampled_from(["Adset_1", "Adset_2"])),
        "creative_type": draw(st.sampled_from(["image", "video", "carousel"])),
        "audience_type": draw(st.sampled_from(["male_18_24", "female_25_34", "all_35_plus"])),
        "platform": draw(st.sampled_from(["Facebook", "Instagram"])),
    }


@st.composite
def valid_dataset(draw, min_rows=10, max_rows=100):
    """Generate a valid dataset."""
    num_rows = draw(st.integers(min_value=min_rows, max_value=max_rows))
    rows = [draw(valid_dataset_row()) for _ in range(num_rows)]
    return pd.DataFrame(rows)


def create_temp_csv(df: pd.DataFrame) -> str:
    """Create a temporary CSV file from DataFrame."""
    fd, path = tempfile.mkstemp(suffix=".csv")
    os.close(fd)
    df.to_csv(path, index=False)
    return path


# Feature: kasparro-fb-analyst, Property 6: Dataset Field Validation
# Validates: Requirements 3.1
@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow], deadline=None)
@given(dataset=valid_dataset())
def test_property_6_dataset_field_validation(dataset):
    """
    Property 6: Dataset Field Validation
    For any dataset loading attempt, the Data Agent should validate that all 
    required fields are present before processing.
    """
    agent = DataAgent(TEST_CONFIG)
    
    # Create temporary CSV with all required fields
    csv_path = create_temp_csv(dataset)
    
    try:
        input_data = {
            "dataset_path": csv_path,
            "config": TEST_CONFIG
        }
        
        # Should succeed with all required fields
        output = agent.execute(input_data)
        
        # Verify output contains dataset_summary
        assert "dataset_summary" in output
        assert output["dataset_summary"]["total_rows"] > 0
        
    finally:
        os.unlink(csv_path)


# Feature: kasparro-fb-analyst, Property 43: Required Field Validation
# Validates: Requirements 13.4
@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
@given(
    dataset=valid_dataset(),
    field_to_remove=st.sampled_from([
        "campaign_name", "date", "spend", "impressions", "clicks", "revenue"
    ])
)
def test_property_43_required_field_validation(dataset, field_to_remove):
    """
    Property 43: Required Field Validation
    For any dataset missing required fields, the Data Agent should raise a 
    ValidationError with all missing field names.
    """
    agent = DataAgent(TEST_CONFIG)
    
    # Remove a required field
    dataset_missing = dataset.drop(columns=[field_to_remove])
    csv_path = create_temp_csv(dataset_missing)
    
    try:
        input_data = {
            "dataset_path": csv_path,
            "config": TEST_CONFIG
        }
        
        # Should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            agent.execute(input_data)
        
        # Verify error mentions missing field
        assert "missing" in str(exc_info.value).lower()
        assert field_to_remove in str(exc_info.value.details.get("missing_fields", []))
        
    finally:
        os.unlink(csv_path)


# Feature: kasparro-fb-analyst, Property 7: Dataset Summary Completeness
# Validates: Requirements 3.2
@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow], deadline=None)
@given(dataset=valid_dataset(min_rows=5, max_rows=50))
def test_property_7_dataset_summary_completeness(dataset):
    """
    Property 7: Dataset Summary Completeness
    For any successfully loaded dataset, the Data Agent should compute and return 
    summary statistics including row count, date range, total spend, total revenue, 
    campaigns count, and data quality metrics.
    """
    agent = DataAgent(TEST_CONFIG)
    csv_path = create_temp_csv(dataset)
    
    try:
        input_data = {
            "dataset_path": csv_path,
            "config": TEST_CONFIG
        }
        
        output = agent.execute(input_data)
        
        # Verify all required summary fields are present
        assert "dataset_summary" in output
        summary = output["dataset_summary"]
        
        assert "total_rows" in summary
        assert "date_range" in summary
        assert "start" in summary["date_range"]
        assert "end" in summary["date_range"]
        assert "total_spend" in summary
        assert "total_revenue" in summary
        assert "campaigns_count" in summary
        assert "data_quality" in summary
        
        # Verify values are reasonable
        assert summary["total_rows"] == len(dataset)
        assert summary["campaigns_count"] > 0
        
    finally:
        os.unlink(csv_path)


# Feature: kasparro-fb-analyst, Property 8: Metric Calculation Accuracy
# Validates: Requirements 3.3
@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow], deadline=None)
@given(dataset=valid_dataset(min_rows=10, max_rows=50))
def test_property_8_metric_calculation_accuracy(dataset):
    """
    Property 8: Metric Calculation Accuracy
    For any dataset, the Data Agent should calculate overall_roas, overall_ctr, 
    and conversion_rate with results matching manual calculations within 0.01% tolerance.
    """
    agent = DataAgent(TEST_CONFIG)
    csv_path = create_temp_csv(dataset)
    
    try:
        input_data = {
            "dataset_path": csv_path,
            "config": TEST_CONFIG
        }
        
        output = agent.execute(input_data)
        
        # Manual calculations
        total_spend = dataset["spend"].sum()
        total_revenue = dataset["revenue"].sum()
        total_impressions = dataset["impressions"].sum()
        total_clicks = dataset["clicks"].sum()
        
        expected_roas = total_revenue / total_spend if total_spend > 0 else 0.0
        expected_ctr = total_clicks / total_impressions if total_impressions > 0 else 0.0
        expected_cpc = total_spend / total_clicks if total_clicks > 0 else 0.0
        
        # Verify metrics match within tolerance
        metrics = output["metrics"]
        tolerance = 0.0001  # 0.01% tolerance
        
        assert abs(metrics["overall_roas"] - expected_roas) <= tolerance * max(abs(expected_roas), 1)
        assert abs(metrics["overall_ctr"] - expected_ctr) <= tolerance * max(abs(expected_ctr), 1)
        assert abs(metrics["avg_cpc"] - expected_cpc) <= tolerance * max(abs(expected_cpc), 1)
        
    finally:
        os.unlink(csv_path)



# Feature: kasparro-fb-analyst, Property 9: Data Quality Reporting
# Validates: Requirements 3.4
@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow], deadline=None)
@given(
    dataset=valid_dataset(min_rows=10, max_rows=30),
    num_missing=st.integers(min_value=1, max_value=5)
)
def test_property_9_data_quality_reporting(dataset, num_missing):
    """
    Property 9: Data Quality Reporting
    For any dataset with missing or invalid values, the Data Agent should report 
    data quality issues with specific row and column references in the output.
    """
    agent = DataAgent(TEST_CONFIG)
    
    # Introduce missing values
    dataset_with_missing = dataset.copy()
    indices = dataset_with_missing.sample(n=min(num_missing, len(dataset_with_missing))).index
    dataset_with_missing.loc[indices, "spend"] = None
    
    csv_path = create_temp_csv(dataset_with_missing)
    
    try:
        input_data = {
            "dataset_path": csv_path,
            "config": TEST_CONFIG
        }
        
        output = agent.execute(input_data)
        
        # Verify data quality issues are reported
        assert "data_quality_issues" in output
        
        # Should have at least one issue reported
        if num_missing > 0:
            assert len(output["data_quality_issues"]) > 0
            
            # Check that issue contains required information
            for issue in output["data_quality_issues"]:
                assert "issue_type" in issue
                assert "count" in issue or "field" in issue
        
    finally:
        os.unlink(csv_path)


# Feature: kasparro-fb-analyst, Property 10: Dataset Caching Consistency
# Validates: Requirements 3.5
@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow], deadline=None)
@given(dataset=valid_dataset(min_rows=10, max_rows=30))
def test_property_10_dataset_caching_consistency(dataset):
    """
    Property 10: Dataset Caching Consistency
    For any successfully loaded dataset, subsequent agent accesses within the same 
    workflow should retrieve the identical cached dataset without reloading from disk.
    """
    agent = DataAgent(TEST_CONFIG)
    csv_path = create_temp_csv(dataset)
    
    try:
        input_data = {
            "dataset_path": csv_path,
            "config": TEST_CONFIG
        }
        
        # First execution - loads from disk
        output1 = agent.execute(input_data)
        
        # Second execution - should use cache
        output2 = agent.execute(input_data)
        
        # Verify outputs are identical
        assert output1["dataset_summary"]["total_rows"] == output2["dataset_summary"]["total_rows"]
        assert output1["dataset_summary"]["total_spend"] == output2["dataset_summary"]["total_spend"]
        assert output1["dataset_summary"]["total_revenue"] == output2["dataset_summary"]["total_revenue"]
        assert output1["metrics"]["overall_roas"] == output2["metrics"]["overall_roas"]
        
    finally:
        os.unlink(csv_path)


# Feature: kasparro-fb-analyst, Property 40: Missing Value Handling
# Validates: Requirements 13.1
@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow], deadline=None)
@given(
    dataset=valid_dataset(min_rows=20, max_rows=50),
    num_missing=st.integers(min_value=1, max_value=10)
)
def test_property_40_missing_value_handling(dataset, num_missing):
    """
    Property 40: Missing Value Handling
    For any dataset row with missing values, the Data Agent should either impute 
    or exclude the row and log the action taken.
    """
    agent = DataAgent(TEST_CONFIG)
    
    # Introduce missing values in required field
    dataset_with_missing = dataset.copy()
    indices = dataset_with_missing.sample(n=min(num_missing, len(dataset_with_missing))).index
    dataset_with_missing.loc[indices, "revenue"] = None
    
    csv_path = create_temp_csv(dataset_with_missing)
    
    try:
        input_data = {
            "dataset_path": csv_path,
            "config": TEST_CONFIG
        }
        
        output = agent.execute(input_data)
        
        # Verify rows with missing required fields are excluded
        expected_rows = len(dataset_with_missing) - num_missing
        assert output["dataset_summary"]["total_rows"] == expected_rows
        
        # Verify action is logged in data quality issues
        assert "data_quality_issues" in output
        missing_issue = [i for i in output["data_quality_issues"] if i.get("issue_type") == "missing_values"]
        assert len(missing_issue) > 0
        assert missing_issue[0].get("action") == "excluded_rows"
        
    finally:
        os.unlink(csv_path)


# Feature: kasparro-fb-analyst, Property 41: Date Parsing Error Handling
# Validates: Requirements 13.2
@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
@given(
    dataset=valid_dataset(min_rows=20, max_rows=50),
    num_invalid=st.integers(min_value=1, max_value=5)
)
def test_property_41_date_parsing_error_handling(dataset, num_invalid):
    """
    Property 41: Date Parsing Error Handling
    For any dataset row with invalid date format, the Data Agent should log the 
    invalid value, skip the row, and continue processing.
    """
    agent = DataAgent(TEST_CONFIG)
    
    # Introduce invalid dates
    dataset_with_invalid = dataset.copy()
    indices = dataset_with_invalid.sample(n=min(num_invalid, len(dataset_with_invalid))).index
    dataset_with_invalid.loc[indices, "date"] = "invalid-date"
    
    csv_path = create_temp_csv(dataset_with_invalid)
    
    try:
        input_data = {
            "dataset_path": csv_path,
            "config": TEST_CONFIG
        }
        
        output = agent.execute(input_data)
        
        # Verify rows with invalid dates are excluded
        expected_rows = len(dataset_with_invalid) - num_invalid
        assert output["dataset_summary"]["total_rows"] == expected_rows
        
        # Verify issue is logged
        assert "data_quality_issues" in output
        date_issues = [i for i in output["data_quality_issues"] if i.get("issue_type") == "invalid_dates"]
        assert len(date_issues) > 0
        assert date_issues[0].get("action") == "excluded_rows"
        
    finally:
        os.unlink(csv_path)


# Feature: kasparro-fb-analyst, Property 42: Numeric Field Error Handling
# Validates: Requirements 13.3
@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow], deadline=None)
@given(
    dataset=valid_dataset(min_rows=20, max_rows=50),
    num_invalid=st.integers(min_value=1, max_value=5)
)
def test_property_42_numeric_field_error_handling(dataset, num_invalid):
    """
    Property 42: Numeric Field Error Handling
    For any dataset row with non-numeric values in numeric fields, the Data Agent 
    should attempt conversion or exclude the row and log a warning.
    """
    agent = DataAgent(TEST_CONFIG)
    
    # Introduce non-numeric values
    dataset_with_invalid = dataset.copy()
    indices = dataset_with_invalid.sample(n=min(num_invalid, len(dataset_with_invalid))).index
    # Convert to object dtype first to avoid pandas warning
    dataset_with_invalid["spend"] = dataset_with_invalid["spend"].astype(object)
    dataset_with_invalid.loc[indices, "spend"] = "not-a-number"
    
    csv_path = create_temp_csv(dataset_with_invalid)
    
    try:
        input_data = {
            "dataset_path": csv_path,
            "config": TEST_CONFIG
        }
        
        output = agent.execute(input_data)
        
        # Verify issue is logged
        assert "data_quality_issues" in output
        numeric_issues = [i for i in output["data_quality_issues"] 
                         if i.get("issue_type") == "non_numeric_values"]
        
        # Should have at least one numeric issue
        if num_invalid > 0:
            assert len(numeric_issues) > 0
        
    finally:
        os.unlink(csv_path)


# Feature: kasparro-fb-analyst, Property 44: Data Quality Summary Inclusion
# Validates: Requirements 13.5
@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow], deadline=None)
@given(
    dataset=valid_dataset(min_rows=20, max_rows=50),
    num_issues=st.integers(min_value=1, max_value=5)
)
def test_property_44_data_quality_summary_inclusion(dataset, num_issues):
    """
    Property 44: Data Quality Summary Inclusion
    For any dataset with detected data quality issues, the Data Agent output should 
    include a data_quality object with issue counts.
    """
    agent = DataAgent(TEST_CONFIG)
    
    # Introduce data quality issues
    dataset_with_issues = dataset.copy()
    indices = dataset_with_issues.sample(n=min(num_issues, len(dataset_with_issues))).index
    dataset_with_issues.loc[indices, "clicks"] = None
    
    csv_path = create_temp_csv(dataset_with_issues)
    
    try:
        input_data = {
            "dataset_path": csv_path,
            "config": TEST_CONFIG
        }
        
        output = agent.execute(input_data)
        
        # Verify data_quality object is present in summary
        assert "dataset_summary" in output
        assert "data_quality" in output["dataset_summary"]
        
        data_quality = output["dataset_summary"]["data_quality"]
        assert "missing_values" in data_quality
        assert "invalid_rows" in data_quality
        
        # Should report invalid rows
        assert data_quality["invalid_rows"] >= num_issues
        
    finally:
        os.unlink(csv_path)



# Feature: kasparro-fb-analyst, Property 51: Trend Calculation Completeness
# Validates: Requirements 17.1
@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow], deadline=None)
@given(dataset=valid_dataset(min_rows=30, max_rows=100))
def test_property_51_trend_calculation_completeness(dataset):
    """
    Property 51: Trend Calculation Completeness
    For any dataset with sufficient historical data, the Data Agent should calculate 
    week-over-week and month-over-month changes for key metrics.
    """
    agent = DataAgent(TEST_CONFIG)
    csv_path = create_temp_csv(dataset)
    
    try:
        input_data = {
            "dataset_path": csv_path,
            "config": TEST_CONFIG
        }
        
        output = agent.execute(input_data)
        
        # Verify trends are present
        assert "trends" in output
        trends = output["trends"]
        
        # Verify ROAS trend
        assert "roas_trend" in trends
        roas_trend = trends["roas_trend"]
        assert "direction" in roas_trend
        assert "week_over_week_change" in roas_trend
        assert "month_over_month_change" in roas_trend
        
        # Verify CTR trend
        assert "ctr_trend" in trends
        ctr_trend = trends["ctr_trend"]
        assert "direction" in ctr_trend
        assert "week_over_week_change" in ctr_trend
        assert "month_over_month_change" in ctr_trend
        
    finally:
        os.unlink(csv_path)


# Feature: kasparro-fb-analyst, Property 52: Trend Direction Classification
# Validates: Requirements 17.2
@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
@given(dataset=valid_dataset(min_rows=30, max_rows=100))
def test_property_52_trend_direction_classification(dataset):
    """
    Property 52: Trend Direction Classification
    For any computed trend change, the Data Agent should classify the trend as 
    increasing, decreasing, or stable based on thresholds.
    """
    agent = DataAgent(TEST_CONFIG)
    csv_path = create_temp_csv(dataset)
    
    try:
        input_data = {
            "dataset_path": csv_path,
            "config": TEST_CONFIG
        }
        
        output = agent.execute(input_data)
        
        # Verify trend directions are valid
        trends = output["trends"]
        
        for trend_key in ["roas_trend", "ctr_trend"]:
            if trend_key in trends:
                direction = trends[trend_key]["direction"]
                assert direction in ["increasing", "decreasing", "stable"]
        
    finally:
        os.unlink(csv_path)


# Feature: kasparro-fb-analyst, Property 53: Seasonality Flagging
# Validates: Requirements 17.3
@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
@given(dataset=valid_dataset(min_rows=60, max_rows=120))
def test_property_53_seasonality_flagging(dataset):
    """
    Property 53: Seasonality Flagging
    For any dataset with detected repeating patterns, the Data Agent should set a 
    seasonality_detected flag in the output.
    
    Note: This is a placeholder test as seasonality detection is not yet implemented.
    The test verifies the structure is in place for future implementation.
    """
    agent = DataAgent(TEST_CONFIG)
    csv_path = create_temp_csv(dataset)
    
    try:
        input_data = {
            "dataset_path": csv_path,
            "config": TEST_CONFIG
        }
        
        output = agent.execute(input_data)
        
        # Verify trends object exists (where seasonality would be reported)
        assert "trends" in output
        
        # Future: Check for seasonality_detected flag when implemented
        # assert "seasonality_detected" in output["trends"]
        
    finally:
        os.unlink(csv_path)


# Feature: kasparro-fb-analyst, Property 54: Trend Data Schema Inclusion
# Validates: Requirements 17.4
@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow], deadline=None)
@given(dataset=valid_dataset(min_rows=30, max_rows=100))
def test_property_54_trend_data_schema_inclusion(dataset):
    """
    Property 54: Trend Data Schema Inclusion
    For any Data Agent output, the schema should include a trends object with 
    direction and change percentages.
    """
    agent = DataAgent(TEST_CONFIG)
    csv_path = create_temp_csv(dataset)
    
    try:
        input_data = {
            "dataset_path": csv_path,
            "config": TEST_CONFIG
        }
        
        output = agent.execute(input_data)
        
        # Verify trends object structure
        assert "trends" in output
        trends = output["trends"]
        
        # Check ROAS trend structure
        if "roas_trend" in trends:
            roas_trend = trends["roas_trend"]
            assert isinstance(roas_trend, dict)
            assert "direction" in roas_trend
            assert isinstance(roas_trend["direction"], str)
            assert "week_over_week_change" in roas_trend
            assert isinstance(roas_trend["week_over_week_change"], (int, float))
            assert "month_over_month_change" in roas_trend
            assert isinstance(roas_trend["month_over_month_change"], (int, float))
        
        # Check CTR trend structure
        if "ctr_trend" in trends:
            ctr_trend = trends["ctr_trend"]
            assert isinstance(ctr_trend, dict)
            assert "direction" in ctr_trend
            assert isinstance(ctr_trend["direction"], str)
            assert "week_over_week_change" in ctr_trend
            assert isinstance(ctr_trend["week_over_week_change"], (int, float))
            assert "month_over_month_change" in ctr_trend
            assert isinstance(ctr_trend["month_over_month_change"], (int, float))
        
    finally:
        os.unlink(csv_path)
