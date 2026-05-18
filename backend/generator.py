"""
Three-stage deal generation pipeline.
Stage 1: Foundation (company, stakeholders, sentiment arc)
Stage 2: Timeline scaffold (event ordering with metadata)
Stage 3: Content generation (batched with concurrency limit)
"""

import json
import asyncio
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Callable, Awaitable
from anthropic import AsyncAnthropic
import os
from dotenv import load_dotenv
from prompts import (
    SYSTEM_PROMPT,
    STAGE_1_PROMPT_TEMPLATE,
    STAGE_1_CS_PROMPT_TEMPLATE,
    STAGE_2_PROMPT_TEMPLATE,
    STAGE_3_CALL_PROMPT_TEMPLATE,
    STAGE_3_EMAIL_PROMPT_TEMPLATE,
    STAGE_3_CRM_NOTE_PROMPT_TEMPLATE,
)

load_dotenv()

client = AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
MODEL = os.environ.get("CLAUDE_MODEL", "claude-haiku-4-5")

# Max tokens per event type — tuned to actual output needs
MAX_TOKENS_BY_TYPE = {
    "stage1": 4096,
    "stage2": 10000,  
    "call": 2500,
    "email": 1024,
    "crm_note": 400,
}

# Tier-1 output tokens per minute by model family
_OUTPUT_TPM = {
    "haiku": 10_000,
    "sonnet": 8_000,
    "opus": 80_000,
}


def _model_output_tpm() -> int:
    m = MODEL.lower()
    for family, tpm in _OUTPUT_TPM.items():
        if family in m:
            return tpm
    return 8_000


class _OutputTokenLimiter:
    """
    Sliding-window output-token rate limiter.
    Blocks callers when the per-minute budget is exhausted and resumes
    once the current window resets.
    """
    def __init__(self, tpm: int):
        self._tpm = tpm
        self._used = 0
        self._window_start = time.monotonic()
        self._lock = asyncio.Lock()

    async def consume(self, tokens: int) -> None:
        async with self._lock:
            now = time.monotonic()
            if now - self._window_start >= 60.0:
                self._used = 0
                self._window_start = now
            if self._used + tokens > self._tpm:
                wait = 61.0 - (now - self._window_start)
                await asyncio.sleep(max(wait, 0))
                self._used = 0
                self._window_start = time.monotonic()
            self._used += tokens

ProgressCallback = Callable[[str, str, int], Awaitable[None]]


def _parse_claude_response(text: str) -> str:
    """Strip markdown fences, validate JSON, return clean JSON string."""
    response = text.strip()
    if response.startswith("```json"):
        response = response[7:]
    if response.startswith("```"):
        response = response[3:]
    if response.endswith("```"):
        response = response[:-3]
    response = response.strip()

    try:
        json.loads(response)
        return response
    except json.JSONDecodeError as parse_err:
        # Claude sometimes uses backslash-newline as a line continuation inside JSON strings,
        # which is an invalid escape sequence. Replace with a space.
        fixed = response.replace("\\\n", " ")
        fixed = fixed.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
        try:
            json.loads(fixed)
            return fixed
        except Exception:
            with open("/tmp/claude_response.json", "w") as f:
                f.write(response)
            raise Exception(f"Claude response is not valid JSON: {str(parse_err)}\n\nFull response saved to /tmp/claude_response.json")


async def _call_with_retry(create_kwargs: dict, max_retries: int = 4) -> tuple[str, int]:
    """
    Call Claude API with exponential backoff on 429 rate limit errors.
    Returns (content, output_token_count).
    """
    from anthropic import RateLimitError
    delay = 5
    for attempt in range(max_retries):
        try:
            message = await client.messages.create(**create_kwargs)
            return _parse_claude_response(message.content[0].text), message.usage.output_tokens
        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(delay)
            delay = min(delay * 2, 60)


async def call_claude(prompt: str, max_tokens: int) -> str:
    """Call Claude with plain system prompt. Returns valid JSON string."""
    text, _ = await _call_with_retry({
        "model": MODEL,
        "max_tokens": max_tokens,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": prompt}],
    })
    return text


