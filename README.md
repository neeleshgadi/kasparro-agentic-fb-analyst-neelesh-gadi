# Kasparro - Autonomous Facebook Ads Performance Analyst

Kasparro is a multi-agent system that analyzes Facebook Ads performance data, identifies root causes of ROAS changes, validates hypotheses through data-driven analysis, and generates creative recommendations for underperforming campaigns.

## Features

- 🔍 **Automated ROAS Analysis**: Identifies root causes of performance changes
- 📊 **Data-Driven Insights**: Generates and validates hypotheses using statistical analysis
- 🎨 **Creative Recommendations**: Suggests new ad creatives for low-CTR campaigns
- 📈 **Trend Detection**: Calculates week-over-week and month-over-month changes
- 📝 **Executive Reports**: Produces stakeholder-friendly Markdown reports
- ✅ **Property-Based Testing**: Comprehensive test coverage with 56 correctness properties

## Quick Start

### Prerequisites

- Python 3.9 or higher
- pip package manager

### Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd kasparro
```

2. Create and activate a virtual environment:

```bash
python -m venv .venv

# On Windows
.venv\Scripts\activate

# On macOS/Linux
source .venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

### Basic Usage

Run a full analysis on the sample dataset:

```bash
python src/run.py "Analyze ROAS performance for the last 14 days"
```

Generate creative recommendations for low-CTR campaigns:

```bash
python src/run.py "Suggest new creatives for underperforming campaigns"
```

Analyze specific time periods:

```bash
python src/run.py "What caused ROAS to drop between January 1 and January 15?"
```

### Output Files

After execution, Kasparro generates three output files in the `reports/` directory:

- **insights.json**: Validated hypotheses with confidence scores and supporting metrics
- **creatives.json**: Creative recommendations for low-CTR campaigns
- **report.md**: Executive summary in Markdown format

## Example Commands

### ROAS Analysis

```bash
python src/run.py "Analyze ROAS changes in the last 7 days"
```

**Expected Output:**

- Identifies ROAS trend direction (increasing/decreasing/stable)
- Generates 3-5 hypotheses explaining changes
- Validates hypotheses with statistical significance
- Ranks insights by confidence score

### Creative Generation

```bash
python src/run.py "Generate new ad creatives for campaigns with CTR below 1%"
```

**Expected Output:**

- Identifies campaigns below CTR threshold
- Analyzes high-performing creative patterns
- Generates 3+ creative variations per campaign
- Provides rationale and confidence scores

### Full Workflow

```bash
python src/run.py "Analyze performance and suggest improvements for the last month"
```

**Expected Output:**

- Complete ROAS analysis
- Hypothesis generation and validation
- Creative recommendations
- Comprehensive Markdown report

## Sample Outputs

### insights.json

```json
{
  "agent_name": "evaluator_agent",
  "timestamp": "2024-01-15T10:30:00Z",
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
          }
        ],
        "statistical_significance": {
          "p_value": 0.041,
          "confidence_interval": [0.15, 0.32]
        }
      },
      "adjusted_confidence_score": 0.82,
      "validation_reasoning": "Strong correlation between CTR drop and ROAS decline with statistical significance"
    }
  ],
  "top_insights": [
    {
      "hypothesis": "Male 18-24 CTR drop caused ROAS decline",
      "validated_confidence": 0.82
    }
  ]
}
```

### creatives.json

```json
{
  "agent_name": "creative_generator",
  "timestamp": "2024-01-15T10:30:15Z",
  "recommendations": [
    {
      "campaign_name": "Undergarments_Male_18-24",
      "current_ctr": 0.0087,
      "current_creative_type": "image",
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
        }
      ]
    }
  ]
}
```

### report.md

