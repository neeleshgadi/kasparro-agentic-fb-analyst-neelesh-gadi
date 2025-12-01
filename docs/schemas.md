# Kasparro JSON Schemas Documentation

This document provides comprehensive documentation of all JSON schemas used for agent communication in the Kasparro system.

## Table of Contents

1. [Communication Envelope](#communication-envelope)
2. [Planner Agent Schemas](#planner-agent-schemas)
3. [Data Agent Schemas](#data-agent-schemas)
4. [Insight Agent Schemas](#insight-agent-schemas)
5. [Evaluator Agent Schemas](#evaluator-agent-schemas)
6. [Creative Generator Schemas](#creative-generator-schemas)
7. [Report Generator Schemas](#report-generator-schemas)
8. [Error Response Schema](#error-response-schema)

---

## Communication Envelope

All agents use a standard communication envelope for consistency and traceability.

### Standard Envelope Schema

```json
{
  "envelope": {
    "agent_name": "string",
    "timestamp": "string (ISO 8601 format)",
    "execution_duration_ms": "integer",
    "status": "string (success|failure|partial)"
  },
  "payload": {
    // Agent-specific output
  },
  "metadata": {
    "config_version": "string",
    "dataset_hash": "string (MD5)",
    "python_version": "string"
  }
}
```

### Field Descriptions

- **envelope.agent_name**: Name of the agent that produced this output
- **envelope.timestamp**: ISO 8601 formatted timestamp (e.g., "2024-01-15T10:30:00Z")
- **envelope.execution_duration_ms**: Time taken to execute in milliseconds
- **envelope.status**: Execution status (success, failure, or partial)
- **metadata.config_version**: Version of configuration used
- **metadata.dataset_hash**: MD5 hash of the dataset for reproducibility
- **metadata.python_version**: Python version used for execution

### Example

```json
{
  "envelope": {
    "agent_name": "data_agent",
    "timestamp": "2024-01-15T10:30:00.123Z",
    "execution_duration_ms": 1250,
    "status": "success"
  },
  "payload": {
    "summary": { ... }
  },
  "metadata": {
    "config_version": "1.0",
    "dataset_hash": "a1b2c3d4e5f6",
    "python_version": "3.9.7"
  }
}
```

---

## Planner Agent Schemas

### Input Schema

```json

```

{
"query": "string",
"context": {
"dataset_path": "string",
"config": "object"
}
}

````

### Output Schema

```json
{
  "agent_name": "planner",
  "timestamp": "string (ISO 8601)",
  "execution_duration_ms": "integer",
  "task": "string",
  "date_range": {
    "from": "string (YYYY-MM-DD)",
    "to": "string (YYYY-MM-DD)"
  },
  "steps": ["array of strings"],
  "task_plan": [
    {
      "step_id": "integer",
      "agent": "string",
      "action": "string",
      "parameters": "object"
    }
  ],
  "routing": {
    "next_agent": "string",
    "workflow_type": "string (analysis|creative_generation|full)"
  },
  "metadata": {
    "agent": "planner",
    "timestamp": "string (ISO 8601)"
  }
}
````

### Field Descriptions

- **task**: Type of analysis requested (e.g., "roas_analysis", "creative_generation")
- **date_range**: Extracted time period for analysis
- **steps**: High-level workflow steps
- **task_plan**: Detailed execution plan with agent routing
- **routing.next_agent**: First agent to execute in the workflow
- **routing.workflow_type**: Type of workflow (analysis, creative_generation, or full)

### Example

```json
{
  "agent_name": "planner",
  "timestamp": "2024-01-15T10:30:00Z",
  "execution_duration_ms": 250,
  "task": "roas_analysis",
  "date_range": {
    "from": "2024-01-01",
    "to": "2024-01-14"
  },
  "steps": ["load_data", "generate_hypothesis", "validate", "report"],
  "task_plan": [
    {
      "step_id": 1,
      "agent": "data_agent",
      "action": "load_and_analyze_dataset",
      "parameters": {
        "date_range": { "from": "2024-01-01", "to": "2024-01-14" },
        "metrics": ["roas", "ctr", "cvr"]
      }
    },
    {
      "step_id": 2,
      "agent": "insight_agent",
      "action": "generate_hypotheses",
      "parameters": { "focus_metric": "roas" }
    }
  ],
  "routing": {
    "next_agent": "data_agent",
    "workflow_type": "full"
  }
}
```

---

## Data Agent Schemas

### Input Schema

```json
{
  "dataset_path": "string",
  "date_range": {
    "start_date": "string (YYYY-MM-DD)",
    "end_date": "string (YYYY-MM-DD)"
  },
  "metrics": ["array of strings"],
  "config": "object"
}
```

### Output Schema

```json
{
  "agent_name": "data_agent",
  "timestamp": "string (ISO 8601)",
  "execution_duration_ms": "integer",
  "summary": {
    "rows": "integer",
    "date_range": ["string", "string"],
    "total_spend": "float",
    "total_revenue": "float",
    "mean_roas": "float",
    "mean_ctr": "float",
    "campaigns_count": "integer"
  },
  "dataset_summary": {
    "total_rows": "integer",
    "date_range": {
      "start": "string",
      "end": "string"
    },
    "total_spend": "float",
    "total_revenue": "float",
    "campaigns_count": "integer",
    "data_quality": {
      "missing_values": "object",
      "invalid_rows": "integer"
    }
  },
  "metrics": {
    "overall_roas": "float",
    "overall_ctr": "float",
    "avg_cpc": "float",
    "conversion_rate": "float"
  },
  "trends": {
    "roas_trend": {
      "direction": "string (increasing|decreasing|stable)",
      "week_over_week_change": "float",
      "month_over_month_change": "float"
    },
    "ctr_trend": {
      "direction": "string",
      "week_over_week_change": "float",
      "month_over_month_change": "float"
    }
  },
  "segmentation": {
    "by_campaign": "array of objects",
    "by_creative_type": "array of objects",
    "by_audience_type": "array of objects",
    "by_platform": "array of objects"
  },
  "data_quality_issues": "array of objects"
}
```

### Field Descriptions

- **summary**: High-level dataset statistics
- **metrics**: Computed performance metrics
- **trends**: Week-over-week and month-over-month changes
- **segmentation**: Performance broken down by dimensions
- **data_quality_issues**: List of detected data quality problems

### Example

```json
{
  "agent_name": "data_agent",
  "timestamp": "2024-01-15T10:30:01Z",
  "execution_duration_ms": 1250,
  "summary": {
    "rows": 1280,
    "date_range": ["2024-01-01", "2024-02-15"],
    "total_spend": 51452.2,
    "total_revenue": 124898.33,
    "mean_roas": 2.43,
    "mean_ctr": 0.0121,
    "campaigns_count": 15
  },
  "metrics": {
    "overall_roas": 2.43,
    "overall_ctr": 0.0121,
    "avg_cpc": 0.85,
    "conversion_rate": 0.042
  },
  "trends": {
    "roas_trend": {
      "direction": "decreasing",
      "week_over_week_change": -4.7,
      "month_over_month_change": -8.2
    },
    "ctr_trend": {
      "direction": "decreasing",
      "week_over_week_change": -11.3,
      "month_over_month_change": -15.1
    }
  },
  "segmentation": {
    "by_campaign": [
      {
        "campaign_name": "Undergarments_Male_18-24",
        "roas": 1.87,
        "ctr": 0.0087,
        "spend": 8234.5
      }
    ]
  },
  "data_quality_issues": []
}
```

---

## Insight Agent Schemas

### Input Schema

```json
{
  "data_summary": "object (from Data Agent)",
  "focus_metric": "string",
  "time_period": "object",
  "config": "object"
}
```

### Output Schema

```json
{
  "agent_name": "insight_agent",
  "timestamp": "string (ISO 8601)",
  "execution_duration_ms": "integer",
  "hypotheses": [
    {
      "hypothesis_id": "string",
      "hypothesis_text": "string",
      "category": "string (creative|audience|platform|budget|seasonality)",
      "supporting_observations": ["array of strings"],
      "evidence_used": ["array of strings"],
      "initial_confidence": "float (0-1)",
      "confidence_score": "float (0-1)",
      "testable": "boolean",
      "validation_approach": "string"
    }
  ],
  "reasoning": {
    "think": "string",
    "analyze": "string",
    "conclude": "string"
  }
}
```

### Field Descriptions

- **hypotheses**: Array of generated hypotheses (3-5 items)
- **hypothesis_id**: Unique identifier for tracking
- **category**: Type of hypothesis for classification
- **supporting_observations**: Data patterns that support the hypothesis
- **initial_confidence**: Confidence before validation (0-1)
- **testable**: Whether hypothesis can be validated with available data
- **reasoning**: Structured reasoning chain (Think-Analyze-Conclude)

### Example

```json
{
  "agent_name": "insight_agent",
  "timestamp": "2024-01-15T10:30:03Z",
  "execution_duration_ms": 1800,
  "hypotheses": [
    {
      "hypothesis_id": "h1",
      "hypothesis_text": "CTR drop in male 18-24 segment caused ROAS decline",
      "category": "audience",
      "supporting_observations": [
        "Male 18-24 CTR dropped 24.2%",
        "ROAS declined 17.1% in same period",
        "Other segments showed stable CTR"
      ],
      "evidence_used": ["ctr_wow_change", "roas_change", "segmentation"],
      "initial_confidence": 0.63,
      "confidence_score": 0.63,
      "testable": true,
      "validation_approach": "Compare male 18-24 segment performance vs other segments"
    },
    {
      "hypothesis_id": "h2",
      "hypothesis_text": "Image creative fatigue in female segments",
      "category": "creative",
      "supporting_observations": [
        "Image creative CTR down 18% in female segments",
        "Video creative CTR stable or increasing"
      ],
      "evidence_used": ["creative_type_segmentation"],
      "initial_confidence": 0.58,
      "confidence_score": 0.58,
      "testable": true,
      "validation_approach": "Compare image vs video creative performance in female segments"
    }
  ],
  "reasoning": {
    "think": "ROAS declined 9% with CTR dropping 11.3%. Need to identify which segments drove the decline.",
    "analyze": "Male 18-24 segment shows disproportionate CTR drop (24.2% vs 11.3% overall). This segment represents 32% of spend.",
    "conclude": "Male 18-24 CTR drop is the primary driver of ROAS decline. Secondary factor is image creative fatigue in female segments."
  }
}
```

---

## Evaluator Agent Schemas

### Input Schema

```json
{
  "hypotheses": "array (from Insight Agent)",
  "dataset_path": "string",
  "data_summary": "object (from Data Agent)",
  "config": "object"
}
```

### Output Schema

```json
{
  "agent_name": "evaluator_agent",
  "timestamp": "string (ISO 8601)",
  "execution_duration_ms": "integer",
  "validated_hypotheses": [
    {
      "hypothesis_id": "string",
      "hypothesis_text": "string",
      "validation_status": "string (confirmed|rejected|inconclusive)",
      "evidence": {
        "metrics": [
          {
            "metric_name": "string",
            "value": "float",
            "comparison": "string"
          }
        ],
        "statistical_significance": {
          "p_value": "float",
          "confidence_interval": ["float", "float"]
        }
      },
      "adjusted_confidence_score": "float (0-1)",
      "validation_reasoning": "string"
    }
  ],
  "top_insights": [
    {
      "hypothesis": "string",
      "validated_confidence": "float (0-1)"
    }
  ],
  "reasoning": {
    "think": "string",
    "analyze": "string",
    "conclude": "string"
  }
}
```

### Field Descriptions

- **validated_hypotheses**: Hypotheses with validation results
- **validation_status**: Result of validation (confirmed/rejected/inconclusive)
- **evidence.metrics**: Supporting metrics computed from dataset
- **statistical_significance**: P-values and confidence intervals when applicable
- **adjusted_confidence_score**: Confidence after validation (weighted formula)
- **top_insights**: Top 3 hypotheses ranked by confidence

### Example

```json
{
  "agent_name": "evaluator_agent",
  "timestamp": "2024-01-15T10:30:06Z",
  "execution_duration_ms": 2500,
  "validated_hypotheses": [
    {
      "hypothesis_id": "h1",
      "hypothesis_text": "CTR drop in male 18-24 segment caused ROAS decline",
      "validation_status": "confirmed",
      "evidence": {
        "metrics": [
          {
            "metric_name": "ctr_change",
            "value": -24.2,
            "comparison": "Male 18-24 CTR decreased 24.2% vs overall 11.3%"
          },
          {
            "metric_name": "roas_change",
            "value": -17.1,
            "comparison": "ROAS declined 17.1% in same period"
          },
          {
            "metric_name": "spend_share",
            "value": 0.32,
            "comparison": "Segment represents 32% of total spend"
          }
        ],
        "statistical_significance": {
          "p_value": 0.041,
          "confidence_interval": [0.15, 0.32]
        }
      },
      "adjusted_confidence_score": 0.82,
      "validation_reasoning": "Strong correlation between CTR drop and ROAS decline with statistical significance. Segment size makes impact material."
    }
  ],
  "top_insights": [
    {
      "hypothesis": "Male 18-24 CTR drop caused ROAS decline",
      "validated_confidence": 0.82
    }
  ],
  "reasoning": {
    "think": "Need to validate each hypothesis by computing segment-specific metrics and comparing to overall trends.",
    "analyze": "H1 shows strong evidence: 24.2% CTR drop in male 18-24 vs 11.3% overall, with p-value 0.041. H2 shows moderate evidence: 18% image CTR drop in female segments.",
    "conclude": "H1 confirmed with high confidence (0.82). H2 partially confirmed with moderate confidence (0.67)."
  }
}
```

---

## Creative Generator Schemas

### Input Schema

```json
{
  "data_summary": "object (from Data Agent)",
  "low_ctr_threshold": "float",
  "dataset_path": "string",
  "config": "object"
}
```

### Output Schema

```json
{
  "agent_name": "creative_generator",
  "timestamp": "string (ISO 8601)",
  "execution_duration_ms": "integer",
  "recommendations": [
    {
      "campaign_name": "string",
      "current_ctr": "float",
      "current_creative_type": "string",
      "current_message": "string",
      "new_creatives": [
        {
          "creative_id": "string",
          "creative_type": "string (image|video|carousel)",
          "creative_message": "string",
          "audience_type": "string",
          "rationale": "string",
          "confidence_score": "float (0-1)",
          "expected_ctr_improvement": "float"
        }
      ]
    }
  ],
  "reasoning": {
    "think": "string",
    "analyze": "string",
    "conclude": "string"
  }
}
```

### Field Descriptions

- **recommendations**: Array of campaign-specific creative recommendations
- **current_ctr**: Current CTR of the campaign
- **new_creatives**: 3+ creative variations per campaign
- **creative_type**: Format of the creative (image, video, carousel)
- **creative_message**: Ad copy text
- **rationale**: Explanation for why this creative should perform better
- **expected_ctr_improvement**: Estimated CTR increase

### Example

```json
{
  "agent_name": "creative_generator",
  "timestamp": "2024-01-15T10:30:08Z",
  "execution_duration_ms": 1500,
  "recommendations": [
    {
      "campaign_name": "Undergarments_Male_18-24",
      "current_ctr": 0.0087,
      "current_creative_type": "image",
      "current_message": "Premium comfort for everyday wear",
      "new_creatives": [
        {
          "creative_id": "c1",
          "creative_type": "carousel",
          "creative_message": "Minimalist athletic cotton stretch — Buy 1 Get 1",
          "audience_type": "male_18_24_interest_fitness",
          "rationale": "Carousel format shows 35% higher CTR for this demographic. BOGO offers drive 28% higher conversion rates.",
          "confidence_score": 0.78,
          "expected_ctr_improvement": 0.0032
        },
        {
          "creative_id": "c2",
          "creative_type": "video",
          "creative_message": "Comfort meets performance. Premium fabrics, everyday prices.",
          "audience_type": "male_18_24_interest_fashion",
          "rationale": "Video creatives achieve 42% higher engagement in male 18-24 segment. Value messaging resonates with price-conscious audience.",
          "confidence_score": 0.75,
          "expected_ctr_improvement": 0.0029
        },
        {
          "creative_id": "c3",
          "creative_type": "carousel",
          "creative_message": "Upgrade your basics. 3-pack bundles starting at $29",
          "audience_type": "male_18_24_interest_shopping",
          "rationale": "Bundle offers increase average order value by 45%. Carousel showcases product variety effectively.",
          "confidence_score": 0.72,
          "expected_ctr_improvement": 0.0025
        }
      ]
    }
  ],
  "reasoning": {
    "think": "Identify campaigns with CTR < 0.01. Analyze high-performing creative patterns in similar segments.",
    "analyze": "Male 18-24 campaign has CTR 0.0087. High-performing campaigns in this segment use carousel (CTR 0.0142) and video (CTR 0.0138) formats. BOGO and bundle offers show strong performance.",
    "conclude": "Recommend 3 creative variations focusing on carousel and video formats with promotional messaging."
  }
}
```

---

## Report Generator Schemas

### Input Schema

```json
{
  "insights": "object (from Evaluator Agent)",
  "creatives": "object (from Creative Generator)",
  "data_summary": "object (from Data Agent)",
  "query": "string (original user query)"
}
```

### Output

The Report Generator produces a Markdown file (report.md) rather than JSON. The file contains:

1. **Executive Summary**: High-level findings and key metrics
2. **Key Insights**: Top 3 validated hypotheses with evidence
3. **Creative Recommendations**: New creative suggestions with rationale
4. **Methodology**: Explanation of analysis approach

See the [README.md](../README.md) for a complete example report.

---

## Error Response Schema

When any agent encounters an error, it returns a standardized error response:

```json
{
  "envelope": {
    "agent_name": "string",
    "timestamp": "string (ISO 8601)",
    "execution_duration_ms": "integer",
    "status": "failure"
  },
  "error": {
    "error_type": "string (ValidationError|IOError|TimeoutError|UnexpectedError)",
    "error_message": "string (human-readable description)",
    "error_details": {
      "field": "string",
      "value": "any",
      "context": "string"
    },
    "stack_trace": "string (if unexpected error)"
  }
}
```

### Error Types

- **ValidationError**: Schema validation failed or data validation failed
- **IOError**: File not found, cannot write output, permissions error
- **TimeoutError**: Agent execution exceeded timeout limit
- **UnexpectedError**: Unexpected exception during execution

### Example Error Response

```json
{
  "envelope": {
    "agent_name": "data_agent",
    "timestamp": "2024-01-15T10:30:00Z",
    "execution_duration_ms": 150,
    "status": "failure"
  },
  "error": {
    "error_type": "ValidationError",
    "error_message": "Missing required field in dataset",
    "error_details": {
      "field": "campaign_name",
      "row": 42,
      "context": "Required field 'campaign_name' is missing in row 42"
    }
  }
}
```

---

## Schema Validation

All schemas are validated using the `jsonschema` library. Validation functions are provided in `src/schemas/validation.py`:

```python
from src.schemas.validation import validate_agent_input, validate_agent_output

# Validate input before processing
validate_agent_input(agent_name="data_agent", data=input_data)

# Validate output before returning
validate_agent_output(agent_name="data_agent", data=output_data)
```

### Validation Rules

1. **Required Fields**: All required fields must be present
2. **Type Checking**: Fields must match specified types (string, integer, float, array, object)
3. **Range Validation**: Numeric fields must be within valid ranges (e.g., confidence scores 0-1)
4. **Format Validation**: Dates must be ISO 8601, timestamps must be valid
5. **Enum Validation**: String fields with limited values must match allowed values

---

## Configuration Schema

The `config/config.yaml` file follows this schema:

```yaml
# Thresholds for analysis
thresholds:
  low_ctr: float (0-1) # CTR below this triggers creative recommendations
  high_confidence: float (0-1) # Confidence threshold for top insights
  roas_change_significant: float # Percentage change considered significant

# Agent-specific configuration
agents:
  max_hypotheses: integer # Maximum hypotheses per Insight Agent run
  min_data_points: integer # Minimum data points for trend analysis

# Retry logic configuration
retry:
  max_retries: integer # Maximum retry attempts on failure
  backoff_multiplier: float # Exponential backoff multiplier

# Logging configuration
logging:
  level: string (DEBUG|INFO|WARNING|ERROR) # Log level
  format: string (json|text) # Log format

# Reproducibility
random_seed: integer # Random seed for reproducible operations

# Data quality thresholds
data_quality:
  max_missing_percentage: float (0-1) # Fail if missing values exceed this
  date_format: string # Expected date format (e.g., "%Y-%m-%d")
```

### Example Configuration

```yaml
thresholds:
  low_ctr: 0.01
  high_confidence: 0.7
  roas_change_significant: 0.15

agents:
  max_hypotheses: 5
  min_data_points: 10

retry:
  max_retries: 3
  backoff_multiplier: 2

logging:
  level: "INFO"
  format: "json"

random_seed: 42

data_quality:
  max_missing_percentage: 0.1
  date_format: "%Y-%m-%d"
```

---

## Dataset Schema

The input dataset (`data/synthetic_fb_ads_undergarments.csv`) must contain these fields:

| Field            | Type    | Required | Description                               |
| ---------------- | ------- | -------- | ----------------------------------------- |
| campaign_name    | string  | Yes      | Campaign identifier                       |
| adset_name       | string  | Yes      | Ad set identifier                         |
| date             | date    | Yes      | Performance date (YYYY-MM-DD)             |
| spend            | float   | Yes      | Ad spend in currency units                |
| impressions      | integer | Yes      | Number of ad impressions                  |
| clicks           | integer | Yes      | Number of clicks                          |
| ctr              | float   | Yes      | Click-through rate (clicks/impressions)   |
| purchases        | integer | Yes      | Number of conversions                     |
| revenue          | float   | Yes      | Revenue generated                         |
| roas             | float   | Yes      | Return on ad spend (revenue/spend)        |
| creative_type    | string  | Yes      | Type of creative (image, video, carousel) |
| creative_message | string  | No       | Ad copy text                              |
| audience_type    | string  | Yes      | Target audience segment                   |
| platform         | string  | Yes      | Platform (Facebook, Instagram)            |
| country          | string  | No       | Geographic target                         |

### Example Dataset Row

```csv
campaign_name,adset_name,date,spend,impressions,clicks,ctr,purchases,revenue,roas,creative_type,creative_message,audience_type,platform,country
Undergarments_Male_18-24,Adset_001,2024-01-15,250.50,28500,248,0.0087,12,468.75,1.87,image,Premium comfort for everyday wear,male_18_24_interest_fitness,Facebook,US
```

---

## Summary

This document provides complete schema definitions for all agent communications in the Kasparro system. Key points:

- All agents use a standard communication envelope
- Input and output schemas are strictly validated
- Error responses follow a consistent format
- Configuration is externalized and validated
- Dataset schema is well-defined with required fields

For implementation details, see:

- `src/schemas/agent_io.py` - Schema definitions
- `src/schemas/validation.py` - Validation functions
- `agent_graph.md` - Agent workflow and interactions
- `README.md` - Usage examples and quickstart guide
