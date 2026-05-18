"""
Test suite for Customer Success models and enums.
Tests Task 1: Add CS Enums and Data Models
"""

import pytest
from backend.models import (
    # New CS Enums
    AdoptionChallengeEnum,
    SupportPriorityEnum,
    SupportCategoryEnum,
    # New CS Models
    CSScenario,
    SupportTicketEvent,
    SupportCallEvent,
    # Modified models
    GenerateRequest,
    DealMetadata,
    RecordTypeEnum,
    # Existing required imports
    SentimentEnum,
    DealOutcomeEnum,
    ChampionEntryEnum,
    BuyerUrgencyEnum,
    ComplexityEnum,
)


class TestAdoptionChallengeEnum:
    """Test AdoptionChallengeEnum values and functionality."""

    def test_adoption_challenge_values(self):
        """Test all required adoption challenge values exist."""
        assert AdoptionChallengeEnum.INTEGRATION_COMPLEXITY.value == "integration_complexity"
        assert AdoptionChallengeEnum.TRAINING_GAP.value == "training_gap"
        assert AdoptionChallengeEnum.WORKFLOW_MISMATCH.value == "workflow_mismatch"
        assert AdoptionChallengeEnum.PERFORMANCE_ISSUES.value == "performance_issues"
        assert AdoptionChallengeEnum.UNCLEAR_ROI.value == "unclear_roi"

    def test_adoption_challenge_is_string_enum(self):
        """Test AdoptionChallengeEnum is a string enum."""
        assert isinstance(AdoptionChallengeEnum.INTEGRATION_COMPLEXITY, str)


class TestSupportPriorityEnum:
    """Test SupportPriorityEnum values and functionality."""

    def test_support_priority_values(self):
        """Test all required support priority values exist."""
        assert SupportPriorityEnum.LOW.value == "low"
        assert SupportPriorityEnum.MEDIUM.value == "medium"
        assert SupportPriorityEnum.HIGH.value == "high"
        assert SupportPriorityEnum.CRITICAL.value == "critical"

    def test_support_priority_is_string_enum(self):
        """Test SupportPriorityEnum is a string enum."""
        assert isinstance(SupportPriorityEnum.LOW, str)


class TestSupportCategoryEnum:
    """Test SupportCategoryEnum values and functionality."""

    def test_support_category_values(self):
        """Test all required support category values exist."""
        assert SupportCategoryEnum.ONBOARDING.value == "onboarding"
        assert SupportCategoryEnum.INTEGRATION.value == "integration"
        assert SupportCategoryEnum.FEATURE_REQUEST.value == "feature_request"
        assert SupportCategoryEnum.BUG.value == "bug"
        assert SupportCategoryEnum.USAGE.value == "usage"

    def test_support_category_is_string_enum(self):
        """Test SupportCategoryEnum is a string enum."""
        assert isinstance(SupportCategoryEnum.ONBOARDING, str)


class TestCSScenario:
    """Test CSScenario model."""

    def test_cs_scenario_defaults(self):
        """Test CSScenario defaults."""
        scenario = CSScenario()
        assert scenario.enabled is False
        assert scenario.adoption_challenge is None
        assert scenario.support_contact_frequency == "low"
        assert scenario.churn_probability == 0.5
        assert scenario.post_close_days == 30

    def test_cs_scenario_with_valid_values(self):
        """Test CSScenario with valid values."""
        scenario = CSScenario(
            enabled=True,
            adoption_challenge=AdoptionChallengeEnum.TRAINING_GAP,
            support_contact_frequency="high",
            churn_probability=0.8,
            post_close_days=60,
        )
        assert scenario.enabled is True
        assert scenario.adoption_challenge == AdoptionChallengeEnum.TRAINING_GAP
        assert scenario.support_contact_frequency == "high"
        assert scenario.churn_probability == 0.8
        assert scenario.post_close_days == 60

    def test_cs_scenario_support_contact_frequency_values(self):
        """Test support_contact_frequency accepts valid values."""
        for freq in ["low", "medium", "high"]:
            scenario = CSScenario(support_contact_frequency=freq)
            assert scenario.support_contact_frequency == freq

    def test_cs_scenario_churn_probability_range(self):
        """Test churn_probability validates range 0.0-1.0."""
        # Valid values
        CSScenario(churn_probability=0.0)
        CSScenario(churn_probability=0.5)
        CSScenario(churn_probability=1.0)

        # Invalid values should raise validation error
        with pytest.raises(ValueError):
            CSScenario(churn_probability=-0.1)
        with pytest.raises(ValueError):
            CSScenario(churn_probability=1.1)

    def test_cs_scenario_post_close_days_range(self):
        """Test post_close_days validates range 7-180."""
        # Valid values
        CSScenario(post_close_days=7)
        CSScenario(post_close_days=30)
        CSScenario(post_close_days=180)

        # Invalid values should raise validation error
        with pytest.raises(ValueError):
            CSScenario(post_close_days=6)
        with pytest.raises(ValueError):
            CSScenario(post_close_days=181)


class TestSupportTicketEvent:
    """Test SupportTicketEvent model."""

    def test_support_ticket_event_creation(self):
        """Test SupportTicketEvent with required fields."""
        event = SupportTicketEvent(
            id="ticket-123",
            timestamp="2024-05-17T10:00:00Z",
            category=SupportCategoryEnum.INTEGRATION,
            priority=SupportPriorityEnum.HIGH,
            subject="API Integration Issues",
            description="Cannot connect to API endpoint",
            assigned_to="John Doe",
            status="open",
        )
        assert event.record_type == "support_ticket"
        assert event.id == "ticket-123"
        assert event.category == SupportCategoryEnum.INTEGRATION
        assert event.priority == SupportPriorityEnum.HIGH
        assert event.status == "open"

    def test_support_ticket_event_record_type_default(self):
        """Test support_ticket record_type is set to 'support_ticket'."""
        event = SupportTicketEvent(
            id="ticket-123",
            timestamp="2024-05-17T10:00:00Z",
            category=SupportCategoryEnum.BUG,
            priority=SupportPriorityEnum.MEDIUM,
            subject="Test",
            description="Test",
            assigned_to="Test",
            status="open",
        )
        assert event.record_type == "support_ticket"


