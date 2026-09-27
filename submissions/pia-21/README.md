# pia-21 · Recovery Manager

## Overview

Recovery Manager is a headless AI-powered pipeline that investigates financial charges against documented operational evidence.

It connects fee and reimbursement records with relevant receiving, prep, pack, and returns evidence, then produces a structured verdict and explanation for each charge.

## Core Flow

**Financial charge → Unit identification → Evidence retrieval → AI reasoning → Verdict → Claim / Review**

## Verdicts

- `SUPPORTED` — evidence supports the documented basis of the charge.
- `CONTRADICTED` — evidence directly conflicts with the charge.
- `SILENT` — relevant evidence is unavailable.
- `UNCERTAIN` — the available information is ambiguous or a safe conclusion cannot be reached.

## Key Principle

Recovery Manager is designed for defensible claims, not maximum claims.

It never invents evidence or treats missing evidence as proof that a charge is incorrect.

## Submission Contents

| File | Purpose |
|---|---|
| [`01-customer-letter.md`](01-customer-letter.md) | Customer-facing explanation |
| [`02-prfaq.md`](02-prfaq.md) | Press release and FAQ |
| [`03-one-pager.md`](03-one-pager.md) | Architecture, decisions, metrics, and kill condition |
| [`CLAUDE.md`](CLAUDE.md) | Durable constraints and hard rules |
| [`build-brief.md`](build-brief.md) | Problem and implementation brief |
| [`build-log.md`](build-log.md) | Development history and observed failure modes |
| [`eval-report.md`](eval-report.md) | Evaluation methodology and current results |
| [`contract/evidence-schema.md`](contract/evidence-schema.md) | Evidence record contract |
| [`contract/recovery-result-schema.md`](contract/recovery-result-schema.md) | Recovery result contract |
| [`agent/recovery_agent.py`](agent/recovery_agent.py) | Headless Recovery Manager implementation |

## Current Run

The final sample run processed **44 units**:

- **41 completed**
- **3 pending review**
- No recovery claim was created for the failed AI evaluations.

The three pending cases resulted from AI response-format failures after retries were exhausted.

## AI Integration

Gemini is used for the reasoning step after deterministic evidence retrieval.

The agent retries rate-limit failures with exponential backoff and falls back to `pending_review` when evaluation cannot safely be completed.

## Limitations

The current sample run is not an independent accuracy benchmark. The repository's separate 50-unit human-labelled evaluation set is not included in the current measured results.

## Kill Condition

> If we cannot reliably connect a charge to relevant evidence, we do not make a recovery claim.
