"""
One-off script: merge ALL usable ECP supplement words into aoa_lookup.json.

The earlier update_aoa_from_ecp.py merged only the ECP words that surfaced as
frequent unmatched lemmas in the HOS corpus (176 words). The project docs,
however, describe the full ECP supplement as included in the lookup. This
script completes the merge: every ECP word with a fine-tuned AoA value that is
not already a key in aoa_lookup.json is added, rounded to 2 dp.

Hygiene filter: only keys matching [a-z]+ are added, because the tool's
tokeniser can only ever look up plain lowercase letter runs — hyphenated or
multi-word entries would be dead keys.

Does not touch hos_override.json.
"""

import json
import re

import pandas as pd

DATA_DIR = "../data"
AoA_COL = "AI_Kuperman_et_al_2012 _AoA_Finetuned"
KEY_RE = re.compile(r"[a-z]+\Z")

with open(f"{DATA_DIR}/aoa_lookup.json", encoding="utf-8") as f:
    aoa = json.load(f)
before = len(aoa)

ecp = pd.read_excel(f"{DATA_DIR}/AI_Generated_AoA_ECP.xlsx")
words = ecp["ECP_Target_Word_Mandera_et_al_2020"].astype(str).str.lower()
values = ecp[AoA_COL]

no_value = 0
non_alpha = 0
already = 0
added = 0
for word, value in zip(words, values):
    if pd.isna(value):
        no_value += 1
        continue
    if not KEY_RE.match(word):
        non_alpha += 1
        continue
    if word in aoa:
        already += 1
        continue
    aoa[word] = round(float(value), 2)
    added += 1

with open(f"{DATA_DIR}/aoa_lookup.json", "w", encoding="utf-8") as f:
    json.dump(aoa, f)

print(f"ECP rows:               {len(ecp):,}")
print(f"  no AoA value:         {no_value:,}")
print(f"  non-alphabetic key:   {non_alpha:,}")
print(f"  already in lookup:    {already:,}")
print(f"  added:                {added:,}")
print(f"aoa_lookup.json: {before:,} -> {len(aoa):,} entries")
