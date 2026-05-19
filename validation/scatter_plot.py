import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import spacy
import textstat

corpus = pd.read_csv("../data/CLEAR_corpus_final.csv", encoding="latin-1")
subtlex = pd.read_csv("../data/SUBTLEX-UK.csv", encoding="latin-1", low_memory=False)

subtlex["word"] = subtlex["Spelling"].str.lower()
subtlex_sorted = subtlex.sort_values("LogFreq(Zipf)", ascending=False).reset_index(drop=True)
top5k = set(subtlex_sorted["word"].iloc[:5000])

nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])
tokens_col = pd.Series(
    list(nlp.pipe(corpus["Excerpt"].astype(str), batch_size=64)),
    index=corpus.index,
).map(lambda doc: [t.lemma_.lower() for t in doc if t.is_alpha])

corpus["cov_5k"] = tokens_col.map(
    lambda t: sum(w in top5k for w in t) / len(t) if t else float("nan")
)

plot_df = corpus[["Flesch-Reading-Ease", "BT_easiness", "cov_5k"]].dropna()
plot_df = plot_df[plot_df["Flesch-Reading-Ease"] >= 0]
plot_df["quartile"] = pd.qcut(plot_df["cov_5k"], 4, labels=False)

# Dark = low familiarity (Q1), light = high familiarity (Q4)
palette = ["#0d3d6b", "#2e7fbf", "#7ab3d9", "#d0e4f7"]
labels = ["Low", "Mid-low", "Mid-high", "High"]

fig, ax = plt.subplots(figsize=(7, 5))

for q in range(4):
    mask = plot_df["quartile"] == q
    ax.scatter(
        plot_df.loc[mask, "Flesch-Reading-Ease"],
        plot_df.loc[mask, "BT_easiness"],
        c=palette[q],
        s=8,
        alpha=0.6,
        linewidths=0,
        label=labels[q],
    )

ax.set_xlabel("Flesch Reading Ease", fontsize=11)
ax.set_ylabel("BT Easiness", fontsize=11)
ax.legend(title="Familiar vocabulary", title_fontsize=9, fontsize=9,
          frameon=False, markerscale=2)

ax.set_title("Each point is one of 4,724 texts rated by human teachers",
             fontsize=9, color="#666666", pad=8)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.grid(False)

plt.tight_layout()
plt.savefig("scatter_flesch_bt.png", dpi=150)
plt.savefig("scatter_flesch_bt.svg")
print("Saved scatter_flesch_bt.png and scatter_flesch_bt.svg")
