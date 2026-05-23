"""
AoA coverage analysis for HOS decisions corpus.

For each decision text: lemmatise content words via spaCy, look up lemma in
aoa_lookup.json. British spellings are normalised to American before lookup.

Outputs:
  aoa_unmatched_1pct.txt          -- baseline (pre-normalisation) >=1% lemmas
  aoa_coverage_normalised_output.txt -- post-normalisation coverage + >=1% lemmas
"""

import io
import json
import sys
from collections import Counter

import pandas as pd
import spacy
from breame.spelling import get_american_spelling

CONTENT_POS = {"NOUN", "VERB", "ADJ", "ADV"}
DATA_DIR = "../data"
OUT_DIR = "."

df = pd.read_csv(f"{DATA_DIR}/hos_decisions_v5.csv")
df = df[df["full_text"].notna()]
n_decisions = len(df)

with open(f"{DATA_DIR}/aoa_lookup.json") as f:
    aoa = json.load(f)

nlp = spacy.load("en_core_web_sm", disable=["ner", "parser"])
nlp.max_length = 2_000_000

print(f"Corpus: {n_decisions:,} decisions")
print("Processing texts...")

# Pre-normalisation counters
pre_total = 0
pre_matched = 0
pre_unmatched_freq: Counter = Counter()
pre_unmatched_docs: Counter = Counter()

# Post-normalisation counters
post_matched = 0
post_unmatched_freq: Counter = Counter()
post_unmatched_docs: Counter = Counter()

for i, text in enumerate(df["full_text"], 1):
    if i % 1000 == 0:
        print(f"  {i:,}/{n_decisions:,}")
    doc = nlp(str(text))
    pre_seen: set = set()
    post_seen: set = set()

    for token in doc:
        if token.pos_ not in CONTENT_POS:
            continue
        if not token.is_alpha:
            continue
        lemma = token.lemma_.lower()
        if len(lemma) <= 1:
            continue

        pre_total += 1

        # Pre-normalisation
        if lemma in aoa:
            pre_matched += 1
        else:
            pre_unmatched_freq[lemma] += 1
            pre_seen.add(lemma)

        # Post-normalisation: try American spelling if not found
        norm = get_american_spelling(lemma)
        if lemma in aoa or norm in aoa:
            post_matched += 1
        else:
            post_unmatched_freq[norm] += 1
            post_seen.add(norm)

    for lemma in pre_seen:
        pre_unmatched_docs[lemma] += 1
    for lemma in post_seen:
        post_unmatched_docs[lemma] += 1

min_docs = n_decisions * 0.01


def build_frequent(freq, docs):
    return sorted(
        [(lemma, f) for lemma, f in freq.items() if docs[lemma] >= min_docs],
        key=lambda x: x[1],
        reverse=True,
    )


def format_table(frequent, docs, n_decisions):
    lines = []
    header = f"{'Rank':<6} {'Lemma':<30} {'Token freq':>12} {'Doc freq':>10} {'Doc %':>7}"
    lines.append(header)
    lines.append("-" * 68)
    for rank, (lemma, freq) in enumerate(frequent, 1):
        doc_pct = docs[lemma] / n_decisions * 100
        lines.append(
            f"{rank:<6} {lemma:<30} {freq:>12,} {docs[lemma]:>10,} {doc_pct:>6.1f}%"
        )
    return "\n".join(lines)


pre_frequent = build_frequent(pre_unmatched_freq, pre_unmatched_docs)
post_frequent = build_frequent(post_unmatched_freq, post_unmatched_docs)

pre_coverage = pre_matched / pre_total * 100
post_coverage = post_matched / pre_total * 100

# --- Save pre-normalisation unmatched list ---
pre_lines = [
    "AoA COVERAGE - HOS DECISIONS CORPUS (pre-normalisation)",
    "=" * 60,
    f"Content word tokens:  {pre_total:>12,}",
    f"Matched (in AoA):     {pre_matched:>12,}  ({pre_coverage:.2f}%)",
    f"Unmatched:            {pre_total - pre_matched:>12,}  ({100 - pre_coverage:.2f}%)",
    "",
    f"UNMATCHED LEMMAS IN >=1% OF DECISIONS  (threshold: {min_docs:.0f} decisions)",
    format_table(pre_frequent, pre_unmatched_docs, n_decisions),
]
pre_out = "\n".join(pre_lines)
with open(f"{OUT_DIR}/aoa_unmatched_1pct.txt", "w", encoding="utf-8") as f:
    f.write(pre_out)

# --- Save post-normalisation output ---
post_lines = [
    "AoA COVERAGE - HOS DECISIONS CORPUS (British spellings normalised to American)",
    "=" * 78,
    f"Content word tokens:  {pre_total:>12,}",
    f"Matched pre-norm:     {pre_matched:>12,}  ({pre_coverage:.2f}%)",
    f"Matched post-norm:    {post_matched:>12,}  ({post_coverage:.2f}%)",
    f"Gain from normalisation: {post_matched - pre_matched:>8,} tokens  "
    f"(+{post_coverage - pre_coverage:.2f}pp)",
    f"Still unmatched:      {pre_total - post_matched:>12,}  ({100 - post_coverage:.2f}%)",
    "",
    f"UNMATCHED LEMMAS IN >=1% OF DECISIONS (post-norm, threshold: {min_docs:.0f} decisions)",
    format_table(post_frequent, post_unmatched_docs, n_decisions),
]
post_out = "\n".join(post_lines)
with open(f"{OUT_DIR}/aoa_coverage_normalised_output.txt", "w", encoding="utf-8") as f:
    f.write(post_out)

# --- Print summary to stdout ---
print()
print(pre_out)
print()
print(post_out)
print()
print("Saved: aoa_unmatched_1pct.txt")
print("Saved: aoa_coverage_normalised_output.txt")
