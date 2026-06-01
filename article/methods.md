# Methods — Technical Appendix

This document records how the readability measures were computed, validated, and
compared, so the figures in the main article can be reproduced or contested. It
covers the validation pipeline (the empirical work behind the AoA finding) and
the runtime processing in the tool itself. The two are deliberately different,
and the difference is documented below.

---

## 1. Data sources

| Dataset | Role | Notes |
|---|---|---|
| CLEAR corpus (Crossley et al., 2022) | Validation criterion | 4,724 texts with `BT_easiness` scores — human readability ratings from trained teachers. American English. |
| Kuperman AoA norms (2012) | Word-difficulty measure | 51,694 words, `AoA_Kup_lem` column (lemma-level ratings). American English (Mechanical Turk raters). |
| Brysbaert et al. (2025) ECP supplement | AoA extension | AI-generated (fine-tuned GPT-4o). Adds 4,042 words not in Kuperman; values cluster at round numbers — see §6. |
| SUBTLEX-UK (van Heuven et al., 2014) | Frequency measure | British English subtitle frequencies, `LogFreq(Zipf)` column. |
| HOS decisions corpus (`hos_decisions_v5.csv`) | Domain corpus | 15,683 Housing Ombudsman decisions, 27.1M content-word tokens. Used for coverage and vocabulary analysis, not for validation. |

The criterion (`BT_easiness`) is a Bradley–Terry easiness score: higher means
teachers judged the text easier to read. All correlations below are signed with
respect to this — a measure of *difficulty* (Flesch, AoA) correlates negatively
with easiness; the magnitude is what is compared.

---

## 2. Text processing (validation pipeline)

All validation text was processed with **spaCy** (`en_core_web_sm`, with the
parser and NER components disabled for speed).

**Tokenisation and lemmatisation.** Each excerpt is run through spaCy; tokens are
reduced to lemmas and lowercased (`token.lemma_.lower()`). Only alphabetic tokens
are kept (`token.is_alpha`), discarding numbers, punctuation, and mixed tokens.

Lemmatisation matters because the AoA and frequency lookups are keyed on base
forms. Without it, "repairs", "repaired", and "repairing" would each miss the
entry for "repair". Lemmatising collapses inflected forms onto the dictionary
headword, which is what the norms actually rate.

**Content-word filtering (AoA only).** For the AoA measures, tokens are further
restricted to content parts of speech — `NOUN`, `VERB`, `ADJ`, `ADV`. Function
words (articles, prepositions, conjunctions) are excluded: they carry little
difficulty signal, are near-universal across texts, and are unevenly represented
in the AoA norms. Mean AoA is therefore the mean rated acquisition age of the
*content* lemmas in a text.

**Coverage measures (SUBTLEX).** The SUBTLEX coverage measures use all alphabetic
lemma tokens (not just content words): coverage is the proportion of tokens
falling within the top-N most frequent words (top-3k / 5k / 10k by Zipf).

---

## 3. British–American normalisation

Kuperman's norms are American English; the HOS corpus is British. A direct lemma
lookup therefore misses British spellings ("organisation", "behaviour",
"recognise") that have American entries in the norms.

For the **HOS coverage analysis**, unmatched lemmas were passed through
`breame.spelling.get_american_spelling()` and re-looked-up. This is a one-way
normalisation: try the British lemma first, fall back to its American spelling.

| Stage | Content-word lemma coverage |
|---|---|
| Pre-normalisation | 96.40% |
| Post-normalisation (breame) | 97.38% |

The +0.98pp gain confirms the British/American spelling divergence is real but
modest in volume. Note this is a *processing step*, distinct from the *limitation*
discussed in the article — that Kuperman's underlying ratings are American and may
diverge in value (not just spelling) for politically specific vocabulary. Spelling
normalisation fixes the first problem; nothing fixes the second without a British
AoA database.

Normalisation was **not** applied to the CLEAR validation corpus, which is already
American English.

---

## 4. Statistical methods

**Correlations.** All measure-vs-criterion associations are Spearman's rho
(`scipy.stats.spearmanr`), computed on the pairwise-complete sample for each
measure (a text is included only where both the measure and `BT_easiness` are
defined).

**Composites.** The composite measures (AoA + sentence length; coverage +
sentence length) are ordinary least-squares linear regressions
(`sklearn.linear_model.LinearRegression`) predicting `BT_easiness` from the two
inputs. The composite's rho is the Spearman correlation between the model's fitted
values and the criterion.

Sentence length is the mean words per sentence, computed by splitting the excerpt
on `.` and averaging whitespace-delimited token counts per segment.

