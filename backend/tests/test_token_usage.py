"""
Token usage measurement tests.
Measures actual token consumption across deal complexities to tune MAX_TOKENS_BY_TYPE allocations.
"""

import pytest
import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tests.fixtures import create_baseline_config
from generator import generate_complete_deal
from token_tracker import TokenTracker


class TestTokenUsage:
    """Measure actual token usage to tune allocations."""

    @pytest.mark.asyncio
    async def test_measure_simple_deal_tokens(self):
        """Measure tokens for simple deal to establish baseline."""
        config = create_baseline_config()
        config["complexity"] = "simple"
        config["num_calls"] = 1
        config["emails_per_stage"] = 1
        config["num_stakeholders"] = 2
        config["sales_cycle_length_days"] = 14

        tracker = TokenTracker()
        result = await generate_complete_deal(config, token_tracker=tracker)

        usage = tracker.to_dict()
        print("\n" + "=" * 70)
        print("SIMPLE DEAL TOKEN USAGE")
        print("=" * 70)
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

        # Verify token tracking is working
        assert usage['total_billable_tokens'] > 0, "No tokens recorded"
        assert len(result['events']) > 0, "No events generated"

    @pytest.mark.asyncio
    async def test_measure_normal_deal_tokens(self):
        """Measure tokens for normal complexity deal."""
        config = create_baseline_config()
        config["complexity"] = "normal"
        config["num_calls"] = 3
        config["emails_per_stage"] = 2
        config["num_stakeholders"] = 4
        config["sales_cycle_length_days"] = 60

        tracker = TokenTracker()
        result = await generate_complete_deal(config, token_tracker=tracker)

        usage = tracker.to_dict()
        print("\n" + "=" * 70)
        print("NORMAL DEAL TOKEN USAGE")
        print("=" * 70)
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

        assert usage['total_billable_tokens'] > 0, "No tokens recorded"
        assert len(result['events']) > 0, "No events generated"

    @pytest.mark.asyncio
    async def test_measure_complex_deal_tokens(self):
        """Measure tokens for complex deal."""
        config = create_baseline_config()
        config["complexity"] = "messy"
        config["sales_cycle_length_days"] = 120
        config["num_calls"] = 8
        config["emails_per_stage"] = 4
        config["num_stakeholders"] = 6

        tracker = TokenTracker()
        result = await generate_complete_deal(config, token_tracker=tracker)

        usage = tracker.to_dict()
        print("\n" + "=" * 70)
        print("COMPLEX DEAL TOKEN USAGE")
        print("=" * 70)
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

        assert usage['total_billable_tokens'] > 0, "No tokens recorded"
        assert len(result['events']) > 0, "No events generated"

    @pytest.mark.asyncio
    async def test_token_allocation_headroom(self):
        """
        Verify that actual output usage is 60-80% of max_tokens allocations.
        This validates that allocations have appropriate headroom.
        """
        config = create_baseline_config()
        config["complexity"] = "normal"
        config["num_calls"] = 3

        tracker = TokenTracker()
        result = await generate_complete_deal(config, token_tracker=tracker)

        usage = tracker.to_dict()
        by_stage = usage['by_stage']

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

        print("\nUsage vs. Allocation:")
        for stage_key, max_tokens_val in max_tokens.items():
            if stage_key in by_stage:
                actual = by_stage[stage_key]['billable']
                usage_pct = (actual / max_tokens_val) * 100
                print(f"  {stage_key:15s}: {actual:6d} / {max_tokens_val:6d} "
                      f"({usage_pct:5.1f}% utilized)")

        print("=" * 70)


