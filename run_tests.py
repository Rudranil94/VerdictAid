#!/usr/bin/env python3
import subprocess
import sys
import os
import time
from datetime import datetime
import json

def run_security_checks():
    """Run security checks using safety and bandit."""
    print("\n=== Running Security Checks ===")
    
    # Check dependencies for known security vulnerabilities
    print("\nChecking dependencies for security vulnerabilities...")
    safety_result = subprocess.run(["safety", "check"], capture_output=True, text=True)
    print(safety_result.stdout)
    
    # Run static security analysis
    print("\nRunning static security analysis...")
    bandit_result = subprocess.run(
        ["bandit", "-r", "app", "-f", "json", "-ll"],
        capture_output=True,
        text=True
    )
    
    if bandit_result.returncode == 0:
        print("No security issues found in static analysis")
    else:
        try:
            issues = json.loads(bandit_result.stdout)
            print(f"Found {len(issues['results'])} potential security issues:")
            for issue in issues['results']:
                print(f"\n- {issue['issue_text']}")
                print(f"  File: {issue['filename']}:{issue['line_number']}")
                print(f"  Severity: {issue['issue_severity']}")
        except json.JSONDecodeError:
            print("Error parsing security analysis results")
            print(bandit_result.stdout)

def run_test_suite():
    """Run the complete test suite with coverage."""
    test_suites = [
        ("Unit Tests", ["pytest", "-v", "-m", "unit"]),
        ("Integration Tests", ["pytest", "-v", "-m", "integration"]),
        ("End-to-End Tests", ["pytest", "-v", "-m", "e2e"]),
        ("Security Tests", ["pytest", "-v", "-m", "security"]),
        ("Performance Tests", ["pytest", "-v", "-m", "performance"]),
        ("API Tests", ["pytest", "-v", "-m", "api"]),
    ]
    
    results = []
    start_time = time.time()
    
    for suite_name, command in test_suites:
        print(f"\n=== Running {suite_name} ===")
        result = subprocess.run(command, capture_output=True, text=True)
        results.append((suite_name, result))
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
    
    total_time = time.time() - start_time
    
    # Generate report
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_duration": total_time,
        "results": []
    }
    
    print("\n=== Test Summary ===")
    for suite_name, result in results:
        success = result.returncode == 0
        report["results"].append({
            "suite": suite_name,
            "success": success,
            "output": result.stdout,
            "errors": result.stderr
        })
        status = "✅ Passed" if success else "❌ Failed"
        print(f"{suite_name}: {status}")
    
    # Save report
    os.makedirs("test_reports", exist_ok=True)
    report_file = f"test_reports/test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\nDetailed test report saved to: {report_file}")
    print(f"Total test duration: {total_time:.2f} seconds")

def main():
    """Main entry point for test runner."""
    # Ensure we're in the correct environment
    os.environ["TESTING"] = "True"
    
    try:
        # Run security checks first
        run_security_checks()
        
        # Run test suite
        run_test_suite()
        
    except subprocess.CalledProcessError as e:
        print(f"Error running tests: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
