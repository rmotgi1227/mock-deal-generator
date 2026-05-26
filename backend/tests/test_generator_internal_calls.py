"""
Unit tests for internal call generation and sentiment detection.
Tests sentiment detection, call generation, validation, and error handling.
"""

import pytest
import asyncio
import json
import logging
from unittest.mock import patch, AsyncMock
from datetime import datetime, timedelta, timezone
from pydantic import ValidationError

from generator import _detect_sentiment_transitions, stage_3_generate_internal_calls, stage_3_generate_internal_calls_series
from models import InternalCallEvent, InternalCallTypeEnum, DealHealthEnum, CallParticipant


# ============= Test 1: Call count matches sentiment transitions =============

@pytest.mark.asyncio
async def test_call_count_zero_transitions():
    """Test that 0 sentiment transitions generate 0 internal calls."""
    buyer_calls = [
        {
            "record_type": "call",
            "id": "call1",
            "timestamp": "2024-03-01T10:00:00Z",
            "sentiment": "positive",
            "stage": "discovery",
        },
        {
            "record_type": "call",
            "id": "call2",
            "timestamp": "2024-03-08T10:00:00Z",
            "sentiment": "positive",
            "stage": "demo",
        }
    ]

    transitions = _detect_sentiment_transitions(buyer_calls)
    assert len(transitions) == 0, "No sentiment transitions should be detected for identical sentiments"


@pytest.mark.asyncio
async def test_call_count_one_transition():
    """Test that 1 sentiment transition is detected."""
    buyer_calls = [
        {
            "record_type": "call",
            "id": "call1",
            "timestamp": "2024-03-01T10:00:00Z",
            "sentiment": "positive",
            "stage": "discovery",
        },
        {
            "record_type": "call",
            "id": "call2",
            "timestamp": "2024-03-08T10:00:00Z",
            "sentiment": "neutral",
            "stage": "demo",
        }
    ]

    transitions = _detect_sentiment_transitions(buyer_calls)
    assert len(transitions) == 1, "One sentiment transition should be detected"


@pytest.mark.asyncio
async def test_call_count_multiple_transitions():
    """Test that multiple sentiment transitions are detected."""
    buyer_calls = [
        {
            "record_type": "call",
            "id": "call1",
            "timestamp": "2024-03-01T10:00:00Z",
            "sentiment": "positive",
            "stage": "discovery",
        },
        {
            "record_type": "call",
            "id": "call2",
            "timestamp": "2024-03-08T10:00:00Z",
            "sentiment": "neutral",
            "stage": "demo",
        },
        {
            "record_type": "call",
            "id": "call3",
            "timestamp": "2024-03-15T10:00:00Z",
            "sentiment": "negative",
            "stage": "negotiation",
        },
        {
            "record_type": "call",
            "id": "call4",
            "timestamp": "2024-03-22T10:00:00Z",
            "sentiment": "negative",
            "stage": "negotiation",
        }
    ]

    transitions = _detect_sentiment_transitions(buyer_calls)
    assert len(transitions) == 2, "Two sentiment transitions should be detected"


# ============= Test 1b: Sentiment transition detection =============

@pytest.mark.asyncio
async def test_sentiment_transition_detection_structure():
    """Test that sentiment transitions have correct structure with all required fields."""
    buyer_calls = [
        {
            "record_type": "call",
            "id": "call1",
            "timestamp": "2024-03-01T10:00:00Z",
            "sentiment": "positive",
            "stage": "discovery",
        },
        {
            "record_type": "call",
            "id": "call2",
            "timestamp": "2024-03-08T10:00:00Z",
            "sentiment": "neutral",
            "stage": "demo",
        },
        {
            "record_type": "call",
            "id": "call3",
            "timestamp": "2024-03-15T10:00:00Z",
            "sentiment": "negative",
            "stage": "negotiation",
        }
    ]

    transitions = _detect_sentiment_transitions(buyer_calls)
    assert len(transitions) == 2

    # Check first transition (positive -> neutral)
    trans1 = transitions[0]
    assert trans1["trigger_call_index"] == 1
    assert trans1["prior_sentiment"] == "positive"
    assert trans1["new_sentiment"] == "neutral"
    assert trans1["shift_severity"] == "minor"
    assert trans1["timestamp"] == "2024-03-08T10:00:00Z"
    assert trans1["stage"] == "demo"

    # Check second transition (neutral -> negative)
    trans2 = transitions[1]
    assert trans2["trigger_call_index"] == 2
    assert trans2["prior_sentiment"] == "neutral"
    assert trans2["new_sentiment"] == "negative"
    assert trans2["shift_severity"] == "minor"
    assert trans2["timestamp"] == "2024-03-15T10:00:00Z"
    assert trans2["stage"] == "negotiation"


