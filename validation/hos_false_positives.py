import re
from collections import Counter

import pandas as pd
import textstat

# Load SUBTLEX
subtlex = pd.read_csv("../data/SUBTLEX-UK.csv", encoding="latin-1", low_memory=False)
subtlex = subtlex.dropna(subset=["Spelling"])
subtlex = subtlex.sort_values("LogFreq(Zipf)", ascending=False).reset_index(drop=True)
subtlex["rank"] = subtlex.index + 1
zipf_map = subtlex.set_index("Spelling")["LogFreq(Zipf)"].to_dict()
top5k = set(subtlex["Spelling"].str.lower().iloc[:5000])

# Load HOS decisions
hos = pd.read_csv("../data/hos_decisions_v5.csv", encoding="latin-1")
text = " ".join(hos["full_text"].dropna().astype(str))

tokens = [t for t in re.findall(r"[a-z]+", text.lower()) if t.isalpha()]
counts = Counter(tokens)

fp_rows, fn_rows = [], []
for word, freq in counts.most_common():
    syl = textstat.syllable_count(word)
    in_top5k = word in top5k
    zipf = zipf_map.get(word)
    row = {"word": word, "freq_in_hos": freq, "syllables": syl, "zipf": round(zipf, 2) if zipf is not None else None}
    if syl >= 3 and in_top5k:
        fp_rows.append(row)
    elif syl <= 2 and not in_top5k:
        fn_rows.append(row)

fp = pd.DataFrame(fp_rows).sort_values("freq_in_hos", ascending=False).head(25)
fn = pd.DataFrame(fn_rows).sort_values("freq_in_hos", ascending=False).head(25)

print("FALSE POSITIVES (polysyllabic but common - top 5k):")
print(fp.to_string(index=False))
print()
print("FALSE NEGATIVES (short but rare - outside top 5k):")
print(fn.to_string(index=False))
