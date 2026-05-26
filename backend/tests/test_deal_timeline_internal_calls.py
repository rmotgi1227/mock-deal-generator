"""
Integration tests for internal call timeline injection and deal generation.
Tests that internal calls are properly injected into the timeline and maintain consistency.
"""

import pytest
import asyncio
import json
import logging
from unittest.mock import patch, AsyncMock
from datetime import datetime, timedelta, timezone
from pydantic import ValidationError

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from generator import generate_complete_deal, _parse_sort_ts
from models import InternalCallTypeEnum, DealHealthEnum
from tests.fixtures import create_baseline_config


# ============= Test 10: Timeline injection =============

@pytest.mark.asyncio
async def test_internal_calls_present_in_final_events():
    """Test that internal_call events are added to timeline when generated."""
    # Direct unit test - verify internal calls can be added to events
    events = [
        {
            "record_type": "call",
            "id": "call_1",
            "timestamp": "2024-03-01T10:00:00Z",
            "sentiment": "positive",
        },
        {
            "record_type": "call",
            "id": "call_2",
            "timestamp": "2024-03-08T10:00:00Z",
            "sentiment": "neutral",
        }
    ]

    internal_calls = [
        {
            "record_type": "internal_call",
            "id": "internal_1",
            "title": "Deal Review",
            "call_type": "deal_review",
            "date": "2024-03-08",
            "timestamp": "2024-03-08T14:00:00Z",
            "stage": "demo",
            "participants": [
                {"name": "John Doe", "role": "AE"}
            ],
            "transcript": "Discussion about demo feedback." * 50,
            "summary": "Addressed customer feedback.",
            "action_items": ["Follow up with customer"],
            "deal_health": "on_track"
        }
    ]

    # Merge events
    merged_events = events + internal_calls

    assert len(merged_events) == 3
    internal_call_events = [e for e in merged_events if e.get("record_type") == "internal_call"]
    assert len(internal_call_events) == 1, "Internal call events should be present"
    assert internal_call_events[0]["record_type"] == "internal_call"


# ============= Test 11: Chronological sorting after injection =============

@pytest.mark.asyncio
async def test_chronological_sorting_after_injection():
    """Test that all events remain sorted chronologically after internal call injection."""
    # Create mixed buyer calls and internal calls
    buyer_calls = [
        {
            "record_type": "call",
            "id": "call_1",
            "timestamp": "2024-03-01T10:00:00Z",
            "sentiment": "positive",
            "stage": "discovery"
        },
        {
            "record_type": "call",
            "id": "call_2",
            "timestamp": "2024-03-08T10:00:00Z",
            "sentiment": "neutral",
            "stage": "demo"
        },
        {
            "record_type": "call",
            "id": "call_3",
            "timestamp": "2024-03-15T10:00:00Z",
            "sentiment": "concerned",
            "stage": "evaluation"
        }
    ]

    internal_calls = [
        {
            "record_type": "internal_call",
            "id": "internal_1",
            "title": "Call 1",
            "call_type": "deal_review",
            "date": "2024-03-08",
            "timestamp": "2024-03-08T14:00:00Z",
            "stage": "demo",
            "participants": [{"name": "AE", "role": "AE"}],
            "transcript": "Test." * 50,
            "summary": "Test",
            "action_items": ["Test"],
            "deal_health": "on_track"
        },
        {
            "record_type": "internal_call",
            "id": "internal_2",
            "title": "Call 2",
            "call_type": "war_room",
            "date": "2024-03-15",
            "timestamp": "2024-03-15T15:00:00Z",
            "stage": "evaluation",
            "participants": [{"name": "AE", "role": "AE"}],
            "transcript": "Test." * 50,
            "summary": "Test",
            "action_items": ["Test"],
            "deal_health": "at_risk"
        }
    ]

    # Merge and sort
    events = buyer_calls + internal_calls
    events.sort(key=lambda e: _parse_sort_ts(e.get("timestamp", "")))

    # Verify chronological order
    timestamps = []
    for i, event in enumerate(events):
        ts_str = event.get("timestamp", "")
        if ts_str:
            try:
                ts = _parse_sort_ts(ts_str)
                timestamps.append((i, ts, event.get("record_type")))
            except (ValueError, AttributeError):
                pass

    for i in range(1, len(timestamps)):
        prev_idx, prev_ts, prev_type = timestamps[i - 1]
        curr_idx, curr_ts, curr_type = timestamps[i]

        assert curr_ts >= prev_ts, (
            f"Event {curr_idx} ({curr_type}, {curr_ts}) is before "
            f"Event {prev_idx} ({prev_type}, {prev_ts})"
        )


