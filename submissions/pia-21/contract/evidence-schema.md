# Evidence Record Schema

Every piece of operational evidence used by Recovery Manager should identify:

- `unit_id` — unit the evidence belongs to
- `org_id` — organization/tenant owning the record
- `evidence_type` — receiving, prep, pack, or return
- `source_record_id` — original upstream record ID
- `captured_at` — when the evidence was recorded
- `details` — relevant documented facts from the source record
- `photo_refs` — references to supporting photos, if available

## Rule

Recovery Manager must use only evidence explicitly present in the source record.

It must never invent missing evidence.