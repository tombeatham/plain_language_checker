import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import spacy

corpus = pd.read_csv("CLEAR_corpus_final.csv", encoding="latin-1")
aoa_df = pd.read_excel("AoA_51715_words.xlsx")
aoa_map = aoa_df.dropna(subset=["Word", "AoA_Kup_lem"]).set_index("Word")["AoA_Kup_lem"].to_dict()
aoa_map = {k.lower(): v for k, v in aoa_map.items()}

nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])

_docs = pd.Series(
    list(nlp.pipe(corpus["Excerpt"].astype(str), batch_size=64)),
    index=corpus.index,
)
content_tokens_col = _docs.map(lambda doc: [
    t.lemma_.lower() for t in doc
    if t.is_alpha and t.pos_ in {"NOUN", "VERB", "ADJ", "ADV"}
])

corpus["mean_aoa"] = content_tokens_col.map(
    lambda t: np.mean([aoa_map[w] for w in t if w in aoa_map])
    if any(w in aoa_map for w in t) else float("nan")
)
corpus["sent_length"] = corpus["Excerpt"].apply(
    lambda x: np.mean([len(s.split()) for s in str(x).split(".") if s.strip()])
)

plot_df = corpus[["mean_aoa", "BT_easiness", "sent_length"]].dropna()
plot_df["quartile"] = pd.qcut(plot_df["sent_length"], 4, labels=False)

# Light = short sentences (Q1), dark = long sentences (Q4)
palette = ["#d0e4f7", "#7ab3d9", "#2e7fbf", "#0d3d6b"]
labels = ["Short", "Mid-short", "Mid-long", "Long"]

fig, ax = plt.subplots(figsize=(7, 5))

for q in range(4):
    mask = plot_df["quartile"] == q
    ax.scatter(
        plot_df.loc[mask, "mean_aoa"],
        plot_df.loc[mask, "BT_easiness"],
        c=palette[q],
        s=8,
        alpha=0.6,
        linewidths=0,
        label=labels[q],
    )

ax.set_xlabel("Mean Age of Acquisition", fontsize=11)
ax.set_ylabel("BT Easiness", fontsize=11)
ax.legend(title="Sentence length", title_fontsize=9, fontsize=9,
          frameon=False, markerscale=2)
ax.set_title("Each point is one of 4,724 texts rated by human teachers",
             fontsize=9, color="#666666", pad=8)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.grid(False)

plt.tight_layout()
plt.savefig("scatter_aoa_bt.png", dpi=150)
plt.savefig("scatter_aoa_bt.svg")
print("Saved scatter_aoa_bt.png and scatter_aoa_bt.svg")
