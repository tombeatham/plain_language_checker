# Plain Language Checker — Project Context

## General rules

Claude Code rules (Karpathy)

Ask, don't assume. If something is unclear, ask before writing a single line. Never make silent assumptions about intent, architecture, or requirements.
Simplest solution first. Always implement the simplest thing that could work. Do not add abstractions or flexibility that weren't explicitly requested. The tool is a single HTML file — not a React app, not a build pipeline.
Don't touch unrelated code. If a file or function is not directly part of the current task, do not modify it, even if you think it could be improved. This applies especially to validation/correlations.py — add new sections, never rewrite existing ones.
Flag uncertainty explicitly. If you are not confident about an approach or technical detail, say so before proceeding. Confidence without certainty causes more damage than admitting a gap.

## What this project is

A plain language checking tool for administrative correspondence, specifically HOS (Housing Ombudsman Service) decisions. The tool flags words that are unfamiliar to general British English readers.

The project has two components:
1. **Validation** — empirical work establishing which word familiarity measure best predicts human readability judgements
2. **Tool** — a single-file HTML/JS application hostable on GitHub Pages, linked to an article

---

## Key finding

AoA + sentence length composite is the strongest predictor of human readability (rho=0.661 against CLEAR corpus BT_easiness scores, n=4,724; Steiger z=10.73 vs Flesch, p<0.001). AoA alone (rho=0.638) is the strongest single-measure predictor and significantly outperforms Flesch Reading Ease (rho=0.560, Steiger z=7.91, p<0.001) and SUBTLEX-UK coverage (rho=0.536).

**The two measures serve different functions in the tool:**
- **AoA** — flagging engine. Words with late acquisition age are highlighted for the writer.
- **SUBTLEX-UK** — tooltip signal. When a flagged word also has Zipf < 4.0, the tooltip shows the Zipf score as a secondary low-frequency indicator. Replacement suggestions (ranked alternatives by Zipf score) were considered but not implemented — requires further work.

---

## Validated thresholds

- **AoA threshold**: AoA > 10.0 (confirmed against CLEAR data). Threshold sweep from 6–18 in 0.5 steps; rho peaks at −0.624 at AoA 10.0, flat between 9.0–10.5 (rho −0.618 to −0.624), drops sharply above 11.5. Corresponds to end of primary school / Year 6.
- **SUBTLEX-UK Zipf 4**: the published boundary between high and low frequency words (van Heuven et al., 2014). Words below Zipf 4 require effortful recognition.
- **Top 5k SUBTLEX-UK**: empirically the strongest coverage threshold against CLEAR BT_easiness

---

## Validation results (CLEAR corpus, n=4,724)

| Measure | rho | R² |
|---|---|---|
| AoA + sentence length composite | 0.661 | 43.7% |
| Mean AoA (Kuperman) | 0.638 | 40.7% |
| SUBTLEX composite (coverage + sentence length) | 0.598 | 35.8% |
| Flesch Reading Ease | 0.560 | 31.4% |
| SUBTLEX coverage top-5k | 0.536 | 28.7% |
| Mean Zipf | 0.410 | 16.8% |

AoA composite beats Flesch: Steiger z=10.73, p<0.001  
SUBTLEX composite beats Flesch: Steiger z=3.68, p<0.001  
AoA beats Flesch: Steiger z=7.91, p<0.001  
Adding Zipf to AoA adds nothing: Δrho=0.001 (AoA absorbs frequency signal entirely)

### Standardised coefficients (AoA composite)

| Predictor | Standardised coef | Share |
|---|---|---|
| Mean AoA | −0.614 | 76.5% |
| Sentence length | −0.189 | 23.5% |

AoA does three-quarters of the work. Sentence length adds meaningfully but the composite remains primarily an AoA measure.

### Genre split

| Measure | Lit (n=2420) | Info (n=2304) |
|---|---|---|
| Flesch | 0.560 | 0.430 |
| SUBTLEX composite | 0.582 | 0.512 |

SUBTLEX composite outperforms Flesch on both subsets. The gap widens on informative text — the register closest to HOS decisions.

### Sentence length vs coverage independence

Sentence length and SUBTLEX-UK coverage are essentially orthogonal (rho=−0.060). They explain different parts of variance. Flesch's predictive power comes primarily from sentence length; the composite improves on this by replacing syllable count with a direct familiarity measure.

### AoA vs SUBTLEX-UK Zipf

