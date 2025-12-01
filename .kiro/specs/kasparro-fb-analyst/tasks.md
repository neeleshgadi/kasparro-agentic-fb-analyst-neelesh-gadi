# Implementation Plan

- [x] 1. Set up project structure and core infrastructure

  - Create directory structure: src/, config/, prompts/, reports/, logs/, tests/, data/
  - Set up Python package structure with **init**.py files
  - Create requirements.txt with dependencies (pandas, PyYAML, jsonschema, pytest, hypothesis)
  - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5_

- [x] 2. Implement configuration management and utilities

  - Create config/config.yaml with all thresholds, agent settings, retry logic, logging, and data quality parameters
  - Implement src/utils/config_loader.py to load and validate configuration
  - Implement src/utils/logger.py for structured JSON logging with ISO 8601 timestamps
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 10.4, 10.5_

- [x] 2.1 Write property test for configuration loading

  - **Property 26: Configuration Loading**
  - **Validates: Requirements 8.1, 8.4**

- [x] 2.2 Write property test for configuration threshold validation

  - **Property 27: Configuration Threshold Validation**
  - **Validates: Requirements 8.2**

- [x] 2.3 Write property test for random seed reproducibility

  - **Property 28: Random Seed Reproducibility**
  - **Validates: Requirements 8.5**

- [x] 2.4 Write property test for log format consistency

  - **Property 36: Log Format Consistency**
  - **Validates: Requirements 10.4**

- [x] 3. Define JSON schemas and validation

  - Create src/schemas/agent_io.py with all agent input/output schemas
  - Implement src/schemas/validation.py with schema validation functions using jsonschema
  - Define standard communication envelope schema
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 3.1 Write property test for schema validation

  - **Property 3: Schema Validation on Agent Communication**
  - **Validates: Requirements 2.1, 2.2, 2.3**

- [x] 3.2 Write property test for JSON serialization round-trip

  - **Property 5: JSON Serialization Round-Trip**
  - **Validates: Requirements 2.4**

- [x] 3.3 Write property test for agent output envelope consistency

  - **Property 4: Agent Output Envelope Consistency**
  - **Validates: Requirements 2.5**

- [x] 4. Implement Data Agent

  - Create src/agents/data_agent.py with DataAgent class
  - Implement dataset loading from CSV with field validation
  - Implement data quality checks (missing values, invalid dates, non-numeric values)
  - Implement metric calculations (ROAS, CTR, CVR, avg_cpc)
  - Implement trend calculations (WoW, MoM changes) and classification (increasing/decreasing/stable)
  - Implement segmentation by campaign, creative_type, audience_type, platform
  - Implement dataset caching mechanism
  - Create prompts/data_agent_prompt.md
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 13.1, 13.2, 13.3, 13.4, 13.5, 17.1, 17.2, 17.3, 17.4_

- [x] 4.1 Write property test for dataset field validation

  - **Property 6: Dataset Field Validation**
  - **Validates: Requirements 3.1**

- [x] 4.2 Write property test for dataset summary completeness

  - **Property 7: Dataset Summary Completeness**
  - **Validates: Requirements 3.2**

- [x] 4.3 Write property test for metric calculation accuracy

  - **Property 8: Metric Calculation Accuracy**
  - **Validates: Requirements 3.3**

- [x] 4.4 Write property test for data quality reporting

  - **Property 9: Data Quality Reporting**
  - **Validates: Requirements 3.4**

- [x] 4.5 Write property test for dataset caching consistency

  - **Property 10: Dataset Caching Consistency**
  - **Validates: Requirements 3.5**

- [x] 4.6 Write property test for missing value handling

  - **Property 40: Missing Value Handling**
  - **Validates: Requirements 13.1**

- [x] 4.7 Write property test for date parsing error handling

  - **Property 41: Date Parsing Error Handling**
  - **Validates: Requirements 13.2**

- [x] 4.8 Write property test for numeric field error handling

  - **Property 42: Numeric Field Error Handling**
  - **Validates: Requirements 13.3**

- [x] 4.9 Write property test for required field validation

  - **Property 43: Required Field Validation**
  - **Validates: Requirements 13.4**

- [x] 4.10 Write property test for data quality summary inclusion

  - **Property 44: Data Quality Summary Inclusion**
  - **Validates: Requirements 13.5**

- [x] 4.11 Write property test for trend calculation completeness

  - **Property 51: Trend Calculation Completeness**
  - **Validates: Requirements 17.1**

- [x] 4.12 Write property test for trend direction classification

  - **Property 52: Trend Direction Classification**
  - **Validates: Requirements 17.2**

- [x] 4.13 Write property test for seasonality flagging

  - **Property 53: Seasonality Flagging**
  - **Validates: Requirements 17.3**

- [x] 4.14 Write property test for trend data schema inclusion

  - **Property 54: Trend Data Schema Inclusion**
  - **Validates: Requirements 17.4**

