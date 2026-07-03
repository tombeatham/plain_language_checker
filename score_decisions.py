"""
Plain language scorer — spreadsheet mode (AoA engine).

Batch port of the single-document tool in tool/index.html. Scores each row of a
spreadsheet with the same Age-of-Acquisition flagging logic the tool uses, and
writes the results back as appended columns in a new spreadsheet.

Flag rule (identical to the tool):
  - A token [A-Za-z]+ is a CONTENT word if it appears in hos_override.json or
    aoa_lookup.json.
  - A content word is FLAGGED if its value is null (specialist term, not rated)
    or its AoA is > 10.0 (later than end of primary school).
  - Counting is per occurrence, as in the tool: aoa_score_pct is flagged
    occurrences over content-word occurrences. flagged_words lists each
    distinct flagged word once.
  - A sentence is LONG if it has more than 25 words.
  - Rows under 20 content words get no aoa_score_pct or mean_aoa (unreliable
    on very short text); the raw counts are still reported.

Tokenisation is simpler than the tool's: plain [A-Za-z]+ runs, no apostrophe
stripping and no proper-noun exclusion, so capitalised names whose lowercase
form has an AoA rating are scored here but skipped by the tool.

In addition to the tool's document score it reports mean AoA and average
sentence length — the two components of the validated composite (rho=0.661
against CLEAR) — so the output is ready for the HOS outcomes study.

Usage:
    python score_decisions.py --text-column "Decision Text" --input decisions.csv [--output output/]
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import NamedTuple

import pandas as pd

AOA_PATH = Path("data/aoa_lookup.json")
OVERRIDE_PATH = Path("data/hos_override.json")
AOA_THRESHOLD = 10.0
LONG_SENTENCE_WORDS = 25
MIN_CONTENT_WORDS = 20

_WORD_RE = re.compile(r"[A-Za-z]+")
_SENT_SPLIT_RE = re.compile(r"(?<=[.!?])[ \t]+|\n+")

SCORE_COLS = [
    "aoa_score_pct",
    "mean_aoa",
    "avg_sentence_length",
    "long_sentence_count",
    "content_word_count",
    "flagged_word_count",
    "total_words",
    "flagged_words",
]


def load_json_map(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


class Score(NamedTuple):
    content: int          # content words (found in override or aoa)
    flagged_count: int    # flagged occurrences (each repeat counts, as in the tool)
    flagged: list[str]    # distinct flagged words, sorted
    mean_aoa: float       # mean AoA over rated content words
    avg_sentence_length: float
    long_sentences: int
    total_words: int


def score_text(text: str, aoa: dict, override: dict) -> Score:
    flagged: set[str] = set()
    flagged_count = 0
    aoa_values: list[float] = []
    content = 0

    tokens = _WORD_RE.findall(text)
    for token in tokens:
        word = token.lower()
        if word in override:
            value = override[word]
        elif word in aoa:
            value = aoa[word]
        else:
            continue  # not a rated content word

        content += 1
        if value is None:
            flagged_count += 1           # specialist term, not rated
            flagged.add(word)
        else:
            aoa_values.append(value)
            if value > AOA_THRESHOLD:
                flagged_count += 1
                flagged.add(word)

    sentences = [s for s in _SENT_SPLIT_RE.split(text) if s.strip()]
    sentence_lengths = [len(s.split()) for s in sentences]
    long_sentences = sum(1 for n in sentence_lengths if n > LONG_SENTENCE_WORDS)
    avg_sentence_length = (
        round(sum(sentence_lengths) / len(sentences), 1) if sentences else 0.0
    )
    mean_aoa = round(sum(aoa_values) / len(aoa_values), 2) if aoa_values else 0.0

    return Score(
        content=content,
        flagged_count=flagged_count,
        flagged=sorted(flagged),
        mean_aoa=mean_aoa,
        avg_sentence_length=avg_sentence_length,
        long_sentences=long_sentences,
        total_words=len(tokens),
    )


def score_row(text: str, aoa: dict, override: dict) -> dict:
    result = score_text(str(text), aoa, override)
    # Percentage and mean are unreliable under 20 content words; the raw
    # counts are still reported.
    reliable = result.content >= MIN_CONTENT_WORDS
    return {
        "aoa_score_pct": (
            round(result.flagged_count / result.content * 100, 1)
            if reliable else None
        ),
        "mean_aoa": result.mean_aoa if reliable else None,
        "avg_sentence_length": result.avg_sentence_length,
        "long_sentence_count": result.long_sentences,
        "content_word_count": result.content,
        "flagged_word_count": result.flagged_count,
        "total_words": result.total_words,
        "flagged_words": "|".join(result.flagged),
    }


def load_spreadsheet(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        try:
            return pd.read_csv(path, encoding="utf-8")
        except UnicodeDecodeError:
            return pd.read_csv(path, encoding="cp1252")
    return pd.read_excel(path, engine="openpyxl")


def write_spreadsheet(df: pd.DataFrame, path: Path) -> None:
    if path.suffix.lower() == ".csv":
        df.to_csv(path, index=False, encoding="utf-8")
    else:
        df.to_excel(path, index=False, engine="openpyxl")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Score spreadsheet rows with the AoA plain-language engine."
    )
    p.add_argument("--input", required=True,
                   help="Spreadsheet to score (.xlsx or .csv)")
    p.add_argument("--text-column", required=True,
                   help="Name of the column containing the text to score")
    p.add_argument("--output", default="output/",
                   help="Directory for the output spreadsheet (default: output/)")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_dir = Path(args.output)

    if not input_path.exists():
        sys.exit(f"ERROR: Input file not found: {input_path}")
    for ref in (AOA_PATH, OVERRIDE_PATH):
        if not ref.exists():
            sys.exit(f"ERROR: {ref} not found. Run from the repo root.")

    output_dir.mkdir(parents=True, exist_ok=True)

    print("Loading AoA + override data…")
    aoa = load_json_map(AOA_PATH)
    override = load_json_map(OVERRIDE_PATH)
    print(f"AoA lookup: {len(aoa):,} words | overrides: {len(override)}")

    print(f"Loading {input_path.name}…")
    df = load_spreadsheet(input_path)

    if args.text_column not in df.columns:
        sys.exit(
            f"Column '{args.text_column}' not found.\n"
            f"Available columns: {list(df.columns)}"
        )

    print(f"Scoring {len(df)} rows on column '{args.text_column}'…")
    results = []
    skipped = 0
    for text in df[args.text_column].fillna(""):
        row = score_row(text, aoa, override)
        if row["aoa_score_pct"] is None:
            skipped += 1
        results.append(row)

    results_df = pd.DataFrame(results)
    output_df = pd.concat([df, results_df], axis=1)

    output_path = output_dir / input_path.name
    if output_path.exists():
        print(f"Note: overwriting existing {output_path}")
    write_spreadsheet(output_df, output_path)

    scored = len(df) - skipped
    print(f"Scored {scored} rows, skipped {skipped} "
          f"(fewer than {MIN_CONTENT_WORDS} content words).")
    if scored:
        scored_rows = results_df[results_df["aoa_score_pct"].notna()]
        for col in ["aoa_score_pct", "mean_aoa", "avg_sentence_length"]:
            print(f"  Mean {col}: {scored_rows[col].mean():.2f}")
    print(f"\nResults written to {output_path}")


if __name__ == "__main__":
    main()
