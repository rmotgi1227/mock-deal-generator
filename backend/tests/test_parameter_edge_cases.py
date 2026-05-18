import pytest
from tests.fixtures import create_baseline_config
from generator import generate_complete_deal


class TestParameterEdgeCases:
    """Test generator with extreme and boundary parameter values."""

    @pytest.mark.asyncio
    async def test_min_sales_cycle(self):
        """Test minimum sales cycle (14 days)."""
        config = create_baseline_config()
        config["sales_cycle_length_days"] = 14

        result = await generate_complete_deal(config, progress_callback=None)

        assert result is not None
        assert result["metadata"]["sales_cycle_length_days"] == 14

    @pytest.mark.asyncio
    async def test_max_sales_cycle(self):
        """Test maximum sales cycle (180 days)."""
        config = create_baseline_config()
        config["sales_cycle_length_days"] = 180

        result = await generate_complete_deal(config, progress_callback=None)

        assert result is not None
        assert result["metadata"]["sales_cycle_length_days"] == 180

    @pytest.mark.asyncio
    async def test_min_stakeholders(self):
        """Test minimum stakeholder count (2)."""
        config = create_baseline_config()
        config["num_stakeholders"] = 2

        result = await generate_complete_deal(config, progress_callback=None)

        assert result is not None
        assert len(result["metadata"]["stakeholders"]) >= 2

    @pytest.mark.asyncio
    async def test_max_stakeholders(self):
        """Test maximum stakeholder count (8)."""
        config = create_baseline_config()
        config["num_stakeholders"] = 8

        result = await generate_complete_deal(config, progress_callback=None)

        assert result is not None
        assert len(result["metadata"]["stakeholders"]) >= 8

    @pytest.mark.asyncio
    async def test_max_calls_max_emails(self):
        """Test maximum events: 10 calls, 5 emails per stage."""
        config = create_baseline_config()
        config["num_calls"] = 10
        config["emails_per_stage"] = 5

        result = await generate_complete_deal(config, progress_callback=None)

        assert result is not None
        events = result["events"]
        call_count = sum(1 for e in events if e.get("type") == "call")
        email_count = sum(1 for e in events if e.get("type") == "email")
        assert call_count >= 10
        assert email_count >= 15

    @pytest.mark.asyncio
    async def test_sentiment_progression_positive_to_negative(self):
        """Test sentiment arc from positive to negative (unusual but valid)."""
        config = create_baseline_config()
        config["starting_sentiment"] = "positive"
        config["ending_sentiment"] = "negative"
        config["deal_outcome"] = "closed_lost"

        result = await generate_complete_deal(config, progress_callback=None)

        assert result is not None
        arc = result["metadata"]["sentiment_arc"]
        assert len(arc) > 0

    @pytest.mark.asyncio
    async def test_all_champion_entry_points(self):
        """Test all valid champion entry points."""
        entry_points = [
            "none",
            "before_discovery",
            "during_discovery",
            "after_demo",
            "during_procurement",
            "late_stage_rescue",
        ]

        for entry in entry_points:
            config = create_baseline_config()
            config["champion_entry"] = entry

            result = await generate_complete_deal(config, progress_callback=None)

            assert result is not None
            assert result["metadata"]["champion_entry"] == entry

    @pytest.mark.asyncio
    async def test_all_complexity_levels(self):
        """Test all complexity levels: simple, normal, messy."""
        for complexity in ["simple", "normal", "messy"]:
            config = create_baseline_config()
            config["complexity"] = complexity

            result = await generate_complete_deal(config, progress_callback=None)

            assert result is not None
            assert result["metadata"]["complexity"] == complexity

    @pytest.mark.asyncio
    async def test_unicode_company_name(self):
        """Test unicode characters in company name."""
        config = create_baseline_config()
        config["company_name"] = "Café FinTech 北京"

        result = await generate_complete_deal(config, progress_callback=None)

        assert result is not None
        assert "Café FinTech 北京" in result["metadata"]["company"]["name"]

    @pytest.mark.asyncio
    async def test_long_business_use_case(self):
        """Test very long business use case string."""
        config = create_baseline_config()
        long_case = "Automate compliance reporting for SEC filings with ML-driven risk scoring and multi-level approval workflows. " * 5
        config["business_use_case"] = long_case

        result = await generate_complete_deal(config, progress_callback=None)

        assert result is not None
        # Should complete without truncation errors

    @pytest.mark.asyncio
    async def test_special_characters_in_fields(self):
        """Test special characters in text fields."""
        config = create_baseline_config()
        config["main_objection"] = "Budget Approval & IT Security/Compliance Review (Q3-Q4)"
        config["industry"] = "Fintech & Crypto/Web3"

        result = await generate_complete_deal(config, progress_callback=None)

        assert result is not None
