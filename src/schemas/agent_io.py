"""
JSON schemas for agent input/output communication.

This module defines all JSON schemas used for inter-agent communication
in the Kasparro multi-agent system.
"""

from typing import Any, Dict

# Standard communication envelope schema
ENVELOPE_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "agent_name": {"type": "string"},
        "timestamp": {"type": "string", "format": "date-time"},
        "execution_duration_ms": {"type": "integer", "minimum": 0},
        "status": {"type": "string", "enum": ["success", "failure", "partial"]},
        "error": {
            "type": "object",
            "properties": {
                "error_type": {
                    "type": "string",
                    "enum": ["ValidationError", "IOError", "TimeoutError", "UnexpectedError"]
                },
                "error_message": {"type": "string"},
                "error_details": {"type": "object"},
                "stack_trace": {"type": "string"}
            },
            "required": ["error_type", "error_message"]
        }
    },
    "required": ["agent_name", "timestamp", "status"]
}

# Planner Agent schemas
PLANNER_INPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "query": {"type": "string"},
        "context": {
            "type": "object",
            "properties": {
                "dataset_path": {"type": "string"},
                "config": {"type": "object"}
            },
            "required": ["dataset_path", "config"]
        }
    },
    "required": ["query", "context"]
}

PLANNER_OUTPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "agent_name": {"type": "string"},
        "timestamp": {"type": "string", "format": "date-time"},
        "execution_duration_ms": {"type": "integer", "minimum": 0},
        "task": {"type": "string"},
        "date_range": {
            "type": "object",
            "properties": {
                "from": {"type": "string"},
                "to": {"type": "string"}
            }
        },
        "steps": {
            "type": "array",
            "items": {"type": "string"}
        },
        "task_plan": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "step_id": {"type": "integer"},
                    "agent": {"type": "string"},
                    "action": {"type": "string"},
                    "parameters": {"type": "object"}
                },
                "required": ["step_id", "agent", "action"]
            }
        },
        "routing": {
            "type": "object",
            "properties": {
                "next_agent": {"type": "string"},
                "workflow_type": {"type": "string"}
            },
            "required": ["next_agent", "workflow_type"]
        },
        "metadata": {
            "type": "object",
            "properties": {
                "agent": {"type": "string"},
                "timestamp": {"type": "string"}
            }
        }
    },
    "required": ["agent_name", "timestamp", "execution_duration_ms", "task", "routing"]
}

# Data Agent schemas
DATA_AGENT_INPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "dataset_path": {"type": "string"},
        "date_range": {
            "type": "object",
            "properties": {
                "start_date": {"type": "string"},
                "end_date": {"type": "string"}
            }
        },
        "metrics": {
            "type": "array",
            "items": {"type": "string"}
        },
        "config": {"type": "object"}
    },
    "required": ["dataset_path", "config"]
}

DATA_AGENT_OUTPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "agent_name": {"type": "string"},
        "timestamp": {"type": "string", "format": "date-time"},
        "execution_duration_ms": {"type": "integer", "minimum": 0},
        "dataset_summary": {
            "type": "object",
            "properties": {
                "total_rows": {"type": "integer", "minimum": 0},
                "date_range": {
                    "type": "object",
                    "properties": {
                        "start": {"type": "string"},
                        "end": {"type": "string"}
                    },
                    "required": ["start", "end"]
                },
                "total_spend": {"type": "number"},
                "total_revenue": {"type": "number"},
                "campaigns_count": {"type": "integer", "minimum": 0},
                "data_quality": {
                    "type": "object",
                    "properties": {
                        "missing_values": {"type": "object"},
                        "invalid_rows": {"type": "integer", "minimum": 0}
                    }
                }
            },
            "required": ["total_rows", "date_range", "campaigns_count"]
        },
        "metrics": {
            "type": "object",
            "properties": {
                "overall_roas": {"type": "number"},
                "overall_ctr": {"type": "number"},
                "avg_cpc": {"type": "number"},
                "conversion_rate": {"type": "number"}
            }
        },
        "trends": {
            "type": "object",
            "properties": {
                "roas_trend": {
                    "type": "object",
                    "properties": {
                        "direction": {"type": "string", "enum": ["increasing", "decreasing", "stable"]},
                        "week_over_week_change": {"type": "number"},
                        "month_over_month_change": {"type": "number"}
                    }
                },
                "ctr_trend": {
                    "type": "object",
                    "properties": {
                        "direction": {"type": "string", "enum": ["increasing", "decreasing", "stable"]},
                        "week_over_week_change": {"type": "number"},
                        "month_over_month_change": {"type": "number"}
                    }
                }
            }
        },
        "segmentation": {
            "type": "object",
            "properties": {
                "by_campaign": {"type": "array"},
                "by_creative_type": {"type": "array"},
                "by_audience_type": {"type": "array"},
                "by_platform": {"type": "array"}
            }
        },
        "data_quality_issues": {
            "type": "array",
            "items": {"type": "object"}
        }
    },
    "required": ["agent_name", "timestamp", "execution_duration_ms", "dataset_summary", "metrics"]
}

# Insight Agent schemas
INSIGHT_AGENT_INPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "data_summary": {"type": "object"},
        "focus_metric": {"type": "string"},
        "time_period": {"type": "object"},
        "config": {"type": "object"}
    },
    "required": ["data_summary", "config"]
}

