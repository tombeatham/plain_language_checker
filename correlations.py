import numpy as np
import pandas as pd
import spacy
import textstat
from scipy.stats import norm, spearmanr
from sklearn.linear_model import LinearRegression


def steiger_z(r1, r2, r12, n):
    """
    r1: correlation of model 1 with criterion
    r2: correlation of model 2 with criterion
    r12: correlation between model 1 predictions and model 2 predictions
    n: sample size
    """
    z1 = np.arctanh(r1)
    z2 = np.arctanh(r2)
    r_avg = (r1 + r2) / 2
    f = (1 - r12) / (2 * (1 - r_avg**2))
    SE = np.sqrt(1/(n-3) * (1 + f*(1 - 2*r_avg**2*(1-r12))))
    z = (z1 - z2) / SE
    p = 2 * (1 - norm.cdf(abs(z)))
    return z, p

# Load data
corpus = pd.read_csv("CLEAR_corpus_final.csv", encoding="latin-1")
subtlex = pd.read_csv("SUBTLEX-UK.csv", encoding="latin-1", low_memory=False)
aoa = pd.read_excel("AoA_51715_words.xlsx")
aoa_map      = aoa.dropna(subset=["Word", "AoA_Kup_lem"]).set_index("Word")["AoA_Kup_lem"].to_dict()
perc_map     = aoa.dropna(subset=["Word", "Perc_known"]).set_index("Word")["Perc_known"].to_dict()
aoa_map      = {k.lower(): v for k, v in aoa_map.items()}
perc_map     = {k.lower(): v for k, v in perc_map.items()}

# Build Zipf lookup: lowercase word -> Zipf score
subtlex["word"] = subtlex["Spelling"].str.lower()
zipf_map = subtlex.set_index("word")["LogFreq(Zipf)"].to_dict()

# Rank words by Zipf descending; top-N sets
subtlex_sorted = subtlex.sort_values("LogFreq(Zipf)", ascending=False).reset_index(drop=True)
top3k  = set(subtlex_sorted["word"].iloc[:3000])
top5k  = set(subtlex_sorted["word"].iloc[:5000])
top10k = set(subtlex_sorted["word"].iloc[:10000])

nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])

def lemmatize(text):
    doc = nlp(str(text))
    return [t.lemma_.lower() for t in doc if t.is_alpha]

def coverage(tokens, word_set):
    if not tokens:
        return float("nan")
    return sum(t in word_set for t in tokens) / len(tokens)

def mean_zipf(tokens):
    scores = [zipf_map[t] for t in tokens if t in zipf_map]
    return sum(scores) / len(scores) if scores else float("nan")

# Compute features per excerpt (batch via nlp.pipe for speed)
_docs = pd.Series(
    list(nlp.pipe(corpus["Excerpt"].astype(str), batch_size=64)),
    index=corpus.index,
)
tokens_col         = _docs.map(lambda doc: [t.lemma_.lower() for t in doc if t.is_alpha])
content_tokens_col = _docs.map(lambda doc: [t.lemma_.lower() for t in doc
                                             if t.is_alpha and t.pos_ in {"NOUN", "VERB", "ADJ", "ADV"}])
corpus["cov_3k"]     = tokens_col.map(lambda t: coverage(t, top3k))
corpus["cov_5k"]     = tokens_col.map(lambda t: coverage(t, top5k))
corpus["cov_10k"]    = tokens_col.map(lambda t: coverage(t, top10k))
corpus["mean_zipf"]  = tokens_col.map(mean_zipf)

corpus["mean_aoa"]   = content_tokens_col.map(
    lambda t: np.mean([aoa_map[w]  for w in t if w in aoa_map])  if any(w in aoa_map  for w in t) else float("nan")
)
corpus["mean_perc"]  = content_tokens_col.map(
    lambda t: np.mean([perc_map[w] for w in t if w in perc_map]) if any(w in perc_map for w in t) else float("nan")
)
corpus["aoa_scores"] = content_tokens_col.map(
    lambda t: [aoa_map[w] for w in t if w in aoa_map]
)

matched = content_tokens_col.map(lambda t: sum(w in aoa_map for w in t)).sum()
total   = content_tokens_col.map(len).sum()
print(f"Kuperman coverage: {matched/total:.1%} of content word lemma tokens matched ({matched:,}/{total:,})\n")

