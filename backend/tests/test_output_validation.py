"""
Output quality validation tests.
Ensures that reduced MAX_TOKENS_BY_TYPE allocations maintain output quality.
These tests validate that deals generated with tuned allocations still have
complete, coherent content across all record types.
"""

import sys
import os
import asyncio
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tests.fixtures import create_baseline_config
from generator import generate_complete_deal


def validate_deal_structure(result):
    """Validate that the generated deal has proper structure."""
    assert "deal" in result, "Deal object missing"
    assert "events" in result["deal"], "Events list missing"
    assert "metadata" in result["deal"], "Metadata missing"
    assert len(result["deal"]["events"]) > 0, "No events generated"
    return True


def validate_event_quality(event):
    """Validate that an event has quality content."""
    assert "record_type" in event, f"Event missing record_type: {event}"
    assert event["record_type"] in [
        "call", "email", "crm_note", "support_ticket", "support_call",
        "slack_channel", "slack_message"
    ], f"Unknown record_type: {event['record_type']}"

    # Type-specific validation
    record_type = event["record_type"]

    if record_type == "call":
        assert "call_summary" in event, "Call missing summary"
        assert len(event["call_summary"].strip()) > 50, "Call summary too short"
        assert "participants" in event, "Call missing participants"
        assert len(event.get("participants", [])) > 0, "Call missing participants list"

    elif record_type == "email":
        assert "subject" in event, "Email missing subject"
        assert "body" in event, "Email missing body"
        assert len(event["subject"].strip()) > 5, "Email subject too short"
        assert len(event["body"].strip()) > 50, "Email body too short"

    elif record_type == "crm_note":
        assert "note_text" in event, "CRM note missing text"
        assert len(event["note_text"].strip()) > 30, "CRM note too short"

    elif record_type == "support_ticket":
        assert "title" in event, "Support ticket missing title"
        assert "description" in event, "Support ticket missing description"
        assert len(event["description"].strip()) > 50, "Support ticket description too short"

    elif record_type == "support_call":
        assert "summary" in event, "Support call missing summary"
        assert len(event["summary"].strip()) > 50, "Support call summary too short"

    elif record_type == "slack_channel":
        assert "channel" in event, "Slack channel missing channel data"
        channel = event["channel"]
        assert isinstance(channel, dict), "Slack channel data must be dict"
        assert "channel_id" in channel, "Slack channel missing channel_id"
        assert "name" in channel, "Slack channel missing name"
        assert "messages" in channel, "Slack channel missing messages"
        assert isinstance(channel["messages"], list), "Slack channel messages must be list"

    elif record_type == "slack_message":
        assert "message" in event, "Slack message missing message data"
        message = event["message"]
        assert isinstance(message, dict), "Slack message data must be dict"
        assert "message_id" in message, "Slack message missing message_id"
        assert "sender" in message, "Slack message missing sender"
        assert "body" in message, "Slack message missing body"
        assert len(message["body"].strip()) > 10, "Slack message body too short"

    return True


def validate_metadata(metadata):
    """Validate that metadata is complete."""
    assert "company" in metadata, "Metadata missing company"
    assert "stakeholders" in metadata, "Metadata missing stakeholders"
    assert "sentiment_arc" in metadata, "Metadata missing sentiment_arc"
    assert "stage_progression" in metadata, "Metadata missing stage_progression"
    assert len(metadata["stakeholders"]) > 0, "No stakeholders in metadata"
    return True


async def test_simple_deal_output_quality():
    """Test that simple deals maintain quality with reduced allocations."""
    print("\n[TEST] Simple deal output quality...")

    config = create_baseline_config()
    config["complexity"] = "simple"
    config["num_calls"] = 1
    config["emails_per_stage"] = 1

    result = await generate_complete_deal(config)

    # Validate structure
    assert validate_deal_structure(result), "Deal structure invalid"

    # Validate all events
    deal = result["deal"]
    for event in deal["events"]:
        assert validate_event_quality(event), f"Event quality invalid: {event.get('record_type')}"

    # Validate metadata
    assert validate_metadata(deal["metadata"]), "Metadata quality invalid"

    print(f"  ✓ Simple deal valid: {len(deal['events'])} events")
    return True