```markdown
# Facebook Ads Performance Analysis Report

**Analysis Period:** January 1, 2024 - January 14, 2024  
**Generated:** January 15, 2024 10:30 AM

## Executive Summary

ROAS declined 9% over the analyzed period, dropping from 2.43 to 2.21. The primary driver was a 24% CTR decrease in the male 18-24 audience segment, which accounts for 32% of total ad spend. This segment's underperformance directly contributed to the overall ROAS decline.

**Key Findings:**

- Overall ROAS: 2.21 (-9% vs previous period)
- Overall CTR: 0.0107 (-11.3% vs previous period)
- Total Spend: $51,452
- Total Revenue: $124,898

## Key Insights

### 1. Male 18-24 CTR Drop Caused ROAS Decline

**Confidence: 82%** | **Status: Confirmed**

The male 18-24 audience segment experienced a 24.2% CTR decline, significantly exceeding the overall 11.3% decrease. This segment's ROAS dropped 17.1% in the same period.

**Supporting Evidence:**

- CTR Change: -24.2% (male 18-24) vs -11.3% (overall)
- ROAS Change: -17.1% (male 18-24) vs -9% (overall)
- Statistical Significance: p-value 0.041 (significant at 95% confidence)

**Recommendation:** Refresh creative targeting male 18-24 with carousel and video formats, which show 35-42% higher engagement for this demographic.

### 2. Image Creative Fatigue in Female Segments

**Confidence: 67%** | **Status: Partially Confirmed**

Female audience segments (18-30, 25-34) show declining engagement with static image creatives, with CTR dropping 18% over the period.

**Supporting Evidence:**

- Image Creative CTR: -18% (female segments)
- Carousel Creative CTR: -3% (female segments)
- Video Creative CTR: +5% (female segments)

**Recommendation:** Shift budget from image to carousel and video formats for female audience segments.

## Creative Recommendations

### Campaign: Undergarments_Male_18-24

**Current CTR:** 0.87% | **Target CTR:** 1.2%

#### Recommended Creative #1

**Format:** Carousel  
**Message:** "Minimalist athletic cotton stretch — Buy 1 Get 1"  
**Audience:** Male 18-24, Interest: Fitness  
**Expected CTR Improvement:** +0.32%  
**Confidence:** 78%

**Rationale:** Carousel format shows 35% higher CTR for this demographic. BOGO offers drive 28% higher conversion rates in male segments.

#### Recommended Creative #2

**Format:** Video  
**Message:** "Comfort meets performance. Premium fabrics, everyday prices."  
**Audience:** Male 18-24, Interest: Fashion  
**Expected CTR Improvement:** +0.29%  
**Confidence:** 75%

**Rationale:** Video creatives achieve 42% higher engagement in male 18-24 segment. Value messaging resonates with price-conscious audience.

## Methodology

### Data Analysis

- **Dataset:** synthetic_fb_ads_undergarments.csv
- **Rows Analyzed:** 1,280 campaign records
- **Date Range:** January 1 - January 14, 2024
- **Metrics Computed:** ROAS, CTR, CVR, CPC, WoW/MoM changes

### Hypothesis Generation

- Generated 5 initial hypotheses based on data patterns
- Categorized by type: audience, creative, platform, budget, seasonality
- Assigned initial confidence scores based on data availability

### Validation Process

- Computed validation metrics for each hypothesis
- Performed statistical significance testing (p-values, confidence intervals)
- Compared performance across segments
- Adjusted confidence scores using weighted formula:
  - Insight Confidence (40%) + Validation Strength (40%) + Segmentation Evidence (20%)

### Creative Generation

- Identified campaigns with CTR < 1.0%
- Analyzed high-performing creative attributes
- Generated 3+ variations per underperforming campaign
- Assigned confidence scores based on historical patterns

---

**Report Generated by Kasparro v1.0**  
**Configuration:** config/config.yaml  
**Random Seed:** 42 (for reproducibility)
```

## Configuration

Kasparro uses `config/config.yaml` for system configuration. Key parameters:

```yaml
# Thresholds
thresholds:
  low_ctr: 0.01 # CTR below this triggers creative recommendations
  high_confidence: 0.7 # Confidence threshold for top insights
  roas_change_significant: 0.15 # 15% change considered significant

# Agent Configuration
agents:
  max_hypotheses: 5 # Maximum hypotheses per analysis
  min_data_points: 10 # Minimum data points for trend analysis

# Retry Logic
retry:
  max_retries: 3 # Maximum retry attempts on failure
  backoff_multiplier: 2 # Exponential backoff multiplier

# Logging
logging:
  level: "INFO" # DEBUG, INFO, WARNING, ERROR
  format: "json" # json or text

# Reproducibility
random_seed: 42 # For reproducible random operations

# Data Quality
data_quality:
  max_missing_percentage: 0.1 # Fail if >10% missing values
  date_format: "%Y-%m-%d"
```