# Spearman correlations against BT_easiness
target = corpus["BT_easiness"]
measures = {
    "Flesch-Reading-Ease": corpus["Flesch-Reading-Ease"],
    "Coverage top-3k":     corpus["cov_3k"],
    "Coverage top-5k":     corpus["cov_5k"],
    "Coverage top-10k":    corpus["cov_10k"],
    "Mean Zipf":           corpus["mean_zipf"],
    "Mean AoA":            corpus["mean_aoa"],
    "Mean Perc Known":     corpus["mean_perc"],
}

rows = []
for name, col in measures.items():
    mask = target.notna() & col.notna()
    rho, p = spearmanr(target[mask], col[mask])
    rows.append({"Measure": name, "rho": round(rho, 4), "p-value": f"{p:.2e}"})

print(pd.DataFrame(rows).to_string(index=False))

# Combined model: coverage_5k + mean sentence length
corpus["sent_length"] = corpus["Excerpt"].apply(
    lambda x: np.mean([len(s.split()) for s in str(x).split(".") if s.strip()])
)

X = corpus[["cov_5k", "sent_length"]].dropna()
y = corpus.loc[X.index, "BT_easiness"].dropna()
X = X.loc[y.index]

model = LinearRegression().fit(X, y)
print(f"Coverage coefficient: {model.coef_[0]:.4f}")
print(f"Sentence length coefficient: {model.coef_[1]:.4f}")
predicted = model.predict(X)
rho, p = spearmanr(predicted, y)
print(f"\nSUBTLEX composite (coverage_5k + sent_length): rho={rho:.3f}, p={p:.2e}")

# Steiger Z: composite vs Flesch on the same aligned sample
aligned = corpus[["BT_easiness", "Flesch-Reading-Ease", "cov_5k", "sent_length"]].dropna()
n = len(aligned)

rho_composite, _ = spearmanr(model.predict(aligned[["cov_5k", "sent_length"]]), aligned["BT_easiness"])
rho_flesch, _    = spearmanr(aligned["Flesch-Reading-Ease"], aligned["BT_easiness"])
r12, _           = spearmanr(model.predict(aligned[["cov_5k", "sent_length"]]), aligned["Flesch-Reading-Ease"])

z, p_sz = steiger_z(rho_composite, rho_flesch, r12, n)
print(f"\nSteiger Z (composite vs Flesch): z={z:.3f}, p={p_sz:.3f} (n={n})")

# AoA + sentence length composite
X_aoa = corpus[["mean_aoa", "sent_length"]].dropna()
y_aoa = corpus.loc[X_aoa.index, "BT_easiness"].dropna()
X_aoa = X_aoa.loc[y_aoa.index]

model_aoa = LinearRegression().fit(X_aoa, y_aoa)
predicted_aoa = model_aoa.predict(X_aoa)
rho, p = spearmanr(predicted_aoa, y_aoa)
print(f"\nAoA + sentence length composite: rho={rho:.3f}, p={p:.2e}")
print(f"AoA coef: {model_aoa.coef_[0]:.4f}, sentence length coef: {model_aoa.coef_[1]:.4f}")

# Steiger Z: AoA composite vs Flesch on the same aligned sample
aligned_aoa = corpus[["BT_easiness", "Flesch-Reading-Ease", "mean_aoa", "sent_length"]].dropna()
n_aoa = len(aligned_aoa)

rho_aoa_comp, _ = spearmanr(model_aoa.predict(aligned_aoa[["mean_aoa", "sent_length"]]), aligned_aoa["BT_easiness"])
rho_flesch_aoa, _ = spearmanr(aligned_aoa["Flesch-Reading-Ease"], aligned_aoa["BT_easiness"])
r12_aoa, _ = spearmanr(model_aoa.predict(aligned_aoa[["mean_aoa", "sent_length"]]), aligned_aoa["Flesch-Reading-Ease"])

z_aoa, p_aoa = steiger_z(rho_aoa_comp, rho_flesch_aoa, r12_aoa, n_aoa)
print(f"\nSteiger Z (AoA composite vs Flesch): z={z_aoa:.3f}, p={p_aoa:.3f} (n={n_aoa})")