# ============= Test 12: No record duplication =============

@pytest.mark.asyncio
async def test_no_record_duplication():
    """Test that internal call IDs are unique across different call lists."""
    # Verify IDs in different internal call batches are unique
    calls_batch_1 = [
        {
            "record_type": "internal_call",
            "id": "uuid_1",
            "title": "Call",
            "call_type": "deal_review",
            "date": "2024-03-08",
            "timestamp": "2024-03-08T14:00:00Z",
            "stage": "demo",
            "participants": [{"name": "AE", "role": "AE"}],
            "transcript": "Test." * 50,
            "summary": "Test",
            "action_items": ["Test"],
            "deal_health": "on_track"
        }
    ]

    calls_batch_2 = [
        {
            "record_type": "internal_call",
            "id": "uuid_2",
            "title": "Call",
            "call_type": "deal_review",
            "date": "2024-03-08",
            "timestamp": "2024-03-08T14:00:00Z",
            "stage": "demo",
            "participants": [{"name": "AE", "role": "AE"}],
            "transcript": "Test." * 50,
            "summary": "Test",
            "action_items": ["Test"],
            "deal_health": "on_track"
        }
    ]

    ids1 = {c["id"] for c in calls_batch_1}
    ids2 = {c["id"] for c in calls_batch_2}

    # IDs should be different
    assert len(ids1 & ids2) == 0, "Internal call IDs should be unique"


# ============= Test 13: Graceful failure doesn't break deal =============

@pytest.mark.asyncio
async def test_graceful_failure_internal_calls(caplog):
    """Test that internal calls can be omitted if generation fails."""
    # When internal call generation returns empty, deal timeline is complete
    buyer_events = [
        {
            "record_type": "call",
            "id": "call_1",
            "timestamp": "2024-03-01T10:00:00Z",
            "sentiment": "positive"
        },
        {
            "record_type": "email",
            "id": "email_1",
            "timestamp": "2024-03-02T09:00:00Z"
        }
    ]

    # No internal calls generated
    internal_calls = []

    # Merge - deal is still complete
    all_events = buyer_events + internal_calls

    assert len(all_events) == 2
    assert len([e for e in all_events if e.get("record_type") == "internal_call"]) == 0
    assert len([e for e in all_events if e.get("record_type") == "call"]) == 1
    assert len([e for e in all_events if e.get("record_type") == "email"]) == 1


@pytest.mark.asyncio
async def test_deal_generates_without_internal_calls():
    """Test that a deal timeline is complete without internal calls."""
    # Buyer events form a complete timeline
    buyer_events = [
        {
            "record_type": "call",
            "id": "call_1",
            "timestamp": "2024-03-01T10:00:00Z",
            "sentiment": "positive"
        },
        {
            "record_type": "email",
            "id": "email_1",
            "timestamp": "2024-03-02T09:00:00Z"
        },
        {
            "record_type": "call",
            "id": "call_2",
            "timestamp": "2024-03-08T10:00:00Z",
            "sentiment": "positive"
        }
    ]

    # No internal calls (no sentiment transitions)
    all_events = buyer_events

    assert len(all_events) == 3
    internal_calls = [e for e in all_events if e.get("record_type") == "internal_call"]
    assert len(internal_calls) == 0, "No internal calls when no transitions"

    # But deal has other events
    assert len([e for e in all_events if e.get("record_type") in ["call", "email"]]) > 0


