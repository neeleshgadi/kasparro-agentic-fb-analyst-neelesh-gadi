# Design Document

## Overview

Kasparro is an autonomous multi-agent Facebook Ads Analyst designed to:

- Load and process campaign data from CSV
- Detect ROAS shifts and root-cause trends
- Generate hypotheses and validate with quantitative metrics
- Recommend new creatives for low CTR campaigns
- Produce structured outputs (JSON + Markdown Report)

The system is orchestrated through a Planner agent, with each agent independently modular, prompt-driven, and schema-validated. The system employs a directed acyclic graph (DAG) architecture where the Planner Agent orchestrates task decomposition and routing, while specialized agents (Data, Insight, Evaluator, Creative Generator) perform focused analytical tasks. The design emphasizes modularity, testability, and reproducibility through explicit schemas, externalized configuration, and structured logging.

The system processes the synthetic_fb_ads_undergarments.csv dataset containing campaign performance metrics and produces three primary outputs: insights.json (validated hypotheses about ROAS changes), creatives.json (ad creative recommendations for low-CTR campaigns), and report.md (executive summary in Markdown format).

**Key Principle**: Agents communicate only using JSON — NO direct function coupling.

## Architecture

### System Architecture

The system follows a **multi-agent orchestration pattern** with the following characteristics:

1. **Agent Autonomy**: Each agent operates independently with well-defined inputs and outputs
2. **Schema-Driven Communication**: All inter-agent communication uses validated JSON schemas
3. **Prompt-Based Reasoning**: Agents use structured prompts stored externally in markdown files
4. **Stateless Execution**: Agents do not maintain state between invocations
5. **Centralized Orchestration**: The Planner Agent coordinates workflow execution

### Agent Workflow

```mermaid
flowchart LR
    User[User Query] --> RunCLI[Run CLI]
    RunCLI --> Planner[Planner Agent]
    Planner --> DataAgent[Data Agent]
    DataAgent --> InsightAgent[Insight Agent]
    InsightAgent --> Evaluator[Evaluator Agent]
    Evaluator --> CreativeGen[Creative Generator]
    CreativeGen --> ReportBuilder[Report Builder]
    ReportBuilder --> Outputs[insights.json + creatives.json + report.md]
```

**Execution Sequence**:

1. User runs query → "Analyze ROAS last 7 days"
2. Planner extracts date window + goal → task breakdown
3. Data Agent loads dataset + generates trends
4. Insight Agent proposes causes for ROAS changes
5. Evaluator Agent validates numerically
6. Creative Generator finds low-CTR + proposes creatives
7. Final → insights.json, creatives.json, report.md

### Technology Stack

- **Language**: Python 3.9+
- **Data Processing**: pandas for dataset manipulation
- **Configuration**: PyYAML for config.yaml parsing
- **CLI**: argparse for command-line interface
- **Logging**: Python logging module with JSON formatting
- **Testing**: pytest for unit and integration tests
- **Schema Validation**: jsonschema library

### Directory Structure

```
kasparro/
├── config/
│   └── config.yaml
├── src/
│   ├── run.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── planner.py
│   │   ├── data_agent.py
│   │   ├── insight_agent.py
│   │   ├── evaluator_agent.py
│   │   └── creative_generator.py
│   ├── schemas/
│   │   ├── agent_io.py
│   │   └── validation.py
│   └── utils/
│       ├── logger.py
│       └── config_loader.py
├── prompts/
│   ├── planner_prompt.md
│   ├── data_agent_prompt.md
│   ├── insight_agent_prompt.md
│   ├── evaluator_agent_prompt.md
│   └── creative_generator_prompt.md
├── reports/
│   ├── insights.json
│   ├── creatives.json
│   └── report.md
├── logs/
│   └── execution_YYYYMMDD_HHMMSS.json
├── tests/
│   ├── test_evaluator.py
│   ├── test_data_agent.py
│   └── test_schemas.py
├── data/
│   └── synthetic_fb_ads_undergarments.csv
├── agent_graph.md
└── README.md
```

## Agent Responsibilities Summary

| Agent              | Responsibilities                                 | Output                               |
| ------------------ | ------------------------------------------------ | ------------------------------------ |
| Planner Agent      | Parse natural query, break task, route execution | Structured Task Graph JSON           |
| Data Agent         | Load CSV, compute metrics, trends, data quality  | summary + metrics + trend JSON       |
| Insight Agent      | Hypothesis generation for ROAS/CTR shift         | 3–5 hypotheses w/ initial confidence |
| Evaluator Agent    | Validate hypotheses using dataset metrics        | confidence-scored results            |
| Creative Generator | New creatives for low CTR segments               | 3+ creatives per campaign            |

## Metrics & Trend Computation

### Core Metrics

| Metric              | Formula                          |
| ------------------- | -------------------------------- |
| ROAS                | revenue / spend                  |
| CTR                 | clicks / impressions             |
| CVR (purchase rate) | purchases / clicks               |
| WoW Change %        | (week2 − week1) / week1 × 100    |
| MoM Change %        | (month2 − month1) / month1 × 100 |

### Trend Classification

| Condition          | Label      |
| ------------------ | ---------- |
| change > +5%       | Increasing |
| -5% < change < +5% | Stable     |
| change < -5%       | Decreasing |

## Confidence Score Engine

The system uses a weighted confidence scoring model:

```
Final confidence = (InsightConfidence * 0.4) +
                   (ValidationStrength * 0.4) +
                   (SegmentationEvidence * 0.2)
```

### Confidence Interpretation

| Score Range | Interpretation                        |
| ----------- | ------------------------------------- |
| 0.80—1.0    | Highly likely and actionable          |
| 0.60—0.79   | Moderately valid, requires monitoring |
| < 0.60      | Low confidence insight                |

## Components and Interfaces

### 1. Planner Agent

**Purpose**: Decomposes user queries into executable tasks and routes them to appropriate agents.

**Input Schema**:

```json
{
  "query": "string - natural language user request",
  "context": {
    "dataset_path": "string - path to CSV file",
    "config": "object - loaded configuration"
  }
}
```

