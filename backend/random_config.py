"""Random deal config generator for bulk generation."""

import random
from typing import Optional

ADOPTION_CHALLENGES = [
    "integration_complexity", "training_gap", "workflow_mismatch",
    "performance_issues", "unclear_roi",
]

SUPPORT_FREQUENCIES = ["low", "medium", "high"]

INDUSTRIES = [
    "Fintech", "Healthcare IT", "Cybersecurity", "DevTools", "HR Tech",
    "Legal Tech", "EdTech", "Supply Chain", "Real Estate Tech", "MarTech",
    "InsurTech", "Logistics", "Manufacturing SaaS", "Retail Tech", "CleanTech",
]

DEAL_SIZES = [
    "$25k ARR", "$50k ARR", "$75k ARR", "$100k ARR", "$150k ARR",
    "$200k ARR", "$300k ARR", "$500k ARR", "$750k ARR", "$1M ARR",
]

OBJECTIONS = [
    "Security Review", "Budget Constraints", "Integration Complexity",
    "Compliance Requirements", "Vendor Risk Assessment", "Contract Negotiation",
    "Technical Fit", "ROI Justification", "Procurement Process",
    "Competing Priority", "Executive Buy-In", "Data Privacy",
    "Scalability Concerns", "Implementation Timeline", "Support SLAs",
]

SENTIMENTS = ["positive", "neutral", "concerned", "negative"]
OUTCOMES = ["closed_won", "closed_lost"]
CHAMPION_ENTRIES = [
    "none", "before_discovery", "during_discovery",
    "after_demo", "during_procurement", "late_stage_rescue",
]
URGENCIES = ["low", "medium", "high"]
COMPLEXITIES = ["simple", "normal", "messy"]


def generate_random_config(overrides: Optional[dict] = None) -> dict:
    industry = random.choice(INDUSTRIES)
    deal_size = random.choice(DEAL_SIZES)
    complexity = random.choice(COMPLEXITIES)
    outcome = random.choice(OUTCOMES)

    # Bias ending sentiment toward outcome
    if outcome == "closed_won":
        ending_sentiment = random.choices(
            SENTIMENTS, weights=[60, 25, 10, 5]
        )[0]
    else:
        ending_sentiment = random.choices(
            SENTIMENTS, weights=[5, 20, 35, 40]
        )[0]

    starting_sentiment = random.choice(SENTIMENTS)

    # Heavier deals get more calls/emails/stakeholders
    if complexity == "messy":
        num_calls = random.randint(4, 10)
        emails_per_stage = random.randint(2, 3)
        num_stakeholders = random.randint(4, 8)
        sales_cycle = random.randint(60, 180)
    elif complexity == "normal":
        num_calls = random.randint(3, 7)
        emails_per_stage = random.randint(1, 3)
        num_stakeholders = random.randint(3, 6)
        sales_cycle = random.randint(30, 90)
    else:
        num_calls = random.randint(1, 4)
        emails_per_stage = random.randint(1, 2)
        num_stakeholders = random.randint(2, 4)
        sales_cycle = random.randint(14, 45)

    # CS scenario: always enabled, weighted toward higher churn for lost deals
    churn_probability = round(
        random.uniform(0.6, 0.95) if outcome == "closed_lost"
        else random.uniform(0.1, 0.6),
        2
    )

    config = {
        "company_name": None,
        "industry": industry,
        "deal_size": deal_size,
        "sales_cycle_length_days": sales_cycle,
        "starting_sentiment": starting_sentiment,
        "ending_sentiment": ending_sentiment,
        "deal_outcome": outcome,
        "champion_entry": random.choice(CHAMPION_ENTRIES),
        "main_objection": random.choice(OBJECTIONS),
        "buyer_urgency": random.choice(URGENCIES),
        "num_calls": num_calls,
        "emails_per_stage": emails_per_stage,
        "num_stakeholders": num_stakeholders,
        "complexity": complexity,
        "cs_scenario": {
            "enabled": outcome == "closed_won",
            "adoption_challenge": random.choice(ADOPTION_CHALLENGES),
            "support_contact_frequency": random.choice(SUPPORT_FREQUENCIES),
            "churn_probability": churn_probability,
            "post_close_days": random.randint(14, 60),
        },
    }

    if overrides:
        # Merge overrides: overrides take precedence; None values in overrides mean "use random"
        for key, val in overrides.items():
            if val is not None:
                config[key] = val
    return config


_FREQUENCY_CALLS = {
    "daily": lambda months: min(months * 20, 10),
    "weekly": lambda months: min(months * 4, 10),
    "biweekly": lambda months: min(months * 2, 10),
    "monthly": lambda months: min(months, 10),
}

_FREQUENCY_EMAILS = {
    "daily": 5,
    "weekly": 3,
    "biweekly": 2,
    "monthly": 1,
}

def series_to_generate_config(series: dict) -> dict:
    """Convert SeriesRequest dict to GenerateRequest-compatible dict."""
    months = series['account_age_months']
    freq = series['frequency']
    num_calls = _FREQUENCY_CALLS[freq](months)
    emails_per_stage = _FREQUENCY_EMAILS[freq]
    num_stakeholders = min(2 + months // 2, 8)
    decision_makers = series.get('number_of_decision_makers')
    return {
        'company_name': series.get('company_name'),
        'industry': series['industry'],
        'deal_size': series['deal_size'],
        'sales_cycle_length_days': months * 30,
        'starting_sentiment': series['starting_sentiment'],
        'ending_sentiment': series['ending_sentiment'],
        'deal_outcome': series['deal_outcome'],
        'champion_entry': series.get('champion_entry', 'after_demo'),
        'main_objection': series['main_objection'],
        'buyer_urgency': series['buyer_urgency'],
        'num_calls': max(num_calls, 1),
        'emails_per_stage': emails_per_stage,
        'num_stakeholders': decision_makers if decision_makers is not None else num_stakeholders,
        'complexity': series['complexity'],
        'ae_name': series.get('ae_name'),
        'se_name': series.get('se_name'),
        'business_use_case': series.get('business_use_case'),
        'is_series': True,
        'cs_scenario': series.get('cs_scenario'),
        'sales_cycle_velocity': series.get('sales_cycle_velocity'),
        'procurement_delay_days': series.get('procurement_delay_days'),
        'eval_iteration_count': series.get('eval_iteration_count'),
        'number_of_decision_makers': decision_makers,
        'champion_replacement': series.get('champion_replacement', False),
        'discount_percentage': series.get('discount_percentage'),
        'win_loss_reason': series.get('win_loss_reason'),
        'customer_company_size': series.get('customer_company_size'),
        'budget_pre_allocated': series.get('budget_pre_allocated', False),
        'competing_vendors': series.get('competing_vendors'),
        'time_to_value_days': series.get('time_to_value_days'),
        'implementation_complexity': series.get('implementation_complexity'),
        'expansion_potential': series.get('expansion_potential'),
    }