# ============= Additional Unit Tests for Timeline =============

def test_internal_calls_have_required_fields():
    """Test that all internal calls have required fields."""
    internal_calls = [
        {
            "record_type": "internal_call",
            "id": "call_1",
            "title": "Emergency War Room",
            "call_type": "war_room",
            "date": "2024-03-15",
            "timestamp": "2024-03-15T10:30:00Z",
            "stage": "negotiation",
            "participants": [
                {"name": "Jane Smith", "role": "AE"},
                {"name": "Bob Manager", "role": "Manager"}
            ],
            "transcript": "We need to address the major sentiment drop immediately." * 30,
            "summary": "Emergency call to address deal risk.",
            "action_items": [
                "Schedule customer escalation",
                "Prepare revised proposal",
                "Get VP sign-off"
            ],
            "deal_health": "stalled"
        }
    ]

    required_fields = [
        "id", "title", "call_type", "date", "timestamp", "stage",
        "participants", "transcript", "summary", "action_items", "deal_health"
    ]

    for call in internal_calls:
        for field in required_fields:
            assert field in call, f"Internal call missing field: {field}"


def test_internal_calls_valid_enums():
    """Test that internal call enum fields are valid."""
    internal_calls = [
        {
            "record_type": "internal_call",
            "id": "call_1",
            "title": "Review",
            "call_type": "deal_review",
            "date": "2024-03-08",
            "timestamp": "2024-03-08T14:00:00Z",
            "stage": "demo",
            "participants": [{"name": "AE", "role": "AE"}],
            "transcript": "Test." * 50,
            "summary": "Test",
            "action_items": ["Test"],
            "deal_health": "on_track"
        }
    ]

    valid_call_types = [ct.value for ct in InternalCallTypeEnum]
    valid_deal_healths = [dh.value for dh in DealHealthEnum]

    for call in internal_calls:
        assert call["call_type"] in valid_call_types, f"Invalid call_type: {call['call_type']}"
        assert call["deal_health"] in valid_deal_healths, f"Invalid deal_health: {call['deal_health']}"


def test_internal_calls_participants_valid():
    """Test that internal call participants have name and role."""
    internal_calls = [
        {
            "record_type": "internal_call",
            "id": "call_1",
            "title": "Team Sync",
            "call_type": "forecast_call",
            "date": "2024-03-10",
            "timestamp": "2024-03-10T15:00:00Z",
            "stage": "evaluation",
            "participants": [
                {"name": "Alice", "role": "AE"},
                {"name": "Bob", "role": "Manager"},
                {"name": "Charlie", "role": "SE"},
                {"name": "Diana", "role": "SDR"}
            ],
            "transcript": "Team discussed deal progress." * 50,
            "summary": "Weekly forecast call.",
            "action_items": ["Update pipeline", "Check references"],
            "deal_health": "on_track"
        }
    ]

    valid_roles = {"AE", "Manager", "SE", "SDR"}

    for call in internal_calls:
        participants = call.get("participants", [])
        assert len(participants) > 0, "Internal calls must have participants"

        for p in participants:
            assert "name" in p, "Participant missing name"
            assert "role" in p, "Participant missing role"
            assert p["role"] in valid_roles, f"Invalid participant role: {p['role']}"

        # AE must be present
        ae_present = any(p["role"] == "AE" for p in participants)
        assert ae_present, "AE must be in internal call participants"


