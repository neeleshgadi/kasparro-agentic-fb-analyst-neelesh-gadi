"""
Final integration tests for the complete Kasparro system.

This test suite validates:
1. Full end-to-end workflow execution
2. Output file generation and validity
3. Report structure and completeness
4. Error handling scenarios
5. JSON schema compliance
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def test_full_workflow_execution():
    """Test complete end-to-end workflow with sample dataset."""
    print("Testing full workflow execution...")
    
    # Run the CLI with a complete query
    result = subprocess.run(
        [
            sys.executable, "-m", "src.run",
            "Analyze ROAS changes for the last 14 days and generate creative recommendations"
        ],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Workflow failed with return code {result.returncode}"
    assert "Analysis complete!" in result.stdout, "Success message not found in output"
    print("✓ Full workflow executed successfully")


def test_output_files_generated():
    """Validate all output files are generated correctly."""
    print("\nTesting output file generation...")
    
    required_files = [
        "reports/insights.json",
        "reports/creatives.json",
        "reports/report.md"
    ]
    
    for filepath in required_files:
        assert os.path.exists(filepath), f"Required file not found: {filepath}"
        assert os.path.getsize(filepath) > 0, f"File is empty: {filepath}"
        print(f"✓ {filepath} exists and is not empty")


def test_insights_json_validity():
    """Validate insights.json is valid JSON with required structure."""
    print("\nTesting insights.json validity...")
    
    with open("reports/insights.json", "r") as f:
        data = json.load(f)
    
    # Check required top-level keys
    assert "validated_hypotheses" in data, "Missing validated_hypotheses key"
    assert "top_insights" in data, "Missing top_insights key"
    assert "metadata" in data, "Missing metadata key"
    
    # Check validated_hypotheses structure
    hypotheses = data["validated_hypotheses"]
    assert isinstance(hypotheses, list), "validated_hypotheses should be a list"
    assert len(hypotheses) >= 3, f"Expected at least 3 hypotheses, got {len(hypotheses)}"
    
    for hypothesis in hypotheses:
        assert "hypothesis_id" in hypothesis, "Missing hypothesis_id"
        assert "hypothesis_text" in hypothesis, "Missing hypothesis_text"
        assert "validation_status" in hypothesis, "Missing validation_status"
        assert "evidence" in hypothesis, "Missing evidence"
        assert "adjusted_confidence_score" in hypothesis, "Missing adjusted_confidence_score"
        
        # Validate confidence score range
        confidence = hypothesis["adjusted_confidence_score"]
        assert 0.0 <= confidence <= 1.0, f"Confidence score out of range: {confidence}"
    
    print(f"✓ insights.json is valid with {len(hypotheses)} hypotheses")


def test_creatives_json_validity():
    """Validate creatives.json is valid JSON."""
    print("\nTesting creatives.json validity...")
    
    with open("reports/creatives.json", "r") as f:
        data = json.load(f)
    
    # Check required keys
    assert "recommendations" in data, "Missing recommendations key"
    assert "metadata" in data, "Missing metadata key"
    
    # Check recommendations structure
    recommendations = data["recommendations"]
    assert isinstance(recommendations, list), "recommendations should be a list"
    
    print(f"✓ creatives.json is valid with {len(recommendations)} recommendations")


def test_report_md_structure():
    """Validate report.md contains all required sections."""
    print("\nTesting report.md structure...")
    
    with open("reports/report.md", "r") as f:
        content = f.read()
    
    # Check required sections
    required_sections = [
        "## Executive Summary",
        "## Key Insights",
        "## Creative Recommendations",
        "## Methodology"
    ]
    
    for section in required_sections:
        assert section in content, f"Missing required section: {section}"
        print(f"✓ Found section: {section}")
    
    # Check for key content elements
    assert "Analysis Request:" in content, "Missing analysis request"
    assert "Dataset Overview:" in content, "Missing dataset overview"
    assert "Confidence Score:" in content, "Missing confidence scores"
    assert "Validation Status:" in content, "Missing validation status"
    
    print("✓ report.md has all required sections and content")


def test_error_handling_missing_dataset():
    """Test error handling for missing dataset file."""
    print("\nTesting error handling for missing dataset...")
    
    result = subprocess.run(
        [
            sys.executable, "-m", "src.run",
            "Test query",
            "--dataset", "nonexistent.csv"
        ],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 1, "Should return error code for missing dataset"
    assert "Dataset file not found" in result.stderr, "Missing error message"
    print("✓ Missing dataset error handled correctly")


def test_error_handling_empty_query():
    """Test error handling for empty query."""
    print("\nTesting error handling for empty query...")
    
    result = subprocess.run(
        [
            sys.executable, "-m", "src.run",
            "   "  # Empty query with whitespace
        ],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 1, "Should return error code for empty query"
    assert "Query cannot be empty" in result.stderr, "Missing error message"
    print("✓ Empty query error handled correctly")


def test_log_file_creation():
    """Validate log files are created."""
    print("\nTesting log file creation...")
    
    logs_dir = Path("logs")
    assert logs_dir.exists(), "Logs directory not found"
    
    log_files = list(logs_dir.glob("execution_*.log"))
    assert len(log_files) > 0, "No log files found"
    
    # Check latest log file has content
    latest_log = max(log_files, key=lambda p: p.stat().st_mtime)
    assert latest_log.stat().st_size > 0, "Log file is empty"
    
    print(f"✓ Log files created ({len(log_files)} files found)")


def test_output_file_locations():
    """Validate output files are in correct locations."""
    print("\nTesting output file locations...")
    
    # Check reports directory structure
    reports_dir = Path("reports")
    assert reports_dir.exists(), "Reports directory not found"
    assert reports_dir.is_dir(), "Reports should be a directory"
    
    # Check all outputs are in reports directory
    assert (reports_dir / "insights.json").exists(), "insights.json not in reports/"
    assert (reports_dir / "creatives.json").exists(), "creatives.json not in reports/"
    assert (reports_dir / "report.md").exists(), "report.md not in reports/"
    
    print("✓ All output files in correct locations")


def run_all_tests():
    """Run all integration tests."""
    print("="*60)
    print("FINAL INTEGRATION TEST SUITE")
    print("="*60)
    
    tests = [
        test_full_workflow_execution,
        test_output_files_generated,
        test_insights_json_validity,
        test_creatives_json_validity,
        test_report_md_structure,
        test_error_handling_missing_dataset,
        test_error_handling_empty_query,
        test_log_file_creation,
        test_output_file_locations,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"\n✗ TEST FAILED: {test.__name__}")
            print(f"  Error: {e}")
            failed += 1
        except Exception as e:
            print(f"\n✗ TEST ERROR: {test.__name__}")
            print(f"  Error: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("="*60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