### Configuration Parameters and Effects

#### Thresholds

**low_ctr** (default: 0.01)

- **Effect**: Campaigns with CTR below this value are flagged for creative recommendations
- **Range**: 0.0 to 1.0
- **Example**: Setting to 0.015 will only flag campaigns with CTR < 1.5%
- **Impact**: Higher values = more campaigns flagged, more creative recommendations generated

**high_confidence** (default: 0.7)

- **Effect**: Insights with confidence above this threshold are highlighted in reports
- **Range**: 0.0 to 1.0
- **Example**: Setting to 0.8 will only highlight very high-confidence insights
- **Impact**: Higher values = fewer insights highlighted, more selective reporting

**roas_change_significant** (default: 0.15)

- **Effect**: ROAS changes above this percentage are considered significant
- **Range**: 0.0 to 1.0 (as decimal, e.g., 0.15 = 15%)
- **Example**: Setting to 0.10 will flag 10%+ ROAS changes as significant
- **Impact**: Lower values = more changes flagged as significant, more hypotheses generated

#### Agent Configuration

**max_hypotheses** (default: 5)

- **Effect**: Maximum number of hypotheses generated by Insight Agent
- **Range**: 1 to 10
- **Example**: Setting to 3 will generate only top 3 hypotheses
- **Impact**: Lower values = faster execution, fewer hypotheses to validate

**min_data_points** (default: 10)

- **Effect**: Minimum data points required for trend analysis
- **Range**: 5 to 100
- **Example**: Setting to 20 requires at least 20 days of data for trends
- **Impact**: Higher values = more reliable trends, but may skip analysis if insufficient data

#### Retry Logic

**max_retries** (default: 3)

- **Effect**: Maximum number of retry attempts when agent execution fails
- **Range**: 0 to 10
- **Example**: Setting to 5 allows up to 5 retry attempts
- **Impact**: Higher values = more resilient to transient errors, but longer execution time on persistent failures

**backoff_multiplier** (default: 2)

- **Effect**: Multiplier for exponential backoff between retries
- **Range**: 1.0 to 5.0
- **Formula**: delay = base_delay \* (backoff_multiplier ^ retry_attempt)
- **Example**: With multiplier 2: delays are 1s, 2s, 4s, 8s...
- **Impact**: Higher values = longer waits between retries, better for rate-limited APIs

#### Logging

**level** (default: "INFO")

- **Effect**: Minimum log level to record
- **Options**: DEBUG, INFO, WARNING, ERROR
- **DEBUG**: All messages including detailed execution traces
- **INFO**: General information about workflow progress
- **WARNING**: Warnings and errors only
- **ERROR**: Errors only
- **Impact**: DEBUG generates large log files, use for troubleshooting only

**format** (default: "json")

- **Effect**: Log output format
- **Options**: json, text
- **json**: Structured JSON logs, machine-readable, ideal for log aggregation
- **text**: Human-readable text logs, easier to read manually
- **Impact**: JSON format required for log analysis tools (ELK, Splunk)

#### Reproducibility

**random_seed** (default: 42)

- **Effect**: Seed for random number generation
- **Range**: Any integer
- **Example**: Same seed + same data = identical results
- **Impact**: Essential for reproducible analysis and testing
- **Note**: Set to null or remove for non-deterministic behavior

#### Data Quality

**max_missing_percentage** (default: 0.1)

- **Effect**: Maximum allowed percentage of missing values in dataset
- **Range**: 0.0 to 1.0 (as decimal, e.g., 0.1 = 10%)
- **Example**: Setting to 0.05 fails if >5% of values are missing
- **Impact**: Lower values = stricter data quality requirements, may reject valid datasets

**date_format** (default: "%Y-%m-%d")

- **Effect**: Expected date format in dataset
- **Format**: Python strftime format string
- **Example**: "%m/%d/%Y" for MM/DD/YYYY format
- **Impact**: Must match actual dataset format or date parsing will fail

### Configuration Examples

#### Development Configuration