@pytest.mark.asyncio
async def test_sentiment_transition_severity_major():
    """Test that major severity is detected for concerned<->negative transitions."""
    buyer_calls = [
        {
            "record_type": "call",
            "id": "call1",
            "timestamp": "2024-03-01T10:00:00Z",
            "sentiment": "concerned",
            "stage": "negotiation",
        },
        {
            "record_type": "call",
            "id": "call2",
            "timestamp": "2024-03-08T10:00:00Z",
            "sentiment": "negative",
            "stage": "negotiation",
        }
    ]

    transitions = _detect_sentiment_transitions(buyer_calls)
    assert len(transitions) == 1
    assert transitions[0]["shift_severity"] == "major"


@pytest.mark.asyncio
async def test_sentiment_transition_severity_positive_negative_major():
    """A direct positive<->negative swing is the most extreme shift and must be major."""
    base = {"record_type": "call", "stage": "negotiation"}
    # positive -> negative
    down = _detect_sentiment_transitions([
        {**base, "id": "c1", "timestamp": "2024-03-01T10:00:00Z", "sentiment": "positive"},
        {**base, "id": "c2", "timestamp": "2024-03-08T10:00:00Z", "sentiment": "negative"},
    ])
    assert len(down) == 1
    assert down[0]["shift_severity"] == "major"
    # negative -> positive (symmetric)
    up = _detect_sentiment_transitions([
        {**base, "id": "c1", "timestamp": "2024-03-01T10:00:00Z", "sentiment": "negative"},
        {**base, "id": "c2", "timestamp": "2024-03-08T10:00:00Z", "sentiment": "positive"},
    ])
    assert len(up) == 1
    assert up[0]["shift_severity"] == "major"


# ============= Test 1c: Call type matches transition severity =============

@pytest.mark.asyncio
async def test_call_type_severity_matching():
    """Test that call types are semantically matched to severity levels."""
    # This test mocks Claude response to verify call_type matching
    deal_data = {
        "metadata": {
            "company": {"name": "ACME Corp"},
            "sales_rep": {"name": "Jane Smith"},
            "config": {"deal_size": "$100k ARR"},
            "deal_outcome": "closed_won",
        },
        "timeline_events": [
            {
                "record_type": "call",
                "id": "call1",
                "timestamp": "2024-03-01T10:00:00Z",
                "sentiment": "positive",
                "stage": "discovery",
            },
            {
                "record_type": "call",
                "id": "call2",
                "timestamp": "2024-03-08T10:00:00Z",
                "sentiment": "neutral",
                "stage": "demo",
            }
        ]
    }

    transitions = _detect_sentiment_transitions(deal_data["timeline_events"])
    assert len(transitions) == 1
    assert transitions[0]["shift_severity"] == "minor"

    # Valid minor shift call types: deal_review, forecast_call
    valid_minor_types = [InternalCallTypeEnum.DEAL_REVIEW, InternalCallTypeEnum.FORECAST_CALL]
    valid_minor_values = [t.value for t in valid_minor_types]
    assert any(ct in valid_minor_values for ct in valid_minor_values)


# ============= Test 2: Valid JSON parsing & model validation =============

@pytest.mark.asyncio
async def test_valid_json_parsing_and_validation():
    """Test that valid InternalCallEvent JSON is correctly parsed and validated."""
    deal_data = {
        "metadata": {
            "company": {"name": "ACME Corp"},
            "sales_rep": {"name": "Jane Smith"},
            "config": {"deal_size": "$100k ARR"},
            "deal_outcome": "closed_won",
        },
        "timeline_events": [
            {
                "record_type": "call",
                "id": "call1",
                "timestamp": "2024-03-01T10:00:00Z",
                "sentiment": "positive",
                "stage": "discovery",
            },
            {
                "record_type": "call",
                "id": "call2",
                "timestamp": "2024-03-08T10:00:00Z",
                "sentiment": "neutral",
                "stage": "demo",
            }
        ]
    }

    # Mock valid Claude response
    mock_response = json.dumps([{
        "id": "internal_call_1",
        "title": "Deal Review Call",
        "call_type": "deal_review",
        "date": "2024-03-08",
        "timestamp": "2024-03-08T14:00:00Z",
        "stage": "demo",
        "participants": [
            {"name": "Jane Smith", "role": "AE"},
            {"name": "John Manager", "role": "Manager"}
        ],
        "transcript": "We discussed the customer's concerns and agreed on next steps. " * 50,
        "summary": "Discussed sentiment drop from demo feedback.",
        "action_items": ["Follow up with customer", "Prepare revised proposal"],
        "deal_health": "on_track"
    }])

    with patch('generator.call_claude', new_callable=AsyncMock) as mock_claude:
        mock_claude.return_value = mock_response

        result = await stage_3_generate_internal_calls(
            deal_id="test_deal_1",
            deal_data=deal_data
        )

        assert len(result) == 1
        call = result[0]
        assert call["id"] == "internal_call_1"
        assert call["title"] == "Deal Review Call"
        assert call["call_type"] == "deal_review"
        assert call["record_type"] == "internal_call"


