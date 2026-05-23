from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Literal
from enum import Enum
from datetime import datetime

# ============= Enums =============

class SentimentEnum(str, Enum):
    """Sentiment states: positive, neutral, concerned, negative."""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    CONCERNED = "concerned"
    NEGATIVE = "negative"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            normalized = value.lower()
            for member in cls:
                if member.value == normalized:
                    return member
            # Map fuzzy values (e.g. "slightly positive") to nearest valid member
            for member in cls:
                if member.value in normalized:
                    return member
        return None

class DealOutcomeEnum(str, Enum):
    """Deal outcome: closed_won or closed_lost."""
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"

class ChampionEntryEnum(str, Enum):
    """When champion enters the deal."""
    NONE = "none"
    BEFORE_DISCOVERY = "before_discovery"
    DURING_DISCOVERY = "during_discovery"
    AFTER_DEMO = "after_demo"
    DURING_PROCUREMENT = "during_procurement"
    LATE_STAGE_RESCUE = "late_stage_rescue"

class BuyerUrgencyEnum(str, Enum):
    """Buyer urgency level."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class ComplexityEnum(str, Enum):
    """Deal complexity."""
    SIMPLE = "simple"
    NORMAL = "normal"
    MESSY = "messy"

class AdoptionChallengeEnum(str, Enum):
    """Customer adoption challenges post-close."""
    INTEGRATION_COMPLEXITY = "integration_complexity"
    TRAINING_GAP = "training_gap"
    WORKFLOW_MISMATCH = "workflow_mismatch"
    PERFORMANCE_ISSUES = "performance_issues"
    UNCLEAR_ROI = "unclear_roi"

class SupportPriorityEnum(str, Enum):
    """Support ticket and call priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SupportCategoryEnum(str, Enum):
    """Support interaction categories."""
    ONBOARDING = "onboarding"
    INTEGRATION = "integration"
    FEATURE_REQUEST = "feature_request"
    BUG = "bug"
    USAGE = "usage"

class SupportContactFrequencyEnum(str, Enum):
    """Support interaction frequency."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class RecordTypeEnum(str, Enum):
    """Timeline event record type."""
    CALL = "call"
    EMAIL = "email"
    CRM_NOTE = "crm_note"
    DEAL_METADATA = "deal_metadata"
    SUPPORT_TICKET = "support_ticket"
    SUPPORT_CALL = "support_call"

class SupportLevelEnum(str, Enum):
    """Stakeholder support level."""
    CHAMPION = "champion"
    SUPPORTER = "supporter"
    NEUTRAL = "neutral"
    SKEPTIC = "skeptic"
    BLOCKER = "blocker"

class InfluenceLevelEnum(str, Enum):
    """Stakeholder influence level."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

# ============= Request Models =============

class GenerateRequest(BaseModel):
    """POST /api/generate request body."""
    company_name: Optional[str] = Field(None, description="Company name or null to auto-generate")
    industry: str = Field(..., description="Industry (e.g., Fintech)")
    deal_size: str = Field(..., description="Deal size (e.g., $75k ARR)")
    sales_cycle_length_days: int = Field(..., ge=14, le=180, description="Sales cycle length")
    starting_sentiment: SentimentEnum = Field(..., description="Starting sentiment")
    ending_sentiment: SentimentEnum = Field(..., description="Ending sentiment")
    deal_outcome: DealOutcomeEnum = Field(..., description="Deal outcome")
    champion_entry: ChampionEntryEnum = Field(..., description="When champion enters")
    main_objection: str = Field(..., description="Main objection (e.g., Security Review)")
    buyer_urgency: BuyerUrgencyEnum = Field(..., description="Buyer urgency")
    num_calls: int = Field(..., ge=1, le=10, description="Number of calls")
    emails_per_stage: int = Field(..., ge=1, le=5, description="Emails per stage")
    num_stakeholders: int = Field(..., ge=2, le=8, description="Number of stakeholders")
    complexity: ComplexityEnum = Field(..., description="Deal complexity")
    cs_scenario: Optional['CSScenario'] = Field(None, description="Customer success post-close scenario")
    ae_name: Optional[str] = Field(None, description="Account Executive name or null to auto-generate")
    se_name: Optional[str] = Field(None, description="Sales Engineer name or null to auto-generate")
    business_use_case: Optional[str] = Field(None, description="Business use case (e.g. 'Automate compliance reporting')")
    is_series: bool = Field(False, description="Whether this is a series deal starting from cold call")

