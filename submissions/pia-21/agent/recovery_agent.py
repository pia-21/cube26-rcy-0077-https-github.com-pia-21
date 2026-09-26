import csv
from pathlib import Path


# -----------------------------
# 1. Load fee / charge report
# -----------------------------

FEE_REPORT = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "fee_report_sample.csv"
)

with open(FEE_REPORT, newline="") as file:
    reader = csv.DictReader(file)
    charges = list(reader)

print(f"Loaded {len(charges)} charge records.")


# -----------------------------
# 2. Load upstream evidence
# -----------------------------

EVIDENCE_FILES = {
    "receiving": (
        Path(__file__).resolve().parents[3]
        / "data"
        / "upstream"
        / "receiving_sample.csv"
    ),
    "prep": (
        Path(__file__).resolve().parents[3]
        / "data"
        / "upstream"
        / "prep_sample.csv"
    ),
    "pack": (
        Path(__file__).resolve().parents[3]
        / "data"
        / "upstream"
        / "pack_sample.csv"
    ),
    "returns": (
        Path(__file__).resolve().parents[3]
        / "data"
        / "upstream"
        / "returns_sample.csv"
    ),
}


evidence = {}

for evidence_type, file_path in EVIDENCE_FILES.items():
    with open(file_path, newline="") as file:
        evidence[evidence_type] = list(csv.DictReader(file))


for evidence_type, records in evidence.items():
    print(f"Loaded {len(records)} {evidence_type} records.")


# -----------------------------
# 3. Find evidence by unit
#    and organization
# -----------------------------

def find_evidence_by_unit(unit_id, org_id):
    matches = {}

    for evidence_type, records in evidence.items():
        matches[evidence_type] = [
            record
            for record in records
            if (
                record.get("unit_id") == unit_id
                and record.get("org_id") == org_id
            )
        ]

    return matches


# -----------------------------
# 4. Group charges by unit
#    and organization
# -----------------------------

def group_charges_by_unit(charges):
    grouped = {}

    for charge in charges:
        key = (
            charge["org_id"],
            charge["unit_id"]
        )

        if key not in grouped:
            grouped[key] = []

        grouped[key].append(charge)

    return grouped


# -----------------------------
# 5. Build one package per unit
# -----------------------------

def build_unit_package(org_id, unit_id, unit_charges):
    return {
        "org_id": org_id,
        "unit_id": unit_id,
        "charges": unit_charges,
        "evidence": find_evidence_by_unit(
            unit_id,
            org_id
        ),
    }


# -----------------------------
# 6. Group the charges
# -----------------------------

grouped_charges = group_charges_by_unit(charges)

print(
    f"\nGrouped {len(charges)} charges "
    f"into {len(grouped_charges)} units."
)


# -----------------------------
# 7. Inspect one unit
# -----------------------------

for (org_id, unit_id), unit_charges in list(
    grouped_charges.items()
)[:3]:

    package = build_unit_package(
        org_id,
        unit_id,
        unit_charges
    )

    print("\n" + "=" * 60)
    print("UNIT PACKAGE")
    print("=" * 60)

    print(f"Organization: {package['org_id']}")
    print(f"Unit: {package['unit_id']}")

    print("\nCharges:")
    for charge in package["charges"]:
        print(
            f"  {charge['line_id']} | "
            f"{charge['charge_type']} | "
            f"${charge['amount_usd']}"
        )

    print("\nEvidence:")
    for evidence_type, records in package["evidence"].items():
        print(
            f"  {evidence_type}: "
            f"{len(records)} record(s)"
        )