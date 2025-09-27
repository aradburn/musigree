#!/usr/bin/env python3
"""
Profiling script for SQLite loader relation pass one test.
Runs the test with detailed performance analysis to identify bottlenecks.
"""

import cProfile
import pstats
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def run_profiled_test() -> None:
    """Run the test with profiling enabled."""
    import pytest
    
    # Run the specific test file with profiling
    test_file = "../integration/offline/sqlite/loader/test_sqlite_loader_relation_pass_one.py"
    
    # Use pytest to run the test
    pytest.main([
        test_file,
        "-v",
        "--tb=short",
        "-s"  # Allow print statements
    ])

def main() -> None:
    """Main function to run profiling."""
    # Create profiler
    profiler = cProfile.Profile()
    
    print("Starting profiling of SQLite loader relation pass one test...")
    print("=" * 60)
    
    # Start profiling
    profiler.enable()
    
    try:
        run_profiled_test()
    except Exception as e:
        print(f"Error during test execution: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Stop profiling
        profiler.disable()
    
    # Create stats object
    stats = pstats.Stats(profiler)
    
    # Sort by cumulative time (most time-consuming functions first)
    stats.sort_stats('cumulative')
    
    print("\n" + "=" * 60)
    print("PROFILING RESULTS - Top 50 functions by cumulative time:")
    print("=" * 60)
    
    # Print top 50 functions
    stats.print_stats(50)
    
    # Also show callers and callees for top functions
    print("\n" + "=" * 60)
    print("TOP FUNCTION CALLERS:")
    print("=" * 60)
    stats.print_callers(20)
    
    print("\n" + "=" * 60)
    print("TOP FUNCTION CALLEES:")
    print("=" * 60)
    stats.print_callees(20)
    
    # Save detailed stats to file
    stats_file = "test_profiling_stats2.txt"
    stats.dump_stats(stats_file)
    print(f"\nDetailed profiling results saved to: {stats_file}")

if __name__ == "__main__":
    main()
