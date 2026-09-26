import csv
import json
import os
import sys
import time
from pathlib import Path

from google import genai
from google.genai import types


BASE_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = BASE_DIR / "data"

FEE_REPORT = DATA_DIR / "fee_report_sample.csv"
RECEIVING = DATA_DIR / "upstream" / "receiving_sample.csv"
PREP = DATA_DIR / "upstream" / "prep_sample.csv"
PACK = DATA_DIR / "upstream" / "pack_sample.csv"
RETURNS = DATA_DIR / "upstream" / "returns_sample.csv"

OUTPUT_DIR = (
    BASE_DIR
    / "submissions"
    / "pia-21"
    / "agent"
    / "output"
)

MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")

# Retry only transient rate-limit/resource-exhaustion failures.
# Delays are deliberately conservative so the script does not hammer
# the API when the project is temporarily rate limited.
MAX_RETRIES = 4
INITIAL_BACKOFF_SECONDS = 3.0
BETWEEN_UNIT_DELAY_SECONDS = 1.0

ALLOWED_VERDICTS = {
    "SUPPORTED",
    "CONTRADICTED",
    "SILENT",
    "UNCERTAIN",
}


def load_csv(path):
    with open(path, newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def find_evidence_by_unit(records, unit_id, org_id):
    return [
        record
        for record in records
        if record.get("unit_id") == unit_id
        and record.get("org_id") == org_id
    ]


def group_charges_by_unit(charges):
    grouped = {}

    for charge in charges:
        key = (charge["org_id"], charge["unit_id"])
        grouped.setdefault(key, []).append(charge)

    return grouped


def build_unit_package(
    org_id,
    unit_id,
    unit_charges,
    receiving_records,
    prep_records,
    pack_records,
    return_records,
):
    return {
        "unit": {
            "org_id": org_id,
            "unit_id": unit_id,
        },
        "charges": unit_charges,
        # The current sample does not contain authoritative channel rules.
        # The model must not invent them.
        "authoritative_requirements": [],
        "evidence": {
            "receiving": find_evidence_by_unit(
                receiving_records, unit_id, org_id
            ),
            "prep": find_evidence_by_unit(
                prep_records, unit_id, org_id
            ),
            "pack": find_evidence_by_unit(
                pack_records, unit_id, org_id
            ),
            "returns": find_evidence_by_unit(
                return_records, unit_id, org_id
            ),
        },
    }


AI_SYSTEM_INSTRUCTIONS = """
You are the reasoning component of a Recovery Manager.

Your job is to evaluate each financial charge against the documented
operational evidence supplied for the same organization and unit.

The objective is defensible recovery claims, not maximizing the number
of claims.

Rules:

1. Use only information supplied in the input.
2. Never invent, assume, or infer undocumented evidence.
3. Never recall or invent real-world channel requirements from memory.
4. Treat authoritative_requirements as the only source of channel
   requirements.
5. Missing evidence does NOT contradict a charge.
6. If relevant evidence is absent, use SILENT.
7. If the available evidence or requirements are ambiguous or
   insufficient for a defensible conclusion, use UNCERTAIN.
8. Use CONTRADICTED only when supplied evidence directly conflicts
   with the documented basis of the charge or supplied requirement.
9. Use SUPPORTED only when supplied evidence directly supports the
   documented basis of the charge under the supplied requirement or
   explicit documented basis.
10. Merely related operational activity is NOT support.
11. Do not treat the existence of a record for the same unit as proof
    that it supports the charge.
12. Prep, receiving, pack, or return evidence cannot support an
    unrelated fee merely because it belongs to the same unit.
13. A fulfillment or weight-tier charge requires evidence addressing
    the relevant weight/tier or another explicit supplied basis.
    A prep record alone does not support such a charge.
14. A charge alleging that an item was not returned is contradicted by
    supplied evidence that explicitly documents the item's return,
    receipt as a return, or processed return. Do not reinterpret a
    documented return as a non-return.
15. A receiving quantity discrepancy alone does not prove an inbound
    loss unless the supplied evidence explicitly establishes that loss.
16. A damage or defect observation does not automatically establish a
    fee or reimbursement claim unless the supplied evidence explicitly
    connects it to the charge basis or supplied requirement.
17. Missing authoritative requirements alone do not automatically mean
    SILENT. If relevant evidence exists but the governing requirement
    is missing or ambiguous, use UNCERTAIN when a defensible conclusion
    cannot be made.
18. Return exactly one result for every input charge.
19. Every input charge_id must appear exactly once.
20. matched_evidence may contain only evidence record IDs that actually
    appear in the supplied evidence.
21. claim_amount_usd must never exceed the charge amount.
22. claim_amount_usd must never be negative.
23. Use a positive claim amount only when the evidence justifies a
    recoverable charge. SILENT and UNCERTAIN should normally have a
    zero claim amount. A contradicted non-zero charge may have a claim
    amount up to the charge amount when the evidence justifies recovery.
24. Explain every verdict using documented facts from the supplied input.
25. Preserve the distinction between missing evidence and contradictory
    evidence.
26. Do not create a claim merely because a charge exists.

Allowed verdicts:
SUPPORTED
CONTRADICTED
SILENT
UNCERTAIN
"""


def build_ai_request(unit_package):
    return {
        "system_instructions": AI_SYSTEM_INSTRUCTIONS.strip(),
        "unit": unit_package["unit"],
        "charges": unit_package["charges"],
        "authoritative_requirements": unit_package[
            "authoritative_requirements"
        ],
        "evidence": unit_package["evidence"],
        "required_output": {
            "results": [
                {
                    "charge_id": "string",
                    "verdict": (
                        "SUPPORTED | CONTRADICTED | SILENT | UNCERTAIN"
                    ),
                    "claim_amount_usd": "number",
                    "matched_evidence": ["evidence record ID"],
                    "explanation": "string",
                }
            ]
        },
    }


def collect_evidence_ids(unit_package):
    evidence_ids = set()

    for records in unit_package["evidence"].values():
        for record in records:
            record_id = record.get("record_id")

            if record_id:
                evidence_ids.add(record_id)

    return evidence_ids


def validate_ai_result(result, charge_by_id, valid_evidence_ids):
    required_fields = {
        "charge_id",
        "verdict",
        "claim_amount_usd",
        "matched_evidence",
        "explanation",
    }

    if not isinstance(result, dict):
        raise ValueError("AI result must be an object.")

    missing_fields = required_fields - result.keys()

    if missing_fields:
        raise ValueError(
            f"AI result is missing fields: {sorted(missing_fields)}"
        )

    charge_id = result["charge_id"]

    if charge_id not in charge_by_id:
        raise ValueError(
            f"AI returned unknown charge_id: {charge_id}"
        )

    verdict = result["verdict"]

    if verdict not in ALLOWED_VERDICTS:
        raise ValueError(
            f"Invalid verdict for {charge_id}: {verdict}"
        )

    matched_evidence = result["matched_evidence"]

    if not isinstance(matched_evidence, list):
        raise ValueError(
            f"matched_evidence must be a list for {charge_id}"
        )

    unknown_evidence = [
        evidence_id
        for evidence_id in matched_evidence
        if evidence_id not in valid_evidence_ids
    ]

    if unknown_evidence:
        raise ValueError(
            f"AI returned unknown evidence IDs for {charge_id}: "
            f"{unknown_evidence}"
        )

    claim_amount = result["claim_amount_usd"]

    if isinstance(claim_amount, bool):
        raise ValueError(
            f"claim_amount_usd must be numeric for {charge_id}"
        )

    try:
        claim_amount = float(claim_amount)
    except (TypeError, ValueError):
        raise ValueError(
            f"claim_amount_usd must be numeric for {charge_id}"
        )

    if claim_amount < 0:
        raise ValueError(
            f"claim_amount_usd cannot be negative for {charge_id}"
        )

    charge_amount = float(charge_by_id[charge_id]["amount_usd"])

    if claim_amount > charge_amount:
        raise ValueError(
            f"Claim amount exceeds charge amount for {charge_id}: "
            f"{claim_amount} > {charge_amount}"
        )

    explanation = result["explanation"]

    if not isinstance(explanation, str) or not explanation.strip():
        raise ValueError(
            f"Explanation cannot be empty for {charge_id}"
        )

    return True


def validate_ai_response(ai_response, unit_package):
    if not isinstance(ai_response, dict):
        raise ValueError("AI response must be an object.")

    results = ai_response.get("results")

    if not isinstance(results, list):
        raise ValueError("AI response must contain a results list.")

    charges = unit_package["charges"]

    charge_by_id = {
        charge["line_id"]: charge
        for charge in charges
    }

    expected_charge_ids = set(charge_by_id.keys())

    returned_charge_ids = [
        result.get("charge_id")
        for result in results
        if isinstance(result, dict)
    ]

    if len(returned_charge_ids) != len(set(returned_charge_ids)):
        raise ValueError("AI returned a duplicate charge_id.")

    returned_charge_id_set = set(returned_charge_ids)

    missing_charge_ids = expected_charge_ids - returned_charge_id_set
    unknown_charge_ids = returned_charge_id_set - expected_charge_ids

    if missing_charge_ids:
        raise ValueError(
            "AI did not return results for charges: "
            f"{sorted(missing_charge_ids)}"
        )

    if unknown_charge_ids:
        raise ValueError(
            "AI returned unknown charges: "
            f"{sorted(unknown_charge_ids)}"
        )

    valid_evidence_ids = collect_evidence_ids(unit_package)

    for result in results:
        validate_ai_result(
            result,
            charge_by_id,
            valid_evidence_ids,
        )

    return True


def parse_json_response(response):
    text = getattr(response, "text", None)

    if not text:
        raise ValueError("Gemini returned an empty response.")

    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "Gemini response was not valid JSON: "
            f"{exc}"
        ) from exc


