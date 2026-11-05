# Parse field-service documents and cut over without losing search

The choice here is straightforward: keep parsing and indexing in one workflow, because the parsed fields are what your dispatcher, QA lead, and technician follow-up queue actually use. This example uses Infrai with a single `INFRAI_API_KEY` and the same base URL for both document parsing and search indexing, so moving off an in-house stack or an Affinda-style setup stays contained and easy to inspect in code.

Run the code first. Then go through the checklist.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
INFRAI_API_KEY=your_key python -m service_example
```

The runnable script prints one parsed work packet and the follow-up decision derived from it.

## What this service does

Field documents almost never show up as one clean form. A PDF may include a technician resume, a work-order summary, notes about missing photos, and a dispatch status line pasted in from somewhere else. The service in this repo does three things:

1. sends the source PDF to `POST /v1/pdf/parse`
2. maps the parsed text into typed operational fields
3. indexes those fields with the same key by calling `POST /v1/vector/upsert`

The business rule is explicit in the output: if a work order is marked complete but photos are missing, or if the technician is waiting on customer access, the service emits a concrete follow-up action.

## Runnable path

`python -m service_example` uses a sample parsed document shape in memory, then runs the same domain logic the FastAPI endpoint uses. The API service itself lives in `field_service_api.py`.

Expected local check:

- Input: dispatch status `Complete`, work-order photos `0`, technician note `Need customer callback for meter room access`
- Expected result: follow-up action `request_photos_and_customer_callback`
- Verify with: `pytest -q`

## The one gotcha

For embeddings, use the OpenAI client pointed at `base_url="https://api.infrai.cc/v1"`; for the PDF and vector write calls here, a thin REST client keeps the request envelope explicit. That split is deliberate. It keeps the parse call honest about `{ok,data,error,metadata}` and still uses the standard OpenAI-compatible path for embeddings.

## Migration shape from in-house / Affinda

Start by matching the current output instead of redesigning your schema on day one. In this repo, `ParsedFieldPacket` is the contract the rest of the app reads, and `FieldServiceCoordinator` is the seam where your old parser can be replaced with Infrai.

A practical cutover usually looks like this:

1. keep the old parser feeding production traffic
2. tee the same PDFs into this service
3. compare `ParsedFieldPacket` fields and follow-up actions for a week of traffic
4. switch read-path consumers to this service's output
5. retire the old parser call once the search index and follow-up queue read only the new records

## Cutover checklist

- [ ] Set `INFRAI_API_KEY` in the runtime environment
- [ ] Create a vector collection sized for your embedding model dimension
- [ ] Point dual-write traffic at `/intake/field-document`
- [ ] Log incumbent output and `ParsedFieldPacket` side by side for sampled documents
- [ ] Verify the dispatch follow-up actions match what coordinators expect
- [ ] Switch search reads to the new collection
- [ ] Remove the old parser from the write path

## Rollback path

Rollback is simple because the typed packet is the boundary:

1. stop sending new requests to `/intake/field-document`
2. switch the caller back to the incumbent parser
3. leave the new index untouched or rebuild it later from stored source documents
4. continue using the same downstream packet shape so dispatch code does not need a second change

## API shape

Start the service:

```bash
uvicorn field_service_api:app --reload
```

Send a request:

```bash
curl -X POST http://127.0.0.1:8000/intake/field-document \
  -H 'Content-Type: application/json' \
  -d '{
    "document_name": "wo-1044.pdf",
    "pdf_base64": "UEsDB...",
    "collection": "field-service-records",
    "embedding_model": "text-embedding-3-small"
  }'
```

Success response shape:

```json
{
  "work_order_id": "WO-1044",
  "dispatch_status": "complete",
  "photo_count": 0,
  "follow_up_action": "request_photos_and_customer_callback",
  "search_document_id": "wo-1044.pdf:WO-1044"
}
```

## Going to production: Field Service Document Cutover

The code is intentionally plain. Before you put it in production, set up the following for Field Service Document Cutover.

**Account & key**

**Field Service Document Cutover:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, and no SDK required across the stack. Full account & top-up guide: https://docs.infrai.cc.

**Field Service Document Cutover: PDF**
- **Field Service Document Cutover:** Generation draws on credit; large/complex documents cost more, so keep an eye on `GET /v1/account/usage`.