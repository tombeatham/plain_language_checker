# Plain Language Checker

A plain language checking tool for administrative correspondence, grounded in psycholinguistic research rather than 1948 readability formulas.

## The problem with Flesch-Kincaid

Flesch Reading Ease uses syllable count as a proxy for word difficulty. This produces systematic errors in both directions:

**False positives** — familiar polysyllabic words penalised as hard:

| Word | Syllables | How common? |
|---|---|---|
| government | 3 | Top 500 British English words |
| different | 3 | Top 300 British English words |
| information | 4 | Top 200 British English words |
| everybody | 4 | Top 1,000 British English words |
| opportunity | 5 | Top 2,000 British English words |

**False negatives** — short domain-specific words passed as easy:

| Word | Syllables | How familiar? |
|---|---|---|
| ASB | 1 | Zipf 1.39 — essentially unknown outside the sector |
| redress | 2 | Zipf 3.29 — low frequency |
| distress | 2 | Zipf 3.82 — below everyday vocabulary threshold |

## The alternative

This tool uses **Age of Acquisition** (Kuperman et al., 2012) as the primary familiarity measure — the age at which a word is typically learned. Words acquired later in life are harder for general readers, regardless of how many syllables they have.

For suggested replacements, the tool uses **SUBTLEX-UK** (van Heuven et al., 2014) — word frequencies derived from British television subtitles — to rank alternatives by familiarity to British English speakers.

## Validation

Tested against the CLEAR corpus (Crossley et al., 2022) — 4,724 texts with human readability ratings from 1,116 teachers using pairwise comparisons.

| Measure | Spearman rho | vs Flesch |
|---|---|---|
| AoA + sentence length composite | 0.661 | +0.101 ✓ |
| Mean AoA (Kuperman) | 0.638 | +0.078 ✓ |
| SUBTLEX composite | 0.598 | +0.038 ✓ |
| Flesch Reading Ease | 0.560 | baseline |
| SUBTLEX coverage top-5k | 0.536 | −0.024 |

The AoA + sentence length composite significantly outperforms Flesch (Steiger z=10.73, p<0.001). AoA alone also significantly outperforms Flesch (Steiger z=7.91, p<0.001). On informative text specifically — the register closest to administrative correspondence — the gap widens further.

### Honest limitations

- No human-rated corpus of administrative prose exists. CLEAR is literary and informative text rated by teachers for student readers.
- Kuperman AoA is American English. No British AoA database exists at scale. The divergence is modest for common vocabulary but real for some civic/political terms.
- AoA covers approximately 96% of content word tokens in HOS decisions. The remaining 4% is mostly adverbs, which Kuperman did not rate. A 2025 extension (Brysbaert et al.) adds AI-generated AoA estimates for a further 4,042 words via the English Crowdsourcing Project; 334 of these appear in the CLEAR corpus above the flagging threshold and are included in the tool.

## How it works

1. Paste or type text into the editor
2. Words above the AoA threshold are highlighted inline
3. Hover for AoA score; low-frequency words also show Zipf score
4. Sentence length over 25 words flagged separately
5. Document-level score shown in the sidebar

No server. No data sent anywhere. Works offline once loaded.

**Tokenising rules.** Hyphenated compounds are split and each part scored separately; internal apostrophes are stripped for lookup so contractions and possessives do not produce stray tokens. A capitalised word that is not in the SUBTLEX top 10k is treated as a proper noun and not scored, unless it opens a sentence (where the capital is grammatical). Override terms are always scored, so domain words such as `ASB` are flagged even when capitalised. Documents under 20 content words show no document score, as the percentage is unreliable on very short text.

## Batch scoring

`score_decisions.py` applies the same AoA engine to a spreadsheet, one row per decision, for corpus-scale work such as the HOS outcomes study. It appends score columns and writes a new file.

```
python score_decisions.py --text-column "Decision Text" --input decisions.csv [--output output/]
```

Alongside the tool's flag percentage (`aoa_score_pct`) it reports `mean_aoa` and `avg_sentence_length` — the two components of the validated composite — plus the flagged word list per row. Run it from the repo root so it can find `data/aoa_lookup.json` and `data/hos_override.json`.

## Data sources

- **Kuperman et al. (2012)**: Age-of-acquisition ratings for 30,000 English words. *Behavior Research Methods*, 44(4), 978–990.
- **Brysbaert et al. (2025)**: Crowdsourced and AI-generated age-of-acquisition norms for vocabulary in print. *Behavior Research Methods*.
- **van Heuven et al. (2014)**: SUBTLEX-UK: A new and improved word frequency database for British English. *Quarterly Journal of Experimental Psychology*, 67(6), 1176–1190.
- **Crossley et al. (2022)**: A large-scaled corpus for assessing text readability. *Behavior Research Methods*, 55, 491–507.

## Files

| File | Description |
|---|---|
| `tool/index.html` | The tool |
| `score_decisions.py` | Batch scorer — applies the AoA engine to a spreadsheet of decisions |
| `data/aoa_lookup.json` | Kuperman + ECP AoA scores |
| `data/subtlex_top10k.json` | SUBTLEX-UK top 10k Zipf scores |
| `data/hos_override.json` | Domain-specific override terms |
| `validation/correlations.py` | Validation script — reproduces all results above |
| `data/CLEAR_corpus_final.csv` | Validation corpus (CC BY-NC-SA, not redistributed here) |

## Future work

- British AoA norms — the ideal foundation for this tool does not yet exist
- HOS outcomes study — correlate AoA scores of Housing Ombudsman decisions against resident outcome data (resolution rates, satisfaction, escalation). `score_decisions.py` provides the bulk scoring this needs
- Replacement suggestions — suggest a plainer alternative for each flagged word, not just the flag. Design options (curated map vs WordNet vs hybrid; tooltip vs click panel) are worked through in CLAUDE.md
- Pre/post editing study — demonstrate that AoA-guided edits improve human preference ratings while Flesch scores do not reliably follow

## Related article

*[Link to article — session 6]*
