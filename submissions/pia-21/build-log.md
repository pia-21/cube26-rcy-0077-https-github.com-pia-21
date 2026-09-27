# Build Log — Recovery Manager

## Build Objective

Build a headless AI-powered Recovery Manager that connects financial charges with documented operational evidence and produces conservative, traceable recovery decisions.

## Build Stages

### 1. Repository and Submission Setup

- Created the submission branch using the required GitHub username.
- Kept all submission work inside `submissions/pia-21/`.
- Added the build brief and evidence/result contract documentation.

### 2. Data Understanding

Reviewed the supplied fee/reimbursement report and upstream operational records:

- Receiving
- Prep
- Pack
- Returns

The records are joined primarily through documented identifiers such as `unit_id`, with additional order, shipment, SKU, and organization fields available where applicable.

The supplied data is synthetic/dummy data and its sample amounts are not treated as authoritative business rules.

### 3. Deterministic Evidence Retrieval

Implemented deterministic record loading and evidence retrieval before the AI reasoning step.

The pipeline groups charges by unit while preserving individual charge lines and retrieves the operational records relevant to each unit.

### 4. AI Reasoning

Integrated Gemini as the reasoning component.

The AI receives the charge information together with the relevant documented evidence and evaluates the relationship between them.

The model is instructed not to invent evidence and to use `SILENT` or `UNCERTAIN` when a defensible conclusion cannot be reached.

### 5. Batch Model Calls

The agent uses one AI reasoning call per unit containing all relevant checks rather than making one model call for every individual check.

### 6. Failure Handling

Implemented retry handling for API rate limits using exponential backoff.

If AI evaluation still cannot be completed, the unit is saved as `pending_review` with an `UNCERTAIN` result and zero claim amount.

This keeps AI availability from blocking preservation of the underlying records.

## Final Sample Run

The final full run processed **44 units**.

- **41 units completed**
- **3 units entered `pending_review`**
- The three pending cases were caused by AI response-format failures after retries were exhausted.
- No recovery claim was created for those failed evaluations.

The pending-review behavior was intentional: an unusable AI response must not be converted into a confident recovery decision.

## Important Corrections During Development

Early AI outputs exposed reasoning errors, including cases where the model treated unrelated evidence as support for a charge.

The reasoning instructions were tightened so that:

- Evidence must be relevant to the specific charge.
- Missing evidence results in `SILENT`.
- Direct evidence against a charge can result in `CONTRADICTED`.
- A charge amount alone is never sufficient to justify a claim.
- Zero-dollar charges do not create a positive recovery amount.
- Ambiguous evidence can result in `UNCERTAIN`.

## Current Limitations

- The system depends on the quality and completeness of supplied operational evidence.
- Authoritative external eligibility rules are not embedded as assumed facts.
- AI response-format failures can still require manual review.
- The current implementation is headless and does not provide a user interface.
- The sample dataset is not a substitute for an independently labelled production evaluation set.

## Current Status

The core Recovery Manager agent is implemented and pushed to the submission branch.

The remaining submission work is documentation, evaluation reporting, final security/repository checks, and submission through the required process.

## Kill Condition

If we cannot reliably connect a charge to relevant evidence, we do not make a recovery claim.
