from __future__ import annotations

import re
from typing import Any

from fieldops_models import FollowUpResult, ParsedFieldPacket


STATUS_MAP = {
    "complete": "complete",
    "completed": "complete",
    "closed": "complete",
    "in progress": "in_progress",
    "in_progress": "in_progress",
    "dispatched": "dispatched",
    "blocked": "blocked",
    "on hold": "blocked",
}


def parse_packet_from_pdf_text(document_name: str, parsed_payload: dict[str, Any]) -> ParsedFieldPacket:
    text = extract_text(parsed_payload)
    work_order_id = first_match(text, r"(?:work order|wo)\s*[:#-]?\s*([A-Z0-9-]+)", default="UNKNOWN")
    technician_name = first_match(text, r"technician\s*[:#-]?\s*([^\n]+)", default="Unknown Technician")
    dispatch_raw = first_match(text, r"dispatch status\s*[:#-]?\s*([^\n]+)", default="dispatched")
    dispatch_status = STATUS_MAP.get(dispatch_raw.strip().lower(), "dispatched")
    photo_count_text = first_match(text, r"photos?\s*[:#-]?\s*(\d+)", default="0")
    notes = first_match(text, r"notes?\s*[:#-]?\s*([^\n]+)", default="")
    resume_summary = first_match(text, r"resume summary\s*[:#-]?\s*([^\n]+)", default="")
    return ParsedFieldPacket(
        document_name=document_name,
        work_order_id=work_order_id,
        technician_name=technician_name.strip(),
        technician_resume_summary=resume_summary.strip(),
        dispatch_status=dispatch_status,
        photo_count=int(photo_count_text),
        notes=notes.strip(),
    )


def decide_follow_up(packet: ParsedFieldPacket) -> FollowUpResult:
    notes_lower = packet.notes.lower()
    needs_customer_callback = "customer callback" in notes_lower or "customer call" in notes_lower or "access" in notes_lower
    missing_photos = packet.dispatch_status == "complete" and packet.photo_count == 0

    if missing_photos and needs_customer_callback:
        action = "request_photos_and_customer_callback"
        reason = "Completed job is missing photos and the note asks for customer contact."
    elif missing_photos:
        action = "request_photos"
        reason = "Completed job is missing closeout photos."
    elif needs_customer_callback:
        action = "customer_callback"
        reason = "Technician note indicates the customer needs follow-up."
    elif packet.dispatch_status == "blocked":
        action = "dispatch_review"
        reason = "Dispatch status is blocked and needs coordinator review."
    else:
        action = "none"
        reason = "No follow-up is required from the parsed fields."

    return FollowUpResult(
        work_order_id=packet.work_order_id,
        dispatch_status=packet.dispatch_status,
        photo_count=packet.photo_count,
        follow_up_action=action,
        reason=reason,
        search_document_id=f"{packet.document_name}:{packet.work_order_id}",
    )


def extract_text(parsed_payload: dict[str, Any]) -> str:
    if isinstance(parsed_payload.get("text"), str):
        return parsed_payload["text"]
    if isinstance(parsed_payload.get("markdown"), str):
        return parsed_payload["markdown"]
    if isinstance(parsed_payload.get("content"), str):
        return parsed_payload["content"]
    data = parsed_payload.get("data")
    if isinstance(data, dict):
        for key in ("text", "markdown", "content"):
            if isinstance(data.get(key), str):
                return data[key]
    return ""


def first_match(text: str, pattern: str, default: str) -> str:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        return default
    return match.group(1).strip()
