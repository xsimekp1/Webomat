#!/usr/bin/env python3
"""
Test Runner Script

Runs pytest for backend and optionally npm test for frontend.
Works on Windows, macOS, and Linux.

Usage:
    python scripts/run_tests.py           # Run backend tests
    python scripts/run_tests.py --all     # Run backend and frontend tests
    python scripts/run_tests.py --frontend # Run only frontend tests
    python scripts/run_tests.py -v        # Verbose output
    python scripts/run_tests.py -k test_name  # Run specific tests
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def get_project_root():
    """Get the project root directory."""
    script_dir = Path(__file__).parent
    return script_dir.parent


def run_backend_tests(verbose=False, pattern=None, coverage=False):
    """Run pytest for backend tests."""
    project_root = get_project_root()
    backend_dir = project_root / "backend"

    if not backend_dir.exists():
        print("Error: backend directory not found")
        return False

    print("\n" + "=" * 60)
    print("Running Backend Tests (pytest)")
    print("=" * 60 + "\n")

    cmd = [sys.executable, "-m", "pytest"]

    if verbose:
        cmd.append("-v")

    if pattern:
        cmd.extend(["-k", pattern])

    if coverage:
        cmd.extend(["--cov=app", "--cov-report=term-missing"])

    # Add test directory
    cmd.append("tests/")

    try:
        result = subprocess.run(
            cmd,
            cwd=backend_dir,
            capture_output=False,
        )
        return result.returncode == 0
    except FileNotFoundError:
        print("Error: pytest not found. Run: pip install pytest")
        return False
    except Exception as e:
        print(f"Error running tests: {e}")
        return False


def run_frontend_tests(verbose=False):
    """Run npm test for frontend tests."""
    project_root = get_project_root()
    frontend_dir = project_root / "frontend"

    if not frontend_dir.exists():
        print("Error: frontend directory not found")
        return False

    # Check if package.json has test script
    package_json = frontend_dir / "package.json"
    if not package_json.exists():
        print("Error: package.json not found in frontend")
        return False

    import json
    with open(package_json) as f:
        pkg = json.load(f)

    if "test" not in pkg.get("scripts", {}):
        print("Warning: No 'test' script in frontend package.json")
        return True  # Not a failure, just no tests

    print("\n" + "=" * 60)
    print("Running Frontend Tests (npm test)")
    print("=" * 60 + "\n")

    # Determine npm command based on platform
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"

    cmd = [npm_cmd, "test"]

    if not verbose:
        cmd.append("--silent")

    try:
        result = subprocess.run(
            cmd,
            cwd=frontend_dir,
            capture_output=False,
            env={**os.environ, "CI": "true"},  # Prevent watch mode
        )
        return result.returncode == 0
    except FileNotFoundError:
        print("Error: npm not found. Make sure Node.js is installed.")
        return False
    except Exception as e:
        print(f"Error running frontend tests: {e}")
        return False


def check_dependencies():
    """Check if required dependencies are installed."""
    missing = []

    # Check pytest
    try:
        import pytest
    except ImportError:
        missing.append("pytest (pip install pytest)")

    # Check httpx for FastAPI testing
    try:
        import httpx
    except ImportError:
        missing.append("httpx (pip install httpx)")

    if missing:
        print("Missing dependencies:")
        for dep in missing:
            print(f"  - {dep}")
        print("\nInstall with: pip install pytest httpx pytest-asyncio")
        return False

    return True


def main():
    parser = argparse.ArgumentParser(description="Run Webomat tests")
    parser.add_argument("--all", "-a", action="store_true", help="Run all tests (backend + frontend)")
    parser.add_argument("--frontend", "-f", action="store_true", help="Run only frontend tests")
    parser.add_argument("--backend", "-b", action="store_true", help="Run only backend tests (default)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--pattern", "-k", help="Run tests matching pattern")
    parser.add_argument("--coverage", "-c", action="store_true", help="Run with coverage report")
    parser.add_argument("--check", action="store_true", help="Check dependencies only")

    args = parser.parse_args()

    if args.check:
        if check_dependencies():
            print("All dependencies are installed!")
        return

    # Default to backend tests if no specific flag
    run_backend = args.backend or args.all or (not args.frontend)
    run_frontend = args.frontend or args.all

    results = []

    if run_backend:
        if not check_dependencies():
            sys.exit(1)
        results.append(("Backend", run_backend_tests(args.verbose, args.pattern, args.coverage)))

    if run_frontend:
        results.append(("Frontend", run_frontend_tests(args.verbose)))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "PASSED" if passed else "FAILED"
        symbol = "✓" if passed else "✗"
        print(f"  {symbol} {name}: {status}")
        if not passed:
            all_passed = False

    print()

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