async def call_claude_cached(
    system_blocks: list,
    prompt: str,
    max_tokens: int,
    limiter: Optional[_OutputTokenLimiter] = None,
) -> str:
    """
    Call Claude with cached system blocks. Pass a limiter to enforce the
    output-token-per-minute budget (Tier 1: 10K/min for Haiku).
    """
    text, output_tokens = await _call_with_retry({
        "model": MODEL,
        "max_tokens": max_tokens,
        "system": system_blocks,
        "messages": [{"role": "user", "content": prompt}],
    })
    if limiter:
        await limiter.consume(output_tokens)
    return text


def build_cached_system_blocks(stage1: Dict[str, Any], config: Dict[str, Any]) -> list:
    """
    Build system content blocks with deal context marked for caching.
    The combined size of SYSTEM_PROMPT + deal context needs to exceed
    the model's minimum cacheable prefix (4096 tokens for Haiku 4.5).
    Cache hits amortize cost across all stage-3 event calls in a deal.
    """
    deal_context = (
        f"Deal context for this generation run:\n"
        f"Company: {json.dumps(stage1['company'])}\n"
        f"Sales Rep: {json.dumps(stage1['sales_rep'])}\n"
        f"Stakeholders: {json.dumps(stage1['stakeholders'])}\n"
        f"Sentiment Arc: {json.dumps(stage1['sentiment_arc'])}\n"
        f"Objections: {json.dumps(stage1['objections'])}\n"
        f"Config: industry={config['industry']}, deal_size={config['deal_size']}, "
        f"complexity={config['complexity']}, main_objection={config['main_objection']}, "
        f"deal_outcome={config['deal_outcome']}"
    )
    return [
        {"type": "text", "text": SYSTEM_PROMPT},
        {"type": "text", "text": deal_context, "cache_control": {"type": "ephemeral"}},
    ]


async def stage_1_generate_foundation(config: Dict[str, Any], deal_start_date: str, deal_end_date: str) -> Dict[str, Any]:
    company_name_line = (
        f"Company Name: {config['company_name']}"
        if config['company_name']
        else "Company Name: Auto-generate a fictional company name appropriate for the industry."
    )

    prompt = STAGE_1_PROMPT_TEMPLATE.format(
        industry=config['industry'],
        deal_size=config['deal_size'],
        sales_cycle_length_days=config['sales_cycle_length_days'],
        deal_outcome=config['deal_outcome'],
        complexity=config['complexity'],
        main_objection=config['main_objection'],
        buyer_urgency=config['buyer_urgency'],
        num_stakeholders=config['num_stakeholders'],
        starting_sentiment=config['starting_sentiment'],
        ending_sentiment=config['ending_sentiment'],
        champion_entry=config['champion_entry'],
        company_name_line=company_name_line,
        deal_start_date=deal_start_date,
        deal_end_date=deal_end_date,
    )

    response = await call_claude(prompt, MAX_TOKENS_BY_TYPE["stage1"])
    return json.loads(response)


async def generate_stage_1_cs_context(
    stage1_json: str,
    cs_scenario,
    adoption_challenge: str,
    support_contact_frequency: str,
    churn_probability: float,
    deal_close_date: str,
    cs_start_date: str,
    cs_end_date: str,
    token_limiter: _OutputTokenLimiter,
) -> Dict[str, Any]:
    """Generate post-close CS context given Stage 1 foundation."""
    prompt = STAGE_1_CS_PROMPT_TEMPLATE.format(
        stage1_json=stage1_json,
        adoption_challenge=adoption_challenge,
        support_contact_frequency=support_contact_frequency,
        churn_probability=churn_probability,
        deal_close_date=deal_close_date,
        cs_start_date=cs_start_date,
        cs_end_date=cs_end_date,
    )

    response = await client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS_BY_TYPE["stage1"],
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    await token_limiter.consume(response.usage.output_tokens)

    cs_json = _parse_claude_response(response.content[0].text)
    return json.loads(cs_json)


