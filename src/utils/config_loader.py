"""Configuration loader with validation for Kasparro system."""

import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml


class ConfigurationError(Exception):
    """Raised when configuration is invalid or cannot be loaded."""
    pass


class ConfigLoader:
    """Loads and validates system configuration from YAML files."""
    
    DEFAULT_CONFIG = {
        "thresholds": {
            "low_ctr": 0.01,
            "high_confidence": 0.7,
            "roas_change_significant": 0.15,
            "trend_stable_threshold": 0.05,
        },
        "agents": {
            "max_hypotheses": 5,
            "min_data_points": 10,
            "min_creatives_per_campaign": 3,
        },
        "retry": {
            "max_retries": 3,
            "backoff_multiplier": 2,
            "base_delay": 1.0,
        },
        "logging": {
            "level": "INFO",
            "format": "json",
            "log_dir": "logs",
        },
        "random_seed": 42,
        "data_quality": {
            "max_missing_percentage": 0.1,
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
        "confidence_weights": {
            "insight_confidence": 0.4,
            "validation_strength": 0.4,
            "segmentation_evidence": 0.2,
        },
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize config loader.
        
        Args:
            config_path: Path to config file. If None, uses default path.
        """
        if config_path is None:
            config_path = "config/config.yaml"
        self.config_path = config_path
        self._config: Optional[Dict[str, Any]] = None
    
    def load(self) -> Dict[str, Any]:
        """Load configuration from file with validation.
        
        Returns:
            Configuration dictionary
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        if self._config is not None:
            return self._config
        
        # Try to load from file
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    loaded_config = yaml.safe_load(f)
                    if loaded_config is None:
                        loaded_config = {}
            except Exception as e:
                raise ConfigurationError(f"Failed to load config from {self.config_path}: {e}")
        else:
            # Use defaults if file doesn't exist
            loaded_config = {}
        
        # Merge with defaults
        self._config = self._merge_with_defaults(loaded_config)
        
        # Validate configuration
        self._validate_config(self._config)
        
        return self._config
    
    def _merge_with_defaults(self, loaded_config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge loaded config with defaults.
        
        Args:
            loaded_config: Configuration loaded from file
            
        Returns:
            Merged configuration
        """
        import copy
        config = copy.deepcopy(self.DEFAULT_CONFIG)
        
        # Deep merge
        for key, value in loaded_config.items():
            if key in config and isinstance(config[key], dict) and isinstance(value, dict):
                config[key].update(value)
            else:
                config[key] = value
        
        return config
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """Validate configuration values.
        
        Args:
            config: Configuration to validate
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        # Validate thresholds are between 0 and 1
        thresholds = config.get("thresholds", {})
        for key, value in thresholds.items():
            if not isinstance(value, (int, float)):
                raise ConfigurationError(f"Threshold '{key}' must be numeric, got {type(value)}")
            if not (0 <= value <= 1):
                raise ConfigurationError(
                    f"Threshold '{key}' must be between 0 and 1, got {value}"
                )
        
        # Validate agent settings
        agents = config.get("agents", {})
        if "max_hypotheses" in agents:
            if not isinstance(agents["max_hypotheses"], int) or agents["max_hypotheses"] < 1:
                raise ConfigurationError("agents.max_hypotheses must be a positive integer")
        
        if "min_data_points" in agents:
            if not isinstance(agents["min_data_points"], int) or agents["min_data_points"] < 1:
                raise ConfigurationError("agents.min_data_points must be a positive integer")
        
        # Validate retry settings
        retry = config.get("retry", {})
        if "max_retries" in retry:
            if not isinstance(retry["max_retries"], int) or retry["max_retries"] < 0:
                raise ConfigurationError("retry.max_retries must be a non-negative integer")
        
        if "backoff_multiplier" in retry:
            if not isinstance(retry["backoff_multiplier"], (int, float)) or retry["backoff_multiplier"] < 1:
                raise ConfigurationError("retry.backoff_multiplier must be >= 1")
        
        if "base_delay" in retry:
            if not isinstance(retry["base_delay"], (int, float)) or retry["base_delay"] < 0:
                raise ConfigurationError("retry.base_delay must be non-negative")
        
        # Validate confidence weights sum to 1.0
        weights = config.get("confidence_weights", {})
        if weights:
            weight_sum = sum(weights.values())
            if not (0.99 <= weight_sum <= 1.01):  # Allow small floating point error
                raise ConfigurationError(
                    f"Confidence weights must sum to 1.0, got {weight_sum}"
                )
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key.
        
        Args:
            key: Configuration key (supports dot notation, e.g., 'thresholds.low_ctr')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        if self._config is None:
            self.load()
        
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from file.
    
    Args:
        config_path: Path to config file. If None, uses default path.
        
    Returns:
        Configuration dictionary
    """
    loader = ConfigLoader(config_path)
    return loader.load()