- [x] 5. Checkpoint - Ensure Data Agent tests pass

  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement Planner Agent

  - Create src/agents/planner.py with PlannerAgent class
  - Implement natural language query parsing to extract intent, time ranges, and parameters
  - Implement task decomposition logic for ROAS analysis, creative generation, and full workflows
  - Implement routing decision logic to determine next agent and workflow type
  - Create prompts/planner_prompt.md with Think-Analyze-Conclude structure
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 4.1, 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 6.1 Write property test for CLI query processing completeness

  - **Property 1: CLI Query Processing Completeness**
  - **Validates: Requirements 1.1, 1.2, 1.5**

- [x] 6.2 Write property test for CLI error handling

  - **Property 2: CLI Error Handling**
  - **Validates: Requirements 1.3**

- [x] 6.3 Write property test for task decomposition completeness

  - **Property 11: Task Decomposition Completeness**
  - **Validates: Requirements 4.1**

- [x] 6.4 Write property test for reasoning structure completeness

  - **Property 16: Reasoning Structure Completeness**
  - **Validates: Requirements 5.1, 5.2, 5.3, 5.4**

- [x] 6.5 Write property test for reasoning chain logging

  - **Property 17: Reasoning Chain Logging**
  - **Validates: Requirements 5.5**

- [x] 7. Implement Insight Agent

  - Create src/agents/insight_agent.py with InsightAgent class
  - Implement hypothesis generation logic based on data patterns and trends
  - Implement confidence scoring model (initial confidence based on data availability)
  - Generate 3-5 hypotheses with categories (creative, audience, platform, budget, seasonality)
  - Implement Think-Analyze-Conclude reasoning structure
  - Create prompts/insight_agent_prompt.md
  - _Requirements: 4.2, 4.3, 14.1, 17.5_

- [x] 7.1 Write property test for hypothesis generation minimum count

  - **Property 12: Hypothesis Generation Minimum Count**
  - **Validates: Requirements 4.2**

- [x] 7.2 Write property test for confidence score bounds

  - **Property 13: Confidence Score Bounds**
  - **Validates: Requirements 4.3, 6.5, 14.1, 14.3**

- [x] 7.3 Write property test for trend incorporation in hypotheses

  - **Property 55: Trend Incorporation in Hypotheses**
  - **Validates: Requirements 17.5**

- [x] 8. Implement Evaluator Agent

  - Create src/agents/evaluator_agent.py with EvaluatorAgent class
  - Implement hypothesis validation logic using dataset metrics
  - Implement segmentation comparison (at least 2 segments per hypothesis)
  - Implement statistical significance testing (p-values, confidence intervals)
  - Implement confidence score adjustment based on validation strength
  - Implement weighted confidence formula: (InsightConfidence _ 0.4) + (ValidationStrength _ 0.4) + (SegmentationEvidence \* 0.2)
  - Implement hypothesis ranking by validation strength and confidence
  - Create prompts/evaluator_agent_prompt.md
  - _Requirements: 4.4, 4.5, 7.1, 7.2, 7.3, 7.4, 7.5, 14.2, 14.5_

- [x] 8.1 Write property test for hypothesis validation evidence

  - **Property 14: Hypothesis Validation Evidence**
  - **Validates: Requirements 4.4, 7.1**

- [x] 8.2 Write property test for hypothesis ranking consistency

  - **Property 15: Hypothesis Ranking Consistency**
  - **Validates: Requirements 4.5, 14.5**

- [x] 8.3 Write property test for hypothesis segmentation comparison

  - **Property 22: Hypothesis Segmentation Comparison**
  - **Validates: Requirements 7.2**

- [x] 8.4 Write property test for statistical significance inclusion

  - **Property 23: Statistical Significance Inclusion**
  - **Validates: Requirements 7.3**

- [x] 8.5 Write property test for weak evidence confidence calibration

  - **Property 24: Weak Evidence Confidence Calibration**
  - **Validates: Requirements 7.4**

- [x] 8.6 Write property test for insights output serialization round-trip

  - **Property 25: Insights Output Serialization Round-Trip**
  - **Validates: Requirements 7.5**

- [x] 8.7 Write property test for confidence score adjustment

  - **Property 45: Confidence Score Adjustment**
  - **Validates: Requirements 14.2**

-

- [x] 9. Checkpoint - Ensure Insight and Evaluator tests pass

  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Implement Creative Generator Agent

  - Create src/agents/creative_generator.py with CreativeGeneratorAgent class
  - Implement low-CTR campaign filtering based on configured threshold
  - Implement creative recommendation generation (3+ variations per campaign)
  - Analyze high-performing vs low-performing creative attributes
  - Generate creative variations with message, type, audience, rationale, and confidence
  - Create prompts/creative_generator_prompt.md
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 14.3_

- [x] 10.1 Write property test for low-CTR campaign filtering

  - **Property 18: Low-CTR Campaign Filtering**
  - **Validates: Requirements 6.1**

- [x] 10.2 Write property test for creative variation minimum count

  - **Property 19: Creative Variation Minimum Count**
  - **Validates: Requirements 6.2**

