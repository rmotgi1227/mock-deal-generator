from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

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

class RecordTypeEnum(str, Enum):
    """Timeline event record type."""
    CALL = "call"
    EMAIL = "email"
    CRM_NOTE = "crm_note"
    DEAL_METADATA = "deal_metadata"

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

# ============= Internal Data Models =============

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
    stakeholders: List[Stakeholder]
    deal_outcome: DealOutcomeEnum
    sentiment_arc: List[SentimentArcPoint]
    stage_progression: List[StageProgression]
    objections: List[Objection]

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