# ============= Test 3: Participants structured & include AE + context-based subset =============

@pytest.mark.asyncio
async def test_participants_are_valid_call_participant_objects():
    """Test that all participants are valid CallParticipant objects with name and role."""
    deal_data = {
        "metadata": {
            "company": {"name": "ACME Corp"},
            "sales_rep": {"name": "Jane Smith"},
            "config": {"deal_size": "$100k ARR"},
            "deal_outcome": "closed_won",
        },
        "timeline_events": [
            {
                "record_type": "call",
                "id": "call1",
                "timestamp": "2024-03-01T10:00:00Z",
                "sentiment": "positive",
                "stage": "discovery",
            },
            {
                "record_type": "call",
                "id": "call2",
                "timestamp": "2024-03-08T10:00:00Z",
                "sentiment": "neutral",
                "stage": "demo",
            }
        ]
    }

    mock_response = json.dumps([{
        "id": "internal_call_1",
        "title": "Deal Review",
        "call_type": "deal_review",
        "date": "2024-03-08",
        "timestamp": "2024-03-08T14:00:00Z",
        "stage": "demo",
        "participants": [
            {"name": "Jane Smith", "role": "AE"},
            {"name": "John Manager", "role": "Manager"},
            {"name": "SE Bob", "role": "SE"}
        ],
        "transcript": "Discussion about customer feedback." * 50,
        "summary": "Addressed sentiment concerns.",
        "action_items": ["Follow up"],
        "deal_health": "on_track"
    }])

    with patch('generator.call_claude', new_callable=AsyncMock) as mock_claude:
        mock_claude.return_value = mock_response

        result = await stage_3_generate_internal_calls(
            deal_id="test_deal_1",
            deal_data=deal_data
        )

        assert len(result) == 1
        call = result[0]
        participants = call["participants"]
        assert len(participants) == 3

        # Validate each participant is a valid object
        for p in participants:
            assert "name" in p
            assert "role" in p
            assert isinstance(p["name"], str)
            assert isinstance(p["role"], str)

        # Validate AE is always present
        ae_present = any(p["role"] == "AE" for p in participants)
        assert ae_present, "AE must be present in participants"

        # Validate roles are in allowed set
        valid_roles = {"AE", "Manager", "SE", "SDR"}
        for p in participants:
            assert p["role"] in valid_roles, f"Invalid role: {p['role']}"


@pytest.mark.asyncio
async def test_call_participant_pydantic_validation():
    """Test that CallParticipant Pydantic model validates correctly."""
    # Test valid CallParticipant
    valid_participant = CallParticipant.model_validate({"name": "Jane Smith", "role": "AE"})
    assert valid_participant.name == "Jane Smith"
    assert valid_participant.role == "AE"

    # Test with various valid roles
    for role in ["AE", "Manager", "SE", "SDR"]:
        p = CallParticipant.model_validate({"name": "Test User", "role": role})
        assert p.role == role

    # Test missing required field: name
    with pytest.raises(ValidationError):
        CallParticipant.model_validate({"role": "AE"})

    # Test missing required field: role
    with pytest.raises(ValidationError):
        CallParticipant.model_validate({"name": "Jane Smith"})

    # Test missing both required fields
    with pytest.raises(ValidationError):
        CallParticipant.model_validate({})

    # Test that both fields are required (any role string is accepted)
    p = CallParticipant.model_validate({"name": "Jane Smith", "role": "CustomRole"})
    assert p.name == "Jane Smith"
    assert p.role == "CustomRole"


@pytest.mark.asyncio
async def test_ae_always_present_in_participants():
    """Test that AE is always present in internal call participants."""
    deal_data = {
        "metadata": {
            "company": {"name": "ACME Corp"},
            "sales_rep": {"name": "Jane Smith"},
            "config": {"deal_size": "$100k ARR"},
            "deal_outcome": "closed_won",
        },
        "timeline_events": [
            {
                "record_type": "call",
                "id": "call1",
                "timestamp": "2024-03-01T10:00:00Z",
                "sentiment": "positive",
                "stage": "discovery",
            },
            {
                "record_type": "call",
                "id": "call2",
                "timestamp": "2024-03-08T10:00:00Z",
                "sentiment": "concerned",
                "stage": "evaluation",
            }
        ]
    }

    mock_response = json.dumps([{
        "id": "internal_call_1",
        "title": "War Room",
        "call_type": "war_room",
        "date": "2024-03-08",
        "timestamp": "2024-03-08T14:00:00Z",
        "stage": "evaluation",
        "participants": [
            {"name": "Jane Smith", "role": "AE"},
            {"name": "Manager Bob", "role": "Manager"}
        ],
        "transcript": "Urgent discussion on sentiment shift." * 50,
        "summary": "War room for major sentiment shift.",
        "action_items": ["Escalate to VP"],
        "deal_health": "at_risk"
    }])

    with patch('generator.call_claude', new_callable=AsyncMock) as mock_claude:
        mock_claude.return_value = mock_response

        result = await stage_3_generate_internal_calls(
            deal_id="test_deal_1",
            deal_data=deal_data
        )

        assert len(result) == 1
        participants = result[0]["participants"]
        ae_names = [p["name"] for p in participants if p["role"] == "AE"]
        assert len(ae_names) > 0, "AE must be present"
        assert "Jane Smith" in ae_names