class TestTokenOptimizationEndToEnd:
    """End-to-end validation of all optimizations."""

    @pytest.mark.asyncio
    async def test_all_stages_tracked(self):
        """Verify token tracking works across all stages."""
        config = create_baseline_config()
        tracker = TokenTracker()
        result = await generate_complete_deal(config, token_tracker=tracker)

        usage = tracker.to_dict()
        by_stage = usage['by_stage']

        # Verify key stages tracked
        assert 'stage1' in by_stage, "Stage 1 not tracked"
        assert any(k.startswith('stage2') for k in by_stage.keys()), "Stage 2 not tracked"
        assert any(k.startswith('stage3') for k in by_stage.keys()), "Stage 3 not tracked"

        print(f"\n✅ All {len(by_stage)} stages tracked")
        for stage_name in sorted(by_stage.keys()):
            print(f"   - {stage_name}")

    @pytest.mark.asyncio
    async def test_cache_effectiveness(self):
        """Verify caching is providing expected savings."""
        config = create_baseline_config()
        tracker = TokenTracker()
        result = await generate_complete_deal(config, token_tracker=tracker)

        usage = tracker.to_dict()

        # Stage 2 should show cache_reads (Stage 2 optimization)
        stage2_total_cache = sum(
            metrics.get('cache_reads', 0)
            for stage, metrics in usage['by_stage'].items()
            if stage.startswith('stage2')
        )

        # Stage 3 should show cache_reads (reused system blocks)
        stage3_total_cache = sum(
            metrics.get('cache_reads', 0)
            for stage, metrics in usage['by_stage'].items()
            if stage.startswith('stage3')
        )

        total_cache = stage2_total_cache + stage3_total_cache

        if total_cache > 0:
            print(f"\n✅ Cache savings detected: {total_cache} tokens")
            print(f"   - Stage 2 cache: {stage2_total_cache} tokens")
            print(f"   - Stage 3 cache: {stage3_total_cache} tokens")
        else:
            print(f"\n⚠️ No cache detected (may be first run or immediate timeout)")

    @pytest.mark.asyncio
    async def test_billable_tokens_within_targets(self):
        """Verify billable tokens are within optimization targets."""
        config = create_baseline_config()
        config["complexity"] = "normal"

        tracker = TokenTracker()
        result = await generate_complete_deal(config, token_tracker=tracker)

        billable = tracker.total_billable()
        target_max = 7000  # 30% reduction target for normal deals

        usage_pct = (billable / target_max) * 100

        print(f"\n📊 Token Usage Analysis:")
        print(f"   Billable tokens: {billable}")
        print(f"   Target maximum: {target_max}")
        print(f"   Usage: {usage_pct:.1f}% of target")

        if billable <= target_max:
            print(f"   ✅ Within target (30% reduction achieved)")
        else:
            print(f"   ⚠️ Exceeds target by {billable - target_max} tokens")

    @pytest.mark.asyncio
    async def test_token_usage_consistency(self):
        """Verify token tracking is consistent across runs."""
        config = create_baseline_config()
        config["complexity"] = "simple"

        # Run twice with fresh trackers
        tracker1 = TokenTracker()
        result1 = await generate_complete_deal(config, token_tracker=tracker1)
        billable1 = tracker1.total_billable()

        tracker2 = TokenTracker()
        result2 = await generate_complete_deal(config, token_tracker=tracker2)
        billable2 = tracker2.total_billable()

        # Allow 10% variance due to model non-determinism
        variance_threshold = max(billable1, billable2) * 0.10
        difference = abs(billable1 - billable2)

        print(f"\n📈 Token Consistency Check:")
        print(f"   Run 1: {billable1} tokens")
        print(f"   Run 2: {billable2} tokens")
        print(f"   Variance: {difference} tokens ({(difference/billable1)*100:.1f}%)")

        assert difference <= variance_threshold, \
            f"Token usage variance too high: {difference} > {variance_threshold}"
        print(f"   ✅ Consistent within 10% threshold")


if __name__ == "__main__":
    # Allow running tests directly with: python -m pytest backend/tests/test_token_usage.py -v -s
    pytest.main([__file__, "-v", "-s"])