**Output Schema**:

```json
{
  "agent_name": "planner",
  "timestamp": "ISO 8601 datetime",
  "execution_duration_ms": "integer",
  "task": "roas_analysis",
  "date_range": {
    "from": "2024-01-01",
    "to": "2024-01-14"
  },
  "steps": ["load_data", "generate_hypothesis", "validate", "creative"],
  "task_plan": [
    {
      "step_id": "integer",
      "agent": "string - target agent name",
      "action": "string - action description",
      "parameters": "object - agent-specific params"
    }
  ],
  "routing": {
    "next_agent": "string - first agent to execute",
    "workflow_type": "string - analysis|creative_generation|full"
  },
  "metadata": {
    "agent": "planner",
    "timestamp": "ISO 8601"
  }
}
```

**Reasoning Structure**:

- **Think**: Parse query intent, identify time ranges, determine required analysis type
- **Analyze**: Map query to agent capabilities, identify dependencies between tasks
- **Conclude**: Generate ordered task plan with routing instructions

### 2. Data Agent

**Purpose**: Loads dataset, validates data quality, computes summary statistics and trends.

**Input Schema**:

```json
{
  "dataset_path": "string - path to CSV",
  "date_range": {
    "start_date": "string - YYYY-MM-DD",
    "end_date": "string - YYYY-MM-DD"
  },
  "metrics": ["array of strings - metrics to compute"],
  "config": "object - configuration parameters"
}
```

**Output Schema**:

```json
{
  "agent_name": "data_agent",
  "timestamp": "ISO 8601 datetime",
  "execution_duration_ms": "integer",
  "summary": {
    "rows": 1280,
    "date_range": ["2024-01-01", "2024-02-15"],
    "total_spend": 51452.2,
    "total_revenue": 124898.33,
    "mean_roas": 2.43,
    "mean_ctr": 0.0121,
    "campaigns_count": 15
  },
  "dataset_summary": {
    "total_rows": "integer",
    "date_range": { "start": "string", "end": "string" },
    "total_spend": "float",
    "total_revenue": "float",
    "campaigns_count": "integer",
    "data_quality": {
      "missing_values": "object - field: count",
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
    "ctr_wow_change": -11.3,
    "roas_mom_change": -4.7,
    "classification": "decreasing",
    "roas_trend": {
      "direction": "string - increasing|decreasing|stable",
      "week_over_week_change": "float - percentage",
      "month_over_month_change": "float - percentage"
    },
    "ctr_trend": "object - same structure as roas_trend"
  },
  "segmentation": {
    "by_campaign": "array of objects",
    "by_creative_type": "array of objects",
    "by_audience_type": "array of objects",
    "by_platform": "array of objects"
  },
  "data_quality_issues": []
}
```

**Reasoning Structure**:

- **Think**: Identify data validation requirements, determine aggregation levels
- **Analyze**: Compute metrics, detect anomalies, calculate trends
- **Conclude**: Summarize data quality and key performance indicators

### 3. Insight Agent

**Purpose**: Generates hypotheses explaining ROAS changes based on data patterns.

**Input Schema**:

```json
{
  "data_summary": "object - output from Data Agent",
  "focus_metric": "string - metric to analyze (e.g., roas)",
  "time_period": "object - date range",
  "config": "object - configuration"
}
```

**Output Schema**:

```json
{
  "agent_name": "insight_agent",
  "timestamp": "ISO 8601 datetime",
  "execution_duration_ms": "integer",
  "hypotheses": [
    {
      "hypothesis_id": "string - unique identifier",
      "hypothesis": "CTR drop caused ROAS decline",
      "hypothesis_text": "string - natural language hypothesis",
      "category": "string - creative|audience|platform|budget|seasonality",
      "supporting_observations": ["array of strings"],
      "evidence_used": ["ctr_wow_change", "cpc_purchase_increase"],
      "initial_confidence": 0.63,
      "confidence_score": "float - 0 to 1",
      "testable": "boolean",
      "validation_approach": "string - how to validate this hypothesis"
    }
  ],
  "reasoning": {
    "think": "string - understanding of the problem",
    "analyze": "string - data patterns observed",
    "conclude": "string - hypothesis generation rationale"
  }
}
```

**Reasoning Structure**:

- **Think**: Understand the ROAS change magnitude and direction, identify potential factors
- **Analyze**: Examine segmentation data, correlate changes with campaign attributes
- **Conclude**: Generate ranked hypotheses with confidence scores

### 4. Evaluator Agent

**Purpose**: Validates hypotheses using quantitative metrics and statistical analysis.

**Input Schema**:

```json
{
  "hypotheses": "array - from Insight Agent",
  "dataset_path": "string - path to CSV",
  "data_summary": "object - from Data Agent",
  "config": "object - configuration"
}
```

**Output Schema**:

```json
{
  "agent_name": "evaluator_agent",
  "timestamp": "ISO 8601 datetime",
  "execution_duration_ms": "integer",
  "validated_hypotheses": [
    {
      "hypothesis_id": "string",
      "hypothesis": "CTR drop caused ROAS decline",
      "hypothesis_text": "string",
      "validation_status": "string - confirmed|rejected|inconclusive",
      "evidence": {
        "metrics": [
          {
            "metric_name": "string",
            "value": "float",
            "comparison": "string - description of comparison"
          }
        ],
        "statistical_significance": {
          "p_value": 0.041,
          "confidence_interval": "array - [lower, upper]"
        }
      },
      "metrics": {
        "ctr_change": -24.2,
        "roas_change": -17.1,
        "p_value": 0.041
      },
      "validated_confidence": 0.82,
      "adjusted_confidence_score": "float - 0 to 1",
      "validation_reasoning": "string"
    }
  ],
  "top_insights": [
    {
      "hypothesis": "Male 18–24 drop in CTR led to ROAS decline",
      "validated_confidence": 0.84
    }
  ],
  "reasoning": {
    "think": "string",
    "analyze": "string",
    "conclude": "string"
  }
}
```

**Reasoning Structure**:

