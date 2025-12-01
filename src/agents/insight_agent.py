"""
Insight Agent for generating hypotheses about performance changes.

This agent analyzes data patterns and trends to generate hypotheses
explaining ROAS/CTR changes with confidence scores.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.schemas.validation import validate_agent_input, validate_agent_output
from src.schemas.agent_io import INSIGHT_AGENT_INPUT_SCHEMA, INSIGHT_AGENT_OUTPUT_SCHEMA
from src.utils.logger import setup_logger


class InsightAgent:
    """Agent responsible for generating hypotheses about performance changes."""
    
    # Hypothesis categories
    CATEGORIES = ["creative", "audience", "platform", "budget", "seasonality"]
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Insight Agent.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.agent_name = "insight_agent"
        self.logger = setup_logger(
            self.agent_name,
            log_level=config.get("logging", {}).get("level", "INFO"),
            log_format=config.get("logging", {}).get("format", "json"),
            log_dir=config.get("logging", {}).get("log_dir", "logs"),
        )
        self.max_hypotheses = config.get("agents", {}).get("max_hypotheses", 5)
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute insight agent workflow.
        
        Args:
            input_data: Input containing data_summary, focus_metric, time_period, config
            
        Returns:
            Insight agent output with hypotheses and reasoning
        """
        start_time = datetime.utcnow()
        
        try:
            # Validate input
            validate_agent_input(input_data, INSIGHT_AGENT_INPUT_SCHEMA, self.agent_name)
            
            # Extract input parameters
            data_summary = input_data["data_summary"]
            focus_metric = input_data.get("focus_metric", "roas")
            time_period = input_data.get("time_period", {})
            
            # Generate hypotheses
            hypotheses = self._generate_hypotheses(data_summary, focus_metric, time_period)
            
            # Generate reasoning
            reasoning = self._generate_reasoning(data_summary, focus_metric, hypotheses)
            
            # Calculate execution duration
            execution_duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            # Build output
            output = {
                "agent_name": self.agent_name,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "execution_duration_ms": execution_duration_ms,
                "hypotheses": hypotheses,
                "reasoning": reasoning,
            }
            
            # Validate output
            validate_agent_output(output, INSIGHT_AGENT_OUTPUT_SCHEMA, self.agent_name)
            
            self.logger.info(
                f"Insight Agent completed successfully",
                extra={
                    "agent_name": self.agent_name,
                    "execution_duration_ms": execution_duration_ms,
                    "hypotheses_count": len(hypotheses),
                }
            )
            
            return output
            
        except Exception as e:
            self.logger.error(
                f"Insight Agent execution failed: {str(e)}",
                extra={"agent_name": self.agent_name, "error_type": type(e).__name__},
                exc_info=True
            )
            raise
    
    def _generate_hypotheses(
        self,
        data_summary: Dict[str, Any],
        focus_metric: str,
        time_period: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate hypotheses based on data patterns and trends.
        
        Args:
            data_summary: Data summary from Data Agent
            focus_metric: Metric to focus on (roas, ctr, etc.)
            time_period: Time period for analysis
            
        Returns:
            List of hypothesis dictionaries
        """
        hypotheses = []
        
        # Extract relevant data
        metrics = data_summary.get("metrics", {})
        trends = data_summary.get("trends", {})
        segmentation = data_summary.get("segmentation", {})
        
        # Generate hypotheses based on trends
        hypotheses.extend(self._generate_trend_hypotheses(trends, focus_metric))
        
        # Generate hypotheses based on segmentation
        hypotheses.extend(self._generate_segmentation_hypotheses(segmentation, focus_metric, metrics))
        
        # Generate hypotheses based on creative performance
        hypotheses.extend(self._generate_creative_hypotheses(segmentation, metrics))
        
        # Generate hypotheses based on audience performance
        hypotheses.extend(self._generate_audience_hypotheses(segmentation, metrics))
        
        # Generate hypotheses based on platform performance
        hypotheses.extend(self._generate_platform_hypotheses(segmentation, metrics))
        
        # Limit to max_hypotheses
        hypotheses = hypotheses[:self.max_hypotheses]
        
        # Ensure we have at least 3 hypotheses
        while len(hypotheses) < 3:
            hypotheses.append(self._generate_default_hypothesis(focus_metric, len(hypotheses)))
        
        return hypotheses
    
    def _generate_trend_hypotheses(
        self,
        trends: Dict[str, Any],
        focus_metric: str
    ) -> List[Dict[str, Any]]:
        """Generate hypotheses based on trend data.
        
        Args:
            trends: Trend data from Data Agent
            focus_metric: Metric to focus on
            
        Returns:
            List of trend-based hypotheses
        """
        hypotheses = []
        
        # Check ROAS trend
        if "roas_trend" in trends:
            roas_trend = trends["roas_trend"]
            direction = roas_trend.get("direction", "stable")
            wow_change = roas_trend.get("week_over_week_change", 0)
            mom_change = roas_trend.get("month_over_month_change", 0)
            
            # Check for significant changes (>5% in either direction)
            has_significant_change = abs(wow_change) > 5 or abs(mom_change) > 5
            
            if has_significant_change:
                if wow_change < -5 or mom_change < -5:
                    # Declining trend
                    hypothesis = {
                        "hypothesis_id": str(uuid.uuid4()),
                        "hypothesis_text": f"ROAS declined due to trend (WoW: {wow_change:.1f}%, MoM: {mom_change:.1f}%)",
                        "category": "seasonality",
                        "supporting_observations": [
                            f"Week-over-week ROAS change: {wow_change:.1f}%",
                            f"Month-over-month ROAS change: {mom_change:.1f}%",
                            f"Trend direction: {direction}"
                        ],
                        "evidence_used": ["roas_trend", "week_over_week_change", "month_over_month_change"],
                        "confidence_score": self._calculate_initial_confidence(abs(wow_change) + abs(mom_change), 20),
                        "testable": True,
                        "validation_approach": "Compare ROAS across time periods and validate trend direction"
                    }
                    hypotheses.append(hypothesis)
                elif wow_change > 5 or mom_change > 5:
                    # Increasing trend
                    hypothesis = {
                        "hypothesis_id": str(uuid.uuid4()),
                        "hypothesis_text": f"ROAS improved due to trend (WoW: {wow_change:.1f}%, MoM: {mom_change:.1f}%)",
                        "category": "seasonality",
                        "supporting_observations": [
                            f"Week-over-week ROAS change: {wow_change:.1f}%",
                            f"Month-over-month ROAS change: {mom_change:.1f}%",
                            f"Trend direction: {direction}"
                        ],
                        "evidence_used": ["roas_trend", "week_over_week_change", "month_over_month_change"],
                        "confidence_score": self._calculate_initial_confidence(abs(wow_change) + abs(mom_change), 20),
                        "testable": True,
                        "validation_approach": "Compare ROAS across time periods and validate trend direction"
                    }
                    hypotheses.append(hypothesis)
        
        # Check CTR trend
        if "ctr_trend" in trends:
            ctr_trend = trends["ctr_trend"]
            direction = ctr_trend.get("direction", "stable")
            wow_change = ctr_trend.get("week_over_week_change", 0)
            mom_change = ctr_trend.get("month_over_month_change", 0)
            
            # Check if there's a significant change (>5% in either direction)
            has_significant_change = abs(wow_change) > 5 or abs(mom_change) > 5
            
            if has_significant_change:
                if wow_change < 0 or mom_change < 0:
                    # Declining trend
                    hypothesis = {
                        "hypothesis_id": str(uuid.uuid4()),
                        "hypothesis_text": f"CTR decline (WoW: {wow_change:.1f}%, MoM: {mom_change:.1f}%) negatively impacted {focus_metric.upper()}",
                        "category": "creative",
                        "supporting_observations": [
                            f"Week-over-week CTR change: {wow_change:.1f}%",
                            f"Month-over-month CTR change: {mom_change:.1f}%",
                            f"CTR trend direction: {direction}"
                        ],
                        "evidence_used": ["ctr_trend", "week_over_week_change", "month_over_month_change"],
                        "confidence_score": self._calculate_initial_confidence(abs(wow_change) + abs(mom_change), 20),
                        "testable": True,
                        "validation_approach": "Correlate CTR changes with ROAS changes across segments"
                    }
                    hypotheses.append(hypothesis)
                else:
                    # Increasing trend
                    hypothesis = {
                        "hypothesis_id": str(uuid.uuid4()),
                        "hypothesis_text": f"CTR improvement (WoW: {wow_change:.1f}%, MoM: {mom_change:.1f}%) positively impacted {focus_metric.upper()}",
                        "category": "creative",
                        "supporting_observations": [
                            f"Week-over-week CTR change: {wow_change:.1f}%",
                            f"Month-over-month CTR change: {mom_change:.1f}%",
                            f"CTR trend direction: {direction}"
                        ],
                        "evidence_used": ["ctr_trend", "week_over_week_change", "month_over_month_change"],
                        "confidence_score": self._calculate_initial_confidence(abs(wow_change) + abs(mom_change), 20),
                        "testable": True,
                        "validation_approach": "Correlate CTR changes with ROAS changes across segments"
                    }
                    hypotheses.append(hypothesis)
        
        return hypotheses
    
    def _generate_segmentation_hypotheses(
        self,
        segmentation: Dict[str, Any],
        focus_metric: str,
        metrics: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate hypotheses based on segmentation data.
        
        Args:
            segmentation: Segmentation data from Data Agent
            focus_metric: Metric to focus on
            metrics: Overall metrics
            
        Returns:
            List of segmentation-based hypotheses
        """
        hypotheses = []
        
        # Analyze campaign segmentation
        if "by_campaign" in segmentation and segmentation["by_campaign"]:
            campaigns = segmentation["by_campaign"]
            overall_roas = metrics.get("overall_roas", 0)
            
            # Find underperforming campaigns
            underperforming = [c for c in campaigns if c.get("roas", 0) < overall_roas * 0.8]
            
            if underperforming and len(underperforming) > 0:
                worst_campaign = min(underperforming, key=lambda x: x.get("roas", 0))
                campaign_name = worst_campaign.get("campaign_name", "Unknown")
                campaign_roas = worst_campaign.get("roas", 0)
                
                hypothesis = {
                    "hypothesis_id": str(uuid.uuid4()),
                    "hypothesis_text": f"Campaign '{campaign_name}' underperformance (ROAS: {campaign_roas:.2f}) is dragging down overall {focus_metric.upper()}",
                    "category": "budget",
                    "supporting_observations": [
                        f"Campaign ROAS: {campaign_roas:.2f} vs Overall: {overall_roas:.2f}",
                        f"Number of underperforming campaigns: {len(underperforming)}",
                        f"Campaign spend: ${worst_campaign.get('spend', 0):.2f}"
                    ],
                    "evidence_used": ["campaign_segmentation", "roas_by_campaign"],
                    "confidence_score": self._calculate_initial_confidence(
                        abs(overall_roas - campaign_roas) / max(overall_roas, 0.01) * 100,
                        50
                    ),
                    "testable": True,
                    "validation_approach": "Compare campaign performance metrics and validate impact on overall ROAS"
                }
                hypotheses.append(hypothesis)
        
        return hypotheses
    
    def _generate_creative_hypotheses(
        self,
        segmentation: Dict[str, Any],
        metrics: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate hypotheses based on creative performance.
        
        Args:
            segmentation: Segmentation data
            metrics: Overall metrics
            
        Returns:
            List of creative-based hypotheses
        """
        hypotheses = []
        
        if "by_creative_type" in segmentation and segmentation["by_creative_type"]:
            creative_types = segmentation["by_creative_type"]
            overall_ctr = metrics.get("overall_ctr", 0)
            
            # Find creative types with low CTR
            low_ctr_creatives = [c for c in creative_types if c.get("ctr", 0) < overall_ctr * 0.8]
            
            if low_ctr_creatives:
                worst_creative = min(low_ctr_creatives, key=lambda x: x.get("ctr", 0))
                creative_type = worst_creative.get("creative_type", "Unknown")
                creative_ctr = worst_creative.get("ctr", 0)
                
                hypothesis = {
                    "hypothesis_id": str(uuid.uuid4()),
                    "hypothesis_text": f"'{creative_type}' creative type underperforming with CTR of {creative_ctr:.4f} vs overall {overall_ctr:.4f}",
                    "category": "creative",
                    "supporting_observations": [
                        f"Creative type CTR: {creative_ctr:.4f}",
                        f"Overall CTR: {overall_ctr:.4f}",
                        f"CTR gap: {((overall_ctr - creative_ctr) / max(overall_ctr, 0.0001) * 100):.1f}%"
                    ],
                    "evidence_used": ["creative_type_segmentation", "ctr_by_creative_type"],
                    "confidence_score": self._calculate_initial_confidence(
                        abs(overall_ctr - creative_ctr) / max(overall_ctr, 0.0001) * 100,
                        50
                    ),
                    "testable": True,
                    "validation_approach": "Compare creative type performance and test correlation with overall metrics"
                }
                hypotheses.append(hypothesis)
        
        return hypotheses
    
    def _generate_audience_hypotheses(
        self,
        segmentation: Dict[str, Any],
        metrics: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate hypotheses based on audience performance.
        
        Args:
            segmentation: Segmentation data
            metrics: Overall metrics
            
        Returns:
            List of audience-based hypotheses
        """
        hypotheses = []
        
        if "by_audience_type" in segmentation and segmentation["by_audience_type"]:
            audiences = segmentation["by_audience_type"]
            overall_roas = metrics.get("overall_roas", 0)
            
            # Find audiences with low ROAS
            low_roas_audiences = [a for a in audiences if a.get("roas", 0) < overall_roas * 0.7]
            
            if low_roas_audiences:
                worst_audience = min(low_roas_audiences, key=lambda x: x.get("roas", 0))
                audience_type = worst_audience.get("audience_type", "Unknown")
                audience_roas = worst_audience.get("roas", 0)
                
                hypothesis = {
                    "hypothesis_id": str(uuid.uuid4()),
                    "hypothesis_text": f"Audience segment '{audience_type}' showing poor ROAS of {audience_roas:.2f} compared to overall {overall_roas:.2f}",
                    "category": "audience",
                    "supporting_observations": [
                        f"Audience ROAS: {audience_roas:.2f}",
                        f"Overall ROAS: {overall_roas:.2f}",
                        f"Performance gap: {((overall_roas - audience_roas) / max(overall_roas, 0.01) * 100):.1f}%"
                    ],
                    "evidence_used": ["audience_segmentation", "roas_by_audience"],
                    "confidence_score": self._calculate_initial_confidence(
                        abs(overall_roas - audience_roas) / max(overall_roas, 0.01) * 100,
                        50
                    ),
                    "testable": True,
                    "validation_approach": "Compare audience segment performance and validate impact on overall ROAS"
                }
                hypotheses.append(hypothesis)
        
        return hypotheses
    
    def _generate_platform_hypotheses(
        self,
        segmentation: Dict[str, Any],
        metrics: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate hypotheses based on platform performance.
        
        Args:
            segmentation: Segmentation data
            metrics: Overall metrics
            
        Returns:
            List of platform-based hypotheses
        """
        hypotheses = []
        
        if "by_platform" in segmentation and segmentation["by_platform"]:
            platforms = segmentation["by_platform"]
            
            if len(platforms) >= 2:
                # Compare platforms
                platforms_sorted = sorted(platforms, key=lambda x: x.get("roas", 0))
                worst_platform = platforms_sorted[0]
                best_platform = platforms_sorted[-1]
                
                worst_name = worst_platform.get("platform", "Unknown")
                best_name = best_platform.get("platform", "Unknown")
                worst_roas = worst_platform.get("roas", 0)
                best_roas = best_platform.get("roas", 0)
                
                if best_roas > worst_roas * 1.2:  # At least 20% difference
                    hypothesis = {
                        "hypothesis_id": str(uuid.uuid4()),
                        "hypothesis_text": f"Platform '{worst_name}' (ROAS: {worst_roas:.2f}) underperforming compared to '{best_name}' (ROAS: {best_roas:.2f})",
                        "category": "platform",
                        "supporting_observations": [
                            f"{worst_name} ROAS: {worst_roas:.2f}",
                            f"{best_name} ROAS: {best_roas:.2f}",
                            f"Performance gap: {((best_roas - worst_roas) / max(worst_roas, 0.01) * 100):.1f}%"
                        ],
                        "evidence_used": ["platform_segmentation", "roas_by_platform"],
                        "confidence_score": self._calculate_initial_confidence(
                            abs(best_roas - worst_roas) / max(worst_roas, 0.01) * 100,
                            50
                        ),
                        "testable": True,
                        "validation_approach": "Compare platform performance metrics and validate statistical significance"
                    }
                    hypotheses.append(hypothesis)
        
        return hypotheses
    
    def _generate_default_hypothesis(self, focus_metric: str, index: int) -> Dict[str, Any]:
        """Generate a default hypothesis when not enough data is available.
        
        Args:
            focus_metric: Metric to focus on
            index: Index for unique ID
            
        Returns:
            Default hypothesis dictionary
        """
        default_hypotheses = [
            {
                "hypothesis_text": f"Seasonal factors may be influencing {focus_metric.upper()} performance",
                "category": "seasonality",
                "supporting_observations": ["Limited historical data available for trend analysis"],
                "evidence_used": ["time_period"],
                "confidence_score": 0.4,
                "validation_approach": "Collect more historical data to identify seasonal patterns"
            },
            {
                "hypothesis_text": f"Ad fatigue may be contributing to {focus_metric.upper()} changes",
                "category": "creative",
                "supporting_observations": ["Creative performance may degrade over time"],
                "evidence_used": ["creative_age"],
                "confidence_score": 0.35,
                "validation_approach": "Analyze creative performance over time and test refresh impact"
            },
            {
                "hypothesis_text": f"Market competition changes may be affecting {focus_metric.upper()}",
                "category": "budget",
                "supporting_observations": ["External market factors can impact performance"],
                "evidence_used": ["market_conditions"],
                "confidence_score": 0.3,
                "validation_approach": "Monitor competitive landscape and correlate with performance changes"
            }
        ]
        
        hypothesis = default_hypotheses[index % len(default_hypotheses)].copy()
        hypothesis["hypothesis_id"] = str(uuid.uuid4())
        hypothesis["testable"] = True
        
        return hypothesis
    
    def _calculate_initial_confidence(self, magnitude: float, max_magnitude: float) -> float:
        """Calculate initial confidence score based on data availability and magnitude.
        
        Args:
            magnitude: Magnitude of the change or difference
            max_magnitude: Maximum expected magnitude for normalization
            
        Returns:
            Confidence score between 0 and 1
        """
        # Normalize magnitude to 0-1 range
        normalized = min(magnitude / max_magnitude, 1.0)
        
        # Map to confidence range 0.3-0.8 (initial confidence before validation)
        confidence = 0.3 + (normalized * 0.5)
        
        # Ensure bounds
        return max(0.0, min(1.0, confidence))
    
    def _generate_reasoning(
        self,
        data_summary: Dict[str, Any],
        focus_metric: str,
        hypotheses: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """Generate reasoning structure for insight agent output.
        
        Args:
            data_summary: Data summary from Data Agent
            focus_metric: Metric being analyzed
            hypotheses: Generated hypotheses
            
        Returns:
            Reasoning dict with think, analyze, conclude sections
        """
        # Think section
        think = f"Analyzing data to understand {focus_metric.upper()} performance changes. "
        
        metrics = data_summary.get("metrics", {})
        if focus_metric == "roas":
            current_value = metrics.get("overall_roas", 0)
            think += f"Current overall ROAS: {current_value:.2f}. "
        elif focus_metric == "ctr":
            current_value = metrics.get("overall_ctr", 0)
            think += f"Current overall CTR: {current_value:.4f}. "
        
        trends = data_summary.get("trends", {})
        if trends:
            think += "Trend data available for analysis. "
        
        segmentation = data_summary.get("segmentation", {})
        segment_count = sum(1 for v in segmentation.values() if v)
        think += f"Segmentation data available across {segment_count} dimensions. "
        
        # Analyze section
        analyze = "Data pattern analysis:\n"
        
        # Analyze trends
        if "roas_trend" in trends:
            roas_trend = trends["roas_trend"]
            analyze += f"- ROAS trend: {roas_trend.get('direction', 'unknown')} "
            analyze += f"(WoW: {roas_trend.get('week_over_week_change', 0):.1f}%, "
            analyze += f"MoM: {roas_trend.get('month_over_month_change', 0):.1f}%)\n"
        
        if "ctr_trend" in trends:
            ctr_trend = trends["ctr_trend"]
            analyze += f"- CTR trend: {ctr_trend.get('direction', 'unknown')} "
            analyze += f"(WoW: {ctr_trend.get('week_over_week_change', 0):.1f}%, "
            analyze += f"MoM: {ctr_trend.get('month_over_month_change', 0):.1f}%)\n"
        
        # Analyze segmentation
        for seg_type, seg_data in segmentation.items():
            if seg_data:
                analyze += f"- {seg_type}: {len(seg_data)} segments identified\n"
        
        analyze += f"\nGenerated {len(hypotheses)} hypotheses across categories: "
        categories = list(set(h["category"] for h in hypotheses))
        analyze += ", ".join(categories)
        
        # Conclude section
        conclude = f"Generated {len(hypotheses)} testable hypotheses to explain {focus_metric.upper()} performance. "
        
        # Identify top hypothesis by confidence
        if hypotheses:
            top_hypothesis = max(hypotheses, key=lambda h: h["confidence_score"])
            conclude += f"Top hypothesis (confidence: {top_hypothesis['confidence_score']:.2f}): "
            conclude += f"{top_hypothesis['hypothesis_text']}. "
        
        conclude += "These hypotheses require validation through the Evaluator Agent using quantitative metrics. "
        conclude += "Each hypothesis includes a validation approach for testing."
        
        return {
            "think": think,
            "analyze": analyze,
            "conclude": conclude
        }
