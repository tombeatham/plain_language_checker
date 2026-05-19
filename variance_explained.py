import matplotlib.pyplot as plt

MEASURES = [
    ("Syllables per word",     21.6),
    ("SUBTLEX coverage top-5k", 28.7),
    ("Flesch Reading Ease",    31.4),
    ("SUBTLEX composite",      35.8),
    ("Mean AoA",               40.7),
    ("AoA composite",          43.7),
]

LABELS = [m[0] for m in MEASURES]
VALUES = [m[1] for m in MEASURES]

AOA_SET    = {"Mean AoA", "AoA composite"}
BASE_COLOUR = "#c5d5e4"
AOA_COLOUR  = "#4a7ba7"
FLESCH_VAL  = 31.4

colours = [AOA_COLOUR if lbl in AOA_SET else BASE_COLOUR for lbl in LABELS]

fig, ax = plt.subplots(figsize=(10, 6))
fig.subplots_adjust(left=0.26, right=0.90, top=0.93, bottom=0.12)

bars = ax.barh(LABELS, VALUES, color=colours, height=0.55)

for bar, val in zip(bars, VALUES):
    ax.text(val + 0.6, bar.get_y() + bar.get_height() / 2,
            f"{val:.1f}%", va="center", ha="left", fontsize=9, color="#333333")

# Flesch reference line
ax.axvline(FLESCH_VAL, color="#888888", linestyle="--", linewidth=1, zorder=0)
ax.text(FLESCH_VAL, 5.45, "Flesch baseline",
        ha="center", va="bottom", fontsize=8, color="#888888")

ax.set_xlabel("Variance explained (R²)", fontsize=10, labelpad=8)
ax.set_xlim(0, 52)
ax.set_ylim(-0.5, 6.1)
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.0f}%"))

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_visible(False)
ax.tick_params(axis="y", length=0, labelsize=10)
ax.tick_params(axis="x", labelsize=9)
ax.grid(False)

plt.savefig("variance_explained.png", dpi=150, bbox_inches="tight")
plt.savefig("variance_explained.svg", bbox_inches="tight")
print("Saved variance_explained.png and .svg")
