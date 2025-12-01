#!/usr/bin/env python3
"""
Kasparro CLI - Multi-agent Facebook Ads Analyst

This module provides the command-line interface for the Kasparro system,
orchestrating the agent workflow from query parsing to report generation.
"""

import argparse
import json
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from src.agents import AgentRegistry, AgentExecutionError
from src.utils.config_loader import load_config, ConfigurationError
from src.utils.logger import (
    create_logger_from_config,
    log_agent_start,
    log_agent_completion,
    log_agent_error,
)
from src.schemas.validation import validate_schema


class CLIError(Exception):
    """Raised when CLI encounters an error."""
    pass


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Kasparro - Multi-agent Facebook Ads Analyst",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/run.py "Analyze ROAS for last 7 days"
  python src/run.py "Why did CTR drop last week?" --dataset data/custom.csv
  python src/run.py "Generate creative recommendations" --config config/custom.yaml
        """
    )
    
    parser.add_argument(
        "query",
        type=str,
        help="Natural language query about ad performance"
    )
    
    parser.add_argument(
        "--dataset",
        type=str,
        default="data/synthetic_fb_ads_undergarments.csv",
        help="Path to dataset CSV file (default: data/synthetic_fb_ads_undergarments.csv)"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        default="config/config.yaml",
        help="Path to configuration file (default: config/config.yaml)"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="reports",
        help="Directory for output files (default: reports)"
    )
    
    return parser.parse_args()


def validate_query(query: str) -> None:
    """Validate user query.
    
    Args:
        query: User query string
        
    Raises:
        CLIError: If query is invalid
    """
    if not query or not query.strip():
        raise CLIError("Query cannot be empty")
    
    if len(query.strip()) < 5:
        raise CLIError(
            "Query is too short. Please provide a more detailed request.\n"
            "Example: 'Analyze ROAS for last 7 days'"
        )


def validate_inputs(args: argparse.Namespace) -> None:
    """Validate CLI inputs.
    
    Args:
        args: Parsed arguments
        
    Raises:
        CLIError: If inputs are invalid
    """
    # Validate query
    validate_query(args.query)
    
    # Validate dataset exists
    if not os.path.exists(args.dataset):
        raise CLIError(
            f"Dataset file not found: {args.dataset}\n"
            f"Please ensure the file exists or specify a different path with --dataset"
        )
    
    # Validate config exists (or will use defaults)
    if args.config != "config/config.yaml" and not os.path.exists(args.config):
        raise CLIError(f"Configuration file not found: {args.config}")


def ensure_output_directory(output_dir: str) -> None:
    """Ensure output directory exists.
    
    Args:
        output_dir: Output directory path
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)


def write_output_file(
    output_dir: str,
    filename: str,
    content: Any,
    logger: Any
) -> None:
    """Write output to file.
    
    Args:
        output_dir: Output directory
        filename: Output filename
        content: Content to write (dict for JSON, str for text)
        logger: Logger instance
    """
    filepath = os.path.join(output_dir, filename)
    
    try:
        if isinstance(content, dict):
            with open(filepath, 'w') as f:
                json.dump(content, f, indent=2)
        else:
            with open(filepath, 'w') as f:
                f.write(str(content))
        
        logger.info(
            f"Output written to {filepath}",
            extra={
                "output_file": filepath,
                "file_type": "json" if isinstance(content, dict) else "text"
            }
        )
    except Exception as e:
        logger.error(
            f"Failed to write output file: {filepath}",
            extra={
                "output_file": filepath,
                "error": str(e)
            }
        )
        raise