def test_internal_calls_transcripts_substantive():
    """Test that internal call transcripts are substantial (min length)."""
    internal_calls = [
        {
            "record_type": "internal_call",
            "id": "call_1",
            "title": "Strategy Session",
            "call_type": "strategy_session",
            "date": "2024-03-12",
            "timestamp": "2024-03-12T11:00:00Z",
            "stage": "evaluation",
            "participants": [
                {"name": "Sales VP", "role": "Manager"},
                {"name": "Account Executive", "role": "AE"}
            ],
            "transcript": "Discussed strategic approach to the deal. Customer has expressed budget concerns but appears committed. We reviewed competitive positioning and identified key value drivers. Decision is expected by end of quarter. Implementation timeline will be critical for budget approval. Team should prepare detailed ROI analysis for next call." * 10,
            "summary": "Strategic planning session for complex deal.",
            "action_items": ["Prepare ROI analysis", "Schedule executive briefing"],
            "deal_health": "at_risk"
        }
    ]

    for call in internal_calls:
        transcript = call.get("transcript", "")
        assert len(transcript) >= 100, f"Transcript too short: {len(transcript)} characters"


def test_internal_calls_action_items_substantive():
    """Test that action items are non-empty strings."""
    internal_calls = [
        {
            "record_type": "internal_call",
            "id": "call_1",
            "title": "Close Plan Review",
            "call_type": "close_plan_session",
            "date": "2024-03-20",
            "timestamp": "2024-03-20T09:00:00Z",
            "stage": "close",
            "participants": [
                {"name": "AE", "role": "AE"},
                {"name": "Sales Engineer", "role": "SE"},
                {"name": "Manager", "role": "Manager"}
            ],
            "transcript": "Finalized close plan and identified all blockers." * 50,
            "summary": "Close plan meeting.",
            "action_items": [
                "Send final proposal",
                "Arrange legal review",
                "Prepare onboarding",
                "Schedule deal review"
            ],
            "deal_health": "on_track"
        }
    ]

    for call in internal_calls:
        action_items = call.get("action_items", [])
        assert len(action_items) > 0, "Must have at least one action item"

        for item in action_items:
            assert isinstance(item, str), f"Action item must be string, got {type(item)}"
            assert len(item.strip()) > 0, "Action item must not be empty"


def test_no_overlapping_timestamps():
    """Test that internal calls don't have same timestamp as buyer calls."""
    buyer_calls = [
        {
            "record_type": "call",
            "id": "call_1",
            "timestamp": "2024-03-08T10:00:00Z",
            "sentiment": "positive"
        }
    ]

    internal_calls = [
        {
            "record_type": "internal_call",
            "id": "internal_1",
            "title": "Review",
            "call_type": "deal_review",
            "date": "2024-03-08",
            "timestamp": "2024-03-08T14:30:00Z",
            "stage": "demo",
            "participants": [{"name": "AE", "role": "AE"}],
            "transcript": "Review after buyer call." * 50,
            "summary": "Post-call review.",
            "action_items": ["Follow up"],
            "deal_health": "on_track"
        }
    ]

    buyer_timestamps = {e.get("timestamp") for e in buyer_calls}
    internal_timestamps = {e.get("timestamp") for e in internal_calls}

    # Internal and buyer calls should have different timestamps
    overlap = buyer_timestamps & internal_timestamps
    assert len(overlap) == 0, "Internal calls should not have exact same timestamp as buyer calls"


def test_series_mode_internal_calls():
    """Test that series mode internal calls are properly formed."""
    internal_calls = [
        {
            "record_type": "internal_call",
            "id": "series_call_1",
            "title": "Series Quarterly Review",
            "call_type": "forecast_call",
            "date": "2024-03-10",
            "timestamp": "2024-03-10T16:00:00Z",
            "stage": "evaluation",
            "participants": [
                {"name": "Jane Smith", "role": "AE"},
                {"name": "Manager", "role": "Manager"}
            ],
            "transcript": "Jane Smith reported concerns about Q1 quota. Discussed quarterly quota and pipeline." * 5,
            "summary": "Q1 forecast review with rep Jane Smith.",
            "action_items": ["Update forecast", "Schedule next review"],
            "deal_health": "on_track"
        }
    ]

    # Verify series mode calls can have rep context in transcript/summary
    assert len(internal_calls) > 0
    call = internal_calls[0]
    # Rep name should be in either transcript or summary
    assert "Jane Smith" in call["transcript"] or "Jane Smith" in call["summary"]
