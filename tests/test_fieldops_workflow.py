from fieldops_models import ParsedFieldPacket
from fieldops_workflow import decide_follow_up, parse_packet_from_pdf_text


def test_complete_job_without_photos_and_access_note_requests_both_followups() -> None:
    packet = ParsedFieldPacket(
        document_name="wo-1044.pdf",
        work_order_id="WO-1044",
        technician_name="Mina Patel",
        technician_resume_summary="EPA certified refrigeration tech.",
        dispatch_status="complete",
        photo_count=0,
        notes="Need customer callback for meter room access",
    )

    result = decide_follow_up(packet)

    assert result.follow_up_action == "request_photos_and_customer_callback"
    assert result.search_document_id == "wo-1044.pdf:WO-1044"


def test_parse_packet_from_pdf_text_extracts_domain_fields() -> None:
    parsed_payload = {
        "text": """
        Work Order: WO-1044
        Technician: Mina Patel
        Dispatch Status: Complete
        Photos: 0
        Notes: Need customer callback for meter room access
        Resume Summary: EPA certified refrigeration tech with 6 years in commercial service.
        """
    }

    packet = parse_packet_from_pdf_text("wo-1044.pdf", parsed_payload)

    assert packet.work_order_id == "WO-1044"
    assert packet.dispatch_status == "complete"
    assert packet.photo_count == 0
    assert packet.technician_name == "Mina Patel"
