"""
Check how many of the 289 unmatched lemmas from aoa_unmatched_1pct.txt appear
in the ECP file. For matches, add word -> AoA score to hos_override.json.
Does not modify aoa_lookup.json or any other file.

NOTE: changes hos_override.json format from list to dict.
"""

import json
import re

import pandas as pd

DATA_DIR = "../data"
AoA_COL = "AI_Kuperman_et_al_2012 _AoA_Finetuned"

# --- Load 289 pre-normalisation unmatched lemmas ---
with open("aoa_unmatched_1pct.txt", encoding="utf-8") as f:
    text = f.read()

lemmas = []
for line in text.splitlines():
    m = re.match(r"^\s*(\d+)\s+(\S+)\s+([\d,]+)\s+([\d,]+)\s+([\d.]+)%", line)
    if m:
        lemmas.append(m.group(2))

print(f"Lemmas loaded from aoa_unmatched_1pct.txt: {len(lemmas)}")

# --- Load ECP ---
ecp = pd.read_excel(f"{DATA_DIR}/AI_Generated_AoA_ECP.xlsx")
ecp_lookup = {
    str(w).lower(): v
    for w, v in zip(ecp["ECP_Target_Word_Mandera_et_al_2020"], ecp[AoA_COL])
    if pd.notna(v)
}

# --- Cross-reference ---
matched = {}
unmatched = []

for lemma in lemmas:
    if lemma in ecp_lookup:
        matched[lemma] = round(float(ecp_lookup[lemma]), 2)
    else:
        unmatched.append(lemma)

print(f"\nMatched in ECP:   {len(matched)}")
print(f"Unmatched in ECP: {len(unmatched)}")

# --- Update hos_override.json ---
# Load current file (list or dict)
with open(f"{DATA_DIR}/hos_override.json") as f:
    existing = json.load(f)

if isinstance(existing, list):
    override = {w: None for w in existing}
else:
    override = existing

added = 0
for lemma, score in matched.items():
    if lemma not in override:
        override[lemma] = score
        added += 1
    else:
        # Update score if not already set
        if override[lemma] is None:
            override[lemma] = score

with open(f"{DATA_DIR}/hos_override.json", "w") as f:
    json.dump(override, f, indent=2, sort_keys=True)

# --- Print summary ---
print(f"\nAdded to hos_override.json: {added} new entries")
print(f"hos_override.json total entries: {len(override)}")

print(f"\nMATCHED ({len(matched)}) — sorted by AoA descending:")
print(f"  {'Lemma':<30} {'AoA':>6}")
print(f"  {'-'*38}")
for lemma, score in sorted(matched.items(), key=lambda x: x[1], reverse=True):
    flag = " *" if score > 10.0 else ""
    print(f"  {lemma:<30} {score:>6.2f}{flag}")

print(f"\nUNMATCHED ({len(unmatched)}) — not in ECP:")
for lemma in unmatched:
    print(f"  {lemma}")

print(f"\nNOTE: hos_override.json is now a dict (word -> AoA or null).")
print("      The tool's JavaScript reads it as a Set — update needed before deploying.")