AoA and SUBTLEX-UK Zipf are only moderately correlated (rho=−0.484, n=45,987 matched words). They capture different constructs:
- Frequency: how often a word appears in British television subtitles
- AoA: the developmental age at which a word is typically acquired

AoA catches false negatives that frequency misses — high-frequency but late-acquired words: "commission", "austerity", "coalition", "referendum".

---

## Key word-level findings

### False positives (Flesch penalises, SUBTLEX correctly passes)

1,097 words in the top 5k SUBTLEX-UK have 3+ syllables. Examples:

| Word | Syllables | Zipf |
|---|---|---|
| responsibility | 6 | 4.9 |
| opportunity | 5 | 5.1 |
| university | 5 | 5.3 |
| information | 4 | 5.6 |
| everybody | 4 | 5.2 |
| government | 3 | 5.8 |
| different | 3 | 6.1 |
| together | 3 | 6.0 |

### False negatives (Flesch passes, SUBTLEX correctly flags) — HOS-specific

| Word | HOS freq | Syllables | Zipf |
|---|---|---|---|
| asb | 74,964 | 1 | 1.39 |
| redress | 26,536 | 2 | 3.29 |
| distress | 60,692 | 2 | 3.82 |
| landlord | 1,374,546 | 2 | 3.87 |
| repairs | 205,365 | 2 | 3.75 |

---

## Honest limitations

- No human-rated corpus of administrative prose exists. CLEAR is literary/informative text rated by trained teachers for student readers — not general adult readers of official correspondence.
- Kuperman AoA is American English (Mechanical Turk raters). No British AoA database exists at scale.
- The American/British calibration issue is real but modest for common vocabulary. The divergent words are mostly political/civic terms (coalition, austerity, referendum) and nursery words absent from HOS decisions.
- AoA has an adverb gap — Kuperman covers nouns, verbs, adjectives. Adverbs are mostly absent. Partially addressed by the 2025 ECP supplement (see below).

### 2025 Kuperman extension (Brysbaert et al.)

A 2025 paper extends the Kuperman norms. Three files are in the repo:

| File | Words | Type |
|---|---|---|
| `Crowdsourced Print AoA Estimates for Earlier Acquired Vocabulary (Study 1).xlsx` | 11,074 | Human-rated (crowdsourced) |
| `AI_Generated_AoA_Kuperman_2012.xlsx` | 28,054 | AI-generated (fine-tuned GPT-4o) |
| `AI_Generated_AoA_ECP.xlsx` | 25,076 | AI-generated (fine-tuned GPT-4o) |

Study 1 covers only early-acquired words (AoA < 10) — all below the flagging threshold, so no new flaggable words.

The ECP supplement adds **4,042 words not in Kuperman**, of which **334 appear in the CLEAR corpus with AoA > 10** (newly flaggable). Top examples: `moreover` (11.0), `nevertheless` (11.0), `consequently` (11.0), `comparatively` (11.0), `levy` (12.0), `stakeholder` (13.0).

**Caution**: ECP AoA values cluster at round numbers (11.0, 12.0, 13.0) — the model rounds rather than producing calibrated estimates. These are included in `aoa_lookup.json` alongside Kuperman values and are not separately distinguished in the tool.

---

## Tool architecture

**Flagging**: Words with AoA > 10.0 highlighted inline; hover shows AoA score and Zipf for low-frequency words.  
**Override**: `hos_override.json` — domain-specific terms flagged regardless of AoA rating.  
**Secondary signal**: Sentences over 25 words flagged separately.  
**Format**: Single-file HTML/JS. No server. Hostable on GitHub Pages.  
**Data files**: `data/aoa_lookup.json` · `data/subtlex_top10k.json` · `data/hos_override.json`

**Tokenising rules** (tool and `score_decisions.py` share this logic):
- Hyphenated compounds are split on the hyphen and each component scored separately.
- Internal apostrophes are stripped for lookup (`don't`, `tenant's`), so contractions and possessives do not leave stray single-letter tokens.
- Proper-noun exclusion: a capitalised token whose lowercase is absent from the SUBTLEX top 10k is treated as a name and not scored. Lookup order is **override → proper-noun check → AoA**, so override terms (`ASB`) are flagged even when capitalised. Sentence-initial words are exempt from the exclusion, since the capital there is grammatical, not a proper noun. Residual limitation: a rare flaggable word capitalised mid-sentence and absent from the override list is dropped — the inherent cost of the capital-letter heuristic (inherited from the Word corpus scorer).
- Documents under 20 content words show no document score; the percentage is unreliable on very short text.