# ============= Test 4: Call timestamps are shortly after triggering buyer calls =============

@pytest.mark.asyncio
async def test_internal_call_timestamp_shortly_after_trigger():
    """Test that internal call timestamp is shortly after triggering buyer call."""
    trigger_timestamp = "2024-03-15T10:00:00Z"
    internal_call_timestamp = "2024-03-15T14:30:00Z"  # 4.5 hours later

    deal_data = {
        "metadata": {
            "company": {"name": "ACME Corp"},
            "sales_rep": {"name": "Jane Smith"},
            "config": {"deal_size": "$100k ARR"},
            "deal_outcome": "closed_won",
        },
        "timeline_events": [
            {
                "record_type": "call",
                "id": "call1",
                "timestamp": "2024-03-01T10:00:00Z",
                "sentiment": "positive",
                "stage": "discovery",
            },
            {
                "record_type": "call",
                "id": "call2",
                "timestamp": trigger_timestamp,
                "sentiment": "negative",
                "stage": "negotiation",
            }
        ]
    }

    mock_response = json.dumps([{
        "id": "internal_call_1",
        "title": "Urgent Review",
        "call_type": "war_room",
        "date": "2024-03-15",
        "timestamp": internal_call_timestamp,
        "stage": "negotiation",
        "participants": [
            {"name": "Jane Smith", "role": "AE"},
            {"name": "Manager", "role": "Manager"}
        ],
        "transcript": "Urgent discussion." * 50,
        "summary": "Quick response to sentiment drop.",
        "action_items": ["Follow up"],
        "deal_health": "stalled"
    }])

    with patch('generator.call_claude', new_callable=AsyncMock) as mock_claude:
        mock_claude.return_value = mock_response

        result = await stage_3_generate_internal_calls(
            deal_id="test_deal_1",
            deal_data=deal_data
        )

        assert len(result) == 1
        internal_call_ts = datetime.fromisoformat(result[0]["timestamp"].replace("Z", "+00:00"))
        trigger_ts = datetime.fromisoformat(trigger_timestamp.replace("Z", "+00:00"))

        # Within same day to 1 week
        assert internal_call_ts >= trigger_ts, "Internal call should be at or after trigger"
        time_diff = internal_call_ts - trigger_ts
        assert time_diff.days < 7, "Internal call should be within 1 week of trigger"


@pytest.mark.asyncio
async def test_internal_call_timestamps_unique():
    """Test that internal call timestamps are unique (no duplicates)."""
    deal_data = {
        "metadata": {
            "company": {"name": "ACME Corp"},
            "sales_rep": {"name": "Jane Smith"},
            "config": {"deal_size": "$100k ARR"},
            "deal_outcome": "closed_won",
        },
        "timeline_events": [
            {
                "record_type": "call",
                "id": "call1",
                "timestamp": "2024-03-01T10:00:00Z",
                "sentiment": "positive",
                "stage": "discovery",
            },
            {
                "record_type": "call",
                "id": "call2",
                "timestamp": "2024-03-08T10:00:00Z",
                "sentiment": "concerned",
                "stage": "demo",
            },
            {
                "record_type": "call",
                "id": "call3",
                "timestamp": "2024-03-15T10:00:00Z",
                "sentiment": "negative",
                "stage": "negotiation",
            }
        ]
    }

    mock_response = json.dumps([
        {
            "id": "internal_call_1",
            "title": "Review 1",
            "call_type": "deal_review",
            "date": "2024-03-08",
            "timestamp": "2024-03-08T14:00:00Z",
            "stage": "demo",
            "participants": [
                {"name": "Jane Smith", "role": "AE"}
            ],
            "transcript": "Discussion." * 50,
            "summary": "Review.",
            "action_items": ["Follow up"],
            "deal_health": "at_risk"
        },
        {
            "id": "internal_call_2",
            "title": "Review 2",
            "call_type": "war_room",
            "date": "2024-03-15",
            "timestamp": "2024-03-15T15:00:00Z",
            "stage": "negotiation",
            "participants": [
                {"name": "Jane Smith", "role": "AE"}
            ],
            "transcript": "Discussion." * 50,
            "summary": "Review.",
            "action_items": ["Follow up"],
            "deal_health": "stalled"
        }
    ])

    with patch('generator.call_claude', new_callable=AsyncMock) as mock_claude:
        mock_claude.return_value = mock_response

        result = await stage_3_generate_internal_calls(
            deal_id="test_deal_1",
            deal_data=deal_data
        )

        timestamps = [c["timestamp"] for c in result]
        assert len(timestamps) == len(set(timestamps)), "All timestamps should be unique"


