"""
Report Generator for creating Markdown reports from analysis results.

This agent synthesizes insights and creative recommendations into a
stakeholder-friendly Markdown report with sections for Executive Summary,
Key Insights, Creative Recommendations, and Methodology.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

from src.utils.logger import setup_logger


class ReportGenerator:
    """Agent responsible for generating Markdown reports from analysis results."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Report Generator.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.agent_name = "report_generator"
        self.logger = setup_logger(
            self.agent_name,
            log_level=config.get("logging", {}).get("level", "INFO"),
            log_format=config.get("logging", {}).get("format", "json"),
            log_dir=config.get("logging", {}).get("log_dir", "logs"),
        )
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute report generation workflow.
        
        Args:
            input_data: Input containing insights, creatives, data_summary, query
            
        Returns:
            Report generator output with report path and metadata
        """
        start_time = datetime.utcnow()
        
        try:
            # Extract input parameters
            insights = input_data.get("insights", {})
            creatives = input_data.get("creatives", {})
            data_summary = input_data.get("data_summary", {})
            query = input_data.get("query", "")
            
            # Generate report sections
            executive_summary = self._generate_executive_summary(
                insights, creatives, data_summary, query
            )
            
            key_insights_section = self._generate_key_insights_section(insights)
            
            creative_recommendations_section = self._generate_creative_recommendations_section(
                creatives
            )
            
            methodology_section = self._generate_methodology_section()
            
            # Combine sections into full report
            report_content = self._assemble_report(
                executive_summary,
                key_insights_section,
                creative_recommendations_section,
                methodology_section
            )
            
            # Write report to file
            report_path = self._write_report(report_content)
            
            # Calculate execution duration
            execution_duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            # Build output
            output = {
                "agent_name": self.agent_name,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "execution_duration_ms": execution_duration_ms,
                "report_path": report_path,
                "sections_generated": [
                    "Executive Summary",
                    "Key Insights",
                    "Creative Recommendations",
                    "Methodology"
                ],
            }
            
            self.logger.info(
                f"Report Generator completed successfully",
                extra={
                    "agent_name": self.agent_name,
                    "execution_duration_ms": execution_duration_ms,
                    "report_path": report_path,
                }
            )
            
            return output
            
        except Exception as e:
            self.logger.error(
                f"Report Generator execution failed: {str(e)}",
                extra={"agent_name": self.agent_name, "error_type": type(e).__name__},
                exc_info=True
            )
            raise
    
    def _generate_executive_summary(
        self,
        insights: Dict[str, Any],
        creatives: Dict[str, Any],
        data_summary: Dict[str, Any],
        query: str
    ) -> str:
        """Generate executive summary section.
        
        Args:
            insights: Validated hypotheses from Evaluator Agent
            creatives: Creative recommendations from Creative Generator
            data_summary: Dataset summary from Data Agent
            query: Original user query
            
        Returns:
            Executive summary markdown text
        """
        summary = "## Executive Summary\n\n"
        
        # Add query context
        if query:
            summary += f"**Analysis Request:** {query}\n\n"
        
        # Add dataset overview
        dataset_summary = data_summary.get("dataset_summary", {})
        if dataset_summary:
            total_rows = dataset_summary.get("total_rows", 0)
            date_range = dataset_summary.get("date_range", {})
            total_spend = dataset_summary.get("total_spend", 0)
            total_revenue = dataset_summary.get("total_revenue", 0)
            
            summary += f"**Dataset Overview:**\n"
            summary += f"- Period: {date_range.get('start', 'N/A')} to {date_range.get('end', 'N/A')}\n"
            summary += f"- Total Records: {total_rows:,}\n"
            summary += f"- Total Spend: ${total_spend:,.2f}\n"
            summary += f"- Total Revenue: ${total_revenue:,.2f}\n\n"
        
        # Add key findings
        validated_hypotheses = insights.get("validated_hypotheses", [])
        recommendations = creatives.get("recommendations", [])
        
        summary += f"**Key Findings:**\n"
        summary += f"- Identified {len(validated_hypotheses)} validated hypotheses explaining performance changes\n"
        summary += f"- Generated {len(recommendations)} creative recommendation sets for underperforming campaigns\n"
        
        # Add top insight if available
        if validated_hypotheses:
            top_hypothesis = validated_hypotheses[0]
            confidence = top_hypothesis.get("adjusted_confidence_score", 0)
            summary += f"- Top insight: {top_hypothesis.get('hypothesis_text', 'N/A')} (confidence: {confidence:.2f})\n"
        
        summary += "\n"
        
        return summary
    
    def _generate_key_insights_section(self, insights: Dict[str, Any]) -> str:
        """Generate key insights section with top 3 validated hypotheses.
        
        Args:
            insights: Validated hypotheses from Evaluator Agent
            
        Returns:
            Key insights markdown text
        """
        section = "## Key Insights\n\n"
        
        validated_hypotheses = insights.get("validated_hypotheses", [])
        
        if not validated_hypotheses:
            section += "*No validated hypotheses available.*\n\n"
            return section
        
        # Get top 3 hypotheses
        top_hypotheses = validated_hypotheses[:3]
        
        for i, hypothesis in enumerate(top_hypotheses, 1):
            hypothesis_text = hypothesis.get("hypothesis_text", "N/A")
            confidence = hypothesis.get("adjusted_confidence_score", 0)
            validation_status = hypothesis.get("validation_status", "unknown")
            
            section += f"### {i}. {hypothesis_text}\n\n"
            section += f"**Confidence Score:** {confidence:.2f}\n\n"
            section += f"**Validation Status:** {validation_status}\n\n"
            
            # Add evidence
            evidence = hypothesis.get("evidence", {})
            metrics = evidence.get("metrics", [])
            
            # Filter out metrics with empty or invalid data
            valid_metrics = []
            for metric in metrics:
                metric_name = str(metric.get("metric_name", "")).strip()
                comparison = str(metric.get("comparison", "")).strip()
                # Remove non-printable characters
                metric_name = ''.join(c for c in metric_name if c.isprintable())
                comparison = ''.join(c for c in comparison if c.isprintable())
                # Only include metrics with non-empty name and comparison
                if metric_name and comparison:
                    valid_metrics.append({
                        "metric_name": metric_name,
                        "value": metric.get("value", 0),
                        "comparison": comparison
                    })
            
            if valid_metrics:
                section += "**Supporting Metrics:**\n\n"
                section += "| Metric | Value | Comparison |\n"
                section += "|--------|-------|------------|\n"
                
                for metric in valid_metrics:
                    metric_name = metric.get("metric_name", "N/A")
                    value = metric.get("value", 0)
                    comparison = metric.get("comparison", "N/A")
                    
                    # Format value based on type
                    if isinstance(value, float):
                        value_str = f"{value:.4f}"
                    else:
                        value_str = str(value)
                    
                    section += f"| {metric_name} | {value_str} | {comparison} |\n"
                
                section += "\n"
            
            # Add statistical significance if available
            statistical_significance = evidence.get("statistical_significance", {})
            if statistical_significance:
                p_value = statistical_significance.get("p_value")
                if p_value is not None:
                    section += f"**Statistical Significance:** p-value = {p_value:.4f}\n\n"
            
            # Add validation reasoning
            validation_reasoning = hypothesis.get("validation_reasoning", "")
            if validation_reasoning:
                section += f"**Analysis:** {validation_reasoning}\n\n"
            
            section += "---\n\n"
        
        return section
    
    def _generate_creative_recommendations_section(
        self,
        creatives: Dict[str, Any]
    ) -> str:
        """Generate creative recommendations section.
        
        Args:
            creatives: Creative recommendations from Creative Generator
            
        Returns:
            Creative recommendations markdown text
        """
        section = "## Creative Recommendations\n\n"
        
        recommendations = creatives.get("recommendations", [])
        
        if not recommendations:
            section += "*No creative recommendations available.*\n\n"
            return section
        
        section += "The following campaigns have been identified as underperforming and would benefit from creative optimization:\n\n"
        
        for rec in recommendations:
            campaign = rec.get("campaign", "Unknown")
            current_ctr = rec.get("current_ctr", 0)
            current_creative_type = rec.get("current_creative_type", "unknown")
            new_creatives = rec.get("new_creatives", [])
            
            section += f"### Campaign: {campaign}\n\n"
            section += f"**Current Performance:**\n"
            section += f"- CTR: {current_ctr:.4f}\n"
            section += f"- Creative Type: {current_creative_type}\n\n"
            
            if new_creatives:
                section += "**Recommended Creative Variations:**\n\n"
                
                for i, creative in enumerate(new_creatives, 1):
                    creative_type = creative.get("creative_type", "unknown")
                    creative_message = creative.get("creative_message", "N/A")
                    audience_type = creative.get("audience_type", "default")
                    rationale = creative.get("rationale", "N/A")
                    confidence = creative.get("confidence_score", 0)
                    expected_improvement = creative.get("expected_ctr_improvement", 0)
                    
                    section += f"{i}. **{creative_type.capitalize()} Creative**\n"
                    section += f"   - **Message:** {creative_message}\n"
                    section += f"   - **Target Audience:** {audience_type}\n"
                    section += f"   - **Expected CTR Improvement:** +{expected_improvement:.1f}%\n"
                    section += f"   - **Confidence:** {confidence:.2f}\n"
                    section += f"   - **Rationale:** {rationale}\n\n"
            
            section += "---\n\n"
        
        return section
    
    def _generate_methodology_section(self) -> str:
        """Generate methodology section explaining the analysis approach.
        
        Returns:
            Methodology markdown text
        """
        section = "## Methodology\n\n"
        
        section += "This analysis was conducted using the Kasparro multi-agent system, "
        section += "which employs a structured approach to Facebook Ads performance analysis:\n\n"
        
        section += "### Analysis Pipeline\n\n"
        section += "1. **Data Loading & Validation**\n"
        section += "   - Dataset loaded and validated for completeness and quality\n"
        section += "   - Missing values handled and data quality issues logged\n"
        section += "   - Metrics computed: ROAS, CTR, conversion rates\n\n"
        
        section += "2. **Trend Analysis**\n"
        section += "   - Week-over-week and month-over-month changes calculated\n"
        section += "   - Trends classified as increasing, decreasing, or stable\n"
        section += "   - Segmentation performed by campaign, creative type, audience, and platform\n\n"
        
        section += "3. **Hypothesis Generation**\n"
        section += "   - Multiple hypotheses generated to explain performance changes\n"
        section += "   - Each hypothesis assigned an initial confidence score\n"
        section += "   - Hypotheses categorized by type (creative, audience, platform, budget, seasonality)\n\n"
        
        section += "4. **Hypothesis Validation**\n"
        section += "   - Each hypothesis validated using quantitative metrics from the dataset\n"
        section += "   - Statistical significance testing performed where applicable\n"
        section += "   - Confidence scores adjusted based on validation strength\n"
        section += "   - Hypotheses ranked by validation strength and confidence\n\n"
        
        section += "5. **Creative Recommendations**\n"
        section += "   - Low-CTR campaigns identified based on configured thresholds\n"
        section += "   - High-performing creative attributes analyzed\n"
        section += "   - Creative variations generated with audience targeting\n"
        section += "   - Expected improvements calculated based on historical performance\n\n"
        
        section += "### Confidence Scoring\n\n"
        section += "Confidence scores range from 0.0 to 1.0 and are calculated using:\n\n"
        section += "```\n"
        section += "Final Confidence = (Initial Confidence × 0.4) + \n"
        section += "                   (Validation Strength × 0.4) + \n"
        section += "                   (Segmentation Evidence × 0.2)\n"
        section += "```\n\n"
        
        section += "**Interpretation:**\n"
        section += "- 0.80-1.0: Highly likely and actionable\n"
        section += "- 0.60-0.79: Moderately valid, requires monitoring\n"
        section += "- Below 0.60: Low confidence insight\n\n"
        
        return section
    
    def _assemble_report(
        self,
        executive_summary: str,
        key_insights: str,
        creative_recommendations: str,
        methodology: str
    ) -> str:
        """Assemble all sections into complete report.
        
        Args:
            executive_summary: Executive summary section
            key_insights: Key insights section
            creative_recommendations: Creative recommendations section
            methodology: Methodology section
            
        Returns:
            Complete report markdown text
        """
        report = "# Facebook Ads Performance Analysis Report\n\n"
        report += f"*Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC*\n\n"
        report += "---\n\n"
        
        report += executive_summary
        report += key_insights
        report += creative_recommendations
        report += methodology
        
        report += "---\n\n"
        report += "*Report generated by Kasparro Multi-Agent Facebook Ads Analyst*\n"
        
        return report
    
    def _write_report(self, report_content: str) -> str:
        """Write report to file.
        
        Args:
            report_content: Complete report markdown text
            
        Returns:
            Path to written report file
        """
        # Ensure reports directory exists
        reports_dir = Path("reports")
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Write report
        report_path = reports_dir / "report.md"
        report_path.write_text(report_content, encoding="utf-8")
        
        return str(report_path)