- [x] 10.3 Write property test for creative schema completeness

  - **Property 20: Creative Schema Completeness**
  - **Validates: Requirements 6.3**

- [x] 10.4 Write property test for creative output serialization round-trip

  - **Property 21: Creative Output Serialization Round-Trip**
  - **Validates: Requirements 6.4**

-

- [x] 11. Implement Report Generator

  - Create src/agents/report_generator.py with ReportGenerator class
  - Implement Markdown report generation with sections: Executive Summary, Key Insights, Creative Recommendations, Methodology
  - Include top 3 validated hypotheses with supporting metrics
  - Include creative recommendations with rationale and confidence scores
  - Ensure proper Markdown formatting (headers, lists, tables)
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] 11.1 Write property test for report generation completeness

  - **Property 29: Report Generation Completeness**
  - **Validates: Requirements 9.1, 9.2**

- [x] 11.2 Write property test for report insights inclusion

  - **Property 30: Report Insights Inclusion**
  - **Validates: Requirements 9.3**

- [x] 11.3 Write property test for report creatives inclusion

  - **Property 31: Report Creatives Inclusion**
  - **Validates: Requirements 9.4**

- [x] 11.4 Write property test for report Markdown validity

  - **Property 32: Report Markdown Validity**
  - **Validates: Requirements 9.5**

- [x] 12. Implement agent orchestration and retry logic

  - Create src/agents/**init**.py with agent registry and factory functions
  - Implement retry logic with exponential backoff in agent execution wrapper
  - Implement agent initialization with configuration-only parameters
  - Ensure agent execution isolation (no direct agent-to-agent calls)
  - _Requirements: 12.2, 12.3, 16.1, 16.2, 16.3, 16.4, 16.5_

- [x] 12.1 Write property test for agent initialization parameters

  - **Property 38: Agent Initialization Parameters**
  - **Validates: Requirements 12.2**

- [x] 12.2 Write property test for agent execution isolation

  - **Property 39: Agent Execution Isolation**
  - **Validates: Requirements 12.3**

- [x] 12.3 Write property test for retry execution on failure

  - **Property 46: Retry Execution on Failure**
  - **Validates: Requirements 16.1**

- [x] 12.4 Write property test for exponential backoff timing

  - **Property 47: Exponential Backoff Timing**
  - **Validates: Requirements 16.2**

- [x] 12.5 Write property test for retry exhaustion handling

  - **Property 48: Retry Exhaustion Handling**
  - **Validates: Requirements 16.3**

- [x] 12.6 Write property test for successful retry logging

  - **Property 49: Successful Retry Logging**
  - **Validates: Requirements 16.4**

- [x] 12.7 Write property test for retry configuration loading

  - **Property 50: Retry Configuration Loading**
  - **Validates: Requirements 16.5**

- [x] 13. Implement CLI interface (src/run.py)

  - Create src/run.py with argparse CLI interface
  - Implement query parsing and validation
  - Implement agent workflow orchestration (Planner → Data → Insight → Evaluator → Creative → Report)
  - Implement logging for agent execution start and completion
  - Implement error handling and structured error responses
  - Write outputs to reports/insights.json, reports/creatives.json, reports/report.md
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 10.1, 10.2, 10.3, 18.5_

- [x] 13.1 Write property test for agent execution start logging

  - **Property 33: Agent Execution Start Logging**
  - **Validates: Requirements 10.1**

- [x] 13.2 Write property test for agent execution completion logging

  - **Property 34: Agent Execution Completion Logging**
  - **Validates: Requirements 10.2**

- [x] 13.3 Write property test for error logging completeness

  - **Property 35: Error Logging Completeness**
  - **Validates: Requirements 10.3**

- [x] 13.4 Write property test for log file creation

  - **Property 37: Log File Creation**
  - **Validates: Requirements 10.5**

- [x] 13.5 Write property test for output file location consistency

  - **Property 56: Output File Location Consistency**
  - **Validates: Requirements 18.5**

- [x] 14. Checkpoint - Ensure all integration tests pass

  - Ensure all tests pass, ask the user if questions arise.

-

- [x] 15. Create documentation

  - Create agent_graph.md with Mermaid workflow diagram and agent interaction explanations
  - Create README.md with quickstart instructions, example commands, and sample outputs
  - Document all JSON schemas with examples
  - Document configuration parameters and their effects
  - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5_

- [x] 16. Create sample dataset and test fixtures

  - Create data/synthetic_fb_ads_undergarments.csv with sample campaign data
  - Create tests/fixtures/sample_dataset.csv for testing
  - Create tests/fixtures/sample_config.yaml for testing
  - _Requirements: 3.1, 3.2, 3.3_

- [x] 17. Final integration testing and validation

  - Run full end-to-end workflow with sample dataset
  - Validate all output files are generated correctly
  - Validate report.md contains all required sections
  - Validate insights.json and creatives.json are valid JSON
  - Test error scenarios and retry logic
  - _Requirements: All_

-

- [x] 18. Final Checkpoint - Complete system validation

  - Ensure all tests pass, ask the user if questions arise.
