"""
Agent modules for Kasparro system.

This module provides agent registry, factory functions, and retry logic
for agent execution with exponential backoff.
"""

import time
from datetime import datetime
from typing import Any, Dict, Type, Callable, Optional
from src.utils.logger import setup_logger


class AgentExecutionError(Exception):
    """Raised when agent execution fails after all retries."""
    pass


class AgentRegistry:
    """Registry for agent classes and factory functions."""
    
    _agents: Dict[str, Type] = {}
    
    @classmethod
    def register(cls, name: str, agent_class: Type) -> None:
        """Register an agent class.
        
        Args:
            name: Agent name
            agent_class: Agent class
        """
        cls._agents[name] = agent_class
    
    @classmethod
    def get(cls, name: str) -> Optional[Type]:
        """Get agent class by name.
        
        Args:
            name: Agent name
            
        Returns:
            Agent class or None if not found
        """
        return cls._agents.get(name)
    
    @classmethod
    def create(cls, name: str, config: Dict[str, Any]) -> Any:
        """Create agent instance.
        
        Args:
            name: Agent name
            config: Configuration dictionary
            
        Returns:
            Agent instance
            
        Raises:
            ValueError: If agent not found
        """
        agent_class = cls.get(name)
        if agent_class is None:
            raise ValueError(f"Agent '{name}' not found in registry")
        
        # Initialize agent with configuration only (no direct agent references)
        return agent_class(config)


def execute_with_retry(
    agent_func: Callable,
    agent_name: str,
    input_data: Dict[str, Any],
    config: Dict[str, Any],
    logger: Optional[Any] = None
) -> Dict[str, Any]:
    """Execute agent function with retry logic and exponential backoff.
    
    Args:
        agent_func: Agent execution function
        agent_name: Name of the agent
        input_data: Input data for agent
        config: Configuration dictionary
        logger: Optional logger instance
        
    Returns:
        Agent output
        
    Raises:
        AgentExecutionError: If all retries are exhausted
    """
    if logger is None:
        logger = setup_logger(
            "agent_orchestration",
            log_level=config.get("logging", {}).get("level", "INFO"),
            log_format=config.get("logging", {}).get("format", "json"),
            log_dir=config.get("logging", {}).get("log_dir", "logs"),
        )
    
    # Get retry configuration
    retry_config = config.get("retry", {})
    max_retries = retry_config.get("max_retries", 3)
    backoff_multiplier = retry_config.get("backoff_multiplier", 2)
    base_delay = retry_config.get("base_delay", 1.0)
    
    last_error = None
    
    for attempt in range(max_retries + 1):
        try:
            # Log execution start
            logger.info(
                f"Agent execution started",
                extra={
                    "agent_name": agent_name,
                    "attempt": attempt + 1,
                    "max_attempts": max_retries + 1,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            )
            
            # Execute agent
            result = agent_func(input_data)
            
            # Log successful execution
            if attempt > 0:
                logger.info(
                    f"Agent execution succeeded after retry",
                    extra={
                        "agent_name": agent_name,
                        "retry_count": attempt,
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                )
            else:
                logger.info(
                    f"Agent execution completed successfully",
                    extra={
                        "agent_name": agent_name,
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                )
            
            return result
            
        except Exception as e:
            last_error = e
            
            # Log the error
            logger.error(
                f"Agent execution failed",
                extra={
                    "agent_name": agent_name,
                    "attempt": attempt + 1,
                    "max_attempts": max_retries + 1,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                },
                exc_info=True
            )
            
            # If this was the last attempt, raise
            if attempt >= max_retries:
                logger.error(
                    f"Agent execution failed after all retries",
                    extra={
                        "agent_name": agent_name,
                        "total_attempts": attempt + 1,
                        "final_error": str(e),
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                )
                raise AgentExecutionError(
                    f"Agent '{agent_name}' failed after {attempt + 1} attempts: {str(e)}"
                ) from last_error
            
            # Calculate delay with exponential backoff
            delay = base_delay * (backoff_multiplier ** attempt)
            
            logger.info(
                f"Retrying agent execution after delay",
                extra={
                    "agent_name": agent_name,
                    "attempt": attempt + 1,
                    "next_attempt": attempt + 2,
                    "delay_seconds": delay,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            )
            
            # Wait before retry
            time.sleep(delay)
    
    # This should never be reached, but just in case
    raise AgentExecutionError(
        f"Agent '{agent_name}' failed after {max_retries + 1} attempts"
    )


# Import and register agents
def register_agents():
    """Register all available agents."""
    from src.agents.planner import PlannerAgent
    from src.agents.data_agent import DataAgent
    from src.agents.insight_agent import InsightAgent
    from src.agents.evaluator_agent import EvaluatorAgent
    from src.agents.creative_generator import CreativeGeneratorAgent
    from src.agents.report_generator import ReportGenerator
    
    AgentRegistry.register("planner", PlannerAgent)
    AgentRegistry.register("data_agent", DataAgent)
    AgentRegistry.register("insight_agent", InsightAgent)
    AgentRegistry.register("evaluator_agent", EvaluatorAgent)
    AgentRegistry.register("creative_generator", CreativeGeneratorAgent)
    AgentRegistry.register("report_generator", ReportGenerator)


# Auto-register agents on import
register_agents()
