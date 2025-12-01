"""Property-based tests for configuration management."""

import os
import tempfile
import random
from pathlib import Path
import yaml
import pytest
from hypothesis import given, settings, strategies as st

from src.utils.config_loader import ConfigLoader, load_config, ConfigurationError


# Feature: kasparro-fb-analyst, Property 26: Configuration Loading
# Validates: Requirements 8.1, 8.4
@settings(max_examples=100)
@given(
    low_ctr=st.floats(min_value=0.0, max_value=1.0),
    high_confidence=st.floats(min_value=0.0, max_value=1.0),
    max_retries=st.integers(min_value=0, max_value=10),
)
def test_property_26_configuration_loading(low_ctr, high_confidence, max_retries):
    """
    Property 26: Configuration Loading
    For any system initialization, the System should load config/config.yaml
    and make all parameters accessible to agents.
    """
    # Create a temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        config_data = {
            "thresholds": {
                "low_ctr": low_ctr,
                "high_confidence": high_confidence,
            },
            "retry": {
                "max_retries": max_retries,
            },
        }
        yaml.dump(config_data, f)
        temp_config_path = f.name
    
    try:
        # Load configuration
        loader = ConfigLoader(temp_config_path)
        config = loader.load()
        
        # Assert configuration is loaded and accessible
        assert config is not None
        assert isinstance(config, dict)
        
        # Assert all parameters are accessible
        assert "thresholds" in config
        assert "retry" in config
        assert config["thresholds"]["low_ctr"] == low_ctr
        assert config["thresholds"]["high_confidence"] == high_confidence
        assert config["retry"]["max_retries"] == max_retries
        
        # Test get method for accessing nested values
        assert loader.get("thresholds.low_ctr") == low_ctr
        assert loader.get("retry.max_retries") == max_retries
        
    finally:
        # Clean up
        os.unlink(temp_config_path)


# Feature: kasparro-fb-analyst, Property 27: Configuration Threshold Validation
# Validates: Requirements 8.2
@settings(max_examples=100)
@given(
    threshold_value=st.floats(min_value=-10.0, max_value=10.0),
)
def test_property_27_configuration_threshold_validation(threshold_value):
    """
    Property 27: Configuration Threshold Validation
    For any loaded configuration, threshold values should be validated
    to be within acceptable ranges (0 to 1).
    """
    # Create a temporary config file with threshold
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        config_data = {
            "thresholds": {
                "low_ctr": threshold_value,
            },
        }
        yaml.dump(config_data, f)
        temp_config_path = f.name
    
    try:
        loader = ConfigLoader(temp_config_path)
        
        # If threshold is in valid range [0, 1], loading should succeed
        if 0 <= threshold_value <= 1:
            config = loader.load()
            assert config["thresholds"]["low_ctr"] == threshold_value
        else:
            # If threshold is outside valid range, should raise ConfigurationError
            with pytest.raises(ConfigurationError) as exc_info:
                loader.load()
            assert "must be between 0 and 1" in str(exc_info.value)
    
    finally:
        # Clean up
        os.unlink(temp_config_path)


# Feature: kasparro-fb-analyst, Property 28: Random Seed Reproducibility
# Validates: Requirements 8.5
@settings(max_examples=100)
@given(
    seed=st.integers(min_value=0, max_value=1000000),
    list_size=st.integers(min_value=10, max_value=100),
)
def test_property_28_random_seed_reproducibility(seed, list_size):
    """
    Property 28: Random Seed Reproducibility
    For any two system executions with the same random_seed and identical input data,
    all random operations should produce identical results.
    """
    # Create config with random seed
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        config_data = {
            "random_seed": seed,
        }
        yaml.dump(config_data, f)
        temp_config_path = f.name
    
    try:
        # Load config and set random seed - first execution
        loader1 = ConfigLoader(temp_config_path)
        config1 = loader1.load()
        random.seed(config1["random_seed"])
        result1 = [random.random() for _ in range(list_size)]
        
        # Load config and set random seed - second execution
        loader2 = ConfigLoader(temp_config_path)
        config2 = loader2.load()
        random.seed(config2["random_seed"])
        result2 = [random.random() for _ in range(list_size)]
        
        # Assert both executions produce identical results
        assert result1 == result2
        assert config1["random_seed"] == config2["random_seed"] == seed
    
    finally:
        # Clean up
        os.unlink(temp_config_path)


def test_configuration_loading_with_missing_file():
    """Test that missing config file uses defaults."""
    # Use a non-existent path
    loader = ConfigLoader("nonexistent/config.yaml")
    config = loader.load()
    
    # Should load with defaults
    assert config is not None
    assert "thresholds" in config
    assert "retry" in config
    assert config["thresholds"]["low_ctr"] == 0.01  # Default value


def test_configuration_loading_with_invalid_yaml():
    """Test that invalid YAML raises ConfigurationError."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("invalid: yaml: content: [")
        temp_config_path = f.name
    
    try:
        loader = ConfigLoader(temp_config_path)
        with pytest.raises(ConfigurationError):
            loader.load()
    finally:
        os.unlink(temp_config_path)