**Batch scorer** (`score_decisions.py`): a Python port of the tool's AoA engine onto the `scorer_rows.py` spreadsheet harness from the Word corpus project. Scores a `.csv`/`.xlsx` one row per decision and appends `aoa_score_pct`, `mean_aoa`, `avg_sentence_length`, `long_sentence_count`, `content_word_count`, `flagged_word_count`, `total_words`, and `flagged_words`. Built for the HOS outcomes study. Run from the repo root.

---

## Key citations

- van Heuven, W. J. B., Mandera, P., Keuleers, E., & Brysbaert, M. (2014). SUBTLEX-UK: A new and improved word frequency database for British English. *Quarterly Journal of Experimental Psychology*, 67(6), 1176–1190.
- Kuperman, V., Stadthagen-Gonzalez, H., & Brysbaert, M. (2012). Age-of-acquisition ratings for 30,000 English words. *Behavior Research Methods*, 44(4), 978–990.
- Brysbaert, M. et al. (2025). Crowdsourced and AI-generated age-of-acquisition norms for vocabulary in print: Extending the Kuperman et al. (2012) norms. *Behavior Research Methods*. https://pmc.ncbi.nlm.nih.gov/articles/PMC12500800/
- Crossley, S. A., Heintz, A., Choi, J. S., Batchelor, J., Karimi, M., & Malatinszky, A. (2022). A large-scaled corpus for assessing text readability. *Behavior Research Methods*, 55, 491–507.

---

## Repository structure

```
plain_language_checker/
├── CLAUDE.md                          ← this file
├── README.md                          ← public-facing summary
├── score_decisions.py                 ← batch scorer (AoA engine on spreadsheet harness)
│
├── data/
│   ├── aoa_lookup.json                ← Kuperman + ECP AoA scores (tool)
│   ├── subtlex_top10k.json            ← SUBTLEX-UK top 10k Zipf scores (tool)
│   ├── hos_override.json              ← domain-specific override terms (tool)
│   ├── aoa_crowdsourced.json          ← Brysbaert 2025 Study 1 crowdsourced norms
│   ├── CLEAR_corpus_final.csv         ← validation corpus (CC BY-NC-SA, not in repo)
│   ├── SUBTLEX-UK.csv                 ← word frequency database (not in repo)
│   ├── hos_decisions_v5.csv           ← HOS decisions corpus (not in repo)
│   ├── AoA_51715_words.xlsx           ← Kuperman AoA ratings (not in repo)
│   ├── AI_Generated_AoA_ECP.xlsx      ← Brysbaert 2025 ECP supplement (not in repo)
│   └── AI_Generated_AoA_Kuperman_2012.xlsx ← Brysbaert 2025 Study 3 (not in repo)
│
├── validation/
│   ├── correlations.py                ← main validation script
│   ├── hos_false_positives.py         ← HOS false positive/negative analysis
│   ├── scatter_plot.py                ← Flesch vs BT_easiness scatter
│   ├── scatter_aoa_bt.py              ← AoA vs BT_easiness scatter
│   ├── readability_measures_comparison.py
│   ├── variance_explained.py
│   ├── aoa_coverage.py                ← AoA coverage analysis for HOS corpus
│   ├── check_ecp_coverage.py          ← ECP cross-reference script
│   └── [chart outputs: .png / .svg]
│
└── tool/
    └── index.html                     ← the tool
```

---

## Session plan

| Session | Status | Goal | Output |
|---|---|---|---|
| 1 | ✓ Done | Data prep | Clean datasets |
| 2 | ✓ Done | Validation | Rho table, Steiger, AoA finding |
| 3 | ✓ Done | Scatter plots | Flesch vs BT_easiness, AoA vs BT_easiness, comparison charts |
| 4 | ✓ Done | JSON prep | aoa_lookup.json + subtlex_top10k.json + hos_override.json |
| 5 | ✓ Done | Build tool | Single-file HTML with AoA flagging + sentence length signal |
| 6 | ✓ Done | Article | draft.md (essay) + methods.md (technical appendix), cross-linked |
| Future | — | HOS outcomes study | Correlate AoA scores of decisions against resident outcomes |

---

## Rules

- Do not start a new session's work before completing the current one
- Each session has one output — name it before starting
- Come back to this file at the start of each session to confirm which one you are in