- **Think**: Determine validation approach for each hypothesis type
- **Analyze**: Compute comparison metrics, perform statistical tests
- **Conclude**: Rank hypotheses by validation strength and confidence

### 5. Creative Generator

**Purpose**: Produces new ad creative recommendations for campaigns with low CTR.

**Input Schema**:

```json
{
  "data_summary": "object - from Data Agent",
  "low_ctr_threshold": "float - from config",
  "dataset_path": "string - path to CSV",
  "config": "object - configuration"
}
```

**Output Schema**:

```json
{
  "agent_name": "creative_generator",
  "timestamp": "ISO 8601 datetime",
  "execution_duration_ms": "integer",
  "recommendations": [
    {
      "campaign_name": "Undergarments_Female_18-30",
      "campaign": "Undergarments_Female_18-30",
      "current_ctr": 0.0087,
      "current_creative_type": "image",
      "current_message": "string",
      "new_creatives": [
        {
          "creative_id": "string",
          "creative_type": "carousel",
          "creative_message": "Breathable comfort, now 20% off!",
          "audience_type": "female_18_30_interest_fashion",
          "rationale": "string - why this creative should perform better",
          "confidence": 0.75,
          "confidence_score": "float - 0 to 1",
          "expected_ctr_improvement": "float - percentage"
        }
      ]
    }
  ],
  "creatives": [
    {
      "audience": "male_18_24",
      "creative": "Minimalist athletic cotton stretch — Buy 1 Get 1",
      "confidence": 0.78
    }
  ],
  "reasoning": {
    "think": "string",
    "analyze": "string",
    "conclude": "string"
  }
}
```

**Reasoning Structure**:

- **Think**: Identify low-CTR campaigns, analyze current creative patterns
- **Analyze**: Compare high-performing vs low-performing creative attributes
- **Conclude**: Generate creative variations with improvement rationale

### 6. Report Generator

**Purpose**: Synthesizes agent outputs into a cohesive Markdown report.

**Input Schema**:

```json
{
  "insights": "object - from Evaluator Agent",
  "creatives": "object - from Creative Generator",
  "data_summary": "object - from Data Agent",
  "query": "string - original user query"
}
```

**Output**: Markdown file (report.md) with structured sections.

## Data Models

### Dataset Schema

The synthetic_fb_ads_undergarments.csv contains the following fields:

| Field            | Type    | Description                               |
| ---------------- | ------- | ----------------------------------------- |
| campaign_name    | string  | Campaign identifier                       |
| adset_name       | string  | Ad set identifier                         |
| date             | date    | Performance date (YYYY-MM-DD)             |
| spend            | float   | Ad spend in currency units                |
| impressions      | integer | Number of ad impressions                  |
| clicks           | integer | Number of clicks                          |
| ctr              | float   | Click-through rate (clicks/impressions)   |
| purchases        | integer | Number of conversions                     |
| revenue          | float   | Revenue generated                         |
| roas             | float   | Return on ad spend (revenue/spend)        |
| creative_type    | string  | Type of creative (image, video, carousel) |
| creative_message | string  | Ad copy text                              |
| audience_type    | string  | Target audience segment                   |
| platform         | string  | Platform (Facebook, Instagram)            |
| country          | string  | Geographic target                         |

### Configuration Schema

The config/config.yaml file structure:

```yaml
# Thresholds
thresholds:
  low_ctr: 0.01 # CTR below this triggers creative recommendations
  high_confidence: 0.7 # Confidence score threshold for top insights
  roas_change_significant: 0.15 # 15% change considered significant

# Agent Configuration
agents:
  max_hypotheses: 5 # Maximum hypotheses per Insight Agent run
  min_data_points: 10 # Minimum data points for trend analysis

# Retry Logic
retry:
  max_retries: 3
  backoff_multiplier: 2 # Exponential backoff: 1s, 2s, 4s

# Logging
logging:
  level: "INFO" # DEBUG, INFO, WARNING, ERROR
  format: "json" # json or text

# Reproducibility
random_seed: 42

# Data Quality
data_quality:
  max_missing_percentage: 0.1 # Fail if >10% missing values
  date_format: "%Y-%m-%d"
```

### Agent Communication Protocol

All agents follow a standard communication envelope:

```json
{
  "envelope": {
    "agent_name": "string",
    "timestamp": "ISO 8601",
    "execution_duration_ms": "integer",
    "status": "success|failure|partial",
    "error": "string - if status is failure"
  },
  "payload": {
    // Agent-specific output schema
  },
  "metadata": {
    "config_version": "string",
    "dataset_hash": "string - MD5 of dataset",
    "python_version": "string"
  }
}
```

## Correctness Properties

_A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees._

### Property Reflection

After analyzing all acceptance criteria, several redundancies were identified:

- Requirements 11.2 and 14.4 both test confidence score ranges (0-1), which is already covered by 4.3
- Requirement 11.4 tests schema validation error handling, which is already covered by 2.3
- Requirements 11.1, 11.3, and 11.5 describe test implementation rather than system properties
- Requirements 12.1, 12.4, 12.5, 15.1-15.5, and 18.1-18.4 describe documentation and code organization rather than runtime behavior

The following properties represent the unique, testable correctness guarantees of the system:

### Core Properties

**Property 1: CLI Query Processing Completeness**
_For any_ valid natural language query submitted via CLI, the System should parse the query, extract parameters, initiate the agent workflow, and log the request with timestamp and query text.
**Validates: Requirements 1.1, 1.2, 1.5**

**Property 2: CLI Error Handling**
_For any_ ambiguous or incomplete query, the System should return a structured clarification request identifying the specific missing parameters.
**Validates: Requirements 1.3**

**Property 3: Schema Validation on Agent Communication**
_For any_ agent input or output, the System should validate the data against the defined JSON schema before processing or transmission, and reject invalid data with structured error messages.
**Validates: Requirements 2.1, 2.2, 2.3**

**Property 4: Agent Output Envelope Consistency**
_For any_ agent execution completion, the output should include metadata fields for agent_name, timestamp, and execution_duration_ms in the standard envelope format.
**Validates: Requirements 2.5**

