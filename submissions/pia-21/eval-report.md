# Evaluation Report — Recovery Manager

## Evaluation Objective

Evaluate whether Recovery Manager can:

- correctly connect charges to relevant operational evidence
- distinguish SUPPORTED, CONTRADICTED, SILENT, and UNCERTAIN cases
- produce correct claim amounts
- preserve evidence traceability
- handle missing, partial, ambiguous, duplicate, and already-reimbursed cases safely
- fail conservatively when AI evaluation is unavailable

## Evaluation Method

The supplied repository describes an evaluation set of 50 unseen units labelled independently by two human labellers.

The evaluation should compare the agent's structured results against those independent labels.

For each charge line, evaluate:

1. Charge-to-evidence matching
2. Verdict correctness
3. Claim amount correctness
4. Evidence-reference correctness
5. Handling of uncertain or unsupported cases

Per-check false positives and false negatives should be calculated from the independently labelled evaluation set.

## Current Evaluation Status

The final sample run processed 44 units:

| Result | Count |
|---|---:|
| Completed | 41 |
| Pending review | 3 |
| Total | 44 |

The three pending-review cases resulted from AI response-format failures after retry handling was exhausted.

No recovery claim was created for those failed evaluations.

These 44 sample-run results are **not** presented as an independent accuracy evaluation because the required unseen 50-unit human-labelled evaluation results are not currently available in this submission.

## Failure Modes Observed

### AI response-format failure

Some Gemini responses could not be parsed into the required structured format.

**Handling:** the affected unit is marked `pending_review`, receives an `UNCERTAIN` result, and has zero claim amount.

### API rate limiting

The AI service returned rate-limit responses during development.

**Handling:** the agent retries rate-limited requests using exponential backoff. Requests that remain unsuccessful after retries fall back to `pending_review`.

### Insufficient evidence

A charge may have no relevant operational evidence.

**Handling:** the charge is classified as `SILENT` rather than assuming the charge is incorrect.

### Ambiguous evidence

Available records may not establish a defensible conclusion.

**Handling:** `UNCERTAIN` is allowed as a first-class verdict.

### Incorrect evidence relevance

Early model outputs demonstrated that merely having operational evidence for a unit does not mean that the evidence supports every charge on that unit.

**Handling:** reasoning instructions were tightened to require evidence relevance to the specific charge.

## Two-Labeller Agreement

The repository specifies independent labelling by two human labellers for the 50-unit evaluation set.

Agreement statistics are not reported here because the independently labelled results are not available in the current submission.

No agreement percentage is invented.

## False Positives / False Negatives

Per-check false-positive and false-negative counts are not reported because the independently labelled evaluation results are not available.

The evaluation framework is defined, but the measured values remain to be populated from the official evaluation set.

## Limitations

- The 44-unit sample run is not an independent accuracy benchmark.
- The 50-unit human-labelled evaluation results are not currently available.
- AI response-format failures can require manual review.
- Performance depends on the completeness and quality of supplied operational evidence.
- Authoritative external eligibility rules are not inferred from sample data.

## Evaluation Principle

The system should prefer an unresolved or reviewable result over an unsupported recovery claim.

If the evidence does not establish a defensible connection between a charge and relevant operational evidence, no recovery claim should be created.
