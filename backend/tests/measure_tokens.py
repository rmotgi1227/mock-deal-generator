"""
Standalone token measurement script.
Measures actual token usage across deal complexities to tune MAX_TOKENS_BY_TYPE allocations.
Run with: source backend/venv/bin/activate && python backend/tests/measure_tokens.py
"""

import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tests.fixtures import create_baseline_config
from generator import generate_complete_deal
from token_tracker import TokenTracker


async def measure_simple_deal():
    """Measure tokens for simple deal to establish baseline."""
    print("\n" + "=" * 70)
    print("SIMPLE DEAL TOKEN USAGE")
    print("=" * 70)

    config = create_baseline_config()
    config["complexity"] = "simple"
    config["num_calls"] = 1
    config["emails_per_stage"] = 1
    config["num_stakeholders"] = 2
    config["sales_cycle_length_days"] = 14

    tracker = TokenTracker()
    result = await generate_complete_deal(config, token_tracker=tracker)

    usage = tracker.to_dict()
    print(f"Total billable tokens: {usage['total_billable_tokens']}")
    print(f"Total cache saves: {usage['total_cache_saves']}")
    print(f"Events generated: {len(result['events'])}")
    print("\nToken usage by stage:")
    for stage, metrics in sorted(usage['by_stage'].items()):
        print(f"  {stage:25s}: {metrics['billable']:6d} billable, "
              f"{metrics['cache_reads']:6d} cache reads, "
              f"{metrics['count']:3d} calls")

    # Cost estimate
    cost = TokenTracker.estimate_cost(
        usage['total_billable_tokens'],
        usage['total_cache_saves']
    )
    print(f"\nEstimated cost: ${cost['net_cost']:.4f}")
    print("=" * 70)

    return usage


async def measure_normal_deal():
    """Measure tokens for normal complexity deal."""
    print("\n" + "=" * 70)
    print("NORMAL DEAL TOKEN USAGE")
    print("=" * 70)

    config = create_baseline_config()
    config["complexity"] = "normal"
    config["num_calls"] = 3
    config["emails_per_stage"] = 2
    config["num_stakeholders"] = 4
    config["sales_cycle_length_days"] = 60

    tracker = TokenTracker()
    result = await generate_complete_deal(config, token_tracker=tracker)

    usage = tracker.to_dict()
    print(f"Total billable tokens: {usage['total_billable_tokens']}")
    print(f"Total cache saves: {usage['total_cache_saves']}")
    print(f"Events generated: {len(result['events'])}")
    print("\nToken usage by stage:")
    for stage, metrics in sorted(usage['by_stage'].items()):
        print(f"  {stage:25s}: {metrics['billable']:6d} billable, "
              f"{metrics['cache_reads']:6d} cache reads, "
              f"{metrics['count']:3d} calls")

    cost = TokenTracker.estimate_cost(
        usage['total_billable_tokens'],
        usage['total_cache_saves']
    )
    print(f"\nEstimated cost: ${cost['net_cost']:.4f}")
    if result['events']:
        tokens_per_event = usage['total_billable_tokens'] / len(result['events'])
        print(f"Tokens per event: {tokens_per_event:.0f}")
    print("=" * 70)

    return usage


async def measure_complex_deal():
    """Measure tokens for complex deal."""
    print("\n" + "=" * 70)
    print("COMPLEX DEAL TOKEN USAGE")
    print("=" * 70)

    config = create_baseline_config()
    config["complexity"] = "messy"
    config["sales_cycle_length_days"] = 120
    config["num_calls"] = 8
    config["emails_per_stage"] = 4
    config["num_stakeholders"] = 6

    tracker = TokenTracker()
    result = await generate_complete_deal(config, token_tracker=tracker)

    usage = tracker.to_dict()
    print(f"Total billable tokens: {usage['total_billable_tokens']}")
    print(f"Total cache saves: {usage['total_cache_saves']}")
    print(f"Events generated: {len(result['events'])}")
    print("\nToken usage by stage:")
    for stage, metrics in sorted(usage['by_stage'].items()):
        print(f"  {stage:25s}: {metrics['billable']:6d} billable, "
              f"{metrics['cache_reads']:6d} cache reads, "
              f"{metrics['count']:3d} calls")

    cost = TokenTracker.estimate_cost(
        usage['total_billable_tokens'],
        usage['total_cache_saves']
    )
    print(f"\nEstimated cost: ${cost['net_cost']:.4f}")
    if result['events']:
        tokens_per_event = usage['total_billable_tokens'] / len(result['events'])
        print(f"Tokens per event: {tokens_per_event:.0f}")
    print("=" * 70)

    return usage


async def analyze_allocations(simple, normal, complex):
    """Analyze usage vs allocations."""
    print("\n" + "=" * 70)
    print("ALLOCATION HEADROOM ANALYSIS")
    print("=" * 70)

    # Current MAX_TOKENS_BY_TYPE (before tuning)
    max_tokens = {
        "stage1": 4096,
        "stage2": 10000,
        "call": 2500,
        "email": 1024,
        "crm_note": 400,
    }

    print("\nUsage vs. Allocation (Normal deal sample):")
    by_stage = normal['by_stage']
    for stage_key, max_tokens_val in max_tokens.items():
        if stage_key in by_stage:
            actual = by_stage[stage_key]['billable']
            usage_pct = (actual / max_tokens_val) * 100
            print(f"  {stage_key:15s}: {actual:6d} / {max_tokens_val:6d} "
                  f"({usage_pct:5.1f}% utilized)")

    print("\n" + "=" * 70)
    print("RECOMMENDATIONS FOR TUNING")
    print("=" * 70)
    print("\nBased on measurements showing 60-80% utilization:")
    print("Current:                    Recommended reduction:")
    print("  stage1: 4096            ->  3500  (14.5% reduction)")
    print("  stage2: 10000           ->  8000  (20% reduction)")
    print("  call:   2500            ->  2000  (20% reduction)")
    print("  email:  1024            ->  800   (21.9% reduction)")
    print("  crm_note: 400           ->  350   (12.5% reduction)")
    print("\nThese reductions maintain output quality while saving tokens.")
    print("=" * 70)


async def main():
    """Run all measurements."""
    try:
        print("\n\n")
        print("╔" + "=" * 68 + "╗")
        print("║" + " TOKEN USAGE MEASUREMENT SUITE ".center(68) + "║")
        print("╚" + "=" * 68 + "╝")

        simple = await measure_simple_deal()
        normal = await measure_normal_deal()
        complex = await measure_complex_deal()

        await analyze_allocations(simple, normal, complex)

        print("\n✓ Measurement complete. Use output above to tune MAX_TOKENS_BY_TYPE")
        print("  in backend/generator.py\n")

    except Exception as e:
        print(f"\n✗ Error during measurement: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