def is_rate_limit_error(error):
    message = str(error).upper()

    return (
        "429" in message
        or "RESOURCE_EXHAUSTED" in message
        or "RATE LIMIT" in message
        or "RATE_LIMIT" in message
    )


def generate_with_retry(client, request):
    """
    Call Gemini with exponential backoff for transient 429/resource
    exhaustion errors.

    Non-rate-limit errors are raised immediately.

    If all retry attempts fail, the final exception is raised so the
    caller can preserve the existing fail-open pending_review behavior.
    """
    for attempt in range(MAX_RETRIES + 1):
        try:
            return client.models.generate_content(
                model=MODEL_NAME,
                contents=json.dumps(request),
                config=types.GenerateContentConfig(
                    system_instruction=AI_SYSTEM_INSTRUCTIONS,
                    response_mime_type="application/json",
                ),
            )

        except Exception as error:
            if not is_rate_limit_error(error):
                raise

            if attempt >= MAX_RETRIES:
                raise

            delay = INITIAL_BACKOFF_SECONDS * (2 ** attempt)

            print(
                f"  ! Gemini rate limited (429). "
                f"Retrying in {delay:.0f}s "
                f"(attempt {attempt + 1}/{MAX_RETRIES})..."
            )

            time.sleep(delay)


def build_pending_review_results(unit_package, error):
    results = []

    for charge in unit_package["charges"]:
        results.append(
            {
                "charge_id": charge["line_id"],
                "verdict": "UNCERTAIN",
                "claim_amount_usd": 0.0,
                "matched_evidence": [],
                "explanation": (
                    "AI evaluation could not be completed. "
                    "No recovery claim was created. "
                    f"Reason: {str(error)}"
                ),
                "status": "pending_review",
            }
        )

    return {
        "unit": unit_package["unit"],
        "status": "pending_review",
        "results": results,
    }