async def test_normal_deal_output_quality():
    """Test that normal complexity deals maintain quality."""
    print("\n[TEST] Normal deal output quality...")

    config = create_baseline_config()
    config["complexity"] = "normal"
    config["num_calls"] = 3
    config["emails_per_stage"] = 2

    result = await generate_complete_deal(config)

    # Validate structure
    assert validate_deal_structure(result), "Deal structure invalid"

    # Validate all events
    deal = result["deal"]
    for event in deal["events"]:
        assert validate_event_quality(event), f"Event quality invalid: {event.get('record_type')}"

    # Validate metadata
    assert validate_metadata(deal["metadata"]), "Metadata quality invalid"

    # Check event distribution
    record_types = {}
    for event in deal["events"]:
        rt = event["record_type"]
        record_types[rt] = record_types.get(rt, 0) + 1

    assert record_types.get("call", 0) > 0, "No calls in deal"
    assert record_types.get("email", 0) > 0, "No emails in deal"
    assert record_types.get("crm_note", 0) > 0, "No CRM notes in deal"

    print(f"  ✓ Normal deal valid: {len(deal['events'])} events")
    print(f"    Event distribution: {record_types}")
    return True


async def test_complex_deal_output_quality():
    """Test that complex deals maintain quality."""
    print("\n[TEST] Complex deal output quality...")

    config = create_baseline_config()
    config["complexity"] = "messy"
    config["sales_cycle_length_days"] = 90
    config["num_calls"] = 6
    config["emails_per_stage"] = 3

    result = await generate_complete_deal(config)

    # Validate structure
    assert validate_deal_structure(result), "Deal structure invalid"

    # Validate all events
    deal = result["deal"]
    for event in deal["events"]:
        assert validate_event_quality(event), f"Event quality invalid: {event.get('record_type')}"

    # Validate metadata
    assert validate_metadata(deal["metadata"]), "Metadata quality invalid"

    print(f"  ✓ Complex deal valid: {len(deal['events'])} events")
    return True


async def test_content_coherence():
    """Test that generated content is coherent and consistent."""
    print("\n[TEST] Content coherence validation...")

    config = create_baseline_config()
    config["complexity"] = "normal"

    result = await generate_complete_deal(config)
    deal = result["deal"]

    # Extract and validate common elements
    metadata = deal["metadata"]
    company_name = metadata["company"].get("name", "")
    stakeholders = {s["name"] for s in metadata["stakeholders"]}

    # Verify stakeholders appear in events
    found_stakeholders = set()
    for event in deal["events"]:
        record_type = event.get("record_type")

        if record_type == "call":
            participants = event.get("participants", [])
            found_stakeholders.update(participants)

        elif record_type == "email":
            sender = event.get("sender", "")
            recipient = event.get("recipient", "")
            if sender:
                found_stakeholders.add(sender)
            if recipient:
                found_stakeholders.add(recipient)

    # Should find most stakeholders referenced
    coverage = len(found_stakeholders & stakeholders) / len(stakeholders) if stakeholders else 1
    assert coverage >= 0.5, f"Stakeholder coverage too low: {coverage:.1%}"

    print(f"  ✓ Content coherent: {coverage:.1%} stakeholder coverage")
    return True


async def run_all_tests():
    """Run all output validation tests."""
    print("\n" + "=" * 70)
    print("OUTPUT QUALITY VALIDATION TESTS")
    print("(Validating reduced MAX_TOKENS_BY_TYPE maintains quality)")
    print("=" * 70)

    tests = [
        test_simple_deal_output_quality,
        test_normal_deal_output_quality,
        test_complex_deal_output_quality,
        test_content_coherence,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            await test()
            passed += 1
        except Exception as e:
            print(f"  ✗ FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70 + "\n")

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
