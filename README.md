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
| Mean AoA (Kuperman) | 0.638 | +0.078 ✓ |
| SUBTLEX composite | 0.598 | +0.038 ✓ |
| Flesch Reading Ease | 0.560 | baseline |
| SUBTLEX coverage top-5k | 0.536 | −0.024 |

AoA significantly outperforms Flesch (Steiger z=7.91, p<0.001). On informative text specifically — the register closest to administrative correspondence — the gap widens further.

### Honest limitations

- No human-rated corpus of administrative prose exists. CLEAR is literary and informative text rated by teachers for student readers.
- Kuperman AoA is American English. No British AoA database exists at scale. The divergence is modest for common vocabulary but real for some civic/political terms.
- AoA covers approximately 96% of content word tokens in general prose. The remaining 4% (mostly adverbs) falls back to SUBTLEX-UK.

## How it works

1. Paste or type text into the editor
2. Words above the AoA threshold are highlighted inline
3. Hover for the AoA score and suggested SUBTLEX-UK alternatives
4. Sentence length over 25 words flagged separately
5. Document-level score shown in the sidebar

No server. No data sent anywhere. Works offline once loaded.

## Data sources

- **Kuperman et al. (2012)**: Age-of-acquisition ratings for 30,000 English words. *Behavior Research Methods*, 44(4), 978–990.
- **van Heuven et al. (2014)**: SUBTLEX-UK: A new and improved word frequency database for British English. *Quarterly Journal of Experimental Psychology*, 67(6), 1176–1190.
- **Crossley et al. (2022)**: A large-scaled corpus for assessing text readability. *Behavior Research Methods*, 55, 491–507.

## Files

| File | Description |
|---|---|
| `correlations.py` | Validation script — reproduces all results above |
| `CLEAR_corpus_final.csv` | Validation corpus (CC BY-NC-SA, not redistributed here) |
| `aoa_lookup.json` | AoA scores for tool use |
| `subtlex_top10k.json` | SUBTLEX-UK top 10k for replacement suggestions |
| `index.html` | The tool |

## Future work

- British AoA norms — the ideal foundation for this tool does not yet exist
- HOS outcomes study — correlate AoA scores of Housing Ombudsman decisions against resident outcome data (resolution rates, satisfaction, escalation)
- Pre/post editing study — demonstrate that AoA-guided edits improve human preference ratings while Flesch scores do not reliably follow

## Related article

*[Link to article — session 6]*