async def stage_2_generate_timeline_scaffold(
    stage1_output: Dict[str, Any],
    config: Dict[str, Any],
    deal_start_date: str,
    deal_end_date: str
) -> List[Dict[str, Any]]:
    prompt = STAGE_2_PROMPT_TEMPLATE.format(
        stage1_json=json.dumps(stage1_output),
        deal_start_date=deal_start_date,
        deal_end_date=deal_end_date,
        num_calls=config['num_calls'],
        emails_per_stage=config['emails_per_stage'],
        champion_entry=config['champion_entry'],
        complexity=config['complexity'],
        main_objection=config['main_objection'],
    )

    response = await call_claude(prompt, MAX_TOKENS_BY_TYPE["stage2"])
    return json.loads(response)


def build_prior_events_summary(events: List[Dict[str, Any]], current_event_index: int, max_prior: int = 7) -> str:
    """
    Summarize the most recent prior events. Capped to avoid O(n²) token growth
    as deal timelines grow — later events no longer pay for the entire history.
    """
    prior = events[:current_event_index]
    if not prior:
        return ""

    # Keep only the most recent max_prior events to control token growth
    prior = prior[-max_prior:]

    lines = [f"Recent prior interactions (last {len(prior)}, oldest first):"]
    for event in prior:
        event_type = event['record_type']
        date = event['date']

        if event_type == 'call':
            label = event.get('title', 'Call')
        elif event_type == 'email':
            label = event.get('subject', 'Email')
        else:
            label = event.get('note_preview', 'CRM Note')

        lines.append(f"- [{date}] {event_type}: {label}")

    return "\n".join(lines)


def get_all_stakeholders_summary(stage1: Dict[str, Any]) -> str:
    lines = []
    for sh in stage1['stakeholders']:
        lines.append(f"- {sh['name']} ({sh['title']}): {sh['archetype']}, support={sh['support_level']}")
    return "\n".join(lines)


def get_champion_context(stage1: Dict[str, Any], champion_entered: bool, current_timestamp: str) -> str:
    if not any(sh.get('is_champion') for sh in stage1['stakeholders']):
        return "No champion in this deal."

    if not champion_entered:
        return "Champion has not yet emerged."

    champion = next(sh for sh in stage1['stakeholders'] if sh.get('is_champion'))
    return f"Champion: {champion['name']} ({champion['title']}) is actively supporting the deal internally."


async def stage_3_generate_call_content(
    event: Dict[str, Any],
    stage1: Dict[str, Any],
    config: Dict[str, Any],
    prior_summary: str,
    champion_entered: bool,
    system_blocks: list,
    limiter: Optional[_OutputTokenLimiter] = None,
) -> Dict[str, Any]:
    participants_detail = "\n".join([
        f"- {p['name']} ({p['role']})"
        for p in event.get('participants', [])
    ])

    champion_context = get_champion_context(stage1, champion_entered, event['timestamp'])

    prompt = STAGE_3_CALL_PROMPT_TEMPLATE.format(
        company_name=stage1['company']['name'],
        industry=stage1['company']['industry'],
        deal_size=config['deal_size'],
        vendor_company=stage1['sales_rep']['vendor_company'],
        sales_rep_name=stage1['sales_rep']['name'],
        sales_rep_title=stage1['sales_rep']['title'],
        stage=event['stage'],
        complexity=config['complexity'],
        main_objection=config['main_objection'],
        sentiment=event['sentiment'],
        champion_context=champion_context,
        participants_detail=participants_detail,
        all_stakeholders_summary=get_all_stakeholders_summary(stage1),
        event_scaffold_json=json.dumps(event, indent=2),
        prior_events_summary=prior_summary,
    )

    response = await call_claude_cached(system_blocks, prompt, MAX_TOKENS_BY_TYPE["call"], limiter)
    content = json.loads(response)
    event.update(content)
    return event


