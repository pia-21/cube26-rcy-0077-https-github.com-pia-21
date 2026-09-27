# PR/FAQ — Recovery Manager

## Press Release

### Recovery Manager turns operational evidence into defensible recovery decisions

Sellers and ecommerce operators often receive fees, reimbursements, and other financial adjustments after the operational event that caused them. Recovery Manager helps investigate those charges by connecting financial records with documented operational evidence.

The agent ingests fee and reimbursement records, identifies the associated unit, retrieves relevant evidence from receiving, preparation, packing, and returns records, and uses an AI reasoning step to classify each charge.

Each charge receives one of four verdicts:

- **SUPPORTED** — supplied evidence supports the documented basis of the charge.
- **CONTRADICTED** — supplied evidence directly conflicts with the charge.
- **SILENT** — relevant evidence is not available to evaluate the charge.
- **UNCERTAIN** — the available information is ambiguous or the evaluation cannot safely reach a conclusion.

Recovery Manager is intentionally conservative. It does not treat missing evidence as proof that a charge is wrong, and it does not invent evidence. A potential recovery amount is recorded only when the evidence supports a defensible claim.

The system is designed as a headless pipeline so that the same evidence-matching and reasoning process can be evaluated independently of a user interface.

## FAQ

### Who is this for?

Recovery Manager is intended for sellers and ecommerce operators who need to investigate financial adjustments against operational records.

### What does it actually do?

It parses charge records, identifies the associated unit and organization, retrieves matching operational evidence, evaluates the relationship between the evidence and the charge, and produces a structured result with a verdict, evidence references, claim amount, and explanation.

### Why use AI?

The deterministic part of the system handles record loading, organization isolation, grouping, and evidence retrieval. Gemini is used for the reasoning step: interpreting whether the retrieved documented evidence supports, contradicts, or is insufficient to evaluate a particular charge.

### What happens when evidence is missing?

The system does not assume that the charge is wrong. When relevant evidence is absent, the appropriate result is **SILENT**.

### What happens when the evidence is ambiguous?

The system can return **UNCERTAIN** rather than forcing a conclusion. AI failures are also handled conservatively as `pending_review` with no recovery claim.

### Can the system invent evidence?

No. The agent is instructed to use only evidence explicitly present in the supplied records. Matched evidence IDs are also validated against the evidence supplied to the model.

### Does every charge become a recovery claim?

No. The objective is defensible claims, not the maximum number of claims. Unsupported or ambiguous charges do not automatically produce claims.

### What happens if the AI service fails?

The operator's captured records are not blocked by the AI failure. The affected unit is saved as `pending_review`, with an `UNCERTAIN` result and zero claim amount.

### What happens if the API rate limit is reached?

The agent retries rate-limit responses using exponential backoff. If evaluation still cannot be completed, the unit falls back to `pending_review` instead of creating an unsupported claim.

### What are the main limitations?

The agent can only reason from the evidence and requirements supplied to it. Missing evidence, ambiguous records, unavailable authoritative requirements, or an unusable AI response can prevent a definitive conclusion.

### What would make us stop or change the approach?

If the agent cannot reliably connect a charge to relevant operational evidence, or if evaluation shows that its claims are not sufficiently traceable and correct, the recovery-claim workflow should not be expanded. The kill condition is:

> If we cannot reliably connect a charge to relevant evidence, we do not make a recovery claim.
