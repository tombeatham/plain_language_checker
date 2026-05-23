"""
One-off script: update aoa_lookup.json and hos_override.json using the
post-normalisation unmatched lemma list from aoa_coverage_normalised_output.txt.

For each unmatched lemma:
  - If found in ECP: add to aoa_lookup.json with fine-tuned AoA score
  - If not found in ECP: add to hos_override.json (unless it's noise or a
    derivationally transparent adverb that simply lacks a rating)
"""

import json
import re

import pandas as pd

DATA_DIR = "../data"
OUT_DIR = "."
AoA_COL = "AI_Kuperman_et_al_2012 _AoA_Finetuned"

# --- Load unmatched lemmas from normalised output file ---
with open(f"{OUT_DIR}/aoa_coverage_normalised_output.txt", encoding="utf-8") as f:
    text = f.read()

# Parse table rows: rank, lemma, token_freq, doc_freq, doc_pct
unmatched_lemmas = []
for line in text.splitlines():
    m = re.match(r"^\s*(\d+)\s+(\S+)\s+([\d,]+)\s+([\d,]+)\s+([\d.]+)%", line)
    if m:
        unmatched_lemmas.append(m.group(2))

print(f"Unmatched lemmas (post-norm): {len(unmatched_lemmas)}")

# --- Load data files ---
with open(f"{DATA_DIR}/aoa_lookup.json") as f:
    aoa = json.load(f)

with open(f"{DATA_DIR}/hos_override.json") as f:
    override = json.load(f)
override_set = set(override)

ecp = pd.read_excel(f"{DATA_DIR}/AI_Generated_AoA_ECP.xlsx")
ecp_lookup = dict(
    zip(
        ecp["ECP_Target_Word_Mandera_et_al_2020"].str.lower(),
        ecp[AoA_COL],
    )
)

# --- Classify lemmas ---
# Noise: spaCy lemmatisation artefacts — truncated/garbled forms
NOISE_PATTERN = re.compile(
    r"(focusse|reoccurre|pende|rebooke|reattende|remedie|complie|"
    r"replastere|wellbee|dehumidifi|monie|notte|furth|faece|reconnecte|"
    r"unaddresse|reattende)$"
)
# Short tokens / acronyms to skip
SKIP = {"re", "co", "ot", "mm", "pm", "gp", "asra", "pre", "non"}

ecp_added = []
override_added = []
skipped_noise = []
skipped_adverb = []
already_present = []

for lemma in unmatched_lemmas:
    if lemma in aoa:
        already_present.append(lemma)
        continue
    if lemma in override_set:
        already_present.append(lemma)
        continue
    if lemma in SKIP or len(lemma) <= 2:
        skipped_noise.append(lemma)
        continue
    if NOISE_PATTERN.search(lemma):
        skipped_noise.append(lemma)
        continue

    ecp_score = ecp_lookup.get(lemma)
    if ecp_score is not None and not pd.isna(ecp_score):
        aoa[lemma] = round(float(ecp_score), 2)
        ecp_added.append((lemma, round(float(ecp_score), 2)))
    else:
        # Only add to override if likely a genuine content/specialist term,
        # not a derivationally transparent -ly adverb (Kuperman gap, not hard)
        if lemma.endswith("ly") or lemma.endswith("ily"):
            skipped_adverb.append(lemma)
        else:
            override_set.add(lemma)
            override_added.append(lemma)

# --- Write updated files ---
with open(f"{DATA_DIR}/aoa_lookup.json", "w") as f:
    json.dump(aoa, f)

with open(f"{DATA_DIR}/hos_override.json", "w") as f:
    json.dump(sorted(override_set), f, indent=2)

# --- Report ---
print(f"\nAdded to aoa_lookup.json ({len(ecp_added)} lemmas):")
for lemma, score in sorted(ecp_added, key=lambda x: x[1], reverse=True):
    print(f"  {lemma:<30} AoA {score:.2f}")

print(f"\nAdded to hos_override.json ({len(override_added)} lemmas):")
for lemma in sorted(override_added):
    print(f"  {lemma}")

print(f"\nSkipped — spaCy noise / acronyms ({len(skipped_noise)}):")
print(" ", ", ".join(sorted(skipped_noise)))

print(f"\nSkipped — -ly adverbs not in ECP ({len(skipped_adverb)}):")
print(" ", ", ".join(sorted(skipped_adverb)))

print(f"\nAlready present: {len(already_present)}")
print(f"\naoa_lookup.json: {len(aoa):,} entries (was {len(aoa) - len(ecp_added):,})")
print(f"hos_override.json: {len(override_set)} entries (was {len(override_set) - len(override_added)})")