async def stage_3_generate_email_content(
    event: Dict[str, Any],
    stage1: Dict[str, Any],
    config: Dict[str, Any],
    prior_summary: str,
    all_events: List[Dict[str, Any]],
    system_blocks: list,
    limiter: Optional[_OutputTokenLimiter] = None,
) -> Dict[str, Any]:
    reply_context = ""
    if event.get('reply_to_id'):
        parent = next((e for e in all_events if e.get('id') == event['reply_to_id']), None)
        if parent:
            reply_context = f"""This email is a direct reply to:
Subject: {parent.get('subject', '')}
From: {parent.get('sender', {}).get('name', '')}

{parent.get('body', '')}"""

    prompt = STAGE_3_EMAIL_PROMPT_TEMPLATE.format(
        company_name=stage1['company']['name'],
        industry=stage1['company']['industry'],
        vendor_company=stage1['sales_rep']['vendor_company'],
        stage=event['stage'],
        sentiment=event['sentiment'],
        purpose=event.get('purpose', 'outbound'),
        event_scaffold_json=json.dumps(event, indent=2),
        reply_context=reply_context,
        prior_events_summary=prior_summary,
    )

    response = await call_claude_cached(system_blocks, prompt, MAX_TOKENS_BY_TYPE["email"], limiter)
    content = json.loads(response)
    event.update(content)
    return event


async def stage_3_generate_crm_note_content(
    event: Dict[str, Any],
    stage1: Dict[str, Any],
    config: Dict[str, Any],
    prior_summary: str,
    system_blocks: list,
    limiter: Optional[_OutputTokenLimiter] = None,
) -> Dict[str, Any]:
    prompt = STAGE_3_CRM_NOTE_PROMPT_TEMPLATE.format(
        company_name=stage1['company']['name'],
        sales_rep_name=stage1['sales_rep']['name'],
        stage=event['stage'],
        sentiment=event['sentiment'],
        note_preview=event.get('note_preview', ''),
    )

    response = await call_claude_cached(system_blocks, prompt, MAX_TOKENS_BY_TYPE["crm_note"], limiter)
    content = json.loads(response)
    event.update(content)
    return event


async def stage_3_generate_all_content(
    events: List[Dict[str, Any]],
    stage1: Dict[str, Any],
    config: Dict[str, Any],
    progress_callback: Optional[ProgressCallback] = None,
    external_limiter: Optional[_OutputTokenLimiter] = None,
) -> List[Dict[str, Any]]:
    """
    Stage 3: Generate content for all events with bounded concurrency.
    Builds a shared cached system block with deal context to amortize
    token cost across all event calls. An output-token limiter enforces
    the Tier-1 per-minute budget to avoid 429s.
    Pass external_limiter to share a single budget across concurrent deals.
    """
    system_blocks = build_cached_system_blocks(stage1, config)
    semaphore = asyncio.Semaphore(2)
    limiter = external_limiter or _OutputTokenLimiter(_model_output_tpm())
    total = len(events)
    completed_count = [0]
    results = [None] * total

    async def generate_one(index: int, event: Dict[str, Any]):
        prior_summary = build_prior_events_summary(events, index)
        champion_entered = any(
            e.get('note_preview', '').find('Champion') >= 0
            for e in events[:index]
        )

        async with semaphore:
            record_type = event['record_type']
            if record_type == 'call':
                result = await stage_3_generate_call_content(event, stage1, config, prior_summary, champion_entered, system_blocks, limiter)
            elif record_type == 'email':
                result = await stage_3_generate_email_content(event, stage1, config, prior_summary, events, system_blocks, limiter)
            elif record_type == 'crm_note':
                result = await stage_3_generate_crm_note_content(event, stage1, config, prior_summary, system_blocks, limiter)
            else:
                result = event

            results[index] = result
            completed_count[0] += 1

            if progress_callback:
                pct = 40 + int((completed_count[0] / total) * 55)
                label = {
                    'call': f"call ({event.get('title', 'untitled')})",
                    'email': f"email ({event.get('subject', '')})",
                    'crm_note': 'CRM note',
                }.get(record_type, record_type)
                await progress_callback(
                    f"stage3_{completed_count[0]}",
                    f"Generating {label} — {completed_count[0]}/{total}",
                    pct
                )

    tasks = [generate_one(i, event) for i, event in enumerate(events)]
    await asyncio.gather(*tasks)

    return results


