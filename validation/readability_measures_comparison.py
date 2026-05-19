import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import spacy
import textstat
from scipy.stats import spearmanr
from sklearn.linear_model import LinearRegression

# ── Data loading ───────────────────────────────────────────────────────────────
corpus = pd.read_csv("../data/CLEAR_corpus_final.csv", encoding="latin-1")
subtlex = pd.read_csv("../data/SUBTLEX-UK.csv", encoding="latin-1", low_memory=False)
aoa_df = pd.read_excel("../data/AoA_51715_words.xlsx")

aoa_map = aoa_df.dropna(subset=["Word", "AoA_Kup_lem"]).set_index("Word")["AoA_Kup_lem"].to_dict()
aoa_map = {k.lower(): v for k, v in aoa_map.items()}

subtlex["word"] = subtlex["Spelling"].str.lower()
subtlex_sorted = subtlex.sort_values("LogFreq(Zipf)", ascending=False).reset_index(drop=True)
top5k = set(subtlex_sorted["word"].iloc[:5000])

# ── NLP pipeline ───────────────────────────────────────────────────────────────
nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])
_docs = pd.Series(
    list(nlp.pipe(corpus["Excerpt"].astype(str), batch_size=64)),
    index=corpus.index,
)
tokens_col = _docs.map(lambda doc: [t.lemma_.lower() for t in doc if t.is_alpha])
content_tokens_col = _docs.map(lambda doc: [
    t.lemma_.lower() for t in doc
    if t.is_alpha and t.pos_ in {"NOUN", "VERB", "ADJ", "ADV"}
])

# ── Features ───────────────────────────────────────────────────────────────────
corpus["cov_5k"] = tokens_col.map(
    lambda t: sum(w in top5k for w in t) / len(t) if t else float("nan")
)
corpus["mean_aoa"] = content_tokens_col.map(
    lambda t: np.mean([aoa_map[w] for w in t if w in aoa_map])
    if any(w in aoa_map for w in t) else float("nan")
)
corpus["mean_syllables"] = corpus["Excerpt"].apply(
    lambda x: textstat.avg_syllables_per_word(str(x)) or float("nan")
)
corpus["sent_length"] = corpus["Excerpt"].apply(
    lambda x: np.mean([len(s.split()) for s in str(x).split(".") if s.strip()])
)

# ── Composite models (OLS on aligned rows) ─────────────────────────────────────
X_sub = corpus[["cov_5k", "sent_length"]].dropna()
y_sub = corpus.loc[X_sub.index, "BT_easiness"].dropna()
X_sub = X_sub.loc[y_sub.index]
model_sub = LinearRegression().fit(X_sub, y_sub)
corpus["subtlex_composite"] = float("nan")
corpus.loc[X_sub.index, "subtlex_composite"] = model_sub.predict(X_sub)

X_aoa = corpus[["mean_aoa", "sent_length"]].dropna()
y_aoa = corpus.loc[X_aoa.index, "BT_easiness"].dropna()
X_aoa = X_aoa.loc[y_aoa.index]
model_aoa = LinearRegression().fit(X_aoa, y_aoa)
corpus["aoa_composite"] = float("nan")
corpus.loc[X_aoa.index, "aoa_composite"] = model_aoa.predict(X_aoa)

# ── Panel definitions ──────────────────────────────────────────────────────────
PANELS = [
    {"col": "mean_syllables",      "title": "Syllables per word",     "xlabel": "Syllables per word (negated)",  "negate": True},
    {"col": "Flesch-Reading-Ease", "title": "Flesch Reading Ease",    "xlabel": "Flesch Reading Ease",           "negate": False},
    {"col": "cov_5k",              "title": "SUBTLEX coverage top-5k","xlabel": "SUBTLEX coverage top-5k",       "negate": False},
    {"col": "subtlex_composite",   "title": "SUBTLEX composite",      "xlabel": "SUBTLEX composite predicted",  "negate": False},
    {"col": "mean_aoa",            "title": "Mean AoA",               "xlabel": "Mean AoA (negated)",           "negate": True},
    {"col": "aoa_composite",       "title": "AoA composite",          "xlabel": "AoA composite predicted",      "negate": False},
]

BLUE = "#4a7ba7"
ARROW_COLOUR = "#aaaaaa"
ARROW_TEXT = "← harder | easier →"

# ── Figure ─────────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(2, 3, figsize=(14, 10), sharey=True)
fig.subplots_adjust(hspace=0.52, wspace=0.12, left=0.12, right=0.97, top=0.94, bottom=0.15)

for ax, panel in zip(axes.flat, PANELS):
    col = corpus[panel["col"]].dropna()
    target = corpus.loc[col.index, "BT_easiness"].dropna()
    col = col.loc[target.index]
    x = -col if panel["negate"] else col

    rho, _ = spearmanr(x, target)

    ax.scatter(x, target, c=BLUE, s=5, alpha=0.3, linewidths=0)

    ax.text(0.05, 0.95, f"ρ = {rho:.3f}",
            transform=ax.transAxes, ha="left", va="top",
            fontsize=9, color="#333333")

    ax.set_title(panel["title"], fontsize=10, pad=6)
    ax.set_xlabel(panel["xlabel"], fontsize=9, labelpad=4)
    ax.text(0.5, -0.21, ARROW_TEXT,
            transform=ax.transAxes, ha="center", va="top",
            fontsize=8, color=ARROW_COLOUR)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(False)
    ax.tick_params(labelsize=8)

# Shared y-axis: label + direction annotation
fig.text(0.047, 0.5, "Human Readability (BT Easiness)",
         va="center", ha="center", rotation="vertical", fontsize=11)
fig.text(0.013, 0.5, ARROW_TEXT,
         va="center", ha="center", rotation="vertical",
         fontsize=8, color=ARROW_COLOUR)

plt.savefig("readability_measures_comparison.png", dpi=150, bbox_inches="tight")
plt.savefig("readability_measures_comparison.svg", bbox_inches="tight")
print("Saved readability_measures_comparison.png and .svg")
