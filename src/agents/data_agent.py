"""
Data Agent for loading, validating, and analyzing Facebook Ads datasets.

This agent handles dataset loading from CSV, data quality checks, metric calculations,
trend analysis, and segmentation.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
import hashlib

from src.schemas.validation import ValidationError, validate_required_fields
from src.utils.logger import setup_logger


class DataAgent:
    """Agent responsible for data loading, validation, and analysis."""
    
    # Required fields in the dataset
    REQUIRED_FIELDS = [
        "campaign_name",
        "date",
        "spend",
        "impressions",
        "clicks",
        "revenue",
    ]
    
    # Additional expected fields
    EXPECTED_FIELDS = [
        "adset_name",
        "ctr",
        "purchases",
        "roas",
        "creative_type",
        "creative_message",
        "audience_type",
        "platform",
        "country",
    ]
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Data Agent.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = setup_logger(
            "data_agent",
            log_level=config.get("logging", {}).get("level", "INFO"),
            log_format=config.get("logging", {}).get("format", "json"),
            log_dir=config.get("logging", {}).get("log_dir", "logs"),
        )
        self._dataset_cache: Optional[pd.DataFrame] = None
        self._cache_key: Optional[str] = None
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data agent workflow.
        
        Args:
            input_data: Input containing dataset_path, date_range, metrics, config
            
        Returns:
            Data agent output with summary, metrics, trends, segmentation
        """
        start_time = datetime.utcnow()
        
        try:
            # Extract input parameters
            dataset_path = input_data["dataset_path"]
            date_range = input_data.get("date_range")
            metrics = input_data.get("metrics", [])
            
            # Load and validate dataset
            df, data_quality_issues = self._load_and_validate_dataset(dataset_path)
            
            # Filter by date range if specified
            if date_range:
                df = self._filter_by_date_range(df, date_range)
            
            # Compute dataset summary
            dataset_summary = self._compute_dataset_summary(df, data_quality_issues)
            
            # Compute metrics
            computed_metrics = self._compute_metrics(df)
            
            # Compute trends
            trends = self._compute_trends(df)
            
            # Compute segmentation
            segmentation = self._compute_segmentation(df)
            
            # Calculate execution duration
            execution_duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            # Build output
            output = {
                "agent_name": "data_agent",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "execution_duration_ms": execution_duration_ms,
                "dataset_summary": dataset_summary,
                "metrics": computed_metrics,
                "trends": trends,
                "segmentation": segmentation,
                "data_quality_issues": data_quality_issues,
            }
            
            self.logger.info(
                f"Data Agent completed successfully",
                extra={
                    "agent_name": "data_agent",
                    "execution_duration_ms": execution_duration_ms,
                    "rows_processed": len(df),
                }
            )
            
            return output
            
        except Exception as e:
            self.logger.error(
                f"Data Agent execution failed: {str(e)}",
                extra={"agent_name": "data_agent", "error_type": type(e).__name__},
                exc_info=True
            )
            raise
    
    def _load_and_validate_dataset(self, dataset_path: str) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
        """Load dataset from CSV and perform validation.
        
        Args:
            dataset_path: Path to CSV file
            
        Returns:
            Tuple of (DataFrame, list of data quality issues)
            
        Raises:
            ValidationError: If required fields are missing or file not found
        """
        # Check if dataset is already cached
        cache_key = self._compute_cache_key(dataset_path)
        if self._cache_key == cache_key and self._dataset_cache is not None:
            self.logger.info("Using cached dataset")
            return self._dataset_cache, []
        
        # Check if file exists
        if not Path(dataset_path).exists():
            raise ValidationError(
                f"Dataset file not found: {dataset_path}",
                {"dataset_path": dataset_path}
            )
        
        data_quality_issues = []
        
        try:
            # Load CSV
            df = pd.read_csv(dataset_path)
            
            # Validate required fields
            missing_fields = [field for field in self.REQUIRED_FIELDS if field not in df.columns]
            if missing_fields:
                raise ValidationError(
                    f"Missing required fields in dataset",
                    {"missing_fields": missing_fields, "required_fields": self.REQUIRED_FIELDS}
                )
            
            # Track original row count
            original_rows = len(df)
            
            # Handle missing values
            df, missing_issues = self._handle_missing_values(df)
            data_quality_issues.extend(missing_issues)
            
            # Handle date parsing
            df, date_issues = self._handle_date_parsing(df)
            data_quality_issues.extend(date_issues)
            
            # Handle numeric fields
            df, numeric_issues = self._handle_numeric_fields(df)
            data_quality_issues.extend(numeric_issues)
            
            # Log data quality summary
            rows_removed = original_rows - len(df)
            if rows_removed > 0:
                self.logger.warning(
                    f"Removed {rows_removed} rows due to data quality issues",
                    extra={"rows_removed": rows_removed, "original_rows": original_rows}
                )
            
            # Cache the dataset
            self._dataset_cache = df
            self._cache_key = cache_key
            
            return df, data_quality_issues
            
        except pd.errors.EmptyDataError:
            raise ValidationError("Dataset file is empty", {"dataset_path": dataset_path})
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(
                f"Failed to load dataset: {str(e)}",
                {"dataset_path": dataset_path, "error": str(e)}
            )
    
    def _compute_cache_key(self, dataset_path: str) -> str:
        """Compute cache key for dataset.
        
        Args:
            dataset_path: Path to dataset file
            
        Returns:
            MD5 hash of file path and modification time
        """
        path = Path(dataset_path)
        if path.exists():
            mtime = path.stat().st_mtime
            key_str = f"{dataset_path}:{mtime}"
        else:
            key_str = dataset_path
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _handle_missing_values(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
        """Handle missing values in dataset.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Tuple of (cleaned DataFrame, list of issues)
        """
        issues = []
        
        # Check for missing values in required fields
        for field in self.REQUIRED_FIELDS:
            if field in df.columns:
                missing_count = df[field].isna().sum()
                if missing_count > 0:
                    issues.append({
                        "issue_type": "missing_values",
                        "field": field,
                        "count": int(missing_count),
                        "action": "excluded_rows"
                    })
                    self.logger.warning(
                        f"Found {missing_count} missing values in required field '{field}'",
                        extra={"field": field, "missing_count": int(missing_count)}
                    )
        
        # Remove rows with missing required fields
        df_cleaned = df.dropna(subset=self.REQUIRED_FIELDS)
        
        return df_cleaned, issues
    
    def _handle_date_parsing(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
        """Handle date parsing and validation.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Tuple of (DataFrame with parsed dates, list of issues)
        """
        issues = []
        date_format = self.config.get("data_quality", {}).get("date_format", "%Y-%m-%d")
        
        if "date" not in df.columns:
            return df, issues
        
        # Try to parse dates
        invalid_dates = []
        parsed_dates = []
        
        for idx, date_val in enumerate(df["date"]):
            try:
                if pd.isna(date_val):
                    parsed_dates.append(pd.NaT)
                else:
                    parsed_date = pd.to_datetime(date_val, format=date_format, errors='coerce')
                    if pd.isna(parsed_date):
                        invalid_dates.append((idx, date_val))
                        parsed_dates.append(pd.NaT)
                    else:
                        parsed_dates.append(parsed_date)
            except Exception as e:
                invalid_dates.append((idx, date_val))
                parsed_dates.append(pd.NaT)
                self.logger.warning(
                    f"Failed to parse date at row {idx}: {date_val}",
                    extra={"row": idx, "value": str(date_val), "error": str(e)}
                )
        
        df["date"] = parsed_dates
        
        if invalid_dates:
            issues.append({
                "issue_type": "invalid_dates",
                "count": len(invalid_dates),
                "action": "excluded_rows",
                "examples": [{"row": idx, "value": str(val)} for idx, val in invalid_dates[:5]]
            })
        
        # Remove rows with invalid dates
        df_cleaned = df.dropna(subset=["date"])
        
        return df_cleaned, issues
    
    def _handle_numeric_fields(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
        """Handle numeric field validation and conversion.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Tuple of (DataFrame with validated numerics, list of issues)
        """
        issues = []
        numeric_fields = ["spend", "impressions", "clicks", "revenue", "purchases", "ctr", "roas"]
        
        for field in numeric_fields:
            if field not in df.columns:
                continue
            
            # Try to convert to numeric
            original_values = df[field].copy()
            df[field] = pd.to_numeric(df[field], errors='coerce')
            
            # Check for conversion failures
            conversion_failures = original_values[df[field].isna() & original_values.notna()]
            if len(conversion_failures) > 0:
                issues.append({
                    "issue_type": "non_numeric_values",
                    "field": field,
                    "count": len(conversion_failures),
                    "action": "converted_to_nan",
                    "examples": conversion_failures.head(5).tolist()
                })
                self.logger.warning(
                    f"Found {len(conversion_failures)} non-numeric values in field '{field}'",
                    extra={"field": field, "count": len(conversion_failures)}
                )
        
        return df, issues
    
    def _filter_by_date_range(self, df: pd.DataFrame, date_range: Dict[str, str]) -> pd.DataFrame:
        """Filter dataset by date range.
        
        Args:
            df: Input DataFrame
            date_range: Dictionary with 'start_date' and 'end_date'
            
        Returns:
            Filtered DataFrame
        """
        if "start_date" in date_range:
            start_date = pd.to_datetime(date_range["start_date"])
            df = df[df["date"] >= start_date]
        
        if "end_date" in date_range:
            end_date = pd.to_datetime(date_range["end_date"])
            df = df[df["date"] <= end_date]
        
        return df
    
    def _compute_dataset_summary(self, df: pd.DataFrame, data_quality_issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compute dataset summary statistics.
        
        Args:
            df: Input DataFrame
            data_quality_issues: List of data quality issues
            
        Returns:
            Dataset summary dictionary
        """
        summary = {
            "total_rows": len(df),
            "date_range": {
                "start": df["date"].min().strftime("%Y-%m-%d") if len(df) > 0 else None,
                "end": df["date"].max().strftime("%Y-%m-%d") if len(df) > 0 else None,
            },
            "total_spend": float(df["spend"].sum()) if "spend" in df.columns else 0.0,
            "total_revenue": float(df["revenue"].sum()) if "revenue" in df.columns else 0.0,
            "campaigns_count": int(df["campaign_name"].nunique()) if "campaign_name" in df.columns else 0,
            "data_quality": {
                "missing_values": self._count_missing_values(df),
                "invalid_rows": sum(issue["count"] for issue in data_quality_issues if "count" in issue)
            }
        }
        
        return summary
    
    def _count_missing_values(self, df: pd.DataFrame) -> Dict[str, int]:
        """Count missing values by field.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Dictionary mapping field names to missing value counts
        """
        missing = {}
        for col in df.columns:
            count = int(df[col].isna().sum())
            if count > 0:
                missing[col] = count
        return missing
    
    def _compute_metrics(self, df: pd.DataFrame) -> Dict[str, float]:
        """Compute aggregate metrics.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Dictionary of computed metrics
        """
        metrics = {}
        
        # Overall ROAS
        total_spend = df["spend"].sum()
        total_revenue = df["revenue"].sum()
        metrics["overall_roas"] = float(total_revenue / total_spend) if total_spend > 0 else 0.0
        
        # Overall CTR
        total_impressions = df["impressions"].sum()
        total_clicks = df["clicks"].sum()
        metrics["overall_ctr"] = float(total_clicks / total_impressions) if total_impressions > 0 else 0.0
        
        # Average CPC
        metrics["avg_cpc"] = float(total_spend / total_clicks) if total_clicks > 0 else 0.0
        
        # Conversion rate
        if "purchases" in df.columns:
            total_purchases = df["purchases"].sum()
            metrics["conversion_rate"] = float(total_purchases / total_clicks) if total_clicks > 0 else 0.0
        else:
            metrics["conversion_rate"] = 0.0
        
        return metrics
    
    def _compute_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Compute trend analysis (WoW, MoM changes).
        
        Args:
            df: Input DataFrame
            
        Returns:
            Dictionary of trend data
        """
        trends = {}
        
        # Ensure date column is datetime
        if "date" not in df.columns or len(df) == 0:
            return trends
        
        df = df.sort_values("date")
        
        # Compute ROAS trend
        trends["roas_trend"] = self._compute_metric_trend(df, "roas")
        
        # Compute CTR trend
        trends["ctr_trend"] = self._compute_metric_trend(df, "ctr")
        
        return trends
    
    def _compute_metric_trend(self, df: pd.DataFrame, metric: str) -> Dict[str, Any]:
        """Compute trend for a specific metric.
        
        Args:
            df: Input DataFrame (sorted by date)
            metric: Metric name to analyze
            
        Returns:
            Trend dictionary with direction and changes
        """
        trend = {
            "direction": "stable",
            "week_over_week_change": 0.0,
            "month_over_month_change": 0.0
        }
        
        if metric not in df.columns or len(df) == 0:
            return trend
        
        # Group by week
        df["week"] = df["date"].dt.to_period("W")
        weekly_data = df.groupby("week").agg({
            "spend": "sum",
            "revenue": "sum",
            "impressions": "sum",
            "clicks": "sum"
        })
        
        # Compute metric for each week
        if metric == "roas":
            weekly_metric = weekly_data["revenue"] / weekly_data["spend"].replace(0, np.nan)
        elif metric == "ctr":
            weekly_metric = weekly_data["clicks"] / weekly_data["impressions"].replace(0, np.nan)
        else:
            weekly_metric = df.groupby("week")[metric].mean()
        
        # Week-over-week change
        if len(weekly_metric) >= 2:
            last_week = weekly_metric.iloc[-1]
            prev_week = weekly_metric.iloc[-2]
            if not pd.isna(prev_week) and prev_week != 0:
                wow_change = ((last_week - prev_week) / prev_week) * 100
                trend["week_over_week_change"] = float(wow_change)
        
        # Group by month
        df["month"] = df["date"].dt.to_period("M")
        monthly_data = df.groupby("month").agg({
            "spend": "sum",
            "revenue": "sum",
            "impressions": "sum",
            "clicks": "sum"
        })
        
        # Compute metric for each month
        if metric == "roas":
            monthly_metric = monthly_data["revenue"] / monthly_data["spend"].replace(0, np.nan)
        elif metric == "ctr":
            monthly_metric = monthly_data["clicks"] / monthly_data["impressions"].replace(0, np.nan)
        else:
            monthly_metric = df.groupby("month")[metric].mean()
        
        # Month-over-month change
        if len(monthly_metric) >= 2:
            last_month = monthly_metric.iloc[-1]
            prev_month = monthly_metric.iloc[-2]
            if not pd.isna(prev_month) and prev_month != 0:
                mom_change = ((last_month - prev_month) / prev_month) * 100
                trend["month_over_month_change"] = float(mom_change)
        
        # Classify trend direction
        threshold = self.config.get("thresholds", {}).get("trend_stable_threshold", 0.05) * 100
        avg_change = (abs(trend["week_over_week_change"]) + abs(trend["month_over_month_change"])) / 2
        
        if avg_change > threshold:
            if trend["week_over_week_change"] > 0 or trend["month_over_month_change"] > 0:
                trend["direction"] = "increasing"
            else:
                trend["direction"] = "decreasing"
        else:
            trend["direction"] = "stable"
        
        return trend
    
    def _compute_segmentation(self, df: pd.DataFrame) -> Dict[str, List[Dict[str, Any]]]:
        """Compute segmentation analysis.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Dictionary of segmentation data
        """
        segmentation = {}
        
        # Segment by campaign
        if "campaign_name" in df.columns:
            segmentation["by_campaign"] = self._segment_by_field(df, "campaign_name")
        
        # Segment by creative type
        if "creative_type" in df.columns:
            segmentation["by_creative_type"] = self._segment_by_field(df, "creative_type")
        
        # Segment by audience type
        if "audience_type" in df.columns:
            segmentation["by_audience_type"] = self._segment_by_field(df, "audience_type")
        
        # Segment by platform
        if "platform" in df.columns:
            segmentation["by_platform"] = self._segment_by_field(df, "platform")
        
        return segmentation
    
    def _segment_by_field(self, df: pd.DataFrame, field: str) -> List[Dict[str, Any]]:
        """Segment data by a specific field.
        
        Args:
            df: Input DataFrame
            field: Field name to segment by
            
        Returns:
            List of segment dictionaries
        """
        segments = []
        
        for value in df[field].unique():
            if pd.isna(value):
                continue
            
            segment_df = df[df[field] == value]
            
            total_spend = segment_df["spend"].sum()
            total_revenue = segment_df["revenue"].sum()
            total_impressions = segment_df["impressions"].sum()
            total_clicks = segment_df["clicks"].sum()
            
            segment = {
                field: str(value),
                "spend": float(total_spend),
                "revenue": float(total_revenue),
                "roas": float(total_revenue / total_spend) if total_spend > 0 else 0.0,
                "impressions": int(total_impressions),
                "clicks": int(total_clicks),
                "ctr": float(total_clicks / total_impressions) if total_impressions > 0 else 0.0,
            }
            
            segments.append(segment)
        
        # Sort by spend descending
        segments.sort(key=lambda x: x["spend"], reverse=True)
        
        return segments
