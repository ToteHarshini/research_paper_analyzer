import re
import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ---------------------------------------------------------------------------
# 1. USER & AUTH SCHEMAS
# ---------------------------------------------------------------------------

class UserBase(BaseModel):
    email: str = Field(..., description="User email address")
    full_name: str | None = None

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if not EMAIL_REGEX.match(cleaned):
            raise ValueError("Invalid email format.")
        return cleaned


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, description="User password (minimum 6 characters)")


class UserLogin(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if not EMAIL_REGEX.match(cleaned):
            raise ValueError("Invalid email format.")
        return cleaned


class UserResponse(UserBase):
    id: uuid.UUID
    is_active: bool = True
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: uuid.UUID | str | None = None
    email: str | None = None


# ---------------------------------------------------------------------------
# 2. PAPER & PDF METADATA SCHEMAS
# ---------------------------------------------------------------------------

class PaperBase(BaseModel):
    title: str
    authors: list[str] | dict | None = None
    abstract: str | None = None


class PaperCreate(PaperBase):
    filename: str
    file_path: str | None = None
    page_count: int | None = None


class PaperResponse(PaperBase):
    id: uuid.UUID
    user_id: uuid.UUID
    filename: str
    file_path: str | None = None
    page_count: int | None = None
    processing_status: str = "uploaded"
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaperListResponse(BaseModel):
    papers: list[PaperResponse]
    total: int


# ---------------------------------------------------------------------------
# 3. RESEARCH REQUEST & RESPONSE SCHEMAS
# ---------------------------------------------------------------------------

class ResearchQueryRequest(BaseModel):
    question: str = Field(..., min_length=3, description="The research question to analyze")
    paper_ids: list[uuid.UUID] | None = Field(default=None, description="Optional paper IDs to restrict search to")
    conversation_id: uuid.UUID | None = Field(default=None, description="Optional conversation session ID")


class ClaimVerification(BaseModel):
    claim: str
    status: str = Field(..., description="supported | contradicted | partially_supported | insufficient_evidence")
    reason: str
    citations: list[str] = Field(default_factory=list)


class StructuredFindingSource(BaseModel):
    citation_id: str
    paper_id: str | None = None
    paper_title: str | None = None
    section: str | None = None
    page_number: int | str | None = None
    text: str | None = None


class StructuredFinding(BaseModel):
    category: str = Field(..., description="models | datasets | performance | methodology | limitations")
    finding: str
    sources: list[StructuredFindingSource | dict[str, Any]] = Field(default_factory=list)


class RetrievedEvidenceItem(BaseModel):
    chunk_id: str
    paper_id: str | None = None
    paper_title: str | None = None
    section: str | None = None
    page_number: int | None = None
    text: str | None = None
    reranker_score: float | None = None


class ResearchQueryResponse(BaseModel):
    question: str
    subquestions: list[str] = Field(default_factory=list)
    final_report: str
    verified_claims: list[ClaimVerification] = Field(default_factory=list)
    structured_findings: list[StructuredFinding] = Field(default_factory=list)
    evidence: list[RetrievedEvidenceItem] = Field(default_factory=list)
    conversation_id: uuid.UUID | None = None


# ---------------------------------------------------------------------------
# 4. CONVERSATION & MESSAGE SCHEMAS
# ---------------------------------------------------------------------------

class MessageBase(BaseModel):
    role: str = Field(..., description="user | assistant | system")
    content: str


class MessageCreate(MessageBase):
    pass


class MessageResponse(MessageBase):
    id: uuid.UUID
    conversation_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationBase(BaseModel):
    title: str | None = None


class ConversationCreate(ConversationBase):
    pass


class ConversationResponse(ConversationBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    messages: list[MessageResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# 5. CITATION SCHEMA
# ---------------------------------------------------------------------------

class CitationResponse(BaseModel):
    id: uuid.UUID
    paper_id: uuid.UUID
    message_id: uuid.UUID | None = None
    page_number: int | None = None
    section: str | None = None
    passage_text: str
    metadata_json: dict[str, Any] | None = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# 6. CHAT & SYSTEM SCHEMAS
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Follow-up question")
    context: str | None = Field(default=None, description="Optional previous research context or report")
    evidence: list[dict[str, Any]] | None = Field(default=None, description="Optional retrieved chunks from analysis")
    history: list[dict[str, str]] | None = Field(default=None, description="Optional conversation turns")


class ChatResponse(BaseModel):
    question: str
    answer: str
    sources: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
    version: str
    llm_provider: str | None = None
    database_connected: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)