async def generate_complete_deal(
    config: Dict[str, Any],
    progress_callback: Optional[ProgressCallback] = None,
    external_limiter: Optional[_OutputTokenLimiter] = None,
) -> Dict[str, Any]:
    """
    Run full 3-stage pipeline and return complete deal object.
    Optional progress_callback(step, message, pct) called at each stage.
    """
    deal_end_date = datetime.now(timezone.utc).date()
    deal_start_date = deal_end_date - timedelta(days=config['sales_cycle_length_days'])
    deal_id = str(uuid.uuid4())

    if progress_callback:
        await progress_callback("stage1", "Generating company profile and stakeholders...", 5)

    stage1 = await stage_1_generate_foundation(config, str(deal_start_date), str(deal_end_date))
    stage_1_json_str = json.dumps(stage1)

    # Generate CS context if enabled
    cs_context = None
    cs_scenario = config.get('cs_scenario')
    output_token_limiter = external_limiter or _OutputTokenLimiter(_model_output_tpm())

    if cs_scenario and cs_scenario.get('enabled'):
        # Sales cycle complete, now add CS period
        deal_close_date = str(deal_end_date)  # This is sales close (end of sales_cycle_length_days)

        # CS period: from close+1 to (close + post_close_days)
        cs_start = (datetime.fromisoformat(deal_close_date) + timedelta(days=1)).strftime("%Y-%m-%d")
        cs_end = (datetime.fromisoformat(deal_close_date) + timedelta(days=cs_scenario.get('post_close_days', 30))).strftime("%Y-%m-%d")

        # Extract enum values (they're already strings from Pydantic dict conversion)
        adoption_challenge_value = cs_scenario.get('adoption_challenge')
        if hasattr(adoption_challenge_value, 'value'):
            adoption_challenge_value = adoption_challenge_value.value

        support_contact_freq_value = cs_scenario.get('support_contact_frequency')
        if hasattr(support_contact_freq_value, 'value'):
            support_contact_freq_value = support_contact_freq_value.value

        cs_context = await generate_stage_1_cs_context(
            stage1_json=stage_1_json_str,
            cs_scenario=cs_scenario,
            adoption_challenge=adoption_challenge_value or '',
            support_contact_frequency=support_contact_freq_value or 'low',
            churn_probability=cs_scenario.get('churn_probability', 0.5),
            deal_close_date=deal_close_date,
            cs_start_date=cs_start,
            cs_end_date=cs_end,
            token_limiter=output_token_limiter,
        )

    if progress_callback:
        await progress_callback("stage2", "Building deal timeline scaffold...", 25)

    events_scaffold = await stage_2_generate_timeline_scaffold(
        stage1, config, str(deal_start_date), str(deal_end_date)
    )

    if progress_callback:
        await progress_callback("stage3_start", f"Generating content for {len(events_scaffold)} events...", 35)

    events = await stage_3_generate_all_content(events_scaffold, stage1, config, progress_callback, external_limiter)

    if progress_callback:
        await progress_callback("saving", "Saving deal...", 96)

    generated_at = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S') + 'Z'

    metadata = {
        'record_type': 'deal_metadata',
        'deal_id': deal_id,
        'filename': '',
        'generated_at': generated_at,
        'deal_start_date': str(deal_start_date),
        'deal_end_date': str(deal_end_date),
        'config': {
            'company_name_input': config.get('company_name'),
            'industry': config['industry'],
            'deal_size': config['deal_size'],
            'sales_cycle_length_days': config['sales_cycle_length_days'],
            'starting_sentiment': config['starting_sentiment'],
            'ending_sentiment': config['ending_sentiment'],
            'champion_entry': config['champion_entry'],
            'main_objection': config['main_objection'],
            'buyer_urgency': config['buyer_urgency'],
            'num_calls': config['num_calls'],
            'emails_per_stage': config['emails_per_stage'],
            'num_stakeholders': config['num_stakeholders'],
            'complexity': config['complexity'],
        },
        'company': stage1['company'],
        'sales_rep': stage1['sales_rep'],
        'stakeholders': stage1['stakeholders'],
        'deal_outcome': config['deal_outcome'],
        'sentiment_arc': stage1['sentiment_arc'],
        'stage_progression': stage1['stage_progression'],
        'objections': stage1['objections'],
    }

    return {
        'deal_id': deal_id,
        'metadata': metadata,
        'events': events
    }
