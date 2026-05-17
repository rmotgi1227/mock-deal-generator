"""
Three-stage deal generation pipeline.
Stage 1: Foundation (company, stakeholders, sentiment arc)
Stage 2: Timeline scaffold (event ordering with metadata)
Stage 3: Content generation (parallel event content fill-in)
"""

import json
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from anthropic import AsyncAnthropic
import os
from dotenv import load_dotenv
from prompts import (
    SYSTEM_PROMPT,
    STAGE_1_PROMPT_TEMPLATE,
    STAGE_2_PROMPT_TEMPLATE,
    STAGE_3_CALL_PROMPT_TEMPLATE,
    STAGE_3_EMAIL_PROMPT_TEMPLATE,
    STAGE_3_CRM_NOTE_PROMPT_TEMPLATE,
)

# Load environment variables
load_dotenv()

# Initialize async Anthropic client
client = AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
MODEL = os.environ.get("CLAUDE_MODEL", "claude-haiku-4-5-20251001")

async def call_claude_with_retry(prompt: str, max_retries: int = 3) -> str:
    """
    Call Claude API with retry logic. Strips markdown backticks if present.

    Args:
        prompt: Full prompt (system + user combined)
        max_retries: Number of retry attempts on JSON parse failure

    Returns:
        Valid JSON string response

    Raises:
        Exception: If all retries fail
    """
    for attempt in range(max_retries):
        try:
            message = await client.messages.create(
                model=MODEL,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            response = message.content[0].text

            # Strip markdown backticks if present
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()

            # Validate JSON - try to parse and log errors
            try:
                json.loads(response)
                return response
            except json.JSONDecodeError as parse_err:
                # Try common fixes: replace smart quotes
                fixed = response.replace('"', '"').replace('"', '"').replace(''', "'").replace(''', "'")
                try:
                    json.loads(fixed)
                    return fixed
                except:
                    pass  # Will retry or fail below
                raise parse_err
        except json.JSONDecodeError as e:
            if attempt == max_retries - 1:
                raise Exception(f"Claude response is not valid JSON after {max_retries} retries: {str(e)}")
            # Retry on JSON parse failure
            await asyncio.sleep(1)
        except Exception as e:
            if attempt == max_retries - 1:
                raise Exception(f"Claude API call failed after {max_retries} retries: {str(e)}")
            await asyncio.sleep(1)

async def stage_1_generate_foundation(config: Dict[str, Any], deal_start_date: str, deal_end_date: str) -> Dict[str, Any]:
    """
    Stage 1: Generate deal foundation (company, stakeholders, sentiment arc, objections).

    Args:
        config: Deal configuration from POST request
        deal_start_date: YYYY-MM-DD
        deal_end_date: YYYY-MM-DD

    Returns:
        Dict with keys: company, sales_rep, stakeholders, sentiment_arc, stage_progression, objections
    """
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

    response = await call_claude_with_retry(prompt)
    return json.loads(response)

async def stage_2_generate_timeline_scaffold(
    stage1_output: Dict[str, Any],
    config: Dict[str, Any],
    deal_start_date: str,
    deal_end_date: str
) -> List[Dict[str, Any]]:
    """
    Stage 2: Generate timeline scaffold (events with metadata, no content).

    Args:
        stage1_output: Result from Stage 1
        config: Deal configuration
        deal_start_date: YYYY-MM-DD
        deal_end_date: YYYY-MM-DD

    Returns:
        List of event scaffold dicts
    """
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

    response = await call_claude_with_retry(prompt)
    return json.loads(response)

def build_prior_events_summary(events: List[Dict[str, Any]], current_event_index: int) -> str:
    """
    Build a text summary of all prior events for context in Stage 3 prompts.

    Args:
        events: All event scaffolds
        current_event_index: Index of current event

    Returns:
        Formatted string of prior events
    """
    prior = events[:current_event_index]
    if not prior:
        return ""

    lines = ["Prior interactions (oldest first):"]
    for event in prior:
        event_type = event['record_type']
        date = event['date']

        if event_type == 'call':
            label = event.get('title', 'Call')
        elif event_type == 'email':
            label = event.get('subject', 'Email')
        else:  # crm_note
            label = event.get('note_preview', 'CRM Note')

        lines.append(f"- [{date}] {event_type}: {label}")

    return "\n".join(lines)

def get_all_stakeholders_summary(stage1: Dict[str, Any]) -> str:
    """Format all stakeholders for Stage 3 context."""
    lines = []
    for sh in stage1['stakeholders']:
        lines.append(f"- {sh['name']} ({sh['title']}): {sh['archetype']}, support={sh['support_level']}")
    return "\n".join(lines)

def get_champion_context(stage1: Dict[str, Any], champion_entered: bool, current_timestamp: str) -> str:
    """Get champion context string for Stage 3 prompts."""
    if not any(sh.get('is_champion') for sh in stage1['stakeholders']):
        return "No champion in this deal."

    if not champion_entered:
        return "Champion has not yet emerged."

    # Find champion
    champion = next((sh for sh in stage1['stakeholders'] if sh.get('is_champion')), None)
    if champion:
        return f"Champion: {champion['name']} ({champion['title']}) is actively supporting the deal internally."

    return "Champion has not yet emerged."

async def stage_3_generate_call_content(
    event: Dict[str, Any],
    stage1: Dict[str, Any],
    config: Dict[str, Any],
    prior_summary: str,
    champion_entered: bool
) -> Dict[str, Any]:
    """Generate full content for a call event."""

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

    response = await call_claude_with_retry(prompt)
    content = json.loads(response)

    # Merge content with scaffold
    event.update(content)
    return event

async def stage_3_generate_email_content(
    event: Dict[str, Any],
    stage1: Dict[str, Any],
    config: Dict[str, Any],
    prior_summary: str,
    all_events: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Generate full content for an email event."""

    # Build reply context
    reply_context = ""
    if event.get('reply_to_id'):
        # Find parent email
        parent = next((e for e in all_events if e.get('id') == event['reply_to_id']), None)
        if parent:
            reply_context = f"""This email is a direct reply to:
Subject: {parent.get('subject', '')}
From: {parent.get('sender', {}).get('name', '')}

{parent.get('body', '')}"""
    elif event.get('is_forward'):
        # Find forwarded email
        parent = next((e for e in all_events if e.get('id') == event['reply_to_id']), None)
        if parent:
            reply_context = f"""This email is being forwarded. Original:
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

    response = await call_claude_with_retry(prompt)
    content = json.loads(response)

    # Merge content with scaffold
    event.update(content)
    return event

async def stage_3_generate_crm_note_content(
    event: Dict[str, Any],
    stage1: Dict[str, Any],
    config: Dict[str, Any],
    prior_summary: str
) -> Dict[str, Any]:
    """Generate full content for a CRM note event."""

    prompt = STAGE_3_CRM_NOTE_PROMPT_TEMPLATE.format(
        company_name=stage1['company']['name'],
        sales_rep_name=stage1['sales_rep']['name'],
        stage=event['stage'],
        sentiment=event['sentiment'],
        note_preview=event.get('note_preview', ''),
    )

    response = await call_claude_with_retry(prompt)
    content = json.loads(response)

    # Merge content with scaffold
    event.update(content)
    return event

async def stage_3_generate_all_content(
    events: List[Dict[str, Any]],
    stage1: Dict[str, Any],
    config: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Stage 3: Generate content for all events in parallel via asyncio.gather().

    Args:
        events: Event scaffolds from Stage 2
        stage1: Foundation output from Stage 1
        config: Deal configuration

    Returns:
        List of fully-populated event objects
    """
    tasks = []

    for index, event in enumerate(events):
        prior_summary = build_prior_events_summary(events, index)

        # Check if champion has entered by this point
        champion_entered = any(
            e.get('note_preview', '').find('Champion') >= 0
            for e in events[:index]
        )

        if event['record_type'] == 'call':
            task = stage_3_generate_call_content(event, stage1, config, prior_summary, champion_entered)
        elif event['record_type'] == 'email':
            task = stage_3_generate_email_content(event, stage1, config, prior_summary, events)
        elif event['record_type'] == 'crm_note':
            task = stage_3_generate_crm_note_content(event, stage1, config, prior_summary)
        else:
            continue

        tasks.append(task)

    # Run all content generation in parallel
    results = await asyncio.gather(*tasks)

    return results

async def generate_complete_deal(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run full 3-stage pipeline and return complete deal object.

    Args:
        config: Deal configuration from POST request

    Returns:
        Dict with: deal_id, metadata, events
    """
    # Calculate dates
    deal_end_date = datetime.utcnow().date()
    deal_start_date = deal_end_date - timedelta(days=config['sales_cycle_length_days'])

    deal_id = str(uuid.uuid4())

    # Stage 1: Foundation
    stage1 = await stage_1_generate_foundation(config, str(deal_start_date), str(deal_end_date))

    # Stage 2: Timeline Scaffold
    events_scaffold = await stage_2_generate_timeline_scaffold(
        stage1, config, str(deal_start_date), str(deal_end_date)
    )

    # Stage 3: Content Generation (parallel)
    events = await stage_3_generate_all_content(events_scaffold, stage1, config)

    # Build metadata object
    generated_at = datetime.utcnow().isoformat() + 'Z'

    metadata = {
        'record_type': 'deal_metadata',
        'deal_id': deal_id,
        'filename': '',  # Will be set by file handler
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
            'deal_outcome': config['deal_outcome'],
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
