from fastapi import FastAPI, HTTPException

from fieldops_infrai import InfraiClient, InfraiError
from fieldops_models import FollowUpResult, IntakeRequest
from fieldops_workflow import decide_follow_up, parse_packet_from_pdf_text

app = FastAPI(title="Field Service Document Intake")


@app.post("/intake/field-document", response_model=FollowUpResult)
def intake_field_document(request: IntakeRequest) -> FollowUpResult:
    client = InfraiClient()
    try:
        parsed_env = client.pdf_parse({"pdf": request.pdf_base64})
        packet = parse_packet_from_pdf_text(request.document_name, parsed_env.get("data", {}))
        follow_up = decide_follow_up(packet)

        embedding_text = (
            f"work_order_id: {packet.work_order_id}\n"
            f"technician_name: {packet.technician_name}\n"
            f"dispatch_status: {packet.dispatch_status}\n"
            f"photo_count: {packet.photo_count}\n"
            f"notes: {packet.notes}\n"
            f"resume_summary: {packet.technician_resume_summary}"
        )
        embedding = client.embed_text(embedding_text, request.embedding_model)
        client.vector_upsert(
            {
                "collection": request.collection,
                "vectors": [
                    {
                        "id": follow_up.search_document_id,
                        "embedding": embedding,
                        "metadata": packet.model_dump(),
                    }
                ],
            }
        )
        return follow_up
    except InfraiError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.payload) from exc
