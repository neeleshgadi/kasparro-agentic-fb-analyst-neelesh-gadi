"""
Planner Agent for Kasparro system.

The Planner Agent orchestrates the multi-agent workflow by:
- Parsing natural language queries
- Extracting intent, time ranges, and parameters
- Decomposing tasks into executable steps
- Routing to appropriate agents
"""

import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from src.schemas.validation import (
    validate_agent_input,
    validate_agent_output,
    create_success_envelope,
    create_error_envelope,
)
from src.schemas.agent_io import PLANNER_INPUT_SCHEMA, PLANNER_OUTPUT_SCHEMA


class PlannerAgent:
    """Planner Agent that decomposes user queries and routes tasks."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Planner Agent.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.agent_name = "planner"
    
    def execute(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute planner agent logic.
        
        Args:
            query: Natural language user query
            context: Context including dataset_path and config
            
        Returns:
            Planner output with task plan and routing
        """
        start_time = datetime.utcnow()
        
        try:
            # Validate input
            input_data = {
                "query": query,
                "context": context
            }
            validate_agent_input(input_data, PLANNER_INPUT_SCHEMA, self.agent_name)
            
            # Parse query to extract intent and parameters
            intent, parameters = self._parse_query(query)
            
            # Check if query is ambiguous or incomplete
            if self._is_ambiguous(intent, parameters):
                clarification = self._generate_clarification(intent, parameters)
                return self._create_clarification_response(clarification, start_time)
            
            # Decompose task based on intent
            task_plan = self._decompose_task(intent, parameters)
            
            # Determine routing
            routing = self._determine_routing(intent, task_plan)
            
            # Create output
            execution_duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            output = {
                "agent_name": self.agent_name,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "execution_duration_ms": execution_duration_ms,
                "task": intent,
                "steps": [step["action"] for step in task_plan],
                "task_plan": task_plan,
                "routing": routing,
                "metadata": {
                    "agent": self.agent_name,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                },
                "reasoning": self._generate_reasoning(query, intent, parameters, task_plan)
            }
            
            # Only include date_range if it exists
            if parameters.get("date_range"):
                output["date_range"] = parameters["date_range"]
            
            # Validate output
            validate_agent_output(output, PLANNER_OUTPUT_SCHEMA, self.agent_name)
            
            return output
            
        except Exception as e:
            execution_duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            return create_error_envelope(
                self.agent_name,
                "UnexpectedError",
                str(e),
                execution_duration_ms=execution_duration_ms
            )
    
    def _parse_query(self, query: str) -> Tuple[str, Dict[str, Any]]:
        """Parse natural language query to extract intent and parameters.
        
        Args:
            query: User query string
            
        Returns:
            Tuple of (intent, parameters)
        """
        query_lower = query.lower()
        parameters: Dict[str, Any] = {}
        
        # Extract time range
        date_range = self._extract_date_range(query_lower)
        if date_range:
            parameters["date_range"] = date_range
        
        # Determine intent
        if any(keyword in query_lower for keyword in ["roas", "return on ad spend", "roi"]):
            if any(keyword in query_lower for keyword in ["why", "cause", "reason", "explain"]):
                intent = "roas_analysis"
            else:
                intent = "roas_analysis"
        elif any(keyword in query_lower for keyword in ["creative", "ad copy", "recommendation"]):
            intent = "creative_generation"
        elif any(keyword in query_lower for keyword in ["analyze", "analysis", "report", "insight"]):
            intent = "full_analysis"
        else:
            # Default to full analysis if unclear
            intent = "full_analysis"
        
        # Extract focus metric if specified
        if "ctr" in query_lower or "click" in query_lower:
            parameters["focus_metric"] = "ctr"
        elif "roas" in query_lower:
            parameters["focus_metric"] = "roas"
        elif "conversion" in query_lower or "cvr" in query_lower:
            parameters["focus_metric"] = "cvr"
        
        return intent, parameters
    
    def _extract_date_range(self, query: str) -> Optional[Dict[str, str]]:
        """Extract date range from query.
        
        Args:
            query: Query string (lowercase)
            
        Returns:
            Date range dict with 'from' and 'to' keys, or None
        """
        today = datetime.utcnow().date()
        
        # Check for relative time expressions
        if "last 7 days" in query or "past 7 days" in query or "last week" in query:
            from_date = today - timedelta(days=7)
            return {
                "from": from_date.isoformat(),
                "to": today.isoformat()
            }
        
        if "last 14 days" in query or "past 14 days" in query or "last 2 weeks" in query:
            from_date = today - timedelta(days=14)
            return {
                "from": from_date.isoformat(),
                "to": today.isoformat()
            }
        
        if "last 30 days" in query or "past 30 days" in query or "last month" in query:
            from_date = today - timedelta(days=30)
            return {
                "from": from_date.isoformat(),
                "to": today.isoformat()
            }
        
        # Check for explicit date patterns (YYYY-MM-DD)
        date_pattern = r'\d{4}-\d{2}-\d{2}'
        dates = re.findall(date_pattern, query)
        
        if len(dates) >= 2:
            return {
                "from": dates[0],
                "to": dates[1]
            }
        elif len(dates) == 1:
            # Single date - use as end date with 7 days before
            to_date = datetime.strptime(dates[0], "%Y-%m-%d").date()
            from_date = to_date - timedelta(days=7)
            return {
                "from": from_date.isoformat(),
                "to": to_date.isoformat()
            }
        
        return None
    
    def _is_ambiguous(self, intent: str, parameters: Dict[str, Any]) -> bool:
        """Check if query is ambiguous or incomplete.
        
        Args:
            intent: Parsed intent
            parameters: Extracted parameters
            
        Returns:
            True if query needs clarification
        """
        # For now, we don't require date range to be specified
        # The system can work with the full dataset if no range is given
        return False
    
    def _generate_clarification(self, intent: str, parameters: Dict[str, Any]) -> str:
        """Generate clarification request for ambiguous queries.
        
        Args:
            intent: Parsed intent
            parameters: Extracted parameters
            
        Returns:
            Clarification message
        """
        missing = []
        
        if "date_range" not in parameters:
            missing.append("time period (e.g., 'last 7 days', '2024-01-01 to 2024-01-31')")
        
        if not missing:
            return "Please provide more details about what you'd like to analyze."
        
        return f"Please specify: {', '.join(missing)}"
    
    def _create_clarification_response(
        self,
        clarification: str,
        start_time: datetime
    ) -> Dict[str, Any]:
        """Create response for ambiguous query.
        
        Args:
            clarification: Clarification message
            start_time: Execution start time
            
        Returns:
            Clarification response
        """
        execution_duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return {
            "agent_name": self.agent_name,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "execution_duration_ms": execution_duration_ms,
            "status": "clarification_needed",
            "clarification": clarification,
            "task": "unknown",
            "routing": {
                "next_agent": "none",
                "workflow_type": "clarification"
            }
        }
    
    def _decompose_task(self, intent: str, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Decompose task into executable steps.
        
        Args:
            intent: Task intent
            parameters: Task parameters
            
        Returns:
            List of task steps
        """
        task_plan = []
        step_id = 1
        
        # All workflows start with data loading
        task_plan.append({
            "step_id": step_id,
            "agent": "data_agent",
            "action": "load_data",
            "parameters": {
                "dataset_path": parameters.get("dataset_path", "data/synthetic_fb_ads_undergarments.csv"),
                "date_range": parameters.get("date_range"),
                "metrics": ["roas", "ctr", "cvr", "cpc"]
            }
        })
        step_id += 1
        
        if intent == "roas_analysis":
            # ROAS analysis workflow
            task_plan.append({
                "step_id": step_id,
                "agent": "insight_agent",
                "action": "generate_hypotheses",
                "parameters": {
                    "focus_metric": parameters.get("focus_metric", "roas")
                }
            })
            step_id += 1
            
            task_plan.append({
                "step_id": step_id,
                "agent": "evaluator_agent",
                "action": "validate_hypotheses",
                "parameters": {}
            })
            step_id += 1
            
            task_plan.append({
                "step_id": step_id,
                "agent": "report_generator",
                "action": "generate_report",
                "parameters": {
                    "sections": ["executive_summary", "key_insights", "methodology"]
                }
            })
            
        elif intent == "creative_generation":
            # Creative generation workflow
            task_plan.append({
                "step_id": step_id,
                "agent": "creative_generator",
                "action": "generate_creatives",
                "parameters": {
                    "low_ctr_threshold": self.config.get("thresholds", {}).get("low_ctr", 0.01)
                }
            })
            step_id += 1
            
            task_plan.append({
                "step_id": step_id,
                "agent": "report_generator",
                "action": "generate_report",
                "parameters": {
                    "sections": ["executive_summary", "creative_recommendations"]
                }
            })
            
        else:  # full_analysis
            # Full workflow with all agents
            task_plan.append({
                "step_id": step_id,
                "agent": "insight_agent",
                "action": "generate_hypotheses",
                "parameters": {
                    "focus_metric": parameters.get("focus_metric", "roas")
                }
            })
            step_id += 1
            
            task_plan.append({
                "step_id": step_id,
                "agent": "evaluator_agent",
                "action": "validate_hypotheses",
                "parameters": {}
            })
            step_id += 1
            
            task_plan.append({
                "step_id": step_id,
                "agent": "creative_generator",
                "action": "generate_creatives",
                "parameters": {
                    "low_ctr_threshold": self.config.get("thresholds", {}).get("low_ctr", 0.01)
                }
            })
            step_id += 1
            
            task_plan.append({
                "step_id": step_id,
                "agent": "report_generator",
                "action": "generate_report",
                "parameters": {
                    "sections": ["executive_summary", "key_insights", "creative_recommendations", "methodology"]
                }
            })
        
        return task_plan
    
    def _determine_routing(self, intent: str, task_plan: List[Dict[str, Any]]) -> Dict[str, str]:
        """Determine routing for workflow execution.
        
        Args:
            intent: Task intent
            task_plan: Decomposed task plan
            
        Returns:
            Routing information
        """
        # First agent is always data_agent
        next_agent = task_plan[0]["agent"] if task_plan else "data_agent"
        
        # Map intent to workflow type
        workflow_type_map = {
            "roas_analysis": "analysis",
            "creative_generation": "creative_generation",
            "full_analysis": "full"
        }
        
        workflow_type = workflow_type_map.get(intent, "full")
        
        return {
            "next_agent": next_agent,
            "workflow_type": workflow_type
        }
    
    def _generate_reasoning(
        self,
        query: str,
        intent: str,
        parameters: Dict[str, Any],
        task_plan: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """Generate reasoning structure for planner output.
        
        Args:
            query: Original query
            intent: Parsed intent
            parameters: Extracted parameters
            task_plan: Generated task plan
            
        Returns:
            Reasoning dict with think, analyze, conclude sections
        """
        # Think section
        think = f"Analyzing user query: '{query}'. "
        think += f"Identified intent as '{intent}'. "
        
        if parameters.get("date_range"):
            date_range = parameters["date_range"]
            think += f"Time range specified: {date_range['from']} to {date_range['to']}. "
        else:
            think += "No specific time range provided, will analyze full dataset. "
        
        if parameters.get("focus_metric"):
            think += f"Focus metric: {parameters['focus_metric']}. "
        
        # Analyze section
        analyze = f"Task decomposition for '{intent}' workflow:\n"
        for step in task_plan:
            analyze += f"- Step {step['step_id']}: {step['agent']} will {step['action']}\n"
        
        analyze += f"\nTotal steps: {len(task_plan)}. "
        analyze += "Dependencies: Each step depends on the output of the previous step. "
        
        # Conclude section
        conclude = f"Workflow type: {self._determine_routing(intent, task_plan)['workflow_type']}. "
        conclude += f"Starting with {task_plan[0]['agent']} for data loading and processing. "
        conclude += f"Expected outputs: "
        
        if intent == "roas_analysis":
            conclude += "insights.json with validated hypotheses, report.md with analysis summary."
        elif intent == "creative_generation":
            conclude += "creatives.json with recommendations, report.md with creative suggestions."
        else:
            conclude += "insights.json, creatives.json, and comprehensive report.md."
        
        return {
            "think": think,
            "analyze": analyze,
            "conclude": conclude
        }
