#!/usr/bin/env python3
"""
Comprehensive stress test suite runner.
Runs all test categories, collects metrics, generates report.
"""

import subprocess
import sys
from pathlib import Path
import time


def run_tests():
    """Run all test suites and generate report."""

    backend_dir = Path(__file__).parent.parent
    test_dir = Path(__file__).parent

    test_suites = [
        ("Parameter Edge Cases", "test_parameter_edge_cases.py"),
        ("Concurrent Load", "test_concurrent_load.py"),
        ("Output Validation", "test_output_validation.py"),
        ("Performance & Cost", "test_performance_cost.py"),
        ("Error Resilience", "test_error_resilience.py"),
        ("Rate Limiter & Cache", "test_rate_limiter_cache.py"),
        ("Token Budget Limits", "test_token_budget_limits.py"),
        ("API vs Direct", "test_api_vs_direct.py"),
    ]

    print("\n" + "="*70)
    print("STRESS TEST SUITE RUNNER")
    print("="*70 + "\n")

    results = {}
    total_start = time.time()

    for idx, (name, module) in enumerate(test_suites, 1):
        progress = f"[{idx}/{len(test_suites)}]"
        print(f"{progress} Running {name}...", end=" ", flush=True)
        suite_start = time.time()

        result = subprocess.run(
            ["python", "-m", "pytest", str(test_dir / module), "-v", "--tb=short"],
            cwd=str(backend_dir),
            capture_output=True,
            text=True,
        )

        elapsed = time.time() - suite_start
        passed = result.stdout.count(" PASSED")
        failed = result.stdout.count(" FAILED")

        results[name] = {
            "passed": passed,
            "failed": failed,
            "exit_code": result.returncode,
            "elapsed": elapsed,
        }

        status = "✓" if result.returncode == 0 else "✗"
        print(f"{status} ({passed}P {failed}F) {elapsed:.1f}s")

        # Show first error if any
        if result.returncode != 0 and failed > 0:
            lines = result.stdout.split('\n')
            for i, line in enumerate(lines):
                if 'FAILED' in line or 'ERROR' in line:
                    print(f"  └─ {line.strip()}")
                    break

    # Print summary
    total_elapsed = time.time() - total_start
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    total_passed = sum(r["passed"] for r in results.values())
    total_failed = sum(r["failed"] for r in results.values())
    all_passed = all(r["exit_code"] == 0 for r in results.values())

    for name, result in results.items():
        status = "✓" if result["exit_code"] == 0 else "✗"
        print(f"{status} {name:30s} {result['passed']:2d}P {result['failed']:2d}F {result['elapsed']:6.1f}s")

    print("-"*70)
    print(f"Total: {total_passed} passed, {total_failed} failed in {total_elapsed:.1f}s")

    if all_passed:
        print("\n✅ ALL TESTS PASSED!")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())
