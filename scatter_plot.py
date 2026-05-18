import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import spacy
import textstat

corpus = pd.read_csv("CLEAR_corpus_final.csv", encoding="latin-1")
subtlex = pd.read_csv("SUBTLEX-UK.csv", encoding="latin-1", low_memory=False)

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
plot_df["quartile"] = pd.qcut(plot_df["cov_5k"], 4, labels=False)

palette = ["#d0e4f7", "#7ab3d9", "#2e7fbf", "#0d3d6b"]

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
        label=f"Q{q + 1}",
    )

ax.set_xlabel("Flesch Reading Ease", fontsize=11)
ax.set_ylabel("BT Easiness", fontsize=11)
ax.legend(title="Coverage\n(top-5k quartile)", title_fontsize=9, fontsize=9,
          frameon=False, markerscale=2)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.grid(False)

plt.tight_layout()
plt.savefig("scatter_flesch_bt.png", dpi=150)
plt.savefig("scatter_flesch_bt.svg")
print("Saved scatter_flesch_bt.png and scatter_flesch_bt.svg")
