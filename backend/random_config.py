"""Random deal config generator for bulk generation."""

import random

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


def generate_random_config() -> dict:
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
        emails_per_stage = random.randint(2, 5)
        num_stakeholders = random.randint(4, 8)
        sales_cycle = random.randint(60, 180)
    elif complexity == "normal":
        num_calls = random.randint(3, 7)
        emails_per_stage = random.randint(2, 4)
        num_stakeholders = random.randint(3, 6)
        sales_cycle = random.randint(30, 90)
    else:
        num_calls = random.randint(1, 4)
        emails_per_stage = random.randint(1, 2)
        num_stakeholders = random.randint(2, 4)
        sales_cycle = random.randint(14, 45)

    return {
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
    }