def save_unit_result(unit_id, result):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_path = OUTPUT_DIR / f"{unit_id}.json"

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(result, file, indent=2)

    return output_path


def evaluate_unit(client, unit_package):
    request = build_ai_request(unit_package)

    response = generate_with_retry(client, request)
    ai_result = parse_json_response(response)

    validate_ai_response(ai_result, unit_package)

    for result in ai_result["results"]:
        result["status"] = "completed"

    return {
        "unit": unit_package["unit"],
        "status": "completed",
        "results": ai_result["results"],
    }


def parse_args(argv):
    limit = None
    process_all = False

    index = 0

    while index < len(argv):
        argument = argv[index]

        if argument == "--all":
            process_all = True

        elif argument == "--limit":
            if index + 1 >= len(argv):
                raise ValueError("--limit requires a number.")

            try:
                limit = int(argv[index + 1])
            except ValueError as exc:
                raise ValueError(
                    "--limit must be an integer."
                ) from exc

            if limit <= 0:
                raise ValueError("--limit must be greater than zero.")

            index += 1

        else:
            raise ValueError(
                f"Unknown argument: {argument}"
            )

        index += 1

    if process_all and limit is not None:
        raise ValueError(
            "Use either --all or --limit, not both."
        )

    return limit, process_all


def create_client():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set."
        )

    return genai.Client(
        vertexai=True,
        api_key=api_key,
    )


