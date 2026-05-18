"""Test fixtures and helper functions."""

def create_baseline_config():
    """Create a baseline configuration for testing."""
    return {
        "company_name": None,
        "industry": "Fintech",
        "deal_size": "$50k ARR",
        "sales_cycle_length_days": 30,
        "starting_sentiment": "neutral",
        "ending_sentiment": "positive",
        "deal_outcome": "closed_won",
        "champion_entry": "after_demo",
        "main_objection": "Pricing",
        "buyer_urgency": "medium",
        "num_calls": 2,
        "emails_per_stage": 1,
        "num_stakeholders": 2,
        "complexity": "simple",
        "cs_scenario": {
            "enabled": True,
            "post_close_days": 30,
            "adoption_challenge": "integration_complexity",
            "support_contact_frequency": "low",
            "churn_probability": 0.3,
        },
    }