def execute_agent(
    agent_name: str,
    input_data: Dict[str, Any],
    config: Dict[str, Any],
    logger: Any
) -> Dict[str, Any]:
    """Execute a single agent with logging and error handling.
    
    Args:
        agent_name: Name of agent to execute
        input_data: Input data for agent
        config: Configuration dictionary
        logger: Logger instance
        
    Returns:
        Agent output
        
    Raises:
        AgentExecutionError: If agent execution fails
    """
    start_time = datetime.utcnow()
    
    # Log agent start
    log_agent_start(logger, agent_name, input_data)
    
    try:
        # Create agent instance
        agent = AgentRegistry.create(agent_name, config)
        
        # Execute agent
        output = agent.execute(input_data)
        
        # Calculate execution duration
        end_time = datetime.utcnow()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Log agent completion
        output_summary = {
            "status": output.get("status", "success"),
            "output_keys": list(output.keys()) if isinstance(output, dict) else []
        }
        log_agent_completion(logger, agent_name, duration_ms, output_summary)
        
        return output
        
    except Exception as e:
        # Calculate execution duration
        end_time = datetime.utcnow()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Log error
        log_agent_error(
            logger,
            agent_name,
            str(e),
            type(e).__name__,
            {"input_data_keys": list(input_data.keys()) if isinstance(input_data, dict) else []}
        )
        
        raise AgentExecutionError(f"Agent '{agent_name}' failed: {str(e)}") from e


def orchestrate_workflow(
    query: str,
    dataset_path: str,
    config: Dict[str, Any],
    output_dir: str,
    logger: Any
) -> Dict[str, Any]:
    """Orchestrate the complete agent workflow.
    
    Args:
        query: User query
        dataset_path: Path to dataset
        config: Configuration dictionary
        output_dir: Output directory
        logger: Logger instance
        
    Returns:
        Dictionary with workflow results
    """
    logger.info(
        "Starting workflow orchestration",
        extra={
            "query": query,
            "dataset_path": dataset_path,
            "output_dir": output_dir
        }
    )
    
    results = {}
    
    try:
        # Step 1: Planner Agent
        logger.info("Executing Planner Agent")
        planner_context = {
            "dataset_path": dataset_path,
            "config": config
        }
        # Create agent and execute with proper signature
        planner_agent = AgentRegistry.create("planner", config)
        start_time = datetime.utcnow()
        log_agent_start(logger, "planner", {"query": query, "context": planner_context})
        
        try:
            planner_output = planner_agent.execute(query, planner_context)
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            log_agent_completion(logger, "planner", duration_ms, {"status": "success"})
        except Exception as e:
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            log_agent_error(logger, "planner", str(e), type(e).__name__, {})
            raise AgentExecutionError(f"Agent 'planner' failed: {str(e)}") from e
        
        results["planner"] = planner_output
        
        # Extract date range and routing from planner
        date_range = planner_output.get("date_range")
        routing = planner_output.get("routing", {})
        workflow_type = routing.get("workflow_type", "full")
        
        # Step 2: Data Agent
        logger.info("Executing Data Agent")
        data_input = {
            "dataset_path": dataset_path,
            "date_range": date_range,
            "metrics": ["roas", "ctr", "cvr", "avg_cpc"],
            "config": config
        }
        data_output = execute_agent("data_agent", data_input, config, logger)
        results["data_agent"] = data_output
        
        # Step 3: Insight Agent
        logger.info("Executing Insight Agent")
        insight_input = {
            "data_summary": data_output,
            "focus_metric": "roas",
            "time_period": date_range,
            "config": config
        }
        insight_output = execute_agent("insight_agent", insight_input, config, logger)
        results["insight_agent"] = insight_output
        
        # Step 4: Evaluator Agent
        logger.info("Executing Evaluator Agent")
        evaluator_input = {
            "hypotheses": insight_output.get("hypotheses", []),
            "dataset_path": dataset_path,
            "data_summary": data_output,
            "config": config
        }
        evaluator_output = execute_agent("evaluator_agent", evaluator_input, config, logger)
        results["evaluator_agent"] = evaluator_output
        
        # Write insights.json
        insights_data = {
            "validated_hypotheses": evaluator_output.get("validated_hypotheses", []),
            "top_insights": evaluator_output.get("top_insights", []),
            "metadata": {
                "query": query,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "dataset": dataset_path
            }
        }
        write_output_file(output_dir, "insights.json", insights_data, logger)
        
        # Step 5: Creative Generator (if applicable)
        if workflow_type in ["creative_generation", "full"]:
            logger.info("Executing Creative Generator Agent")
            creative_input = {
                "data_summary": data_output,
                "low_ctr_threshold": config.get("thresholds", {}).get("low_ctr", 0.01),
                "dataset_path": dataset_path,
                "config": config
            }
            creative_output = execute_agent("creative_generator", creative_input, config, logger)
            results["creative_generator"] = creative_output
            
            # Write creatives.json
            creatives_data = {
                "recommendations": creative_output.get("recommendations", []),
                "metadata": {
                    "query": query,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "dataset": dataset_path,
                    "low_ctr_threshold": config.get("thresholds", {}).get("low_ctr", 0.01)
                }
            }
            write_output_file(output_dir, "creatives.json", creatives_data, logger)
        else:
            # Write empty creatives file
            creatives_data = {
                "recommendations": [],
                "metadata": {
                    "query": query,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "note": "Creative generation not requested for this workflow"
                }
            }
            write_output_file(output_dir, "creatives.json", creatives_data, logger)
            results["creative_generator"] = {"recommendations": []}
        
        # Step 6: Report Generator
        logger.info("Executing Report Generator")
        report_input = {
            "insights": evaluator_output,
            "creatives": results.get("creative_generator", {"recommendations": []}),
            "data_summary": data_output,
            "query": query
        }
        report_output = execute_agent("report_generator", report_input, config, logger)
        results["report_generator"] = report_output
        
        # Report Generator writes the file itself, just log the path
        report_path = report_output.get("report_path", "reports/report.md")
        logger.info(
            f"Report generated at {report_path}",
            extra={"report_path": report_path}
        )
        
        logger.info(
            "Workflow completed successfully",
            extra={
                "agents_executed": list(results.keys()),
                "output_files": ["insights.json", "creatives.json", "report.md"]
            }
        )
        
        return results
        
    except Exception as e:
        logger.error(
            "Workflow orchestration failed",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "completed_agents": list(results.keys())
            },
            exc_info=True
        )
        raise