**Property 5: JSON Serialization Round-Trip**
_For any_ data structure exchanged between agents, serializing to JSON and deserializing should produce an equivalent structure with preserved types.
**Validates: Requirements 2.4**

**Property 6: Dataset Field Validation**
_For any_ dataset loading attempt, the Data Agent should validate that all required fields are present before processing.
**Validates: Requirements 3.1**

**Property 7: Dataset Summary Completeness**
_For any_ successfully loaded dataset, the Data Agent should compute and return summary statistics including row count, date range, total spend, total revenue, campaigns count, and data quality metrics.
**Validates: Requirements 3.2**

**Property 8: Metric Calculation Accuracy**
_For any_ dataset, the Data Agent should calculate overall_roas, overall_ctr, and conversion_rate with results matching manual calculations within 0.01% tolerance.
**Validates: Requirements 3.3**

**Property 9: Data Quality Reporting**
_For any_ dataset with missing or invalid values, the Data Agent should report data quality issues with specific row and column references in the output.
**Validates: Requirements 3.4**

**Property 10: Dataset Caching Consistency**
_For any_ successfully loaded dataset, subsequent agent accesses within the same workflow should retrieve the identical cached dataset without reloading from disk.
**Validates: Requirements 3.5**

**Property 11: Task Decomposition Completeness**
_For any_ ROAS analysis request, the Planner Agent should decompose the request into at least three steps: data retrieval, hypothesis generation, and validation.
**Validates: Requirements 4.1**

**Property 12: Hypothesis Generation Minimum Count**
_For any_ Insight Agent execution with sufficient data, the output should contain at least three distinct hypotheses.
**Validates: Requirements 4.2**

**Property 13: Confidence Score Bounds**
_For any_ hypothesis, insight, or creative recommendation, the confidence_score field should be between 0.0 and 1.0 inclusive.
**Validates: Requirements 4.3, 6.5, 14.1, 14.3**

**Property 14: Hypothesis Validation Evidence**
_For any_ hypothesis validated by the Evaluator Agent, the output should include at least two distinct supporting metrics computed from the dataset.
**Validates: Requirements 4.4, 7.1**

**Property 15: Hypothesis Ranking Consistency**
_For any_ set of validated hypotheses, the System should rank them in descending order by validation strength and confidence score.
**Validates: Requirements 4.5, 14.5**

**Property 16: Reasoning Structure Completeness**
_For any_ agent execution that produces reasoning output, the output should contain three distinct sections: think, analyze, and conclude.
**Validates: Requirements 5.1, 5.2, 5.3, 5.4**

**Property 17: Reasoning Chain Logging**
_For any_ agent execution with reasoning, the full reasoning chain should be preserved in the structured log file.
**Validates: Requirements 5.5**

**Property 18: Low-CTR Campaign Filtering**
_For any_ dataset and configured low_ctr_threshold, the Creative Generator should identify and return only campaigns where ctr < threshold.
**Validates: Requirements 6.1**

**Property 19: Creative Variation Minimum Count**
_For any_ low-CTR campaign, the Creative Generator should produce at least three distinct creative variations.
**Validates: Requirements 6.2**

**Property 20: Creative Schema Completeness**
_For any_ generated creative recommendation, the output should include all required fields: creative_message, creative_type, audience_type, rationale, and confidence_score.
**Validates: Requirements 6.3**

**Property 21: Creative Output Serialization Round-Trip**
_For any_ creative recommendations output, writing to creatives.json and reading back should produce valid JSON that deserializes to an equivalent data structure.
**Validates: Requirements 6.4**

**Property 22: Hypothesis Segmentation Comparison**
_For any_ hypothesis validation, the Evaluator Agent should compute metrics comparing performance across at least two segments identified in the hypothesis.
**Validates: Requirements 7.2**

**Property 23: Statistical Significance Inclusion**
_For any_ hypothesis validation where sample size permits statistical testing, the Evaluator Agent should include p_value or confidence_interval in the evidence.
**Validates: Requirements 7.3**

**Property 24: Weak Evidence Confidence Calibration**
_For any_ hypothesis where validation evidence shows contradictory metrics or insufficient data, the adjusted_confidence_score should be below 0.5.
**Validates: Requirements 7.4**

**Property 25: Insights Output Serialization Round-Trip**
_For any_ validated hypotheses output, writing to insights.json and reading back should produce valid JSON containing hypothesis_text, metrics, and confidence_scores.
**Validates: Requirements 7.5**

**Property 26: Configuration Loading**
_For any_ system initialization, the System should load config/config.yaml and make all parameters accessible to agents.
**Validates: Requirements 8.1, 8.4**

**Property 27: Configuration Threshold Validation**
_For any_ loaded configuration, threshold values should be validated to be within acceptable ranges (0 to 1).
**Validates: Requirements 8.2**

**Property 28: Random Seed Reproducibility**
_For any_ two system executions with the same random_seed and identical input data, all random operations should produce identical results.
**Validates: Requirements 8.5**

**Property 29: Report Generation Completeness**
_For any_ successful workflow completion, the System should generate a report.md file containing all required sections.
**Validates: Requirements 9.1, 9.2**

**Property 30: Report Insights Inclusion**
_For any_ generated report with validated hypotheses, the Key Insights section should present the top three hypotheses with supporting metrics.
**Validates: Requirements 9.3**

**Property 31: Report Creatives Inclusion**
_For any_ generated report with creative recommendations, the section should display recommendations with all required fields.
**Validates: Requirements 9.4**

**Property 32: Report Markdown Validity**
_For any_ generated report.md, parsing the file with a Markdown parser should succeed without syntax errors.
**Validates: Requirements 9.5**

**Property 33: Agent Execution Start Logging**
_For any_ agent execution start, the System should write a log entry containing agent_name, input_parameters, and start_timestamp.
**Validates: Requirements 10.1**

**Property 34: Agent Execution Completion Logging**
_For any_ agent execution completion, the System should write a log entry containing agent_name, output_summary, and execution_duration_ms.
**Validates: Requirements 10.2**

