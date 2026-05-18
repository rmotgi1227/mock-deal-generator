from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class TokenEvent:
    """Single API call token usage."""
    stage: str  # "stage1", "stage2_calls", "stage2_emails", "stage2_crm", "stage3_call", etc.
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        """Total billable tokens (input + output + writes)."""
        return self.input_tokens + self.output_tokens + self.cache_write_tokens

    @property
    def cache_savings(self) -> int:
        """Tokens saved by cache reads (free tokens)."""
        return self.cache_read_tokens

class TokenTracker:
    """Track token usage across deal generation stages."""

    def __init__(self):
        self.events: List[TokenEvent] = []

    def record(
        self,
        stage: str,
        input_tokens: int,
        output_tokens: int,
        cache_read_tokens: int = 0,
        cache_write_tokens: int = 0,
    ):
        """Record a single API call's token usage."""
        self.events.append(TokenEvent(
            stage=stage,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_tokens=cache_read_tokens,
            cache_write_tokens=cache_write_tokens,
        ))

    def total_billable(self) -> int:
        """Total billable tokens (excludes cache reads)."""
        return sum(e.total_tokens for e in self.events)

    def total_cache_savings(self) -> int:
        """Total tokens saved by cache reads."""
        return sum(e.cache_savings for e in self.events)

    def by_stage(self) -> Dict[str, Dict[str, int]]:
        """Breakdown of tokens by stage."""
        result = {}
        for event in self.events:
            if event.stage not in result:
                result[event.stage] = {
                    "billable": 0,
                    "cache_reads": 0,
                    "count": 0,
                }
            result[event.stage]["billable"] += event.total_tokens
            result[event.stage]["cache_reads"] += event.cache_savings
            result[event.stage]["count"] += 1
        return result

    def to_dict(self) -> Dict:
        """Serialize for response/logging."""
        return {
            "total_billable_tokens": self.total_billable(),
            "total_cache_saves": self.total_cache_savings(),
            "by_stage": self.by_stage(),
            "events": [
                {
                    "stage": e.stage,
                    "input": e.input_tokens,
                    "output": e.output_tokens,
                    "cache_read": e.cache_read_tokens,
                    "cache_write": e.cache_write_tokens,
                }
                for e in self.events
            ],
        }

    @staticmethod
    def estimate_cost(billable_tokens: int, cache_saves: int, model: str = "haiku") -> Dict[str, float]:
        """Estimate cost at Anthropic Tier-1 pricing."""
        # Haiku pricing: $0.80 per 1M input tokens, $4 per 1M output tokens
        # Simplified: Haiku input+output blended ~$1.60 per 1M tokens
        haiku_rate = 1.60 / 1_000_000

        total_cost = billable_tokens * haiku_rate
        savings = cache_saves * 0.10 * haiku_rate  # Cache reads save 90%

        return {
            "estimated_cost": round(total_cost, 4),
            "cache_savings": round(savings, 4),
            "net_cost": round(total_cost - savings, 4),
        }