def main() -> int:
    """Main CLI entry point.
    
    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        # Parse arguments
        args = parse_arguments()
        
        # Validate inputs
        validate_inputs(args)
        
        # Load configuration
        try:
            config = load_config(args.config)
        except ConfigurationError as e:
            print(f"Configuration error: {e}", file=sys.stderr)
            return 1
        
        # Set up logger
        logger = create_logger_from_config(config, name="kasparro_cli")
        
        logger.info(
            "Kasparro CLI started",
            extra={
                "query": args.query,
                "dataset": args.dataset,
                "config_file": args.config,
                "output_dir": args.output_dir
            }
        )
        
        # Ensure output directory exists
        ensure_output_directory(args.output_dir)
        
        # Execute workflow
        results = orchestrate_workflow(
            query=args.query,
            dataset_path=args.dataset,
            config=config,
            output_dir=args.output_dir,
            logger=logger
        )
        
        # Print success message
        print("\n" + "="*60)
        print("Analysis complete!")
        print("="*60)
        print(f"\nOutputs written to: {args.output_dir}/")
        print(f"  - insights.json    (validated hypotheses)")
        print(f"  - creatives.json   (creative recommendations)")
        print(f"  - report.md        (executive summary)")
        print("\n" + "="*60 + "\n")
        
        logger.info("Kasparro CLI completed successfully")
        
        return 0
        
    except CLIError as e:
        print(f"\nError: {e}\n", file=sys.stderr)
        return 1
        
    except AgentExecutionError as e:
        print(f"\nAgent execution failed: {e}\n", file=sys.stderr)
        print("Check logs for detailed error information.", file=sys.stderr)
        return 1
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user", file=sys.stderr)
        return 1
        
    except Exception as e:
        print(f"\nUnexpected error: {e}\n", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