**Property 35: Error Logging Completeness**
_For any_ error occurrence during agent execution, the System should log error_message, stack_trace, agent_name, and agent_state.
**Validates: Requirements 10.3**

**Property 36: Log Format Consistency**
_For any_ log entry written by the System, the entry should be valid JSON with consistent field names and ISO 8601 timestamps.
**Validates: Requirements 10.4**

**Property 37: Log File Creation**
_For any_ system execution, the System should create a log file in the logs directory with timestamp-based filename.
**Validates: Requirements 10.5**

**Property 38: Agent Initialization Parameters**
_For any_ agent instantiation, the agent constructor should accept only a configuration object and no direct references to other agents.
**Validates: Requirements 12.2**

**Property 39: Agent Execution Isolation**
_For any_ agent execution, the agent should not directly invoke other agents but should return routing instructions.
**Validates: Requirements 12.3**

**Property 40: Missing Value Handling**
_For any_ dataset row with missing values, the Data Agent should either impute or exclude the row and log the action taken.
**Validates: Requirements 13.1**

**Property 41: Date Parsing Error Handling**
_For any_ dataset row with invalid date format, the Data Agent should log the invalid value, skip the row, and continue processing.
**Validates: Requirements 13.2**

**Property 42: Numeric Field Error Handling**
_For any_ dataset row with non-numeric values in numeric fields, the Data Agent should attempt conversion or exclude the row and log a warning.
**Validates: Requirements 13.3**

**Property 43: Required Field Validation**
_For any_ dataset missing required fields, the Data Agent should raise a ValidationError with all missing field names.
**Validates: Requirements 13.4**

**Property 44: Data Quality Summary Inclusion**
_For any_ dataset with detected data quality issues, the Data Agent output should include a data_quality object with issue counts.
**Validates: Requirements 13.5**

**Property 45: Confidence Score Adjustment**
_For any_ hypothesis that undergoes validation, the Evaluator Agent should output an adjusted_confidence_score based on validation evidence.
**Validates: Requirements 14.2**

**Property 46: Retry Execution on Failure**
_For any_ agent execution that raises an exception, the System should retry up to max_retries times before propagating failure.
**Validates: Requirements 16.1**

**Property 47: Exponential Backoff Timing**
_For any_ agent retry sequence, the delay between retries should follow exponential backoff based on configured multiplier.
**Validates: Requirements 16.2**

**Property 48: Retry Exhaustion Handling**
_For any_ agent execution where all retries are exhausted, the System should log the final error and return failure status.
**Validates: Requirements 16.3**

**Property 49: Successful Retry Logging**
_For any_ agent retry that succeeds, the System should log the retry count and continue workflow execution.
**Validates: Requirements 16.4**

**Property 50: Retry Configuration Loading**
_For any_ system initialization with retry configuration, the System should load and apply max_retries and backoff_multiplier to all agents.
**Validates: Requirements 16.5**

**Property 51: Trend Calculation Completeness**
_For any_ dataset with sufficient historical data, the Data Agent should calculate week-over-week and month-over-month changes for key metrics.
**Validates: Requirements 17.1**

**Property 52: Trend Direction Classification**
_For any_ computed trend change, the Data Agent should classify the trend as increasing, decreasing, or stable based on thresholds.
**Validates: Requirements 17.2**

**Property 53: Seasonality Flagging**
_For any_ dataset with detected repeating patterns, the Data Agent should set a seasonality_detected flag in the output.
**Validates: Requirements 17.3**

**Property 54: Trend Data Schema Inclusion**
_For any_ Data Agent output, the schema should include a trends object with direction and change percentages.
**Validates: Requirements 17.4**

**Property 55: Trend Incorporation in Hypotheses**
_For any_ Insight Agent execution with trend data available, at least one hypothesis should reference trend information.
**Validates: Requirements 17.5**

**Property 56: Output File Location Consistency**
_For any_ system execution that produces outputs, all JSON and Markdown files should be written to the reports directory.
**Validates: Requirements 18.5**
**Validates: Requirements 17.5**

**Property 56: Output File Location Consistency**
_For any_ system execution that produces outputs, all JSON and Markdown files should be written to the reports directory.
**Validates: Requirements 18.5**

## Error Handling

### Error Categories

1. **Data Errors**

   - Missing required fields → ValidationError with field list
   - Invalid date formats → Log warning, skip row, continue
   - Non-numeric values → Attempt conversion, log warning if failed
   - Empty dataset → ValidationError with descriptive message

2. **Configuration Errors**

   - Missing config.yaml → Use defaults, log warning
   - Invalid threshold values → ValidationError with valid ranges
   - Missing required config keys → Use defaults, log warning

3. **Agent Execution Errors**

   - Schema validation failure → Return structured error in envelope
   - Timeout → Retry with exponential backoff
   - Unexpected exception → Log full stack trace, retry up to max_retries

4. **I/O Errors**
   - Dataset file not found → FileNotFoundError with path
   - Cannot write output files → IOError with directory and permissions info
   - Log directory not writable → Create directory or fail with clear message

### Error Response Format

All errors should be returned in a standard envelope:

