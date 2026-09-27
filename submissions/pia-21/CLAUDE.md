# Recovery Manager — Durable Constraints

## Purpose

Recovery Manager evaluates financial charges against documented operational evidence and produces defensible recovery decisions.

## Hard Rules

1. Never invent evidence.
2. Never invent claim amounts.
3. Use only evidence explicitly present in supplied records.
4. Match charges using documented identifiers such as `unit_id`, order ID, shipment ID, SKU, or other supplied fields.
5. Process each charge line independently, even when multiple charges belong to the same unit.
6. Missing relevant evidence must not be treated as proof that a charge is incorrect.
7. Use `SILENT` when relevant evidence is unavailable.
8. Use `UNCERTAIN` when the available evidence is ambiguous.
9. Do not force a verdict when the evidence does not support one.
10. Preserve evidence references so every conclusion can be traced to supplied records.
11. If the AI evaluation fails, do not create a recovery claim. Save the case as `pending_review`.
12. Rate-limit failures may be retried, but repeated failure must fall back safely to `pending_review`.
13. The operator's captured records must not depend on successful AI evaluation to be preserved.
14. Do not silently resolve contradictions between records. Surface them for review.
15. Do not treat sample fee amounts or examples as authoritative business rules.

## AI Responsibilities

The AI reasoning step interprets the relationship between a charge and the documented evidence supplied to it.

The AI must not:

- fabricate evidence
- fabricate evidence IDs
- infer undocumented operational events
- assume missing evidence exists
- create a claim solely because a charge exists
- treat an ambiguous case as certain

## Verdicts

- `SUPPORTED` — supplied evidence supports the documented basis of the charge.
- `CONTRADICTED` — supplied evidence directly conflicts with the charge.
- `SILENT` — relevant evidence is not available to evaluate the charge.
- `UNCERTAIN` — the available evidence is ambiguous or a safe conclusion cannot be reached.

## Claim Rule

A potential recovery claim may be recorded only when the documented evidence supports a defensible claim.

If the evidence is missing, ambiguous, or the AI evaluation fails, the claim amount must remain zero.

## Data Integrity

- Preserve the organization/tenant associated with each record.
- Do not cross-match evidence between organizations.
- Do not modify upstream source records.
- Preserve original evidence identifiers and timestamps.
- Keep generated results traceable to their source records.

## Forbidden Language

Do not describe an unsupported charge as fraudulent, invalid, or definitely recoverable.

Do not claim that evidence is immutable, tamper-proof, or independently verified unless that capability is actually implemented.

Do not claim that the system maximizes recoveries.

The objective is defensible, evidence-backed recovery decisions.

## Kill Condition

If we cannot reliably connect a charge to relevant evidence, we do not make a recovery claim.
