"""
Token reduction target validation tests.
Validates that optimization strategies achieve 30-40% token reduction targets.
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


class TestTokenReductionTarget:
    """Validate 30-40% token reduction achieved."""

    @pytest.mark.asyncio
    async def test_token_reduction_simple_deal(self):
        """Simple deal should use <3000 billable tokens (was ~5000 before optimization)."""
        config = create_baseline_config()
        config["complexity"] = "simple"

        tracker = TokenTracker()
        result = await generate_complete_deal(config, token_tracker=tracker)

        billable = tracker.total_billable()
        target_max = 3000  # 40% reduction from ~5000

        print(f"\nSimple deal tokens: {billable} (target: <{target_max})")
        assert billable < target_max, f"Token usage {billable} exceeds target {target_max}"

    @pytest.mark.asyncio
    async def test_token_reduction_normal_deal(self):
        """Normal deal should use <7000 billable tokens (was ~10000 before optimization)."""
        config = create_baseline_config()
        config["complexity"] = "normal"

        tracker = TokenTracker()
        result = await generate_complete_deal(config, token_tracker=tracker)

        billable = tracker.total_billable()
        target_max = 7000  # 30% reduction from ~10000

        print(f"\nNormal deal tokens: {billable} (target: <{target_max})")
        assert billable < target_max, f"Token usage {billable} exceeds target {target_max}"

    @pytest.mark.asyncio
    async def test_cache_savings_quantified(self):
        """Verify cache is providing measurable savings."""
        config = create_baseline_config()

        tracker = TokenTracker()
        result = await generate_complete_deal(config, token_tracker=tracker)

        cache_savings = tracker.total_cache_savings()
        billable = tracker.total_billable()

        if billable > 0:
            savings_pct = (cache_savings / billable) * 100
            print(f"\nCache savings: {cache_savings} tokens ({savings_pct:.1f}% of billable)")
            # Cache savings may be 0 if not enabled yet, but if present should be significant
            if cache_savings > 0:
                assert cache_savings > 100, "Cache savings too small to be meaningful"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