```json
{
  "envelope": {
    "agent_name": "string",
    "timestamp": "ISO 8601",
    "status": "failure",
    "error": {
      "error_type": "ValidationEr
redentials)I, ce data (PIensitiv sid logging: AvoingLoggues
-  valnfigidate all codation: Valon valiatinfigur
- Col attackssaory traverctt direen Prevon:idati path valilets
- Fl user inpue alSanitiztion: daut valins

- InpiderationsCoity urs

### Secut file sizeutp time
- OingcessroDataset ps rates
- success and y rateetror type
- R errnt ands by ageateror r
- Er5, p99)on (p50, p9n duratint executio- Age

nitor:trics to mo

Key metoring Monih

###k, CloudWatc SplunK stack,ELtible with mpaion: Co aggregat Logays
-0 d keep 3tion,: Daily rota rotation- Logrmat
vel, JSON foNFO lection: Iat
- Produ formvel, text leDEBUGent: velopm
- Deegy
 Stratggingig

### LoconfV to select RRO_ENPAriable KASt va environmenseaml
- Ug.prod.y/confin: configoductio- Prg.dev.yaml
/confinfignt: co Developme

-entagemon ManConfiguratig)

### estinrty-based tpe (for pro= 6.0.0is >
- hypothesing)st0 (for test >= 6.2..0
- pyteema >= 3.2nsch jso5.4
->=
- PyYAML das >= 1.3.0- panon 3.9+
- Pythrements

nt Requi# Environmeons

##rati Conside# Deployment.)

#tcTML, es (PDF, Hor generatw report*: Add nemats*put ForutNew O
- **riestegoght Agent ca Insixtend E**:pes TyHypothesis
- **New putationic comtrgent me AExtend Datarics**: ew Metmpt
- **N, create proemaefine schnts/, drc/age class in sgentdd new a Ats**:w Agen
- **Neon:
easy extensiigned for em is des

The systensibility# Ext

##upildemory bu avoid mentally toemcrgs inrite lo: Wg Logs**eamin**Stror)
-  Generatand Creativegent Insight A.g., lel (ein paralt agents enindependun ssible, rre poution**: Wheallel ExecParated
- ** is instanti agentompts wheny load pr: Onling**y Load- **Lazall agents
ory for  in mem cacheaset once,ad datg**: LoCachinet  **Datasions

-ideratormance Cons
### Perf
 Generatoreportsed to Rd and pastes are collecinal outputgent
7. Fut to next ased as inp pastput isent ou Each age
6. in sequenctes agentspy execun.op in ruexecution loin s
5. Maruction instns routing4. Retur
teps ordered splan witherates task Gens
3. eterparamnd intent a. Parses r query
2use1. Receives

strator:che orcts as the Agent alannerion

The Pt Orchestrat
### Agens]
```