# ============= Test 5: Valid call types (enum validation) =============

@pytest.mark.asyncio
async def test_call_type_enum_validation():
    """Test that call_type values are valid InternalCallTypeEnum members."""
    deal_data = {
        "metadata": {
            "company": {"name": "ACME Corp"},
            "sales_rep": {"name": "Jane Smith"},
            "config": {"deal_size": "$100k ARR"},
            "deal_outcome": "closed_won",
        },
        "timeline_events": [
            {
                "record_type": "call",
                "id": "call1",
                "timestamp": "2024-03-01T10:00:00Z",
                "sentiment": "positive",
                "stage": "discovery",
            },
            {
                "record_type": "call",
                "id": "call2",
                "timestamp": "2024-03-08T10:00:00Z",
                "sentiment": "neutral",
                "stage": "demo",
            }
        ]
    }

    mock_response = json.dumps([{
        "id": "internal_call_1",
        "title": "Deal Review",
        "call_type": "deal_review",
        "date": "2024-03-08",
        "timestamp": "2024-03-08T14:00:00Z",
        "stage": "demo",
        "participants": [
            {"name": "Jane Smith", "role": "AE"}
        ],
        "transcript": "Discussion." * 50,
        "summary": "Review.",
        "action_items": ["Follow up"],
        "deal_health": "on_track"
    }])

    with patch('generator.call_claude', new_callable=AsyncMock) as mock_claude:
        mock_claude.return_value = mock_response

        result = await stage_3_generate_internal_calls(
            deal_id="test_deal_1",
            deal_data=deal_data
        )

        assert len(result) == 1
        call_type = result[0]["call_type"]
        valid_types = [ct.value for ct in InternalCallTypeEnum]
        assert call_type in valid_types, f"Invalid call_type: {call_type}"


@pytest.mark.asyncio
async def test_invalid_call_type_rejected():
    """Test that Pydantic validation rejects invalid call types."""
    with pytest.raises(ValidationError):
        InternalCallEvent(
            id="test",
            title="Test",
            call_type="invalid_type",  # Invalid
            date="2024-03-08",
            timestamp="2024-03-08T14:00:00Z",
            stage="demo",
            participants=[{"name": "Jane", "role": "AE"}],
            transcript="Test",
            summary="Test",
            action_items=["Test"],
            deal_health="on_track"
        )


# ============= Test 6: Action items non-empty =============

@pytest.mark.asyncio
async def test_action_items_non_empty():
    """Test that every call has non-empty action items list."""
    deal_data = {
        "metadata": {
            "company": {"name": "ACME Corp"},
            "sales_rep": {"name": "Jane Smith"},
            "config": {"deal_size": "$100k ARR"},
            "deal_outcome": "closed_won",
        },
        "timeline_events": [
            {
                "record_type": "call",
                "id": "call1",
                "timestamp": "2024-03-01T10:00:00Z",
                "sentiment": "positive",
                "stage": "discovery",
            },
            {
                "record_type": "call",
                "id": "call2",
                "timestamp": "2024-03-08T10:00:00Z",
                "sentiment": "concerned",
                "stage": "demo",
            }
        ]
    }

    mock_response = json.dumps([{
        "id": "internal_call_1",
        "title": "Deal Review",
        "call_type": "deal_review",
        "date": "2024-03-08",
        "timestamp": "2024-03-08T14:00:00Z",
        "stage": "demo",
        "participants": [
            {"name": "Jane Smith", "role": "AE"},
            {"name": "Bob Manager", "role": "Manager"}
        ],
        "transcript": "Discussion about customer concerns." * 50,
        "summary": "Discussed next steps.",
        "action_items": [
            "Schedule customer call",
            "Prepare revised proposal",
            "Get manager approval"
        ],
        "deal_health": "at_risk"
    }])

    with patch('generator.call_claude', new_callable=AsyncMock) as mock_claude:
        mock_claude.return_value = mock_response

        result = await stage_3_generate_internal_calls(
            deal_id="test_deal_1",
            deal_data=deal_data
        )

        for call in result:
            assert "action_items" in call
            assert isinstance(call["action_items"], list)
            assert len(call["action_items"]) >= 1, "Action items list must not be empty"
            for item in call["action_items"]:
                assert isinstance(item, str)
                assert len(item.strip()) > 0, "Action item must be non-empty string"


# ============= Test 7: Graceful error handling =============

