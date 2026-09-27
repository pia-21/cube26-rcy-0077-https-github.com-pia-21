# One-Pager — Recovery Manager

## Problem

Sellers and ecommerce operators may receive fees, reimbursements, and other financial adjustments after the operational event that caused them. The evidence needed to investigate those charges may be distributed across multiple operational records.

## Solution

Recovery Manager connects financial charge records with documented operational evidence.

The pipeline:

1. Ingests fee and reimbursement records.
2. Identifies the associated unit and organization.
3. Retrieves relevant receiving, preparation, packing, and returns evidence.
4. Sends the charge and retrieved evidence to an AI reasoning step.
5. Classifies the charge as **SUPPORTED**, **CONTRADICTED**, **SILENT**, or **UNCERTAIN**.
6. Records relevant evidence references and a potential claim amount.
7. Sends failed or unresolved evaluations to `pending_review` rather than creating an unsupported claim.

## Architecture

**Financial records → Unit identification → Evidence retrieval → AI reasoning → Verdict → Claim / Review**

The implementation is headless and produces structured JSON results for each processed unit.

## Key Design Decisions

| Decision | Approach |
|---|---|
| Evidence retrieval | Deterministic matching using documented record identifiers |
| AI usage | One reasoning call per unit containing its charges and relevant evidence |
| Missing evidence | `SILENT` |
| Ambiguous evidence | `UNCERTAIN` |
| AI failure | `pending_review` with zero claim amount |
| Rate limiting | Retry with exponential backoff |
| Evidence integrity | Only evidence explicitly supplied to the agent may be referenced |
| Claim creation | Conservative; unsupported evidence does not create a claim |

## Current Run

The sample dataset contains **44 units**.

The final run produced:

- **41 units completed**
- **3 units sent to `pending_review`**
- **0 unsupported claims created for those failed evaluations**

The three pending cases resulted from AI response-format failures after the retry policy was exhausted. They were deliberately preserved as review cases rather than being treated as successful evaluations.

## What We Measure

Evaluation should measure:

- Correctness of charge-to-evidence matching
- Correctness of SUPPORT / CONTRADICT / SILENT / UNCERTAIN decisions
- Claim amount correctness
- Evidence traceability
- False positives and false negatives
- Handling of duplicate, ambiguous, partial, and missing evidence
- Safe behavior when the AI service fails

## Kill Condition

> If we cannot reliably connect a charge to relevant evidence, we do not make a recovery claim.