nd outputnputs ample iExaples
[Exam# nt 2]

#strai- [Conraint 1]
nstCo- [ints
Constran]

## tio secConcludens for

[Instructioudeoncl## C

#ection] szer Analys fostructionyze
[In

### Anal]

ink section Thuctions fornk
[Instr### Thi

follows:oning as re your reas
Structug Structureonin# Reas
#a]
JSON schem schema:
[lowing JSON in the foltput oust produceou murmat
Y Foutput O

##cription] 2]: [desInput fieldiption]

- [1]: [descrld nput fie:
- [Iill receiveu w# Input
  Yoion]

#riptdescific task
[Specsk# Taystem.

#ro s Kasparn thent iription] age descare a [rolee
You

## Rolompt

me] Prt Nawn

# [Agenarkdo:

```murehis struct towllould forompts shgent pll ag

Angineerin Prompt E
###n Notes
mentatiole Imp##
l
```

*config.yamle └── sampaset.csv
─ sample_dat ├─
res/ixtu── f
└covery.pyrror_re─ test_e └─py
│ orkflow.test_full_w ├──
│ ation/ integr──y.py
├cibilitprodues_ret_propertitespy
│ └── idence.nfes_cortiopet_pr├── tes ics.py
│ metries_propertst*│ ├── tezation.py
ties*serialist_proper│ ├── te/
─ propertymas.py
├─st_schete│ └──
.pyert_planntes ├── ator.py
│ nereative_ge─ test_cr ├─tor.py
│ lua─ test_eva.py
│ ├─sight_agentt_in
│ ├── tesagent.pyest_data* ├── t
│ it/uns/
├── ``
teston

`zatiOrganile Fi# Testy

##s gracefulltes or failompleorkflow c w - Assertxecutes
logic ery ert ret

- Asst failuret agen
- Injecorkflow\*\*ecovery Wr R

3. \*\*Erroiedtife idenns arTR campaigssert low-Cted

   - A genera isives.jsonssert creat - Aport
     → Retor ative GeneraCreta Agent → → Daset oad data
   - L\*\*owation WorkflGenerive Creatons

4. \*\*cted sectins expecontaiert report - Assated
   e generarputs l outrt alt
   - Asse → Reporator AgentEvaluht Agent → sigAgent → Int → Data dataseoad \*\*
   - Llows WorkfysiAnal
5. \*\*Full
   orkflows:d-to-end wenld verify tests shoutegration

Inestingon TIntegrati

### old ruleshreshmatches tification t classsere

    - As/stablreasingsing/dec as increasifyClas
    - estagd percenndom trenerate ra
    - Genents 17.2)Requiremication** (ifon ClassectiDiry 52: Trend opert

10. **Pr
    ernential pattonw exploays folel - Assert d
    estribetween ree delays - Measurences
    y sequtrandom reenerate r - G 16.2)
    entsequirem(Rg** koff Timinial Baconenterty 47: Exp\*\*Prop
11. d
    typectlyd correanesent ds prielrequired fall sert As - as JSON

- Parsetries
  ndom log enate raGener
  - )nts 10.4meuire\*\* (ReqConsistencyt Formag erty 36: Lo

8. **Properrors
   yntax o s- Assert n
   wn parserrkdose with Ma- Parntent
   com reporte rando- Generat 5)
   ts 9.equiremen** (Raliditywn VdoMark: Report \*Property 32

9. \*tical idenputs arert all out - Assenput
   ieed andsame stwice with ystem
   - Run snts 8.5)uiremety** (ReqliReproducibiSeed Random : 28rty . **Prope

6eservedelds are prrequired fit all

- Asserd read backle anON fite to JS - Wriheses
  ed hypotalidatm vnerate rando - Ges 7.5)
  irementqurip\*\* (Ren Round-Trializatioutput Sensights O: Ioperty 25

5. \*\*Pr
   ls originala equaalized datseriert de - Assack
   read bnd aJSON file Write to -s
   ionrecommendatve reatidom cranGenerate

   - ts 6.4)remen(Requiip** d-Trion Rounerializatut StpCreative Ou21: y **Propert0

6. 0.0 and 1.e betweenores art all scsser

- Ae fields_scordencel confiExtract al
- d creativesghts, annsiotheses, irandom hypGenerate -
  1, 14.3), 14.ts 4.3, 6.5Requiremenunds** (nce Score BodeConfi: 13Property 3. **erance

n tolwithi expected ues matchmputed valco - Assert rate
rsionveS, CTR, conROA- Compute cs
own metrih knts witdatasem te randonera - Gents 3.3)

- (Requiremeacy*ion Accuric Calculat Metr 8:roperty*P

2. \*als originalure equructlized stt deseriaAsser
   - deserializeo JSON and ialize tes
   - Serurutput structnt orandom ageerate 4)
   - Gens 2.irement* (Requip* Round-TrializationN Serty 5: JSO
1. **Properverage**:
   erty Test Coop
   \*\*Pr
   Bounds

````ore fidence Sc Conerty 13:Propt, ro-fb-analys kaspar# Feature:on
pythrmat:
```using the foent sign docums defrom thity ss properctne correncing they refereexplicitl a comment MUST includeased test h property-bging**: Eacag T
**Test space.
e inputof thrage gh covee thorouto ensuriterations mum of 100 run a minit should sed testy-baach proper*: Efiguration*

**Conhedocs.io/)s.readtypothesi//hs:ttp(h for Python s**pothesiHyse **ibrary**: U Testing LBasedperty-ro

**PstingBased Te## Property-iming

#ackoff t btialonent exp
   - Tesresock failuith mgic wretry loest
   - Tnvelopeect error e corry producesrror categorTest each e - ling**
  *Error Hand
4. *validation
ld Test thresho
   - ssingfig is mions when ct valueTest defaul
   - ig.yamlalid confng voadi l
   - Testn Loading**atioConfigur

3. **behaviorhing  - Test cacries
   time seh syntheticulations wit calcnd Test tre   -wed data
tionally fla intenithdetection wality t data qu
   - Tesetsn dataswith knowations ulcalcc rist met  - Te*
 Agent**Data ers)

2. *e numb-rangout-ofues, ull valrings, npty stses (em cadge
   - Test ete errorsiah approprjected witts are realid input inv   - Testion
validas  pas inputs Test validon**
   -tilida**Schema Va:

1. sts for unit tesivecomprehenquires  retem
The sys Testing
## Unit

#ategytrting S# Tes: 3)

# (defaultg.yaml confiable viaConfigurtries**: **Max Rempt)
- try_atteier ^ reff_multiplbacko * (elaybase_d delay = a**:uloff Formckions
- **Baa violathemes, scg filrors, missintion erlidarors**: Vatryable Er
- **Non-Rete limits errors, ra/Oorary Iempts, t**: TimeouErrors*Retryable - *tegy

Retry Stra```

###  }
  }
}

   d error"xpecteif unering - ace": "sttr"stack_,
         }fo"
   tional in: "addit"ontex      "ce",
  d": "valuel       "fiils": {
 taror_de      "erription",
adable descan-re: "Humsage"_mesorrr   "e,
   "ErrorectedError|Unexpor|TimeoutIOErrror|
````

## Error Handling

### Error Categories

1. **Data Errors**

   - Missing required fields → ValidationError with field list
   - Invalid date formats → Log warning, skip row, continue
   - Non-numeric values → Attempt conversion, log warning if failed
   - Empty dataset → ValidationError with descriptive message

2. **Configuration Errors**

   - Missing config.yaml → Use defaults, log warning
   - Invalid threshold values → ValidationError with valid ranges
   - Missing required config keys → Use defaults, log warning

3. **Agent Execution Errors**

   - Schema validation failure → Return structured error in envelope
   - Timeout → Retry with exponential backoff
   - Unexpected exception → Log full stack trace, retry up to max_retries

4. **I/O Errors**
   - Dataset file not found → FileNotFoundError with path
   - Cannot write output files → IOError with directory and permissions info
   - Log directory not writable → Create directory or fail with clear message

### Error Response Format

All errors should be returned in a standard envelope:

```json
{
  "envelope": {
    "agent_name": "string",
    "timestamp": "ISO 8601",
    "status": "failure",
    "error": {
      "error_type": "ValidationError|IOError|TimeoutError|UnexpectedError",
      "error_message": "Human-readable description",
      "error_details": {
        "field": "value",
        "context": "additional info"
      },
      "stack_trace": "string - if unexpected error"
    }
  }
}
```

### Retry Strategy

- **Retryable Errors**: Timeouts, temporary I/O errors, rate limits
- **Non-Retryable Errors**: Validation errors, missing files, schema violations
- **Backoff Formula**: delay = base_delay \* (backoff_multiplier ^ retry_attempt)
- **Max Retries**: Configurable via config.yaml (default: 3)

## Testing Strategy

### Unit Testing

The system requires comprehensive unit tests for:

1. **Schema Validation**

   - Test valid inputs pass validation
   - Test invalid inputs are rejected with appropriate errors
   - Test edge cases (empty strings, null values, out-of-range numbers)

2. **Data Agent**

   - Test metric calculations with known datasets
   - Test data quality detection with intentionally flawed data
   - Test trend calculations with synthetic time series
   - Test caching behavior

3. **Configuration Loading**

   - Test loading valid config.yaml
   - Test default values when config is missing
   - Test threshold validation

4. **Error Handling**
   - Test each error category produces correct error envelope
   - Test retry logic with mock failures
   - Test exponential backoff timing

### Property-Based Testing

**Property-Based Testing Library**: Use **Hypothesis** for Python (https://hypothesis.readthedocs.io/)

**Configuration**: Each property-based test should run a minimum of 100 iterations to ensure thorough coverage of the input space.

**Test Tagging**: Each property-based test MUST include a comment explicitly referencing the correctness property from this design document using the format:

```python
# Feature: kasparro-fb-analyst, Property 13: Confidence Score Bounds
```

**Property Test Coverage**:

1. **Property 5: JSON Serialization Round-Trip** (Requirements 2.4)

   - Generate random agent output structures
   - Serialize to JSON and deserialize
   - Assert deserialized structure equals original

2. **Property 8: Metric Calculation Accuracy** (Requirements 3.3)

   - Generate random datasets with known metrics
   - Compute ROAS, CTR, conversion rate
   - Assert computed values match expected within tolerance

3. **Property 13: Confidence Score Bounds** (Requirements 4.3, 6.5, 14.1, 14.3)

   - Generate random hypotheses, insights, and creatives
   - Extract all confidence_score fields
   - Assert all scores are between 0.0 and 1.0

4. **Property 21: Creative Output Serialization Round-Trip** (Requirements 6.4)

   - Generate random creative recommendations
   - Write to JSON file and read back
   - Assert deserialized data equals original

5. **Property 25: Insights Output Serialization Round-Trip** (Requirements 7.5)

   - Generate random validated hypotheses
   - Write to JSON file and read back
   - Assert all required fields are preserved

6. **Property 28: Random Seed Reproducibility** (Requirements 8.5)

   - Run system twice with same seed and input
   - Assert all outputs are identical

7. **Property 32: Report Markdown Validity** (Requirements 9.5)

   - Generate random report content
   - Parse with Markdown parser
   - Assert no syntax errors

8. **Property 36: Log Format Consistency** (Requirements 10.4)

   - Generate random log entries
   - Parse as JSON
   - Assert all required fields present and correctly typed

9. **Property 47: Exponential Backoff Timing** (Requirements 16.2)

   - Generate random retry sequences
   - Measure delays between retries
   - Assert delays follow exponential pattern

10. **Property 52: Trend Direction Classification** (Requirements 17.2)
    - Generate random trend percentages
    - Classify as increasing/decreasing/stable
    - Assert classification matches threshold rules

### Integration Testing

Integration tests should verify end-to-end workflows:

1. **Full Analysis Workflow**

   - Load dataset → Data Agent → Insight Agent → Evaluator Agent → Report
   - Assert all outputs are generated
   - Assert report contains expected sections

2. **Creative Generation Workflow**

   - Load dataset → Data Agent → Creative Generator → Report
   - Assert creatives.json is generated
   - Assert low-CTR campaigns are identified

3. **Error Recovery Workflow**
   - Inject agent failure
   - Assert retry logic executes
   - Assert workflow completes or fails gracefully

### Test File Organization

```
tests/
├── unit/
│   ├── test_data_agent.py
│   ├── test_insight_agent.py
│   ├── test_evaluator.py
│   ├── test_creative_generator.py
│   ├── test_planner.py
│   └── test_schemas.py
├── property/
│   ├── test_properties_serialization.py
│   ├── test_properties_metrics.py
│   ├── test_properties_confidence.py
│   └── test_properties_reproducibility.py
├── integration/
│   ├── test_full_workflow.py
│   └── test_error_recovery.py
└── fixtures/
    ├── sample_dataset.csv
    └── sample_config.yaml
```

## Implementation Notes

### Prompt Engineering

All agent prompts should follow this structure:

```markdown
# [Agent Name] Prompt

## Role

You are a [role description] agent in the Kasparro system.

## Task

[Specific task description]

## Input

You will receive:

- [Input field 1]: [description]
- [Input field 2]: [description]

## Output Format

You must produce output in the following JSON schema:
[JSON schema]

## Reasoning Structure

Structure your reasoning as follows:

### Think

[Instructions for Think section]

### Analyze

[Instructions for Analyze section]

### Conclude

[Instructions for Conclude section]

## Constraints

- [Constraint 1]
- [Constraint 2]

## Examples

[Example inputs and outputs]
```

### Agent Orchestration

The Planner Agent acts as the orchestrator:

1. Receives user query
2. Parses intent and parameters
3. Generates task plan with ordered steps
4. Returns routing instructions
5. Main execution loop in run.py executes agents in sequence
6. Each agent output is passed as input to next agent
7. Final outputs are collected and passed to Report Generator

### Performance Considerations

- **Dataset Caching**: Load dataset once, cache in memory for all agents
- **Lazy Loading**: Only load prompts when agent is instantiated
- **Parallel Execution**: Where possible, run independent agents in parallel (e.g., Insight Agent and Creative Generator)
- **Streaming Logs**: Write logs incrementally to avoid memory buildup

### Extensibility

The system is designed for easy extension:

- **New Agents**: Add new agent class in src/agents/, define schema, create prompt
- **New Metrics**: Extend Data Agent metric computation
- **New Hypothesis Types**: Extend Insight Agent categories
- **New Output Formats**: Add new report generators (PDF, HTML, etc.)

## Final Output Files

| File                   | Purpose                      |
| ---------------------- | ---------------------------- |
| reports/insights.json  | Sorted validated hypotheses  |
| reports/creatives.json | New creatives for low CTR    |
| reports/report.md      | Stakeholder-friendly summary |

## Sample End-to-End Output

```json
{
  "top_insights": [
    {
      "hypothesis": "Male 18–24 drop in CTR led to ROAS decline",
      "validated_confidence": 0.84
    }
  ],
  "creatives": [
    {
      "audience": "male_18_24",
      "creative": "Minimalist athletic cotton stretch — Buy 1 Get 1",
      "confidence": 0.78
    }
  ]
}
```

## Deployment Considerations

### Environment Requirements

- Python 3.9+
- pandas >= 1.3.0
- PyYAML >= 5.4
- jsonschema >= 3.2.0
- pytest >= 6.2.0 (for testing)
- hypothesis >= 6.0.0 (for property-based testing)

### Configuration Management

- Development: config/config.dev.yaml
- Production: config/config.prod.yaml
- Use environment variable KASPARRO_ENV to select config

### Logging Strategy

- Development: DEBUG level, text format
- Production: INFO level, JSON format
- Log rotation: Daily rotation, keep 30 days
- Log aggregation: Compatible with ELK stack, Splunk, CloudWatch

### Monitoring

Key metrics to monitor:

- Agent execution duration (p50, p95, p99)
- Error rates by agent and error type
- Retry rates and success rates
- Dataset processing time
- Output file sizes

### Security Considerations

- Input validation: Sanitize all user inputs
- File path validation: Prevent directory traversal attacks
- Configuration validation: Validate all config values
- Logging: Avoid logging sensitive data (PII, credentials)
