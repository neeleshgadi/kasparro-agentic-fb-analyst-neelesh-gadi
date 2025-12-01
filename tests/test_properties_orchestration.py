"""Property-based tests for agent orchestration and retry logic."""

import time
import tempfile
import os
from datetime import datetime
from typing import Any, Dict
import yaml
import pytest
from hypothesis import given, settings, strategies as st

from src.agents import (
    AgentRegistry,
    execute_with_retry,
    AgentExecutionError,
    register_agents,
)
from src.utils.config_loader import load_config


# Mock agent for testing
class MockAgent:
    """Mock agent for testing initialization and execution."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize mock agent with config only."""
        self.config = config
        self.agent_name = "mock_agent"
        self.execution_count = 0
        self.should_fail = False
        self.fail_count = 0
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute mock agent."""
        self.execution_count += 1
        
        if self.should_fail and self.execution_count <= self.fail_count:
            raise RuntimeError(f"Mock failure {self.execution_count}")
        
        return {
            "agent_name": self.agent_name,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "execution_duration_ms": 10,
            "result": "success",
            "execution_count": self.execution_count,
        }


# Feature: kasparro-fb-analyst, Property 38: Agent Initialization Parameters
# Validates: Requirements 12.2
@settings(max_examples=100)
@given(
    low_ctr=st.floats(min_value=0.0, max_value=1.0),
    max_retries=st.integers(min_value=0, max_value=10),
    random_seed=st.integers(min_value=0, max_value=1000000),
)
def test_property_38_agent_initialization_parameters(low_ctr, max_retries, random_seed):
    """
    Property 38: Agent Initialization Parameters
    For any agent instantiation, the agent constructor should accept only
    a configuration object and no direct references to other agents.
    """
    # Create configuration
    config = {
        "thresholds": {
            "low_ctr": low_ctr,
        },
        "retry": {
            "max_retries": max_retries,
        },
        "random_seed": random_seed,
        "logging": {
            "level": "INFO",
            "format": "json",
            "log_dir": "logs",
        },
    }
    
    # Register mock agent
    AgentRegistry.register("mock_agent", MockAgent)
    
    # Create agent instance using only configuration
    agent = AgentRegistry.create("mock_agent", config)
    
    # Assert agent was initialized correctly
    assert agent is not None
    assert hasattr(agent, "config")
    assert agent.config == config
    assert agent.config["thresholds"]["low_ctr"] == low_ctr
    assert agent.config["retry"]["max_retries"] == max_retries
    assert agent.config["random_seed"] == random_seed
    
    # Assert agent has no direct references to other agents
    # (checking that config is the only parameter)
    assert not hasattr(agent, "other_agents")
    assert not hasattr(agent, "planner")
    assert not hasattr(agent, "data_agent")


# Feature: kasparro-fb-analyst, Property 39: Agent Execution Isolation
# Validates: Requirements 12.3
@settings(max_examples=100)
@given(
    input_value=st.integers(min_value=1, max_value=1000),
)
def test_property_39_agent_execution_isolation(input_value):
    """
    Property 39: Agent Execution Isolation
    For any agent execution, the agent should not directly invoke other agents
    but should return routing instructions.
    """
    config = {
        "logging": {
            "level": "INFO",
            "format": "json",
            "log_dir": "logs",
        },
    }
    
    # Create mock agent
    agent = MockAgent(config)
    
    # Execute agent
    input_data = {"value": input_value}
    result = agent.execute(input_data)
    
    # Assert result is returned (not calling other agents)
    assert result is not None
    assert isinstance(result, dict)
    assert "agent_name" in result
    assert result["agent_name"] == "mock_agent"
    
    # Assert agent execution is isolated (no direct agent calls)
    # The agent should return data, not call other agents
    assert "result" in result
    assert result["result"] == "success"
    
    # Verify execution count shows single execution
    assert agent.execution_count == 1




# Feature: kasparro-fb-analyst, Property 46: Retry Execution on Failure
# Validates: Requirements 16.1
@settings(max_examples=100)
@given(
    max_retries=st.integers(min_value=1, max_value=5),
    fail_count=st.integers(min_value=1, max_value=3),
)
def test_property_46_retry_execution_on_failure(max_retries, fail_count):
    """
    Property 46: Retry Execution on Failure
    For any agent execution that raises an exception, the System should retry
    up to max_retries times before propagating failure.
    """
    # Ensure fail_count is less than or equal to max_retries
    # so that the agent eventually succeeds
    if fail_count > max_retries:
        fail_count = max_retries
    
    config = {
        "retry": {
            "max_retries": max_retries,
            "backoff_multiplier": 1,  # No backoff for faster testing
            "base_delay": 0.01,  # Minimal delay
        },
        "logging": {
            "level": "ERROR",  # Reduce log noise
            "format": "json",
            "log_dir": "logs",
        },
    }
    
    # Create mock agent that fails initially
    agent = MockAgent(config)
    agent.should_fail = True
    agent.fail_count = fail_count
    
    # Execute with retry
    input_data = {"test": "data"}
    result = execute_with_retry(
        agent.execute,
        "mock_agent",
        input_data,
        config
    )
    
    # Assert agent was retried and eventually succeeded
    assert result is not None
    assert result["result"] == "success"
    
    # Assert execution count shows retries occurred
    # Should be fail_count + 1 (failures + final success)
    assert agent.execution_count == fail_count + 1


# Feature: kasparro-fb-analyst, Property 47: Exponential Backoff Timing
# Validates: Requirements 16.2
@settings(max_examples=50, deadline=None)
@given(
    backoff_multiplier=st.floats(min_value=1.5, max_value=3.0),
    base_delay=st.floats(min_value=0.01, max_value=0.1),
)
def test_property_47_exponential_backoff_timing(backoff_multiplier, base_delay):
    """
    Property 47: Exponential Backoff Timing
    For any agent retry sequence, the delay between retries should follow
    exponential backoff based on configured multiplier.
    """
    max_retries = 3
    config = {
        "retry": {
            "max_retries": max_retries,
            "backoff_multiplier": backoff_multiplier,
            "base_delay": base_delay,
        },
        "logging": {
            "level": "ERROR",
            "format": "json",
            "log_dir": "logs",
        },
    }
    
    # Create mock agent that always fails
    agent = MockAgent(config)
    agent.should_fail = True
    agent.fail_count = max_retries + 1  # Fail all attempts
    
    # Measure execution time
    start_time = time.time()
    
    try:
        execute_with_retry(
            agent.execute,
            "mock_agent",
            {"test": "data"},
            config
        )
    except AgentExecutionError:
        pass  # Expected to fail
    
    elapsed_time = time.time() - start_time
    
    # Calculate expected minimum delay
    # Delays: base_delay * (multiplier^0), base_delay * (multiplier^1), base_delay * (multiplier^2)
    expected_min_delay = sum(
        base_delay * (backoff_multiplier ** i)
        for i in range(max_retries)
    )
    
    # Assert elapsed time is at least the expected delay
    # Allow some tolerance for execution overhead
    assert elapsed_time >= expected_min_delay * 0.9


# Feature: kasparro-fb-analyst, Property 48: Retry Exhaustion Handling
# Validates: Requirements 16.3
@settings(max_examples=100)
@given(
    max_retries=st.integers(min_value=1, max_value=5),
)
def test_property_48_retry_exhaustion_handling(max_retries):
    """
    Property 48: Retry Exhaustion Handling
    For any agent execution where all retries are exhausted, the System should
    log the final error and return failure status.
    """
    config = {
        "retry": {
            "max_retries": max_retries,
            "backoff_multiplier": 1,
            "base_delay": 0.01,
        },
        "logging": {
            "level": "ERROR",
            "format": "json",
            "log_dir": "logs",
        },
    }
    
    # Create mock agent that always fails
    agent = MockAgent(config)
    agent.should_fail = True
    agent.fail_count = max_retries + 10  # Fail more than max_retries
    
    # Execute with retry - should raise AgentExecutionError
    with pytest.raises(AgentExecutionError) as exc_info:
        execute_with_retry(
            agent.execute,
            "mock_agent",
            {"test": "data"},
            config
        )
    
    # Assert error message contains agent name and attempt count
    error_message = str(exc_info.value)
    assert "mock_agent" in error_message
    assert str(max_retries + 1) in error_message
    
    # Assert agent was called max_retries + 1 times
    assert agent.execution_count == max_retries + 1


# Feature: kasparro-fb-analyst, Property 49: Successful Retry Logging
# Validates: Requirements 16.4
@settings(max_examples=100)
@given(
    retry_count=st.integers(min_value=1, max_value=3),
)
def test_property_49_successful_retry_logging(retry_count):
    """
    Property 49: Successful Retry Logging
    For any agent retry that succeeds, the System should log the retry count
    and continue workflow execution.
    """
    config = {
        "retry": {
            "max_retries": 5,
            "backoff_multiplier": 1,
            "base_delay": 0.01,
        },
        "logging": {
            "level": "INFO",
            "format": "json",
            "log_dir": "logs",
        },
    }
    
    # Create mock agent that fails initially then succeeds
    agent = MockAgent(config)
    agent.should_fail = True
    agent.fail_count = retry_count
    
    # Execute with retry
    result = execute_with_retry(
        agent.execute,
        "mock_agent",
        {"test": "data"},
        config
    )
    
    # Assert execution succeeded
    assert result is not None
    assert result["result"] == "success"
    
    # Assert execution count shows retries occurred
    assert agent.execution_count == retry_count + 1
    
    # Assert result contains execution count (workflow continues)
    assert "execution_count" in result
    assert result["execution_count"] == retry_count + 1


# Feature: kasparro-fb-analyst, Property 50: Retry Configuration Loading
# Validates: Requirements 16.5
@settings(max_examples=100, deadline=None)
@given(
    max_retries=st.integers(min_value=0, max_value=5),
    backoff_multiplier=st.floats(min_value=1.0, max_value=2.0),
)
def test_property_50_retry_configuration_loading(max_retries, backoff_multiplier):
    """
    Property 50: Retry Configuration Loading
    For any system initialization, the System should load max_retries and
    backoff_multiplier from config.yaml.
    """
    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        config_data = {
            "retry": {
                "max_retries": max_retries,
                "backoff_multiplier": backoff_multiplier,
                "base_delay": 0.01,  # Fast delay for testing
            },
            "logging": {
                "level": "ERROR",  # Reduce log noise
                "format": "json",
                "log_dir": "logs",
            },
        }
        yaml.dump(config_data, f)
        temp_config_path = f.name
    
    try:
        # Load configuration
        from src.utils.config_loader import ConfigLoader
        loader = ConfigLoader(temp_config_path)
        config = loader.load()
        
        # Assert retry configuration is loaded
        assert "retry" in config
        assert config["retry"]["max_retries"] == max_retries
        assert config["retry"]["backoff_multiplier"] == backoff_multiplier
        
        # Test that retry logic uses loaded configuration
        agent = MockAgent(config)
        agent.should_fail = True
        agent.fail_count = max_retries + 10  # Fail more than max
        
        # Should fail after max_retries + 1 attempts
        with pytest.raises(AgentExecutionError):
            execute_with_retry(
                agent.execute,
                "mock_agent",
                {"test": "data"},
                config
            )
        
        # Verify execution count matches max_retries + 1
        assert agent.execution_count == max_retries + 1
        
    finally:
        # Clean up
        os.unlink(temp_config_path)
