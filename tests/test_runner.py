#!/usr/bin/env python3
"""
Comprehensive test runner for narko testing suite.
Provides multiple test execution modes and reporting options.
"""
import sys
import os
import subprocess
import argparse
import time
import json
from pathlib import Path
from typing import Dict, List, Optional, Any

# Test categories and their corresponding pytest markers
TEST_CATEGORIES = {
    'unit': {
        'marker': 'unit',
        'description': 'Fast unit tests for individual functions',
        'timeout': 300  # 5 minutes
    },
    'integration': {
        'marker': 'integration', 
        'description': 'Integration tests for API and external services',
        'timeout': 600  # 10 minutes
    },
    'e2e': {
        'marker': 'e2e',
        'description': 'End-to-end workflow tests',
        'timeout': 900  # 15 minutes
    },
    'performance': {
        'marker': 'performance',
        'description': 'Performance and load tests',
        'timeout': 1200  # 20 minutes
    },
    'security': {
        'marker': 'security',
        'description': 'Security validation tests',
        'timeout': 600  # 10 minutes
    },
    'slow': {
        'marker': 'slow',
        'description': 'Long-running tests (includes real API calls)',
        'timeout': 1800  # 30 minutes
    }
}

class TestRunner:
    """Main test runner class."""
    
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path(__file__).parent
        self.project_root = self.base_dir.parent
        
    def run_tests(
        self,
        categories: List[str] = None,
        coverage: bool = True,
        parallel: bool = False,
        verbose: bool = False,
        html_report: bool = False,
        benchmark: bool = False,
        fail_fast: bool = False,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """Run tests with specified options."""
        
        # Build pytest command
        cmd = ['python', '-m', 'pytest']
        
        # Add test categories
        if categories:
            valid_categories = [cat for cat in categories if cat in TEST_CATEGORIES]
            if not valid_categories:
                print(f"Warning: No valid categories specified. Available: {list(TEST_CATEGORIES.keys())}")
                return {"success": False, "error": "Invalid test categories"}
            
            # Build marker expression
            marker_expr = " or ".join(f"({TEST_CATEGORIES[cat]['marker']})" for cat in valid_categories)
            cmd.extend(['-m', marker_expr])
        
        # Add test directory
        cmd.append(str(self.base_dir))
        
        # Coverage options
        if coverage:
            cmd.extend([
                '--cov=narko',
                '--cov-report=html:htmlcov',
                '--cov-report=term-missing',
                '--cov-report=xml',
                '--cov-fail-under=85'
            ])
        
        # Parallel execution
        if parallel:
            cmd.extend(['-n', 'auto'])
        
        # Verbose output
        if verbose:
            cmd.extend(['-v', '-s'])
        
        # HTML report
        if html_report:
            cmd.extend(['--html=test_report.html', '--self-contained-html'])
        
        # Benchmark
        if benchmark:
            cmd.extend(['--benchmark-only', '--benchmark-json=benchmark_results.json'])
        
        # Fail fast
        if fail_fast:
            cmd.extend(['-x'])
        
        # Additional options
        cmd.extend([
            '--tb=short',
            '--strict-markers',
            '--junitxml=test-results.xml'
        ])
        
        print(f"Running command: {' '.join(cmd)}")
        
        if dry_run:
            return {"success": True, "command": cmd, "dry_run": True}
        
        # Run tests
        start_time = time.time()
        try:
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
            duration = time.time() - start_time
            
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "duration": duration,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": cmd
            }
        
        except Exception as e:
            duration = time.time() - start_time
            return {
                "success": False,
                "error": str(e),
                "duration": duration,
                "command": cmd
            }
    
    def run_security_scan(self) -> Dict[str, Any]:
        """Run security scans on the codebase."""
        results = {}
        
        # Bandit security scan
        try:
            bandit_cmd = [
                'python', '-m', 'bandit', 
                '-r', str(self.project_root),
                '-f', 'json',
                '-o', 'security_report.json',
                '-ll'  # Low level and above
            ]
            
            result = subprocess.run(bandit_cmd, capture_output=True, text=True)
            results['bandit'] = {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "output": result.stdout
            }
        
        except Exception as e:
            results['bandit'] = {"success": False, "error": str(e)}
        
        # Safety check for dependencies
        try:
            safety_cmd = ['python', '-m', 'safety', 'check', '--json']
            result = subprocess.run(safety_cmd, capture_output=True, text=True)
            results['safety'] = {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "output": result.stdout
            }
        
        except Exception as e:
            results['safety'] = {"success": False, "error": str(e)}
        
        return results
    
    def run_performance_profile(self) -> Dict[str, Any]:
        """Run performance profiling on test suite."""
        profile_cmd = [
            'python', '-m', 'pytest',
            '--profile',
            '--profile-svg',
            '-m', 'performance',
            str(self.base_dir)
        ]
        
        try:
            result = subprocess.run(profile_cmd, cwd=self.project_root, capture_output=True, text=True)
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "output": result.stdout
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def generate_test_summary(self) -> Dict[str, Any]:
        """Generate summary of available tests."""
        summary = {
            "categories": TEST_CATEGORIES,
            "test_files": [],
            "total_tests": 0
        }
        
        # Find all test files
        for test_file in self.base_dir.rglob("test_*.py"):
            relative_path = test_file.relative_to(self.base_dir)
            
            # Count tests in file
            try:
                with open(test_file, 'r') as f:
                    content = f.read()
                    test_count = content.count('def test_')
                
                summary["test_files"].append({
                    "file": str(relative_path),
                    "test_count": test_count
                })
                summary["total_tests"] += test_count
            
            except Exception:
                summary["test_files"].append({
                    "file": str(relative_path),
                    "test_count": 0,
                    "error": "Could not count tests"
                })
        
        return summary
    
    def run_quick_smoke_test(self) -> Dict[str, Any]:
        """Run a quick smoke test to verify basic functionality."""
        cmd = [
            'python', '-m', 'pytest',
            '-m', 'unit and not slow',
            '--maxfail=5',
            '-x',
            str(self.base_dir)
        ]
        
        try:
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "duration": "quick",
                "output": result.stdout[-1000:] if result.stdout else ""  # Last 1000 chars
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def validate_test_environment(self) -> Dict[str, Any]:
        """Validate that the test environment is properly configured."""
        validation = {
            "python_version": sys.version,
            "pytest_available": False,
            "required_packages": {},
            "environment_vars": {},
            "test_files": 0,
            "issues": []
        }
        
        # Check pytest
        try:
            import pytest
            validation["pytest_available"] = True
            validation["pytest_version"] = pytest.__version__
        except ImportError:
            validation["issues"].append("pytest not installed")
        
        # Check required packages
        required_packages = [
            'requests', 'pathlib', 'json', 'unittest.mock',
            'psutil', 'time', 'threading', 'concurrent.futures'
        ]
        
        for package in required_packages:
            try:
                __import__(package)
                validation["required_packages"][package] = "✓ Available"
            except ImportError:
                validation["required_packages"][package] = "✗ Missing"
                validation["issues"].append(f"Package {package} not available")
        
        # Check environment variables
        env_vars = ['NOTION_API_KEY', 'NOTION_IMPORT_ROOT']
        for var in env_vars:
            value = os.environ.get(var)
            if value:
                validation["environment_vars"][var] = "✓ Set (hidden for security)"
            else:
                validation["environment_vars"][var] = "✗ Not set"
        
        # Count test files
        validation["test_files"] = len(list(self.base_dir.rglob("test_*.py")))
        
        return validation


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Narko Test Runner")
    
    parser.add_argument(
        '--categories', '-c',
        nargs='+',
        choices=list(TEST_CATEGORIES.keys()),
        help='Test categories to run'
    )
    
    parser.add_argument(
        '--no-coverage',
        action='store_true',
        help='Disable coverage reporting'
    )
    
    parser.add_argument(
        '--parallel', '-p',
        action='store_true',
        help='Run tests in parallel'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    
    parser.add_argument(
        '--html-report',
        action='store_true',
        help='Generate HTML test report'
    )
    
    parser.add_argument(
        '--benchmark',
        action='store_true',
        help='Run benchmarks only'
    )
    
    parser.add_argument(
        '--fail-fast', '-x',
        action='store_true',
        help='Stop on first failure'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show command that would be run'
    )
    
    parser.add_argument(
        '--smoke-test',
        action='store_true',
        help='Run quick smoke test only'
    )
    
    parser.add_argument(
        '--security-scan',
        action='store_true',
        help='Run security scans'
    )
    
    parser.add_argument(
        '--profile',
        action='store_true',
        help='Run performance profiling'
    )
    
    parser.add_argument(
        '--summary',
        action='store_true',
        help='Show test summary and exit'
    )
    
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate test environment'
    )
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    # Handle special commands
    if args.summary:
        summary = runner.generate_test_summary()
        print(json.dumps(summary, indent=2))
        return
    
    if args.validate:
        validation = runner.validate_test_environment()
        print(json.dumps(validation, indent=2))
        
        if validation["issues"]:
            print(f"\n❌ Found {len(validation['issues'])} issues:")
            for issue in validation["issues"]:
                print(f"  - {issue}")
            sys.exit(1)
        else:
            print("\n✅ Test environment validation passed")
        return
    
    if args.smoke_test:
        result = runner.run_quick_smoke_test()
        print(f"Smoke test: {'✅ PASSED' if result['success'] else '❌ FAILED'}")
        if not result["success"]:
            print(result.get("output", ""))
            sys.exit(1)
        return
    
    if args.security_scan:
        results = runner.run_security_scan()
        print("Security scan results:")
        for tool, result in results.items():
            status = "✅ PASSED" if result["success"] else "❌ FAILED"
            print(f"  {tool}: {status}")
        return
    
    if args.profile:
        result = runner.run_performance_profile()
        print(f"Performance profiling: {'✅ COMPLETED' if result['success'] else '❌ FAILED'}")
        return
    
    # Run main tests
    result = runner.run_tests(
        categories=args.categories,
        coverage=not args.no_coverage,
        parallel=args.parallel,
        verbose=args.verbose,
        html_report=args.html_report,
        benchmark=args.benchmark,
        fail_fast=args.fail_fast,
        dry_run=args.dry_run
    )
    
    if args.dry_run:
        print("Dry run - command would be:")
        print(" ".join(result["command"]))
        return
    
    # Print results
    if result["success"]:
        print(f"\n✅ Tests PASSED in {result['duration']:.2f}s")
    else:
        print(f"\n❌ Tests FAILED in {result['duration']:.2f}s")
        if result.get("stderr"):
            print("STDERR:")
            print(result["stderr"])
        sys.exit(result.get("returncode", 1))


if __name__ == "__main__":
    main()