from fieldops_models import ParsedFieldPacket
from fieldops_workflow import decide_follow_up


def main() -> None:
    packet = ParsedFieldPacket(
        document_name="wo-1044.pdf",
        work_order_id="WO-1044",
        technician_name="Mina Patel",
        technician_resume_summary="EPA certified refrigeration tech with 6 years in commercial service.",
        dispatch_status="complete",
        photo_count=0,
        notes="Need customer callback for meter room access before final sign-off."
    )
    result = decide_follow_up(packet)
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
