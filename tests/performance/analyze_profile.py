#!/usr/bin/env python3
"""
Analyze profiling results to identify performance bottlenecks.
"""

import pstats
import sys
from pathlib import Path


def analyze_profile_stats(stats_file: str) -> None:
    """Analyze the profiling statistics and print key insights."""

    # Load the stats
    stats = pstats.Stats(stats_file)

    print("=" * 80)
    print("PERFORMANCE ANALYSIS - SQLite Loader Relation Pass One Test")
    print("=" * 80)

    # Sort by cumulative time to find the biggest bottlenecks
    stats.sort_stats("cumulative")

    print("\nTOP 100 FUNCTIONS BY CUMULATIVE TIME:")
    print("-" * 80)
    stats.print_stats(100)

    # Sort by time to find functions that spend the most time in themselves
    stats.sort_stats("time")

    print("\nTOP 100 FUNCTIONS BY SELF TIME (excluding calls):")
    print("-" * 80)
    stats.print_stats(100)

    # Sort by calls to find most frequently called functions
    stats.sort_stats("calls")

    print("\nTOP 100 FUNCTIONS BY CALL COUNT:")
    print("-" * 80)
    stats.print_stats(100)


def main() -> None:
    """Main function to analyze profiling results."""
    stats_file = "test_profiling_stats2.dat"

    if not Path(stats_file).exists():
        print(f"Error: {stats_file} not found. Run the profiling script first.")
        sys.exit(1)

    analyze_profile_stats(stats_file)


if __name__ == "__main__":
    main()