```yaml
# config/config.dev.yaml
thresholds:
  low_ctr: 0.008 # More lenient for testing
  high_confidence: 0.6
  roas_change_significant: 0.10

agents:
  max_hypotheses: 7 # Generate more hypotheses for exploration
  min_data_points: 5 # Lower threshold for small test datasets

retry:
  max_retries: 1 # Fail fast in development
  backoff_multiplier: 1.5

logging:
  level: "DEBUG" # Detailed logs for debugging
  format: "text" # Human-readable

random_seed: 42 # Reproducible for testing

data_quality:
  max_missing_percentage: 0.15 # More lenient for test data
  date_format: "%Y-%m-%d"
```

#### Production Configuration

```yaml
# config/config.prod.yaml
thresholds:
  low_ctr: 0.01
  high_confidence: 0.75 # Higher bar for production insights
  roas_change_significant: 0.15

agents:
  max_hypotheses: 5
  min_data_points: 14 # Require 2 weeks of data

retry:
  max_retries: 3
  backoff_multiplier: 2

logging:
  level: "INFO" # Less verbose
  format: "json" # Machine-readable for log aggregation

random_seed: 42 # Reproducible

data_quality:
  max_missing_percentage: 0.05 # Strict data quality
  date_format: "%Y-%m-%d"
```

#### High-Volume Configuration

```yaml
# config/config.highvolume.yaml
thresholds:
  low_ctr: 0.012 # Higher threshold to reduce creative recommendations
  high_confidence: 0.8 # Only show highest confidence insights
  roas_change_significant: 0.20 # Only flag major changes

agents:
  max_hypotheses: 3 # Fewer hypotheses for faster execution
  min_data_points: 10

retry:
  max_retries: 2 # Faster failure
  backoff_multiplier: 1.5

logging:
  level: "WARNING" # Minimal logging
  format: "json"

random_seed: 42

data_quality:
  max_missing_percentage: 0.08
  date_format: "%Y-%m-%d"
```

### Using Different Configurations

Set the `KASPARRO_ENV` environment variable to select configuration:

```bash
# Use development configuration
export KASPARRO_ENV=dev
python src/run.py "Analyze ROAS"

# Use production configuration
export KASPARRO_ENV=prod
python src/run.py "Analyze ROAS"

# Use custom configuration
export KASPARRO_CONFIG=config/custom.yaml
python src/run.py "Analyze ROAS"
```

## Architecture

Kasparro uses a multi-agent architecture with six specialized agents:

1. **Planner Agent**: Parses queries and orchestrates workflow
2. **Data Agent**: Loads dataset, computes metrics, detects trends
3. **Insight Agent**: Generates hypotheses about performance changes
4. **Evaluator Agent**: Validates hypotheses with statistical analysis
5. **Creative Generator**: Produces ad creative recommendations
6. **Report Generator**: Synthesizes outputs into Markdown report

See [agent_graph.md](agent_graph.md) for detailed workflow diagrams and agent interactions.

## Project Structure

```
kasparro/
├── config/
│   └── config.yaml              # System configuration
├── src/
│   ├── run.py                   # CLI entry point
│   ├── agents/                  # Agent implementations
│   │   ├── __init__.py
│   │   ├── planner.py
│   │   ├── data_agent.py
│   │   ├── insight_agent.py
│   │   ├── evaluator_agent.py
│   │   ├── creative_generator.py
│   │   └── report_generator.py
│   ├── schemas/                 # JSON schema definitions
│   │   ├── agent_io.py
│   │   └── validation.py
│   └── utils/                   # Utility modules
│       ├── logger.py
│       └── config_loader.py
├── prompts/                     # Agent prompts
│   ├── planner_prompt.md
│   ├── data_agent_prompt.md
│   ├── insight_agent_prompt.md
│   ├── evaluator_agent_prompt.md
│   └── creative_generator_prompt.md
├── reports/                     # Generated outputs
│   ├── insights.json
│   ├── creatives.json
│   └── report.md
├── logs/                        # Execution logs
│   └── execution_YYYYMMDD_HHMMSS.log
├── tests/                       # Test suite
│   ├── unit/
│   ├── property/
│   └── integration/
├── data/                        # Dataset
│   └── synthetic_fb_ads_undergarments.csv
├── agent_graph.md               # Workflow documentation
└── README.md                    # This file
```

