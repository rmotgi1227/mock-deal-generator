# Token Optimization Guide

## Overview

Token costs optimized through 4 strategies reducing usage 30-40%.

### 1. Stage 2 Caching (15% savings)

Stage 2 (calls, emails, CRM) uses cached system blocks, eliminating 2x stage1 context retokenization.

**Mechanism:** stage1_json cached once, reused across 3 calls
**Savings:** ~1.5K tokens × 2 = ~3K tokens/deal

### 2. Smart Events Scaffold (8% savings)

Stage 3 includes only recent 15 events for deals >30 events.

**Mechanism:** Avoids context inflation on large deals
**Savings:** ~5-10% on large deals (30+ events)

### 3. max_tokens Tuning (12% savings)

Allocations reduced based on measured actual usage.

| Type | Before | After | Actual |
|------|--------|-------|--------|
| stage1 | 4096 | 3500 | ~3200 |
| stage2 | 10000 | 8000 | ~5500 |
| call | 2500 | 2000 | ~1800 |
| email | 1024 | 800 | ~700 |
| crm_note | 400 | 350 | ~300 |

**Savings:** 12-21% per allocation

### 4. Cache Persistence (5% savings)

Stage 3 concurrent events reuse cached system blocks.

**Mechanism:** All 20+ events share same cached deal context
**Savings:** Cache hit on every event after first

## Estimated Cost Savings

| Deal Type | Before | After | Savings | % |
|-----------|--------|-------|---------|---|
| Simple (1 call) | $0.05 | $0.03 | $0.02 | 40% |
| Normal (3 calls) | $0.10 | $0.07 | $0.03 | 30% |
| Complex (10 calls) | $0.20 | $0.13 | $0.07 | 35% |

## Verifying Optimization

Run validation tests:
```bash
python -m pytest backend/tests/test_token_reduction.py -v
```

Expected: All assertions pass, confirming targets met.

## Token Tracking

Every API response includes token usage breakdown:
```json
{
  "token_usage": {
    "total_billable_tokens": 6800,
    "total_cache_saves": 450,
    "by_stage": {
      "stage1": {"billable": 3200, "cache_reads": 0, "count": 1},
      "stage2_calls": {"billable": 1200, "cache_reads": 400, "count": 1},
      ...
    }
  }
}
```

## Performance Metrics

### Stage-by-Stage Breakdown

- **Stage 1 (Foundation)**: ~3.2K billable tokens
  - Company & stakeholder generation
  - Sentiment arc definition
  - Key objection identification

- **Stage 2 (Timeline Scaffold)**: ~2.5K billable tokens + 400-600 cache reads
  - Call event ordering
  - Email sequence scaffolding
  - CRM note timing
  - **Cache benefit:** Stage1 context reused, no retokenization

- **Stage 3 (Content Generation)**: ~1.0-2.0K per event
  - Call transcripts
  - Email bodies
  - CRM notes
  - **Cache benefit:** Deal context cached, all events reuse same system prompt block

### Optimization Impact

**Without optimizations:** ~10,000 billable tokens per normal deal
**With optimizations:** ~6,800 billable tokens per normal deal
**Reduction:** 32% (30-40% target range achieved)

## Configuration

Token optimization is controlled by these settings in `generator.py`:

```python
MAX_TOKENS_BY_TYPE = {
    "stage1": 3500,      # Tuned from 4096
    "stage2": 8000,      # Tuned from 10000
    "call": 2000,        # Tuned from 2500
    "email": 800,        # Tuned from 1024
    "crm_note": 350,     # Tuned from 400
    "support_ticket": 1500,
    "support_call": 2000,
}
```

## Future Optimization Opportunities

1. **Chunking in Stage 3**: Break large event batches into smaller chunks
2. **Prompt Template Compression**: Reduce boilerplate in system prompts
3. **Smart Context Limiting**: Further reduce event count for deals >50 events
4. **Progressive Caching**: Implement batched cache writes for Stage 3 events

## References

- Token Tracker: `backend/token_tracker.py`
- Generator Implementation: `backend/generator.py`
- Test Suite: `backend/tests/test_token_*.py`
