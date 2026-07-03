"""
One-off script: add missing inflected surface forms of hos_override.json
entries.

The tool and batch scorer look up exact surface forms, so an override entry
covers only the form listed: "freeholder" was flagged while "freeholders"
matched nothing and was silently unscored. For each override entry this script
generates simple inflections (plural, -ed, -ing), keeps those that actually
occur in the HOS corpus but are absent from both aoa_lookup.json and the
override, and adds them with the base entry's value (a variant of a specialist
term is equally specialist).
"""

import json
import re
from collections import Counter

import pandas as pd

DATA_DIR = "../data"


def variants(word):
    out = {word + "s"}
    if word.endswith(("s", "x", "z", "ch", "sh")):
        out.add(word + "es")
    if word.endswith("y") and word[-2] not in "aeiou":
        out.add(word[:-1] + "ies")
    if word.endswith("e"):
        out.update({word + "d", word[:-1] + "ing"})
    else:
        out.update({word + "ed", word + "ing"})
    return out


with open(f"{DATA_DIR}/aoa_lookup.json", encoding="utf-8") as f:
    aoa = json.load(f)
with open(f"{DATA_DIR}/hos_override.json", encoding="utf-8") as f:
    override = json.load(f)
before = len(override)

hos = pd.read_csv(f"{DATA_DIR}/hos_decisions_v5.csv", encoding="latin-1")
text = " ".join(hos["full_text"].dropna().astype(str)).lower()
counts = Counter(re.findall(r"[a-z]+", text))

added = []
for base, value in list(override.items()):
    for form in variants(base):
        if form in counts and form not in aoa and form not in override:
            override[form] = value
            added.append((form, base, value, counts[form]))

with open(f"{DATA_DIR}/hos_override.json", "w", encoding="utf-8") as f:
    json.dump(override, f, indent=2, sort_keys=True)

print(f"hos_override.json: {before} -> {len(override)} entries")
for form, base, value, freq in sorted(added, key=lambda x: -x[3]):
    print(f"  {form:<22} <- {base:<18} value={value!s:<6} corpus freq={freq:,}")
