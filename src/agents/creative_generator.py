"""
Creative Generator Agent for generating ad creative recommendations.

This agent identifies low-CTR campaigns and generates creative recommendations
with variations in message, type, audience, and rationale.
"""

import uuid
import pandas as pd
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

from src.schemas.validation import validate_agent_input, validate_agent_output
from src.schemas.agent_io import CREATIVE_GENERATOR_INPUT_SCHEMA, CREATIVE_GENERATOR_OUTPUT_SCHEMA
from src.utils.logger import setup_logger


class CreativeGeneratorAgent:
    """Agent responsible for generating creative recommendations for low-CTR campaigns."""
    
    # Creative types to recommend
    CREATIVE_TYPES = ["image", "video", "carousel", "collection"]
    
    # Message templates by audience type
    MESSAGE_TEMPLATES = {
        "female_18_30": [
            "Trendy comfort meets style - {discount}",
            "Feel confident all day - {discount}",
            "Your perfect fit awaits - {discount}",
        ],
        "female_31_45": [
            "Premium quality for everyday comfort - {discount}",
            "Designed for your lifestyle - {discount}",
            "Comfort that lasts - {discount}",
        ],
        "male_18_24": [
            "Athletic performance meets comfort - {discount}",
            "Minimalist design, maximum comfort - {discount}",
            "Built for your active life - {discount}",
        ],
        "male_25_40": [
            "Professional comfort for busy days - {discount}",
            "Quality essentials for modern men - {discount}",
            "Upgrade your basics - {discount}",
        ],
        "default": [
            "Premium comfort at great prices - {discount}",
            "Discover your new favorites - {discount}",
            "Quality you can feel - {discount}",
        ]
    }
    
    # Discount offers
    DISCOUNTS = ["20% off", "Buy 1 Get 1", "30% off first order", "Free shipping"]
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Creative Generator Agent.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.agent_name = "creative_generator"
        self.logger = setup_logger(
            self.agent_name,
            log_level=config.get("logging", {}).get("level", "INFO"),
            log_format=config.get("logging", {}).get("format", "json"),
            log_dir=config.get("logging", {}).get("log_dir", "logs"),
        )
        self.low_ctr_threshold = config.get("thresholds", {}).get("low_ctr", 0.01)
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute creative generator workflow.
        
        Args:
            input_data: Input containing data_summary, low_ctr_threshold, dataset_path, config
            
        Returns:
            Creative generator output with recommendations and reasoning
        """
        start_time = datetime.utcnow()
        
        try:
            # Validate input
            validate_agent_input(input_data, CREATIVE_GENERATOR_INPUT_SCHEMA, self.agent_name)
            
            # Extract input parameters
            data_summary = input_data["data_summary"]
            dataset_path = input_data["dataset_path"]
            low_ctr_threshold = input_data.get("low_ctr_threshold", self.low_ctr_threshold)
            
            # Load dataset
            df = self._load_dataset(dataset_path)
            
            # Identify low-CTR campaigns
            low_ctr_campaigns = self._identify_low_ctr_campaigns(df, data_summary, low_ctr_threshold)
            
            # Generate creative recommendations
            recommendations = self._generate_creative_recommendations(
                low_ctr_campaigns,
                df,
                data_summary
            )
            
            # Generate reasoning
            reasoning = self._generate_reasoning(low_ctr_campaigns, recommendations, low_ctr_threshold)
            
            # Calculate execution duration
            execution_duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            # Build output
            output = {
                "agent_name": self.agent_name,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "execution_duration_ms": execution_duration_ms,
                "recommendations": recommendations,
                "reasoning": reasoning,
            }
            
            # Validate output
            validate_agent_output(output, CREATIVE_GENERATOR_OUTPUT_SCHEMA, self.agent_name)
            
            self.logger.info(
                f"Creative Generator completed successfully",
                extra={
                    "agent_name": self.agent_name,
                    "execution_duration_ms": execution_duration_ms,
                    "recommendations_count": len(recommendations),
                }
            )
            
            return output
            
        except Exception as e:
            self.logger.error(
                f"Creative Generator execution failed: {str(e)}",
                extra={"agent_name": self.agent_name, "error_type": type(e).__name__},
                exc_info=True
            )
            raise
    
    def _load_dataset(self, dataset_path: str) -> pd.DataFrame:
        """Load dataset from CSV.
        
        Args:
            dataset_path: Path to CSV file
            
        Returns:
            DataFrame with loaded data
        """
        if not Path(dataset_path).exists():
            raise FileNotFoundError(f"Dataset file not found: {dataset_path}")
        
        df = pd.read_csv(dataset_path)
        
        # Parse dates
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors='coerce')
        
        # Ensure numeric fields
        numeric_fields = ["spend", "impressions", "clicks", "revenue", "purchases", "ctr", "roas"]
        for field in numeric_fields:
            if field in df.columns:
                df[field] = pd.to_numeric(df[field], errors='coerce')
        
        return df
    
    def _identify_low_ctr_campaigns(
        self,
        df: pd.DataFrame,
        data_summary: Dict[str, Any],
        low_ctr_threshold: float
    ) -> List[Dict[str, Any]]:
        """Identify campaigns with CTR below threshold.
        
        Args:
            df: Dataset DataFrame
            data_summary: Data summary from Data Agent
            low_ctr_threshold: CTR threshold for filtering
            
        Returns:
            List of low-CTR campaign dictionaries
        """
        low_ctr_campaigns = []
        
        # Get campaign segmentation from data summary
        segmentation = data_summary.get("segmentation", {})
        campaign_segments = segmentation.get("by_campaign", [])
        
        # Filter campaigns with low CTR
        for campaign in campaign_segments:
            campaign_ctr = campaign.get("ctr", 0)
            
            if campaign_ctr < low_ctr_threshold:
                campaign_name = campaign.get("campaign_name", "Unknown")
                
                # Get campaign data from DataFrame
                campaign_df = df[df["campaign_name"] == campaign_name]
                
                if len(campaign_df) > 0:
                    # Get current creative info
                    current_creative_type = campaign_df["creative_type"].mode()[0] if "creative_type" in campaign_df.columns else "unknown"
                    current_message = campaign_df["creative_message"].mode()[0] if "creative_message" in campaign_df.columns else ""
                    
                    low_ctr_campaigns.append({
                        "campaign": campaign_name,
                        "current_ctr": campaign_ctr,
                        "current_creative_type": current_creative_type,
                        "current_message": current_message,
                        "campaign_df": campaign_df
                    })
        
        return low_ctr_campaigns
    
    def _generate_creative_recommendations(
        self,
        low_ctr_campaigns: List[Dict[str, Any]],
        df: pd.DataFrame,
        data_summary: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate creative recommendations for low-CTR campaigns.
        
        Args:
            low_ctr_campaigns: List of low-CTR campaign dictionaries
            df: Dataset DataFrame
            data_summary: Data summary from Data Agent
            
        Returns:
            List of recommendation dictionaries
        """
        recommendations = []
        
        # Analyze high-performing creatives
        high_performing_creatives = self._analyze_high_performing_creatives(df, data_summary)
        
        for campaign_info in low_ctr_campaigns:
            campaign_name = campaign_info["campaign"]
            current_ctr = campaign_info["current_ctr"]
            current_creative_type = campaign_info["current_creative_type"]
            current_message = campaign_info["current_message"]
            campaign_df = campaign_info["campaign_df"]
            
            # Extract audience type from campaign name or data
            audience_type = self._extract_audience_type(campaign_name, campaign_df)
            
            # Generate 3+ creative variations
            new_creatives = self._generate_creative_variations(
                campaign_name,
                current_creative_type,
                audience_type,
                high_performing_creatives,
                current_ctr
            )
            
            recommendation = {
                "campaign": campaign_name,
                "current_ctr": float(current_ctr),
                "current_creative_type": current_creative_type,
                "current_message": current_message,
                "new_creatives": new_creatives
            }
            
            recommendations.append(recommendation)
        
        return recommendations
    
    def _analyze_high_performing_creatives(
        self,
        df: pd.DataFrame,
        data_summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze high-performing creative attributes.
        
        Args:
            df: Dataset DataFrame
            data_summary: Data summary from Data Agent
            
        Returns:
            Dictionary of high-performing creative insights
        """
        insights = {
            "best_creative_types": [],
            "best_messages": [],
            "avg_ctr_by_type": {}
        }
        
        # Get creative type segmentation
        segmentation = data_summary.get("segmentation", {})
        creative_segments = segmentation.get("by_creative_type", [])
        
        if creative_segments:
            # Sort by CTR
            sorted_creatives = sorted(creative_segments, key=lambda x: x.get("ctr", 0), reverse=True)
            
            # Get top performing creative types
            insights["best_creative_types"] = [c.get("creative_type", "image") for c in sorted_creatives[:2]]
            
            # Store average CTR by type
            for creative in creative_segments:
                creative_type = creative.get("creative_type", "unknown")
                insights["avg_ctr_by_type"][creative_type] = creative.get("ctr", 0)
        
        # Analyze messages from high-CTR campaigns
        if "creative_message" in df.columns and "ctr" in df.columns:
            high_ctr_df = df[df["ctr"] > df["ctr"].quantile(0.75)]
            if len(high_ctr_df) > 0:
                insights["best_messages"] = high_ctr_df["creative_message"].value_counts().head(3).index.tolist()
        
        return insights
    
    def _extract_audience_type(self, campaign_name: str, campaign_df: pd.DataFrame) -> str:
        """Extract audience type from campaign name or data.
        
        Args:
            campaign_name: Campaign name
            campaign_df: Campaign DataFrame
            
        Returns:
            Audience type string
        """
        # Try to extract from campaign name
        campaign_lower = campaign_name.lower()
        
        if "female" in campaign_lower and "18" in campaign_lower:
            return "female_18_30"
        elif "female" in campaign_lower and ("30" in campaign_lower or "31" in campaign_lower):
            return "female_31_45"
        elif "male" in campaign_lower and "18" in campaign_lower:
            return "male_18_24"
        elif "male" in campaign_lower and ("25" in campaign_lower or "30" in campaign_lower):
            return "male_25_40"
        
        # Try to extract from DataFrame
        if "audience_type" in campaign_df.columns:
            audience_type = campaign_df["audience_type"].mode()[0]
            return audience_type
        
        return "default"
    
    def _generate_creative_variations(
        self,
        campaign_name: str,
        current_creative_type: str,
        audience_type: str,
        high_performing_creatives: Dict[str, Any],
        current_ctr: float
    ) -> List[Dict[str, Any]]:
        """Generate creative variations for a campaign.
        
        Args:
            campaign_name: Campaign name
            current_creative_type: Current creative type
            audience_type: Target audience type
            high_performing_creatives: High-performing creative insights
            current_ctr: Current CTR
            
        Returns:
            List of creative variation dictionaries (minimum 3)
        """
        variations = []
        
        # Get message templates for audience
        templates = self.MESSAGE_TEMPLATES.get(audience_type, self.MESSAGE_TEMPLATES["default"])
        
        # Get best performing creative types
        best_types = high_performing_creatives.get("best_creative_types", ["video", "carousel"])
        if not best_types:
            best_types = ["video", "carousel", "image"]
        
        # Ensure we have at least 3 different creative types to recommend
        recommended_types = []
        for creative_type in best_types:
            if creative_type != current_creative_type:
                recommended_types.append(creative_type)
        
        # Add other types if needed
        for creative_type in self.CREATIVE_TYPES:
            if creative_type not in recommended_types and creative_type != current_creative_type:
                recommended_types.append(creative_type)
        
        # Generate at least 3 variations
        for i in range(max(3, len(recommended_types[:4]))):
            creative_type = recommended_types[i % len(recommended_types)]
            template = templates[i % len(templates)]
            discount = self.DISCOUNTS[i % len(self.DISCOUNTS)]
            
            # Generate message
            creative_message = template.format(discount=discount)
            
            # Calculate expected CTR improvement
            avg_ctr_for_type = high_performing_creatives.get("avg_ctr_by_type", {}).get(creative_type, current_ctr * 1.5)
            expected_improvement = ((avg_ctr_for_type - current_ctr) / max(current_ctr, 0.001)) * 100
            expected_improvement = max(10, min(100, expected_improvement))  # Clamp between 10% and 100%
            
            # Calculate confidence based on data availability
            confidence = self._calculate_creative_confidence(
                creative_type,
                high_performing_creatives,
                current_ctr
            )
            
            # Generate rationale
            rationale = self._generate_rationale(
                creative_type,
                current_creative_type,
                audience_type,
                high_performing_creatives,
                expected_improvement
            )
            
            variation = {
                "creative_id": str(uuid.uuid4()),
                "creative_type": creative_type,
                "creative_message": creative_message,
                "audience_type": audience_type,
                "rationale": rationale,
                "confidence_score": confidence,
                "expected_ctr_improvement": float(expected_improvement)
            }
            
            variations.append(variation)
        
        return variations
    
    def _calculate_creative_confidence(
        self,
        creative_type: str,
        high_performing_creatives: Dict[str, Any],
        current_ctr: float
    ) -> float:
        """Calculate confidence score for creative recommendation.
        
        Args:
            creative_type: Recommended creative type
            high_performing_creatives: High-performing creative insights
            current_ctr: Current CTR
            
        Returns:
            Confidence score between 0 and 1
        """
        base_confidence = 0.6
        
        # Boost confidence if this type is in best performing
        best_types = high_performing_creatives.get("best_creative_types", [])
        if creative_type in best_types:
            rank = best_types.index(creative_type)
            if rank == 0:
                base_confidence += 0.2
            elif rank == 1:
                base_confidence += 0.1
        
        # Boost confidence based on historical CTR data
        avg_ctr_by_type = high_performing_creatives.get("avg_ctr_by_type", {})
        if creative_type in avg_ctr_by_type:
            type_ctr = avg_ctr_by_type[creative_type]
            if type_ctr > current_ctr * 1.5:
                base_confidence += 0.1
        
        # Ensure bounds
        return max(0.0, min(1.0, base_confidence))
    
    def _generate_rationale(
        self,
        creative_type: str,
        current_creative_type: str,
        audience_type: str,
        high_performing_creatives: Dict[str, Any],
        expected_improvement: float
    ) -> str:
        """Generate rationale for creative recommendation.
        
        Args:
            creative_type: Recommended creative type
            current_creative_type: Current creative type
            audience_type: Target audience type
            high_performing_creatives: High-performing creative insights
            expected_improvement: Expected CTR improvement percentage
            
        Returns:
            Rationale string
        """
        rationale_parts = []
        
        # Explain creative type change
        if creative_type != current_creative_type:
            rationale_parts.append(f"Switching from {current_creative_type} to {creative_type} format")
        
        # Mention performance data
        best_types = high_performing_creatives.get("best_creative_types", [])
        if creative_type in best_types:
            rationale_parts.append(f"{creative_type} is among top-performing creative types")
        
        # Mention audience fit
        if audience_type != "default":
            rationale_parts.append(f"tailored for {audience_type} audience")
        
        # Mention expected improvement
        rationale_parts.append(f"expected to improve CTR by {expected_improvement:.0f}%")
        
        # Combine parts
        rationale = ", ".join(rationale_parts)
        rationale = rationale[0].upper() + rationale[1:] + "."
        
        return rationale
    
    def _generate_reasoning(
        self,
        low_ctr_campaigns: List[Dict[str, Any]],
        recommendations: List[Dict[str, Any]],
        low_ctr_threshold: float
    ) -> Dict[str, str]:
        """Generate reasoning structure for creative generator output.
        
        Args:
            low_ctr_campaigns: List of low-CTR campaigns
            recommendations: Generated recommendations
            low_ctr_threshold: CTR threshold used
            
        Returns:
            Reasoning dict with think, analyze, conclude sections
        """
        # Think section
        think = f"Analyzing campaigns to identify those with CTR below {low_ctr_threshold:.4f}. "
        think += f"Found {len(low_ctr_campaigns)} campaigns requiring creative optimization. "
        think += "Will generate creative variations based on high-performing creative attributes and audience targeting."
        
        # Analyze section
        analyze = "Creative performance analysis:\n"
        
        if low_ctr_campaigns:
            avg_low_ctr = sum(c["current_ctr"] for c in low_ctr_campaigns) / len(low_ctr_campaigns)
            analyze += f"- Average CTR of low-performing campaigns: {avg_low_ctr:.4f}\n"
            analyze += f"- Campaigns identified: {len(low_ctr_campaigns)}\n"
            
            # List campaigns
            for campaign in low_ctr_campaigns[:3]:
                analyze += f"  * {campaign['campaign']}: CTR {campaign['current_ctr']:.4f}\n"
            
            if len(low_ctr_campaigns) > 3:
                analyze += f"  * ... and {len(low_ctr_campaigns) - 3} more\n"
        else:
            analyze += "- No campaigns found below CTR threshold\n"
        
        analyze += f"\nGenerated {sum(len(r['new_creatives']) for r in recommendations)} creative variations "
        analyze += f"across {len(recommendations)} campaigns."
        
        # Conclude section
        conclude = f"Generated creative recommendations for {len(recommendations)} low-CTR campaigns. "
        
        if recommendations:
            total_variations = sum(len(r["new_creatives"]) for r in recommendations)
            avg_variations = total_variations / len(recommendations) if recommendations else 0
            conclude += f"Each campaign received {avg_variations:.1f} creative variations on average. "
            
            # Mention confidence
            all_confidences = [
                creative["confidence_score"]
                for rec in recommendations
                for creative in rec["new_creatives"]
            ]
            if all_confidences:
                avg_confidence = sum(all_confidences) / len(all_confidences)
                conclude += f"Average confidence score: {avg_confidence:.2f}. "
        
        conclude += "Recommendations include creative type, message, audience targeting, and expected CTR improvement."
        
        return {
            "think": think,
            "analyze": analyze,
            "conclude": conclude
        }