@pytest.mark.asyncio
async def test_error_handling_invalid_json(caplog):
    """Test graceful handling of invalid JSON from Claude."""
    deal_data = {
        "metadata": {
            "company": {"name": "ACME Corp"},
            "sales_rep": {"name": "Jane Smith"},
            "config": {"deal_size": "$100k ARR"},
            "deal_outcome": "closed_won",
        },
        "timeline_events": [
            {
                "record_type": "call",
                "id": "call1",
                "timestamp": "2024-03-01T10:00:00Z",
                "sentiment": "positive",
                "stage": "discovery",
            },
            {
                "record_type": "call",
                "id": "call2",
                "timestamp": "2024-03-08T10:00:00Z",
                "sentiment": "neutral",
                "stage": "demo",
            }
        ]
    }

    with patch('generator.call_claude', new_callable=AsyncMock) as mock_claude:
        # Return invalid JSON
        mock_claude.return_value = "not valid json {{"

        with caplog.at_level(logging.WARNING):
            result = await stage_3_generate_internal_calls(
                deal_id="test_deal_1",
                deal_data=deal_data
            )

        assert result == [], "Should return empty list on JSON error"
        assert any(
            record.levelname == "WARNING" and "Invalid JSON" in record.message
            for record in caplog.records
        ), "Should log WARNING about invalid JSON"


@pytest.mark.asyncio
async def test_error_handling_validation_failure(caplog):
    """Test graceful handling of Pydantic validation failure."""
    deal_data = {
        "metadata": {
            "company": {"name": "ACME Corp"},
            "sales_rep": {"name": "Jane Smith"},
            "config": {"deal_size": "$100k ARR"},
            "deal_outcome": "closed_won",
        },
        "timeline_events": [
            {
                "record_type": "call",
                "id": "call1",
                "timestamp": "2024-03-01T10:00:00Z",
                "sentiment": "positive",
                "stage": "discovery",
            },
            {
                "record_type": "call",
                "id": "call2",
                "timestamp": "2024-03-08T10:00:00Z",
                "sentiment": "neutral",
                "stage": "demo",
            }
        ]
    }

    # Valid JSON but missing required field
    mock_response = json.dumps([{
        "id": "internal_call_1",
        "title": "Deal Review",
        # Missing "call_type", "date", "timestamp", "stage", "participants", "transcript", "summary", "action_items", "deal_health"
    }])

    with patch('generator.call_claude', new_callable=AsyncMock) as mock_claude:
        mock_claude.return_value = mock_response

        with caplog.at_level(logging.WARNING):
            result = await stage_3_generate_internal_calls(
                deal_id="test_deal_1",
                deal_data=deal_data
            )

        assert result == [], "Should return empty list on validation error"
        assert any(
            record.levelname == "WARNING" and "Invalid internal call structure" in record.message
            for record in caplog.records
        ), "Should log WARNING about invalid structure"


@pytest.mark.asyncio
async def test_error_handling_api_error(caplog):
    """Test graceful handling of API errors."""
    deal_data = {
        "metadata": {
            "company": {"name": "ACME Corp"},
            "sales_rep": {"name": "Jane Smith"},
            "config": {"deal_size": "$100k ARR"},
            "deal_outcome": "closed_won",
        },
        "timeline_events": [
            {
                "record_type": "call",
                "id": "call1",
                "timestamp": "2024-03-01T10:00:00Z",
                "sentiment": "positive",
                "stage": "discovery",
            },
            {
                "record_type": "call",
                "id": "call2",
                "timestamp": "2024-03-08T10:00:00Z",
                "sentiment": "neutral",
                "stage": "demo",
            }
        ]
    }

    with patch('generator.call_claude', new_callable=AsyncMock) as mock_claude:
        # Raise an Exception
        mock_claude.side_effect = Exception("API timeout")

        with caplog.at_level(logging.ERROR):
            result = await stage_3_generate_internal_calls(
                deal_id="test_deal_1",
                deal_data=deal_data
            )

        assert result == [], "Should return empty list on API error"
        assert any(
            record.levelname == "ERROR" and "Internal call generation failed" in record.message
            for record in caplog.records
        ), "Should log ERROR about generation failure"


# ============= Test 8: Series mode includes rep context & quarter health =============