INSIGHT_AGENT_OUTPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "agent_name": {"type": "string"},
        "timestamp": {"type": "string", "format": "date-time"},
        "execution_duration_ms": {"type": "integer", "minimum": 0},
        "hypotheses": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "hypothesis_id": {"type": "string"},
                    "hypothesis_text": {"type": "string"},
                    "category": {
                        "type": "string",
                        "enum": ["creative", "audience", "platform", "budget", "seasonality"]
                    },
                    "supporting_observations": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "evidence_used": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "confidence_score": {"type": "number", "minimum": 0, "maximum": 1},
                    "testable": {"type": "boolean"},
                    "validation_approach": {"type": "string"}
                },
                "required": ["hypothesis_id", "hypothesis_text", "category", "confidence_score"]
            },
            "minItems": 3
        },
        "reasoning": {
            "type": "object",
            "properties": {
                "think": {"type": "string"},
                "analyze": {"type": "string"},
                "conclude": {"type": "string"}
            },
            "required": ["think", "analyze", "conclude"]
        }
    },
    "required": ["agent_name", "timestamp", "execution_duration_ms", "hypotheses", "reasoning"]
}

# Evaluator Agent schemas
EVALUATOR_INPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "hypotheses": {"type": "array"},
        "dataset_path": {"type": "string"},
        "data_summary": {"type": "object"},
        "config": {"type": "object"}
    },
    "required": ["hypotheses", "dataset_path", "data_summary", "config"]
}

EVALUATOR_OUTPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "agent_name": {"type": "string"},
        "timestamp": {"type": "string", "format": "date-time"},
        "execution_duration_ms": {"type": "integer", "minimum": 0},
        "validated_hypotheses": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "hypothesis_id": {"type": "string"},
                    "hypothesis_text": {"type": "string"},
                    "validation_status": {
                        "type": "string",
                        "enum": ["confirmed", "rejected", "inconclusive"]
                    },
                    "evidence": {
                        "type": "object",
                        "properties": {
                            "metrics": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "metric_name": {"type": "string"},
                                        "value": {"type": "number"},
                                        "comparison": {"type": "string"}
                                    },
                                    "required": ["metric_name", "value"]
                                },
                                "minItems": 2
                            },
                            "statistical_significance": {
                                "type": "object",
                                "properties": {
                                    "p_value": {"type": "number"},
                                    "confidence_interval": {
                                        "type": "array",
                                        "items": {"type": "number"},
                                        "minItems": 2,
                                        "maxItems": 2
                                    }
                                }
                            }
                        },
                        "required": ["metrics"]
                    },
                    "adjusted_confidence_score": {"type": "number", "minimum": 0, "maximum": 1},
                    "validation_reasoning": {"type": "string"}
                },
                "required": ["hypothesis_id", "hypothesis_text", "validation_status", "evidence", "adjusted_confidence_score"]
            }
        },
        "top_insights": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "hypothesis": {"type": "string"},
                    "validated_confidence": {"type": "number", "minimum": 0, "maximum": 1}
                },
                "required": ["hypothesis", "validated_confidence"]
            }
        },
        "reasoning": {
            "type": "object",
            "properties": {
                "think": {"type": "string"},
                "analyze": {"type": "string"},
                "conclude": {"type": "string"}
            },
            "required": ["think", "analyze", "conclude"]
        }
    },
    "required": ["agent_name", "timestamp", "execution_duration_ms", "validated_hypotheses", "reasoning"]
}

# Creative Generator schemas
CREATIVE_GENERATOR_INPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "data_summary": {"type": "object"},
        "low_ctr_threshold": {"type": "number"},
        "dataset_path": {"type": "string"},
        "config": {"type": "object"}
    },
    "required": ["data_summary", "dataset_path", "config"]
}

CREATIVE_GENERATOR_OUTPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "agent_name": {"type": "string"},
        "timestamp": {"type": "string", "format": "date-time"},
        "execution_duration_ms": {"type": "integer", "minimum": 0},
        "recommendations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "campaign": {"type": "string"},
                    "current_ctr": {"type": "number"},
                    "current_creative_type": {"type": "string"},
                    "current_message": {"type": "string"},
                    "new_creatives": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "creative_id": {"type": "string"},
                                "creative_type": {"type": "string"},
                                "creative_message": {"type": "string"},
                                "audience_type": {"type": "string"},
                                "rationale": {"type": "string"},
                                "confidence_score": {"type": "number", "minimum": 0, "maximum": 1},
                                "expected_ctr_improvement": {"type": "number"}
                            },
                            "required": ["creative_message", "creative_type", "audience_type", "rationale", "confidence_score"]
                        },
                        "minItems": 3
                    }
                },
                "required": ["campaign", "current_ctr", "new_creatives"]
            }
        },
        "reasoning": {
            "type": "object",
            "properties": {
                "think": {"type": "string"},
                "analyze": {"type": "string"},
                "conclude": {"type": "string"}
            },
            "required": ["think", "analyze", "conclude"]
        }
    },
    "required": ["agent_name", "timestamp", "execution_duration_ms", "recommendations", "reasoning"]
}

# Report Generator schemas
REPORT_GENERATOR_INPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "insights": {"type": "object"},
        "creatives": {"type": "object"},
        "data_summary": {"type": "object"},
        "query": {"type": "string"}
    },
    "required": ["insights", "creatives", "data_summary", "query"]
}
