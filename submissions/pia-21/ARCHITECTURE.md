# Recovery Manager — Architecture

## 1. Overview

Recovery Manager is a headless AI-powered pipeline that investigates fee and reimbursement charges against documented operational evidence.

The system separates deterministic data handling from AI reasoning:

**Financial records → Charge grouping → Evidence retrieval → AI reasoning → Verdict → Claim / Review**

The goal is to produce evidence-backed, traceable recovery decisions without treating missing evidence as proof that a charge is incorrect.

---

## 2. System Components

### Financial Record Loader

Loads the supplied fee/reimbursement report and parses individual charge lines.

Each charge retains its documented identifiers and amount rather than being reduced to a unit-level summary.

### Evidence Loader

Loads the available upstream operational records:

- Receiving
- Prep
- Pack
- Returns

These records provide the documented evidence used by the Recovery Manager.

### Evidence Retrieval

Retrieves operational evidence using documented identifiers such as:

- `unit_id`
- `org_id`
- order ID
- shipment ID
- SKU / ASIN / FNSKU

The retrieval step is deterministic. The AI model does not decide which raw records exist.

### AI Reasoning Layer

Gemini is used after deterministic retrieval.

The model receives the charge information together with the relevant documented evidence and evaluates whether the evidence:

- supports the charge
- contradicts the charge
- is insufficient to evaluate the charge
- is ambiguous

The model is instructed not to invent evidence, identifiers, events, or claim amounts.

### Result Builder

The agent converts the AI evaluation into structured JSON results containing the charge, verdict, matched evidence, claim amount, and explanation.

### Failure Handling

Rate-limited model requests are retried using exponential backoff.

If AI evaluation still cannot be completed, the affected unit is saved as `pending_review` with an `UNCERTAIN` result and zero claim amount.

---

## 3. Data Flow

For each unit:

1. Load the fee/reimbursement records.
2. Identify the unit and organization associated with each charge.
3. Preserve each charge line independently.
4. Retrieve relevant upstream operational records.
5. Build one reasoning request containing the unit's charges and relevant evidence.
6. Send the request to Gemini.
7. Validate the returned structured result.
8. Validate referenced evidence against the evidence supplied to the model.
9. Produce the final structured recovery result.
10. If evaluation fails, preserve the case as `pending_review`.

### Simplified Flow

```text
Fee / Reimbursement Report
            │
            ▼
      Charge Parsing
            │
            ▼
      Unit / Org Match
            │
            ▼
     Evidence Retrieval
            │
            ▼
   Charges + Evidence
            │
            ▼
       Gemini Reasoning
            │
       ┌────┴────┐
       ▼         ▼
   Valid      Failure
   Result       │
       │        ▼
       │   pending_review
       ▼
   Verdict
       │
 ┌─────┼─────────────┐
 ▼     ▼             ▼
Claim  No Claim    Review