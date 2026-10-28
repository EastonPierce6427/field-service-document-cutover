from typing import Literal

from pydantic import BaseModel, Field


DispatchStatus = Literal["complete", "in_progress", "dispatched", "blocked"]
FollowUpAction = Literal[
    "none",
    "request_photos",
    "customer_callback",
    "request_photos_and_customer_callback",
    "dispatch_review"
]


class IntakeRequest(BaseModel):
    document_name: str
    pdf_base64: str = Field(description="Base64-encoded source PDF")
    collection: str
    embedding_model: str = "text-embedding-3-small"


class ParsedFieldPacket(BaseModel):
    document_name: str
    work_order_id: str
    technician_name: str
    technician_resume_summary: str
    dispatch_status: DispatchStatus
    photo_count: int = Field(ge=0)
    notes: str


class FollowUpResult(BaseModel):
    work_order_id: str
    dispatch_status: DispatchStatus
    photo_count: int
    follow_up_action: FollowUpAction
    reason: str
    search_document_id: str
