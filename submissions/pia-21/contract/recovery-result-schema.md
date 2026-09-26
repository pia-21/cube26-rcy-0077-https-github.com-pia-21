# Recovery Result Schema

Recovery Manager produces one result for each charge line.

Each result should contain:

- `charge_id` — unique fee/reimbursement line ID
- `unit_id` — associated unit
- `charge_type` — type of financial adjustment
- `amount_usd` — amount of the charge
- `verdict` — SUPPORTED, CONTRADICTED, SILENT, or UNCERTAIN
- `matched_evidence` — relevant evidence records
- `claim_amount_usd` — amount potentially recoverable
- `explanation` — concise evidence-based reasoning

## Golden Rule

A claim must never be created merely because evidence is missing.

If relevant evidence is absent, the result should be SILENT.

If the available evidence is ambiguous, the result may be UNCERTAIN.