## Testing

Kasparro has comprehensive test coverage with 56 correctness properties:

```bash
# Run all tests
pytest tests/

# Run unit tests only
pytest tests/unit/

# Run property-based tests
pytest tests/property/

# Run integration tests
pytest tests/integration/

# Run with coverage
pytest --cov=src tests/
```

### Property-Based Testing

Kasparro uses [Hypothesis](https://hypothesis.readthedocs.io/) for property-based testing. Each property test validates a correctness guarantee across 100+ random inputs.

Example properties:

- **Property 13**: All confidence scores are between 0.0 and 1.0
- **Property 8**: Metric calculations match manual computations within 0.01% tolerance
- **Property 28**: Same random seed produces identical results

See [design.md](.kiro/specs/kasparro-fb-analyst/design.md) for all 56 correctness properties.

## Development

### Adding a New Agent

1. Create agent class in `src/agents/new_agent.py`
2. Define input/output schemas in `src/schemas/agent_io.py`
3. Create agent prompt in `prompts/new_agent_prompt.md`
4. Register agent in `src/agents/__init__.py`
5. Update routing logic in Planner Agent
6. Add tests in `tests/unit/test_new_agent.py`

### Adding New Metrics

1. Update Data Agent metric computation in `src/agents/data_agent.py`
2. Add metric to data summary schema in `src/schemas/agent_io.py`
3. Update Insight Agent to use new metric
4. Update Evaluator Agent validation logic
5. Document metric in design documentation

## Troubleshooting

### Common Issues

**Issue: "Dataset file not found"**

```bash
# Ensure dataset exists
ls data/synthetic_fb_ads_undergarments.csv

# Check file path in error message
```

**Issue: "Configuration file missing"**

```bash
# System uses defaults, but you can create config
cp config/config.yaml.example config/config.yaml
```

**Issue: "Schema validation failed"**

```bash
# Check logs for detailed error
cat logs/execution_*.log | grep "ValidationError"

# Verify dataset has required fields
head -1 data/synthetic_fb_ads_undergarments.csv
```

**Issue: "No insights generated"**

```bash
# Check if date range has sufficient data
python src/run.py "Analyze ROAS for last 30 days"  # Try longer period

# Check data quality in logs
cat logs/execution_*.log | grep "data_quality"
```

### Debug Mode

Enable debug logging for detailed execution traces:

```yaml
# config/config.yaml
logging:
  level: "DEBUG"
  format: "json"
```

Then run:

```bash
python src/run.py "Your query here"
cat logs/execution_*.log | python -m json.tool
```

## Performance

Typical execution times on standard hardware:

- **Dataset Loading**: 0.5-1.0 seconds (1,280 rows)
- **Metric Computation**: 0.2-0.5 seconds
- **Hypothesis Generation**: 1.0-2.0 seconds
- **Hypothesis Validation**: 1.5-3.0 seconds
- **Creative Generation**: 1.0-2.0 seconds
- **Report Generation**: 0.3-0.5 seconds

**Total End-to-End**: 5-10 seconds for full workflow

### Optimization Tips

- **Dataset Caching**: Data Agent caches loaded dataset for all subsequent agents
- **Parallel Execution**: Run independent agents (Insight + Creative) in parallel
- **Lazy Loading**: Agent prompts loaded only when needed
- **Streaming Logs**: Logs written incrementally to avoid memory buildup

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for new functionality
4. Ensure all tests pass (`pytest tests/`)
5. Update documentation as needed
6. Commit changes (`git commit -m 'Add amazing feature'`)
7. Push to branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Code Style

- Follow PEP 8 style guidelines
- Use type hints for function signatures
- Write docstrings for all public functions
- Keep functions focused and under 50 lines
- Add property-based tests for new correctness guarantees

## License

[Add your license here]

## Acknowledgments

- Built with [Hypothesis](https://hypothesis.readthedocs.io/) for property-based testing
- Uses [pandas](https://pandas.pydata.org/) for data processing
- Inspired by multi-agent system architectures

## Contact

[Add contact information]

---

**Kasparro** - Autonomous Facebook Ads Performance Analyst  
Version 1.0 | Built with ❤️ for data-driven marketing
