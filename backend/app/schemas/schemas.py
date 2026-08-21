"""AgentOps — Pydantic Schemas for all API endpoints."""

from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List, Any
from datetime import datetime
import uuid


# ── Auth Schemas ───────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    full_name: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    is_verified: bool
    is_active: bool
    is_demo: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── Chat Schemas ───────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

    @field_validator("message")
    @classmethod
    def message_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Message cannot be empty")
        return v.strip()


class ToolCallTrace(BaseModel):
    tool: str
    input: Any
    output: str
    tool_call_id: str = ""


class Source(BaseModel):
    source: str
    section: str


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    tool_calls_trace: List[ToolCallTrace] = []
    sources: List[Source] = []
    duration_ms: int = 0


# ── Conversation Schemas ────────────────────────────────────

class ConversationResponse(BaseModel):
    id: uuid.UUID
    title: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    metadata_: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Order Schemas ──────────────────────────────────────────

class OrderItemResponse(BaseModel):
    id: uuid.UUID
    product_name: str
    quantity: int
    unit_price: float
    subtotal: float

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: uuid.UUID
    order_number: str
    status: str
    total_amount: float
    tracking_number: Optional[str]
    delivery_date: Optional[datetime]
    created_at: datetime
    items: List[OrderItemResponse] = []

    class Config:
        from_attributes = True


# ── Ticket Schemas ─────────────────────────────────────────

class CreateTicketRequest(BaseModel):
    title: str
    description: str
    priority: str = "MEDIUM"
    order_number: Optional[str] = None


class TicketResponse(BaseModel):
    id: uuid.UUID
    ticket_number: str
    title: str
    description: str
    status: str
    priority: str
    order_id: Optional[uuid.UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Document/RAG Schemas ───────────────────────────────────

class IngestResponse(BaseModel):
    total_chunks: int
    documents: List[dict]
    status: str


class DocumentResponse(BaseModel):
    id: uuid.UUID
    filename: str
    doc_type: str
    chunk_count: int
    created_at: datetime

    class Config:
        from_attributes = True