# Standardised coefficients: relative contribution of each predictor
aoa_std = X_aoa['mean_aoa'].std()
sent_std = X_aoa['sent_length'].std()

aoa_standardised = model_aoa.coef_[0] * aoa_std
sent_standardised = model_aoa.coef_[1] * sent_std

print(f"\nStandardised AoA coefficient: {aoa_standardised:.4f}")
print(f"Standardised sentence length coefficient: {sent_standardised:.4f}")
print(f"AoA share: {abs(aoa_standardised) / (abs(aoa_standardised) + abs(sent_standardised)):.1%}")
print(f"Sentence length share: {abs(sent_standardised) / (abs(aoa_standardised) + abs(sent_standardised)):.1%}")

# Per-category correlations
def corr_table(df, label):
    target = df["BT_easiness"]
    composite_pred = model.predict(df[["cov_5k", "sent_length"]].fillna(df[["cov_5k", "sent_length"]].mean()))
    measures = {
        "Flesch-Reading-Ease": df["Flesch-Reading-Ease"],
        "Coverage top-5k":     df["cov_5k"],
        "Mean Zipf":           df["mean_zipf"],
        "Composite":           pd.Series(composite_pred, index=df.index),
    }
    rows = []
    for name, col in measures.items():
        mask = target.notna() & col.notna()
        rho, p = spearmanr(target[mask], col[mask])
        rows.append({"Measure": name, "rho": round(rho, 4), "p-value": f"{p:.2e}", "n": int(mask.sum())})
    print(f"\n--- {label} ---")
    print(pd.DataFrame(rows).to_string(index=False))

for label, categ in [("Lit", "Lit"), ("Info", "Info")]:
    corr_table(corpus[corpus["Categ"] == categ], label)

# Error asymmetry: syllable-based vs frequency-based word difficulty
corpus["false_positives"] = corpus["Excerpt"].apply(
    lambda x: sum(1 for w in x.split()
    if textstat.syllable_count(w) >= 3
    and w.lower() in top5k) / len(x.split())
)

corpus["false_negatives"] = corpus["Excerpt"].apply(
    lambda x: sum(1 for w in x.split()
    if textstat.syllable_count(w) <= 2
    and w.lower() not in top5k) / len(x.split())
)

corpus["error_asymmetry"] = corpus["false_positives"] - corpus["false_negatives"]

rho, p = spearmanr(corpus["error_asymmetry"].dropna(), corpus.loc[corpus["error_asymmetry"].notna(), "BT_easiness"])
print(f"\nError asymmetry vs BT_easiness: rho={rho:.3f}, p={p:.4f}")

# Sentence length correlations
sl_mask = corpus["sent_length"].notna()
rho, p = spearmanr(corpus.loc[sl_mask, "sent_length"], corpus.loc[sl_mask, "cov_5k"])
print(f"\nSentence length vs SUBTLEX coverage: rho={rho:.3f}, p={p:.4f}")

rho2, p2 = spearmanr(corpus.loc[sl_mask, "sent_length"], corpus.loc[sl_mask, "Flesch-Reading-Ease"])
print(f"Sentence length vs Flesch: rho={rho2:.3f}, p={p2:.4f}")

rho3, p3 = spearmanr(corpus.loc[sl_mask, "sent_length"], corpus.loc[sl_mask, "BT_easiness"])
print(f"Sentence length vs BT_easiness: rho={rho3:.3f}, p={p3:.4f}")

# Proportion of content words with AoA > 10 vs mean AoA vs BT_easiness
corpus["prop_aoa_over_10"] = corpus.apply(
    lambda row: sum(1 for w in row["aoa_scores"] if w > 10) / len(row["aoa_scores"])
    if row["aoa_scores"] else None, axis=1
)

rho, p = spearmanr(corpus["prop_aoa_over_10"].dropna(),
                   corpus.loc[corpus["prop_aoa_over_10"].notna(), "BT_easiness"])
print(f"\nProportion AoA > 10 vs BT_easiness: rho={rho:.3f}, p={p:.2e}")

rho2, p2 = spearmanr(corpus["mean_aoa"].dropna(),
                     corpus.loc[corpus["mean_aoa"].notna(), "BT_easiness"])
print(f"Mean AoA vs BT_easiness: rho={rho2:.3f}, p={p2:.2e}")
