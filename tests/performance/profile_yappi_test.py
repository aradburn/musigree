#!/usr/bin/env python3
"""
Yappi profiling script for SQLite loader relation pass one test.
Runs the test with detailed performance analysis to identify bottlenecks.
"""

import yappi  # type: ignore
import sys
import time
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def run_profiled_test() -> None:
    """Run the test with yappi profiling enabled."""
    import pytest

    # Run the specific test file
    test_file = "../integration/transfer/sqlite/test_sqlite_transfer.py"

    # Use pytest to run the test
    pytest.main([
        test_file,
        "-v",
        "--tb=short",
        "-s"  # Allow print statements
    ])


def analyze_yappi_stats() -> None:
    """Analyze and display yappi profiling statistics."""
    print("\n" + "=" * 80)
    print("YAPPI PROFILING RESULTS")
    print("=" * 80)

    # Get function stats sorted by total time
    func_stats = yappi.get_func_stats()
    func_stats.sort("ttot", "desc")  # Sort by total time, descending

    print("\nTOP 100 FUNCTIONS BY TOTAL TIME:")
    print("-" * 80)
    print(f"{'Function':<150} {'Total Time (s)':<15} {'Calls':<10} {'Avg Time (s)':<15}")
    print("-" * 80)

    for stat in func_stats[:100]:
        func_name = f"{stat.module}.{stat.name}"
        if len(func_name) > 149:
            func_name = func_name[:146] + "..."

        total_time = stat.ttot
        calls = stat.ncall
        avg_time = total_time / calls if calls > 0 else 0

        print(f"{func_name:<150} {total_time:<15.6f} {calls:<10} {avg_time:<15.6f}")

    # Get thread stats
    thread_stats = yappi.get_thread_stats()
    print("\nTHREAD STATISTICS:")
    print("-" * 80)
    print(f"{'Thread Name':<30} {'Total Time (s)':<15}")
    print("-" * 80)

    for stat in thread_stats:
        thread_name = stat.name if stat.name else "MainThread"
        if len(thread_name) > 29:
            thread_name = thread_name[:26] + "..."
        func_name = f"{stat.name}:{stat.id}"
        if len(func_name) > 149:
            func_name = func_name[:146] + "..."

        print(f"{thread_name:<30} {stat.ttot:<15.6f} {func_name:<150}")

    # Show additional details for top functions
    print("\nDETAILED ANALYSIS OF TOP 10 FUNCTIONS:")
    print("-" * 80)

    for i, stat in enumerate(func_stats[:10]):
        func_name = f"{stat.module}.{stat.name}"
        print(f"\n{i + 1}. Function: {func_name}")
        print(f"   Total Time: {stat.ttot:.6f}s")
        print(f"   Calls: {stat.ncall}")
        print(f"   Average Time: {stat.ttot / stat.ncall:.6f}s" if stat.ncall > 0 else "   Average Time: N/A")
        # print(f"   File: {stat.path}")
        print(f"   Line: {stat.lineno}")


def save_detailed_stats() -> None:
    """Save detailed profiling statistics to files."""
    # Save function stats
    func_stats = yappi.get_func_stats()
    func_stats.sort("ttot", "desc")

    with open("yappi_function_stats.txt", "w") as f:
        f.write("YAPPI FUNCTION STATISTICS\n")
        f.write("=" * 80 + "\n\n")

        for stat in func_stats:
            f.write(f"Function: {stat.module}.{stat.name}\n")
            f.write(f"Total Time: {stat.ttot:.6f}s\n")
            f.write(f"Calls: {stat.ncall}\n")
            f.write(f"Average Time: {stat.ttot / stat.ncall:.6f}s\n" if stat.ncall > 0 else "Average Time: N/A\n")
            # f.write(f"File: {stat.path}\n")
            f.write(f"Line: {stat.lineno}\n")
            f.write("-" * 40 + "\n")

    # Save thread stats
    thread_stats = yappi.get_thread_stats()

    with open("yappi_thread_stats.txt", "w") as f:
        f.write("YAPPI THREAD STATISTICS\n")
        f.write("=" * 80 + "\n\n")

        for stat in thread_stats:
            f.write(f"Thread: {stat.name}\n")
            f.write(f"Total Time: {stat.ttot:.6f}s\n")
            f.write("-" * 40 + "\n")

    print("\nDetailed statistics saved to:")
    print("  - yappi_function_stats.txt")
    print("  - yappi_thread_stats.txt")


def main() -> None:
    """Main function to run yappi profiling."""
    print("Starting Yappi profiling of SQLite loader relation pass one test...")
    print("=" * 80)

    # Start yappi profiling
    yappi.set_clock_type("cpu")  # Use CPU time
    yappi.start()

    start_time = time.time()

    try:
        run_profiled_test()
    except Exception as e:
        print(f"Error during test execution: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Stop profiling
        yappi.stop()
        end_time = time.time()

    print(f"\nTest execution completed in {end_time - start_time:.2f} seconds")

    # Analyze and display results
    analyze_yappi_stats()

    # Save detailed statistics
    save_detailed_stats()

    # Clean up
    yappi.clear_stats()


if __name__ == "__main__":
    main()