# ============= Internal Data Models =============

class CSScenario(BaseModel):
    """Customer success post-close scenario configuration."""
    enabled: bool = Field(False, description="Whether to generate post-close support events")
    adoption_challenge: Optional[AdoptionChallengeEnum] = Field(None, description="Primary adoption challenge")
    support_contact_frequency: SupportContactFrequencyEnum = Field(SupportContactFrequencyEnum.LOW, description="Support interaction frequency")
    churn_probability: float = Field(0.5, ge=0.0, le=1.0, description="Probability of churn (0.0-1.0)")
    post_close_days: int = Field(30, ge=7, le=180, description="Days to generate post-close events (7-180)")


class Company(BaseModel):
    """Company profile."""
    name: str
    industry: str
    employee_count: str
    arr_range: str
    tech_stack: List[str]
    icp_type: str
    hq_location: str

class SalesRep(BaseModel):
    """Sales representative."""
    name: str
    title: str = "Account Executive"
    email: str
    vendor_company: str

class SalesEngineer(BaseModel):
    """Sales engineer — joins deal at demo/evaluation stage."""
    name: str
    email: str
    vendor_company: str

class FrequencyEnum(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"

class Stakeholder(BaseModel):
    """Deal stakeholder."""
    id: str  # UUID
    name: str
    title: str
    email: str
    archetype: str
    support_level: SupportLevelEnum
    influence_level: InfluenceLevelEnum
    is_champion: bool = False

class SentimentArcPoint(BaseModel):
    """Single point in sentiment arc."""
    stage: str
    sentiment: SentimentEnum

class StageProgression(BaseModel):
    """Stage progression timing."""
    stage: str
    entered_date: str  # YYYY-MM-DD
    exited_date: Optional[str] = None

class Objection(BaseModel):
    """Deal objection."""
    id: str  # UUID
    text: str
    stage: str
    raised_by_stakeholder_id: str  # UUID
    resolved: bool

class DealConfig(BaseModel):
    """Original deal configuration (stored in metadata)."""
    company_name_input: Optional[str]
    industry: str
    deal_size: str
    sales_cycle_length_days: int
    starting_sentiment: SentimentEnum
    ending_sentiment: SentimentEnum
    champion_entry: ChampionEntryEnum
    main_objection: str
    buyer_urgency: BuyerUrgencyEnum
    num_calls: int
    emails_per_stage: int
    num_stakeholders: int
    complexity: ComplexityEnum
    ae_name: Optional[str] = None
    se_name: Optional[str] = None
    business_use_case: Optional[str] = None
    is_series: bool = False

class DealMetadata(BaseModel):
    """Deal metadata (line 1 of NDJson file)."""
    record_type: str = "deal_metadata"
    deal_id: str  # UUID
    filename: str
    generated_at: str  # ISO 8601
    deal_start_date: str  # YYYY-MM-DD
    deal_end_date: str  # YYYY-MM-DD
    config: DealConfig
    company: Company
    sales_rep: SalesRep
    sales_engineer: Optional['SalesEngineer'] = None
    stakeholders: List[Stakeholder]
    deal_outcome: DealOutcomeEnum
    sentiment_arc: List[SentimentArcPoint]
    stage_progression: List[StageProgression]
    objections: List[Objection]
    cs_scenario: Optional[CSScenario] = None
    support_events_count: int = 0

# ============= Timeline Event Models =============

class EventParticipant(BaseModel):
    """Call participant."""
    stakeholder_id: Optional[str] = None
    name: str
    role: str  # "buyer" or "seller"

class CallEvent(BaseModel):
    """Call timeline event."""
    record_type: str = "call"
    id: str  # UUID
    title: str
    call_type: str
    date: str  # YYYY-MM-DD
    timestamp: str  # ISO 8601
    stage: str
    sentiment: SentimentEnum
    participants: List[EventParticipant]
    transcript: str  # Min 800 words
    summary: str
    objections_raised: List[str]
    next_steps: List[str]

class EmailRecipient(BaseModel):
    """Email recipient/CC."""
    name: str
    email: str

class EmailSender(BaseModel):
    """Email sender."""
    stakeholder_id: Optional[str] = None
    name: str
    email: str

class EmailEvent(BaseModel):
    """Email timeline event."""
    record_type: str = "email"
    id: str  # UUID
    thread_id: str  # UUID
    reply_to_id: Optional[str] = None
    is_forward: bool = False
    subject: str
    sender: EmailSender
    recipients: List[EmailRecipient]
    cc: List[EmailRecipient]
    timestamp: str  # ISO 8601
    body: str
    sentiment: SentimentEnum
    stage: str
    purpose: str

class CRMNoteEvent(BaseModel):
    """CRM note timeline event."""
    record_type: str = "crm_note"
    id: str  # UUID
    timestamp: str  # ISO 8601
    author: str
    stage: str
    content: str
    is_internal: bool = True

class SupportTicketEvent(BaseModel):
    """Support ticket post-close event."""
    record_type: str = "support_ticket"  # Fixed record type for this event
    id: str  # UUID
    timestamp: str  # ISO 8601
    category: SupportCategoryEnum  # Support ticket category
    priority: SupportPriorityEnum  # Ticket priority level
    subject: str  # Ticket subject line
    description: str  # Detailed ticket description
    assigned_to: str  # Support agent assigned to ticket
    status: str  # Ticket status (open, in_progress, resolved, closed, etc.)

class SupportCallEvent(BaseModel):
    """Support call post-close event."""
    record_type: str = "support_call"  # Fixed record type for this event
    id: str  # UUID
    timestamp: str  # ISO 8601
    category: SupportCategoryEnum  # Support call category
    priority: SupportPriorityEnum  # Call priority level
    duration_minutes: int  # Call duration in minutes
    resolution: str  # Call outcome (issue_resolved, escalated, etc.)
    transcript: str  # Detailed notes from the support call
    support_agent: str  # Name of support agent who took the call

# ============= Slack Data Models =============

class SlackMessage(BaseModel):
    """Slack message."""
    message_id: str  # UUID
    channel_id: str
    sender: Literal["AE", "SDR", "Manager", "SE", "Legal", "CS", "Rep"]
    body: str  # Casual, may include emoji
    timestamp: datetime
    reactions: Optional[List[str]] = None  # Emoji reactions
    is_thread_reply: bool = False
    thread_parent_id: Optional[str] = None

class SlackChannel(BaseModel):
    """Slack channel."""
    channel_id: str
    name: str  # e.g., "deal-acme-corp", "pipeline-jane-doe"
    topic: str
    is_shared: bool = False  # True for rep-level channels in series mode
    created_at: datetime
    messages: List[SlackMessage] = Field(default_factory=list)

class SlackEvent(BaseModel):
    """Slack timeline event."""
    record_type: Literal["slack_channel", "slack_message"]
    channel: Optional[SlackChannel] = None
    message: Optional[SlackMessage] = None
    timestamp: datetime
    stage: str  # Sales stage

class SlackContext(BaseModel):
    """Slack context for series mode."""
    rep_name: str
    shared_channels: List[str]
    other_deals_summary: str
    quarter_health: str

# ============= Response Models =============

class DealSummary(BaseModel):
    """Summary of deal for GET /api/deals list."""
    deal_id: str
    filename: str
    company_name: str
    industry: str
    deal_size: str
    deal_outcome: DealOutcomeEnum
    complexity: ComplexityEnum
    generated_at: str  # ISO 8601
    num_events: int

class DealsListResponse(BaseModel):
    """GET /api/deals response."""
    deals: List[DealSummary]

class DealContent(BaseModel):
    """Deal object containing metadata and events."""
    metadata: DealMetadata
    events: List[dict]  # Union of CallEvent, EmailEvent, CRMNoteEvent

class GenerateResponse(BaseModel):
    """POST /api/generate response."""
    deal_id: str
    filename: str
    deal: DealContent
    token_usage: Optional['TokenUsage'] = None

class DealResponse(BaseModel):
    """GET /api/deals/{deal_id} response."""
    deal_id: str
    filename: str
    deal: DealContent

class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool

class BulkGenerateRequest(BaseModel):
    """POST /api/bulk-generate-stream request body."""
    count: int = Field(..., ge=1, le=20, description="Number of random deals to generate")
    overrides: Optional[dict] = Field(None, description="Per-variable overrides; unset fields are randomized")

class SeriesRequest(BaseModel):
    """POST /api/generate-series-stream request body."""
    account_age_months: int = Field(..., ge=1, le=24, description="How old the account is in months")
    frequency: FrequencyEnum = Field(..., description="Touchpoint frequency")
    ae_name: Optional[str] = Field(None, description="Account Executive name")
    se_name: Optional[str] = Field(None, description="Sales Engineer name")
    business_use_case: str = Field(..., description="Business use case for this deal")
    company_name: Optional[str] = Field(None)
    industry: str = Field(...)
    deal_size: str = Field(...)
    deal_outcome: DealOutcomeEnum = Field(..., description="Deal outcome (closed_won or closed_lost)")
    complexity: ComplexityEnum = Field(...)
    main_objection: str = Field(...)
    buyer_urgency: BuyerUrgencyEnum = Field(...)
    starting_sentiment: SentimentEnum = Field(...)
    ending_sentiment: SentimentEnum = Field(...)
    champion_entry: ChampionEntryEnum = Field(ChampionEntryEnum.AFTER_DEMO)
    cs_scenario: Optional['CSScenario'] = Field(None)

    # Deal dynamics and timing
    sales_cycle_velocity: Optional[str] = Field(None, description="Pace of deal progression: slow, normal, or fast")
    procurement_delay_days: Optional[int] = Field(None, ge=0, le=60, description="Days added to procurement stage")
    eval_iteration_count: Optional[int] = Field(None, ge=1, le=5, description="Number of evaluation cycles")

    # Stakeholders and dynamics
    number_of_decision_makers: Optional[int] = Field(None, ge=1, le=8, description="Number of people with final decision power")
    champion_replacement: Optional[bool] = Field(False, description="Whether primary champion leaves during deal")

    # Deal specifics
    discount_percentage: Optional[float] = Field(None, ge=0.0, le=50.0, description="Deal discount as percentage")
    win_loss_reason: Optional[str] = Field(None, description="Specific reason for win or loss")

    # Customer context
    customer_company_size: Optional[str] = Field(None, description="Customer employee count category: startup, sme, mid-market, enterprise")
    budget_pre_allocated: Optional[bool] = Field(False, description="Whether budget was committed before deal start")
    competing_vendors: Optional[int] = Field(None, ge=0, le=5, description="Number of competing vendors in evaluation")

    # Post-sale expectations
    time_to_value_days: Optional[int] = Field(None, ge=14, le=180, description="Expected days to realize ROI")
    implementation_complexity: Optional[str] = Field(None, description="Post-close implementation difficulty: simple, standard, complex")
    expansion_potential: Optional[str] = Field(None, description="Likelihood of future expansion: none, low, medium, high")

class TokenUsage(BaseModel):
    """Token usage summary for a generation run."""
    total_billable_tokens: int = Field(..., description="Total billable tokens (input + output + cache writes)")
    total_cache_saves: int = Field(0, description="Free tokens from cache reads")
    by_stage: Dict[str, Dict[str, int]] = Field(default_factory=dict, description="Token breakdown by stage")
    estimated_cost: float = Field(..., description="Estimated cost at Tier-1 pricing")