def main():
    try:
        limit, process_all = parse_args(sys.argv[1:])
    except ValueError as error:
        print(f"Argument error: {error}")
        print(
            "Usage: python3 submissions/pia-21/agent/"
            "recovery_agent.py [--limit N | --all]"
        )
        return 1

    charges = load_csv(FEE_REPORT)
    receiving_records = load_csv(RECEIVING)
    prep_records = load_csv(PREP)
    pack_records = load_csv(PACK)
    return_records = load_csv(RETURNS)

    print(f"Loaded {len(charges)} charge records.")
    print(f"Loaded {len(receiving_records)} receiving records.")
    print(f"Loaded {len(prep_records)} prep records.")
    print(f"Loaded {len(pack_records)} pack records.")
    print(f"Loaded {len(return_records)} returns records.")

    grouped_charges = group_charges_by_unit(charges)

    print(
        f"\nGrouped {len(charges)} charges "
        f"into {len(grouped_charges)} units."
    )

    packages = []

    for (org_id, unit_id), unit_charges in grouped_charges.items():
        packages.append(
            build_unit_package(
                org_id,
                unit_id,
                unit_charges,
                receiving_records,
                prep_records,
                pack_records,
                return_records,
            )
        )

    if process_all:
        selected_packages = packages
    elif limit is not None:
        selected_packages = packages[:limit]
    else:
        selected_packages = packages[:1]

    print(
        f"\nProcessing {len(selected_packages)} unit(s) with Gemini."
    )
    print(f"Model: {MODEL_NAME}")
    print(
        f"429 retry policy: {MAX_RETRIES} retries, "
        f"starting at {INITIAL_BACKOFF_SECONDS:.0f}s."
    )

    client = create_client()

    completed = 0
    pending_review = 0

    for index, unit_package in enumerate(selected_packages, start=1):
        unit_id = unit_package["unit"]["unit_id"]

        print(
            f"\n[{index}/{len(selected_packages)}] "
            f"Evaluating {unit_id}..."
        )

        try:
            result = evaluate_unit(client, unit_package)

            completed += 1

            print(
                f"  ✓ Valid AI response "
                f"({len(result['results'])} charge results)"
            )

        except Exception as error:
            pending_review += 1

            print(
                f"  ! AI evaluation failed safely: {error}"
            )
            print(
                "  → Unit saved as pending_review."
            )

            result = build_pending_review_results(
                unit_package,
                error,
            )

        output_path = save_unit_result(unit_id, result)

        print(f"  Saved: {output_path}")

        if index < len(selected_packages):
            time.sleep(BETWEEN_UNIT_DELAY_SECONDS)

    print("\n" + "-" * 40)
    print("RECOVERY MANAGER RUN COMPLETE")
    print("-" * 40)
    print(f"Completed: {completed}")
    print(f"Pending review: {pending_review}")
    print(f"Output directory: {OUTPUT_DIR}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
