import json
from pathlib import Path

import streamlit as st


BASE_DIR = Path(__file__).resolve().parents[3]

OUTPUT_DIR = (
    BASE_DIR
    / "submissions"
    / "pia-21"
    / "agent"
    / "output"
)


st.set_page_config(
    page_title="Recovery Manager",
    page_icon="💰",
    layout="centered",
)

st.title("Recovery Manager")

st.write(
    "AI-powered evidence-to-recovery agent for fee and reimbursement charges."
)

st.divider()

st.subheader("Analyze Recovery Result")


# Load saved JSON results only.
# This does NOT run the recovery agent or Gemini.
output_files = sorted(OUTPUT_DIR.glob("UNIT-*.json"))

# Hide the old failed demo result.
output_files = [
    file for file in output_files
    if file.name != "UNIT-0002.json"
]

if not output_files:
    st.error("No recovery results found.")
    st.stop()


# Build a charge-level list from the saved results.
charges = []

for file in output_files:
    with open(file, encoding="utf-8") as f:
        data = json.load(f)

    unit_id = data.get("unit", {}).get("unit_id", "N/A")

    for index, result in enumerate(data.get("results", [])):
        charges.append({
            "label": (
                f"{result.get('charge_id', 'Unknown')} — "
                f"{result.get('verdict', 'UNKNOWN')}"
            ),
            "file": file,
            "unit_id": unit_id,
            "result_index": index,
            "data": data,
        })


# Put representative verdicts first.
preferred_charges = [
    "FEE-0003-1",   # SILENT
    "FEE-0018-1",   # SUPPORTED
    "FEE-0014-4",   # CONTRADICTED
    "FEE-0096-1",   # UNCERTAIN
]

ordered_charges = []

for charge_id in preferred_charges:
    for charge in charges:
        if charge["data"]["results"][charge["result_index"]].get(
            "charge_id"
        ) == charge_id:
            ordered_charges.append(charge)
            break

for charge in charges:
    if charge not in ordered_charges:
        ordered_charges.append(charge)


selected_label = st.selectbox(
    "Select a processed charge",
    [charge["label"] for charge in ordered_charges],
)

selected_charge = next(
    charge
    for charge in ordered_charges
    if charge["label"] == selected_label
)

data = selected_charge["data"]
result = data["results"][selected_charge["result_index"]]

unit = data.get("unit", {})


st.markdown(
    f"**Organization:** `{unit.get('org_id', 'N/A')}`  \n"
    f"**Unit:** `{unit.get('unit_id', 'N/A')}`  \n"
    f"**Processing status:** `{data.get('status', 'N/A')}`"
)

st.divider()

st.subheader(result.get("charge_id", "Unknown charge"))

st.write(
    f"**Verdict:** `{result.get('verdict', 'UNKNOWN')}`"
)

st.write(
    f"**Claim amount:** "
    f"${result.get('claim_amount_usd', 0.0):.2f}"
)

evidence = result.get("matched_evidence", [])

if evidence:
    st.write("**Matched evidence:**")
    for evidence_id in evidence:
        st.code(evidence_id)
else:
    st.write("**Matched evidence:** None")

st.write("**Explanation:**")

st.info(
    result.get(
        "explanation",
        "No explanation available."
    )
)

st.divider()

st.caption(
    "Recovery Manager — CUBE Buildathon 2026 | Problem 05"
)