class TestSupportCallEvent:
    """Test SupportCallEvent model."""

    def test_support_call_event_creation(self):
        """Test SupportCallEvent with required fields."""
        event = SupportCallEvent(
            id="call-456",
            timestamp="2024-05-17T11:00:00Z",
            category=SupportCategoryEnum.ONBOARDING,
            priority=SupportPriorityEnum.MEDIUM,
            duration_minutes=30,
            outcome="issue_resolved",
            call_notes="User walked through onboarding process",
            support_agent="Jane Smith",
        )
        assert event.record_type == "support_call"
        assert event.id == "call-456"
        assert event.category == SupportCategoryEnum.ONBOARDING
        assert event.duration_minutes == 30
        assert event.outcome == "issue_resolved"

    def test_support_call_event_record_type_default(self):
        """Test support_call record_type is set to 'support_call'."""
        event = SupportCallEvent(
            id="call-456",
            timestamp="2024-05-17T11:00:00Z",
            category=SupportCategoryEnum.ONBOARDING,
            priority=SupportPriorityEnum.MEDIUM,
            duration_minutes=30,
            outcome="issue_resolved",
            call_notes="Test",
            support_agent="Test",
        )
        assert event.record_type == "support_call"


class TestGenerateRequestCSScenario:
    """Test cs_scenario field in GenerateRequest."""

    def test_generate_request_cs_scenario_optional(self):
        """Test cs_scenario is optional in GenerateRequest."""
        req = GenerateRequest(
            company_name="Test Company",
            industry="Fintech",
            deal_size="$100k ARR",
            sales_cycle_length_days=30,
            starting_sentiment=SentimentEnum.NEUTRAL,
            ending_sentiment=SentimentEnum.POSITIVE,
            deal_outcome=DealOutcomeEnum.CLOSED_WON,
            champion_entry=ChampionEntryEnum.AFTER_DEMO,
            main_objection="Security",
            buyer_urgency=BuyerUrgencyEnum.MEDIUM,
            num_calls=3,
            emails_per_stage=2,
            num_stakeholders=3,
            complexity=ComplexityEnum.NORMAL,
            cs_scenario=None,
        )
        assert req.cs_scenario is None

    def test_generate_request_cs_scenario_with_value(self):
        """Test cs_scenario can be provided in GenerateRequest."""
        scenario = CSScenario(
            enabled=True,
            adoption_challenge=AdoptionChallengeEnum.TRAINING_GAP,
            support_contact_frequency="high",
            churn_probability=0.7,
            post_close_days=60,
        )
        req = GenerateRequest(
            company_name="Test Company",
            industry="Fintech",
            deal_size="$100k ARR",
            sales_cycle_length_days=30,
            starting_sentiment=SentimentEnum.NEUTRAL,
            ending_sentiment=SentimentEnum.POSITIVE,
            deal_outcome=DealOutcomeEnum.CLOSED_WON,
            champion_entry=ChampionEntryEnum.AFTER_DEMO,
            main_objection="Security",
            buyer_urgency=BuyerUrgencyEnum.MEDIUM,
            num_calls=3,
            emails_per_stage=2,
            num_stakeholders=3,
            complexity=ComplexityEnum.NORMAL,
            cs_scenario=scenario,
        )
        assert req.cs_scenario is not None
        assert req.cs_scenario.enabled is True
        assert req.cs_scenario.adoption_challenge == AdoptionChallengeEnum.TRAINING_GAP


class TestDealMetadataCSFields:
    """Test new CS fields in DealMetadata."""

    def test_deal_metadata_cs_scenario_optional(self):
        """Test cs_scenario field in DealMetadata."""
        # This is a simplified test - full DealMetadata test would need all required fields
        from backend.models import Company, SalesRep, DealConfig

        # Create minimal DealMetadata-like structure
        # Note: This tests the field exists and is optional
        assert hasattr(DealMetadata, "__fields__")
        fields = DealMetadata.__fields__
        assert "cs_scenario" in fields
        # Default should be None
        assert fields["cs_scenario"].default is None

    def test_deal_metadata_support_events_count(self):
        """Test support_events_count field in DealMetadata."""
        assert hasattr(DealMetadata, "__fields__")
        fields = DealMetadata.__fields__
        assert "support_events_count" in fields
        # Default should be 0
        assert fields["support_events_count"].default == 0


class TestRecordTypeEnumCSTypes:
    """Test new record types in RecordTypeEnum."""

    def test_record_type_support_ticket(self):
        """Test SUPPORT_TICKET record type exists."""
        assert RecordTypeEnum.SUPPORT_TICKET.value == "support_ticket"

    def test_record_type_support_call(self):
        """Test SUPPORT_CALL record type exists."""
        assert RecordTypeEnum.SUPPORT_CALL.value == "support_call"

    def test_record_type_is_string_enum(self):
        """Test RecordTypeEnum values are strings."""
        assert isinstance(RecordTypeEnum.SUPPORT_TICKET, str)
        assert isinstance(RecordTypeEnum.SUPPORT_CALL, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