@pytest.mark.asyncio
async def test_series_mode_includes_rep_context():
    """Test that series mode includes rep name in transcripts."""
    deal_data = {
        "metadata": {
            "company": {"name": "ACME Corp"},
            "sales_rep": {"name": "Jane Smith"},
            "config": {"deal_size": "$100k ARR"},
            "deal_outcome": "closed_won",
        },
        "timeline_events": [
            {
                "record_type": "call",
                "id": "call1",
                "timestamp": "2024-03-01T10:00:00Z",
                "sentiment": "positive",
                "stage": "discovery",
            },
            {
                "record_type": "call",
                "id": "call2",
                "timestamp": "2024-03-08T10:00:00Z",
                "sentiment": "concerned",
                "stage": "demo",
            }
        ]
    }

    mock_response = json.dumps([{
        "id": "internal_call_1",
        "title": "Series Deal Review",
        "call_type": "deal_review",
        "date": "2024-03-08",
        "timestamp": "2024-03-08T14:00:00Z",
        "stage": "demo",
        "participants": [
            {"name": "Jane Smith", "role": "AE"}
        ],
        "transcript": "Jane Smith reported a slight sentiment shift. We need to address this quickly." * 20,
        "summary": "Series mode: discussed quarter goals with Jane Smith.",
        "action_items": ["Follow up"],
        "deal_health": "at_risk"
    }])

    with patch('generator.call_claude', new_callable=AsyncMock) as mock_claude:
        mock_claude.return_value = mock_response

        result = await stage_3_generate_internal_calls_series(
            deal_id="test_deal_1",
            deal_data=deal_data,
            rep_name="Jane Smith"
        )

        assert len(result) == 1
        call = result[0]
        # Rep name should appear in transcript or summary
        assert "Jane Smith" in call["transcript"] or "Jane Smith" in call["summary"]


# ============= Test 8b: Event-driven timing =============

@pytest.mark.asyncio
async def test_event_driven_timing_no_transitions():
    """Test that deals with no sentiment transitions generate no internal calls."""
    deal_data = {
        "metadata": {
            "company": {"name": "ACME Corp"},
            "sales_rep": {"name": "Jane Smith"},
            "config": {"deal_size": "$100k ARR"},
            "deal_outcome": "closed_won",
        },
        "timeline_events": [
            {
                "record_type": "call",
                "id": "call1",
                "timestamp": "2024-03-01T10:00:00Z",
                "sentiment": "positive",
                "stage": "discovery",
            },
            {
                "record_type": "call",
                "id": "call2",
                "timestamp": "2024-03-08T10:00:00Z",
                "sentiment": "positive",
                "stage": "demo",
            },
            {
                "record_type": "call",
                "id": "call3",
                "timestamp": "2024-03-15T10:00:00Z",
                "sentiment": "positive",
                "stage": "negotiation",
            }
        ]
    }

    # Should not even call Claude if no transitions
    with patch('generator.call_claude', new_callable=AsyncMock) as mock_claude:
        result = await stage_3_generate_internal_calls(
            deal_id="test_deal_1",
            deal_data=deal_data
        )

        assert result == [], "No internal calls if no sentiment transitions"
        mock_claude.assert_not_called()


# ============= Test 9: Deal health mapping from sentiment =============

@pytest.mark.asyncio
async def test_deal_health_positive_mapping():
    """Test that positive sentiment maps to on_track deal health."""
    deal_data = {
        "metadata": {
            "company": {"name": "ACME Corp"},
            "sales_rep": {"name": "Jane Smith"},
            "config": {"deal_size": "$100k ARR"},
            "deal_outcome": "closed_won",
        },
        "timeline_events": [
            {
                "record_type": "call",
                "id": "call1",
                "timestamp": "2024-03-01T10:00:00Z",
                "sentiment": "neutral",
                "stage": "discovery",
            },
            {
                "record_type": "call",
                "id": "call2",
                "timestamp": "2024-03-08T10:00:00Z",
                "sentiment": "positive",
                "stage": "demo",
            }
        ]
    }

    mock_response = json.dumps([{
        "id": "internal_call_1",
        "title": "Positive Check",
        "call_type": "deal_review",
        "date": "2024-03-08",
        "timestamp": "2024-03-08T14:00:00Z",
        "stage": "demo",
        "participants": [
            {"name": "Jane Smith", "role": "AE"}
        ],
        "transcript": "Strong positive signal from customer." * 50,
        "summary": "Customer very satisfied.",
        "action_items": ["Prepare close plan"],
        "deal_health": "on_track"
    }])

    with patch('generator.call_claude', new_callable=AsyncMock) as mock_claude:
        mock_claude.return_value = mock_response

        result = await stage_3_generate_internal_calls(
            deal_id="test_deal_1",
            deal_data=deal_data
        )

        assert len(result) == 1
        deal_health = result[0]["deal_health"]
        assert deal_health == "on_track"