**Significance of the difference between measures.** Because the measures are
correlated with each other as well as with the criterion, comparing two
correlations requires a dependent-samples test. Steiger's z is used (custom
implementation, validated against the standard formula), taking the two
measure–criterion correlations, the inter-measure correlation, and n. This is the
source of the headline result:

| Comparison | Steiger z | p |
|---|---|---|
| AoA composite vs Flesch | 10.73 | < 0.001 |
| AoA alone vs Flesch | 7.91 | < 0.001 |
| SUBTLEX composite vs Flesch | 3.68 | < 0.001 |

**Standardised coefficients.** To decompose the AoA composite, each predictor's
raw coefficient is multiplied by that predictor's standard deviation in the
sample. The two standardised coefficients are then expressed as shares of their
combined absolute magnitude: AoA 76.5%, sentence length 23.5%.

---

## 5. Threshold selection

The flagging threshold (AoA > 10.0) was set by a parameter sweep, not assumed. The
threshold was varied from 6 to 18 in 0.5 steps; at each value the proportion of
content words above threshold was correlated with `BT_easiness`. Rho peaks at
−0.624 at AoA 10.0, is flat across 9.0–10.5 (−0.618 to −0.624), and drops sharply
above 11.5. AoA 10.0 corresponds to the end of primary school (Year 6) — a
defensible plain-language target as well as the empirical optimum.

The sentence-length signal uses a 25-word threshold, consistent with standard
plain-English guidance; it is reported as a secondary flag rather than folded into
the primary score.

---

## 6. The ECP supplement caveat

The 2025 Brysbaert ECP file adds 4,042 words not in Kuperman, of which 334 appear
in CLEAR with AoA > 10 (newly flaggable). These values are AI-generated by a
fine-tuned GPT-4o and **cluster at round numbers** (11.0, 12.0, 13.0) — the model
rounds rather than producing calibrated estimates. They are merged into
`aoa_lookup.json` alongside Kuperman values and are **not** separately
distinguished in the tool. A reader who wants only human-rated norms should treat
the round-numbered entries with caution. The Brysbaert Study 1 crowdsourced norms
were not used for flagging because they cover only early-acquired words (AoA < 10),
all below threshold.

---

## 7. The tool's runtime processing (and how it differs)

The live tool (`tool/index.html`) does **not** replicate the validation pipeline.
It is a single HTML file with no server and no NLP library, and it makes a
deliberate trade of linguistic precision for zero-dependency portability. The
differences are worth stating plainly:

| Step | Validation pipeline | Live tool |
|---|---|---|
| Tokenisation | spaCy | split on letter runs (`/([A-Za-z]+)/`) |
| Lemmatisation | yes (spaCy) | **none** — surface form only |
| POS filtering | content words only | none — every word is looked up |
| British→American | breame fallback | **none** |
| Lookup | lemma → AoA | lowercased surface form → `override` then `aoa_lookup` |
| Flag rule | — | AoA > 10.0, or `null` → "Specialist term" |

The practical consequence: the tool flags a word only if that **exact surface
form** is a key in the lookup files. Inflected forms ("granted", "repairs") are
caught only where the data already contains them. This is a known simplification,
accepted because the tool's purpose is to surface obvious candidates for revision
in the browser, not to reproduce the corpus-level statistics. The override file
(`hos_override.json`) compensates for the most important domain terms by listing
them explicitly, including surface variants where needed.

If the tool were ever to need corpus-grade accuracy, the right change would be to
pre-lemmatise the lookup keys or ship a lightweight stemmer — not to add a runtime
NLP dependency.

---

## 8. Reproducing the figures

| Output | Script |
|---|---|
| Correlation table, composites, Steiger z, standardised coefficients, genre split | `validation/correlations.py` |
| HOS AoA coverage (pre/post normalisation) | `validation/aoa_coverage.py` |
| HOS false positives / negatives vs Flesch | `validation/hos_false_positives.py` |
| Flesch vs BT_easiness scatter | `validation/scatter_plot.py` |
| AoA vs BT_easiness scatter | `validation/scatter_aoa_bt.py` |
| Six-measure comparison chart | `validation/readability_measures_comparison.py` |
| Variance-explained chart | `validation/variance_explained.py` |
| ECP cross-reference | `validation/check_ecp_coverage.py` |

The CLEAR corpus, SUBTLEX-UK, the Kuperman spreadsheet, and the HOS corpus are
licensed datasets and are not committed to the repository; paths are configured at
the top of each script. The derived lookup files the tool depends on
(`aoa_lookup.json`, `subtlex_top10k.json`, `hos_override.json`) are in `data/`.

---

## References

See the main article for full citations (Crossley et al. 2022; Flesch 1948;
Kuperman et al. 2012; Brysbaert et al. 2025; van Heuven et al. 2014).
