# Plain Language Checker — Project Context

## What this project is

A plain language checking tool for administrative correspondence, specifically HOS (Housing Ombudsman Service) decisions. The tool flags words that are unfamiliar to general British English readers and suggests simpler alternatives.

The project has two components:
1. **Validation** — empirical work establishing which word familiarity measure best predicts human readability judgements
2. **Tool** — a single-file HTML/JS application hostable on GitHub Pages, linked to an article

---

## Key finding

Age of Acquisition (AoA, Kuperman et al. 2012) is the strongest predictor of human readability (rho=0.638 against CLEAR corpus BT_easiness scores, n=4,724). It significantly outperforms Flesch Reading Ease (rho=0.560, Steiger z=7.91, p<0.001) and SUBTLEX-UK coverage (rho=0.536).

**The two measures serve different functions in the tool:**
- **AoA** — flagging engine. Words with late acquisition age are highlighted for the writer.
- **SUBTLEX-UK** — replacement engine. When a word is flagged, SUBTLEX-UK provides ranked British English alternatives sorted by Zipf score.

---

## Validated thresholds

- **AoA threshold**: AoA > 10.0 (confirmed against CLEAR data). Threshold sweep from 6–18 in 0.5 steps; rho peaks at −0.624 at AoA 10.0, flat between 9.0–10.5 (rho −0.618 to −0.624), drops sharply above 11.5. Corresponds to end of primary school / Year 6.
- **SUBTLEX-UK Zipf 4**: the published boundary between high and low frequency words (van Heuven et al., 2014). Words below Zipf 4 require effortful recognition.
- **Top 5k SUBTLEX-UK**: empirically the strongest coverage threshold against CLEAR BT_easiness

---

## Validation results (CLEAR corpus, n=4,724)

| Measure | rho | R² |
|---|---|---|
| Mean AoA (Kuperman) | 0.638 | 40.7% |
| SUBTLEX composite (coverage + sentence length) | 0.598 | 35.8% |
| Flesch Reading Ease | 0.560 | 31.4% |
| SUBTLEX coverage top-5k | 0.536 | 28.7% |
| Mean Zipf | 0.410 | 16.8% |

Composite beats Flesch: Steiger z=3.68, p<0.001  
AoA beats Flesch: Steiger z=7.91, p<0.001  
Adding Zipf to AoA adds nothing: Δrho=0.001 (AoA absorbs frequency signal entirely)

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
- AoA has an adverb gap — Kuperman covers nouns, verbs, adjectives. Adverbs are mostly absent. SUBTLEX-UK fallback covers this.

---

## Tool architecture

**Flagging**: Mean AoA of content word lemmas. Words above AoA threshold highlighted inline.  
**Replacement**: SUBTLEX-UK Zipf-ranked alternatives for flagged words.  
**Secondary signal**: Sentence length over 25 words flagged separately.  
**Format**: Single-file HTML/JS. No server. Hostable on GitHub Pages.  
**Data files**: `aoa_lookup.json` (Kuperman top entries) + `subtlex_top10k.json` (replacement suggestions)

---

## Key citations

- van Heuven, W. J. B., Mandera, P., Keuleers, E., & Brysbaert, M. (2014). SUBTLEX-UK: A new and improved word frequency database for British English. *Quarterly Journal of Experimental Psychology*, 67(6), 1176–1190.
- Kuperman, V., Stadthagen-Gonzalez, H., & Brysbaert, M. (2012). Age-of-acquisition ratings for 30,000 English words. *Behavior Research Methods*, 44(4), 978–990.
- Crossley, S. A., Heintz, A., Choi, J. S., Batchelor, J., Karimi, M., & Malatinszky, A. (2022). A large-scaled corpus for assessing text readability. *Behavior Research Methods*, 55, 491–507.

---

## Repository structure

```
plain_language_checker/
├── CLAUDE.md                  ← this file
├── README.md                  ← public-facing summary
├── CLEAR_corpus.csv           ← validation corpus (CC BY-NC-SA)
├── SUBTLEX-UK.xlsx            ← word frequency database
├── AoA_ratings_Kuperman.xlsx  ← age of acquisition ratings
├── correlations.py            ← main validation script
├── scatter_flesch_bt.png      ← scatter plot (session 3)
├── scatter_flesch_bt.svg      ← scatter plot (SVG)
├── aoa_lookup.json            ← tool data (session 4)
├── subtlex_top10k.json        ← tool data (session 4)
└── index.html                 ← the tool (session 5)
```

---

## Session plan

| Session | Status | Goal | Output |
|---|---|---|---|
| 1 | ✓ Done | Data prep | Clean datasets |
| 2 | ✓ Done | Validation | Rho table, Steiger, AoA finding |
| 3 | Next | Scatter plot | One chart: Flesch vs BT_easiness, coloured by AoA quartile |
| 4 | — | JSON prep | aoa_lookup.json + subtlex_top10k.json |
| 5 | — | Build tool | Single-file HTML with AoA flagging + SUBTLEX suggestions |
| 6 | — | Article | Write up, link to tool |
| Future | — | HOS outcomes study | Correlate AoA scores of decisions against resident outcomes |

---

## Rules

- Do not start a new session's work before completing the current one
- Each session has one output — name it before starting
- The distraction risk is highest after session 2 — resist building before the chart is done
- Come back to this file at the start of each session to confirm which one you are in