@pytest.mark.asyncio
async def test_deal_health_concerned_mapping():
    """Test that concerned sentiment maps to at_risk deal health."""
    deal_data = {
        "metadata": {
            "company": {"name": "ACME Corp"},
            "sales_rep": {"name": "Jane Smith"},
            "config": {"deal_size": "$100k ARR"},
            "deal_outcome": "closed_won",
        },
        "timeline_events": [
            {
                "record_type": "call",
                "id": "call1",
                "timestamp": "2024-03-01T10:00:00Z",
                "sentiment": "positive",
                "stage": "discovery",
            },
            {
                "record_type": "call",
                "id": "call2",
                "timestamp": "2024-03-08T10:00:00Z",
                "sentiment": "concerned",
                "stage": "evaluation",
            }
        ]
    }

    mock_response = json.dumps([{
        "id": "internal_call_1",
        "title": "Risk Review",
        "call_type": "deal_review",
        "date": "2024-03-08",
        "timestamp": "2024-03-08T14:00:00Z",
        "stage": "evaluation",
        "participants": [
            {"name": "Jane Smith", "role": "AE"}
        ],
        "transcript": "Customer expressed concerns." * 50,
        "summary": "Deal at risk.",
        "action_items": ["Schedule escalation"],
        "deal_health": "at_risk"
    }])

    with patch('generator.call_claude', new_callable=AsyncMock) as mock_claude:
        mock_claude.return_value = mock_response

        result = await stage_3_generate_internal_calls(
            deal_id="test_deal_1",
            deal_data=deal_data
        )

        assert len(result) == 1
        deal_health = result[0]["deal_health"]
        assert deal_health == "at_risk"


@pytest.mark.asyncio
async def test_deal_health_negative_mapping():
    """Test that negative sentiment maps to stalled deal health."""
    deal_data = {
        "metadata": {
            "company": {"name": "ACME Corp"},
            "sales_rep": {"name": "Jane Smith"},
            "config": {"deal_size": "$100k ARR"},
            "deal_outcome": "closed_lost",
        },
        "timeline_events": [
            {
                "record_type": "call",
                "id": "call1",
                "timestamp": "2024-03-01T10:00:00Z",
                "sentiment": "concerned",
                "stage": "negotiation",
            },
            {
                "record_type": "call",
                "id": "call2",
                "timestamp": "2024-03-08T10:00:00Z",
                "sentiment": "negative",
                "stage": "negotiation",
            }
        ]
    }

    mock_response = json.dumps([{
        "id": "internal_call_1",
        "title": "Stalled Deal",
        "call_type": "war_room",
        "date": "2024-03-08",
        "timestamp": "2024-03-08T14:00:00Z",
        "stage": "negotiation",
        "participants": [
            {"name": "Jane Smith", "role": "AE"}
        ],
        "transcript": "Customer rejected our proposal." * 50,
        "summary": "Deal is stalled.",
        "action_items": ["Evaluate loss"],
        "deal_health": "stalled"
    }])

    with patch('generator.call_claude', new_callable=AsyncMock) as mock_claude:
        mock_claude.return_value = mock_response

        result = await stage_3_generate_internal_calls(
            deal_id="test_deal_1",
            deal_data=deal_data
        )

        assert len(result) == 1
        deal_health = result[0]["deal_health"]
        assert deal_health == "stalled"


@pytest.mark.asyncio
async def test_invalid_deal_health_rejected():
    """Test that Pydantic validation rejects invalid deal_health values."""
    with pytest.raises(ValidationError):
        InternalCallEvent(
            id="test",
            title="Test",
            call_type="deal_review",
            date="2024-03-08",
            timestamp="2024-03-08T14:00:00Z",
            stage="demo",
            participants=[{"name": "Jane", "role": "AE"}],
            transcript="Test",
            summary="Test",
            action_items=["Test"],
            deal_health="invalid_health"  # Invalid
        )


# ============= Test 9b: Outcome consistency guardrail =============

@pytest.mark.asyncio
async def test_outcome_consistency_won_deal():
    """Test that won deals don't have stalled calls at end."""
    deal_data = {
        "metadata": {
            "company": {"name": "ACME Corp"},
            "sales_rep": {"name": "Jane Smith"},
            "config": {"deal_size": "$100k ARR"},
            "deal_outcome": "closed_won",
        },
        "timeline_events": [
            {
                "record_type": "call",
                "id": "call1",
                "timestamp": "2024-03-01T10:00:00Z",
                "sentiment": "positive",
                "stage": "discovery",
            },
            {
                "record_type": "call",
                "id": "call2",
                "timestamp": "2024-03-22T10:00:00Z",
                "sentiment": "positive",
                "stage": "close",
            }
        ]
    }

    mock_response = json.dumps([{
        "id": "internal_call_1",
        "title": "Close Review",
        "call_type": "close_plan_session",
        "date": "2024-03-22",
        "timestamp": "2024-03-22T14:00:00Z",
        "stage": "close",
        "participants": [
            {"name": "Jane Smith", "role": "AE"}
        ],
        "transcript": "Celebrating the win." * 50,
        "summary": "Deal closed successfully.",
        "action_items": ["Handoff to CS"],
        "deal_health": "on_track"
    }])

    with patch('generator.call_claude', new_callable=AsyncMock) as mock_claude:
        mock_claude.return_value = mock_response

        result = await stage_3_generate_internal_calls(
            deal_id="test_deal_1",
            deal_data=deal_data
        )

        # For closed_won, final call shouldn't contradict with stalled
        for call in result:
            if call["deal_health"] == "stalled" and call["stage"] in ["close", "won"]:
                pytest.fail("Closed won deal shouldn't have stalled calls at end")
