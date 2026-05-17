"""
NDJson file I/O operations for deal storage and retrieval.
Deals are stored as .ndjson files in backend/deals/ directory.
Line 1: metadata object
Lines 2+: timeline events (call, email, crm_note)
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime, timezone
import aiofiles

DEALS_DIR = "deals"

async def ensure_deals_dir_exists() -> None:
    """Create backend/deals directory if it doesn't exist."""
    Path(DEALS_DIR).mkdir(parents=True, exist_ok=True)

def generate_deal_filename(company_name: str, deal_id: str) -> str:
    """
    Generate NDJson filename in format: {company_slug}_{deal_id_short}_{timestamp}.ndjson

    Args:
        company_name: Company name (will be slugified)
        deal_id: Full UUID string (will use first 8 chars)

    Returns:
        Filename string
    """
    # Slugify company name: lowercase, spaces->underscores, remove non-alphanumeric
    company_slug = re.sub(r'[^a-z0-9_]', '', company_name.lower().replace(' ', '_'))
    deal_id_short = deal_id[:8]
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    return f"{company_slug}_{deal_id_short}_{timestamp}.ndjson"

async def write_deal(deal_id: str, metadata: Dict[str, Any], events: List[Dict[str, Any]]) -> str:
    """
    Write deal to NDJson file. Metadata on line 1, events sorted by timestamp.

    Args:
        deal_id: UUID string
        metadata: Deal metadata object
        events: List of timeline event objects

    Returns:
        Filename written to disk

    Raises:
        Exception: If write fails
    """
    await ensure_deals_dir_exists()

    filename = generate_deal_filename(metadata['company']['name'], deal_id)
    filepath = os.path.join(DEALS_DIR, filename)

    # Sort events by timestamp
    sorted_events = sorted(events, key=lambda e: e['timestamp'])

    try:
        async with aiofiles.open(filepath, 'w') as f:
            # Line 1: metadata
            await f.write(json.dumps(metadata) + '\n')

            # Lines 2+: events
            for event in sorted_events:
                await f.write(json.dumps(event) + '\n')
    except Exception as e:
        raise Exception(f"Failed to write deal file {filename}: {str(e)}")

    return filename

async def read_deal(filepath: str) -> Dict[str, Any]:
    """
    Read deal from NDJson file. Parse metadata and events, sort events by timestamp.

    Args:
        filepath: Path to .ndjson file relative to project root

    Returns:
        Dict with 'metadata' and 'events' keys

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If JSON parsing fails
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Deal file not found: {filepath}")

    try:
        async with aiofiles.open(filepath, 'r') as f:
            lines = await f.readlines()
    except Exception as e:
        raise Exception(f"Failed to read deal file {filepath}: {str(e)}")

    if not lines:
        raise ValueError(f"Deal file is empty: {filepath}")

    try:
        metadata = json.loads(lines[0])
        events = [json.loads(line) for line in lines[1:] if line.strip()]
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in deal file {filepath}: {str(e)}")

    # Sort events by timestamp ascending (oldest first)
    events.sort(key=lambda e: e['timestamp'])

    return {
        'metadata': metadata,
        'events': events
    }

def find_deal_file(deal_id: str) -> str:
    """
    Find .ndjson file containing deal_id in first line.
    Intentionally synchronous — called from delete/get endpoints via FastAPI's
    thread pool (run_in_executor), keeping aiofiles for large I/O only.

    Args:
        deal_id: UUID string to search for

    Returns:
        Full filepath if found

    Raises:
        FileNotFoundError: If no file contains deal_id
    """
    if not os.path.exists(DEALS_DIR):
        raise FileNotFoundError("Deal not found")

    for filename in os.listdir(DEALS_DIR):
        if not filename.endswith('.ndjson'):
            continue

        filepath = os.path.join(DEALS_DIR, filename)
        try:
            with open(filepath, 'r') as f:
                first_line = f.readline()
                if not first_line:
                    continue
                metadata = json.loads(first_line)
                if metadata.get('deal_id') == deal_id:
                    return filepath
        except (json.JSONDecodeError, IOError):
            continue

    raise FileNotFoundError("Deal not found")

async def list_deal_files() -> List[Dict[str, Any]]:
    """
    List all deals. Returns metadata summaries sorted by generated_at descending.

    Returns:
        List of deal summary dicts with keys: deal_id, filename, company_name, industry,
        deal_size, deal_outcome, complexity, generated_at, num_events
    """
    await ensure_deals_dir_exists()

    deals = []

    for filename in os.listdir(DEALS_DIR):
        if not filename.endswith('.ndjson'):
            continue

        filepath = os.path.join(DEALS_DIR, filename)
        try:
            async with aiofiles.open(filepath, 'r') as f:
                first_line = await f.readline()
                if not first_line:
                    continue
                metadata = json.loads(first_line)

                # Count events (number of lines minus metadata)
                all_lines = await f.readlines()
                num_events = len(all_lines)

                deals.append({
                    'deal_id': metadata['deal_id'],
                    'filename': metadata['filename'],
                    'company_name': metadata['company']['name'],
                    'industry': metadata['company']['industry'],
                    'deal_size': metadata['config']['deal_size'],
                    'deal_outcome': metadata['deal_outcome'],
                    'complexity': metadata['config']['complexity'],
                    'generated_at': metadata['generated_at'],
                    'num_events': num_events
                })
        except (json.JSONDecodeError, IOError, KeyError):
            continue

    # Sort by generated_at descending (newest first)
    deals.sort(key=lambda d: d['generated_at'], reverse=True)

    return deals

async def delete_deal(deal_id: str) -> None:
    """
    Delete deal file by deal_id.

    Args:
        deal_id: UUID string

    Raises:
        FileNotFoundError: If deal not found
    """
    try:
        filepath = find_deal_file(deal_id)
    except FileNotFoundError:
        raise FileNotFoundError("Deal not found")

    try:
        os.remove(filepath)
    except Exception as e:
        raise Exception(f"Failed to delete deal file: {str(e)}")
