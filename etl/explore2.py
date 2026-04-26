import pandas as pd
import json

CSV = "/Users/chenliangyu/Desktop/active/training-log/etl/tfnd/20_2.csv"
df = pd.read_csv(CSV, dtype=str, keep_default_na=False)

print("=== 食品分類 (categories) ===")
cats = df.drop_duplicates("整合編號")["食品分類"].value_counts()
print(cats.to_string())
print("total cats:", len(cats), "total foods:", df["整合編號"].nunique())

print("\n=== 分析項分類 unique ===")
print(df["分析項分類"].value_counts().to_string())

print("\n=== 分析項 unique (top 60) ===")
print(df["分析項"].value_counts().head(60).to_string())

# Look for kcal / protein / fat / carb / fiber / sodium
print("\n=== KEY ANALYTES ===")
for kw in ["熱量", "蛋白", "脂肪", "碳水", "纖維", "鈉", "水分", "灰分"]:
    rows = df[df["分析項"].str.contains(kw, na=False)]["分析項"].unique()
    print(f"  {kw}: {list(rows)}")

# 含量單位 for 熱量
print("\n=== units for 熱量 ===")
e = df[df["分析項"].str.contains("熱量", na=False)]
print(e["含量單位"].value_counts().to_string())
print("sample 熱量 row:")
print(json.dumps(e.iloc[0].to_dict(), ensure_ascii=False))

# Pivot test on 4 sample foods
samples = df[df["樣品名稱"].isin(["白飯", "雞胸肉(生)", "雞蛋", "豬肉(瘦)"])]
print("\n=== sample names matched ===")
print(samples["樣品名稱"].value_counts().to_string())

# search loosely
print("\n=== loose grep 雞胸 / 牛肉麵 / 滷 / 蛋 ===")
for kw in ["雞胸", "牛肉麵", "滷", "雞蛋"]:
    hits = df[df["樣品名稱"].str.contains(kw, na=False)]["樣品名稱"].unique()[:8]
    print(f"  {kw}: {list(hits)}")

# Build pivot with macros for 4 picks
picks = ["白飯", "雞胸肉(生,平均值)", "牛肉麵", "滷肉飯"]
# get any one for each keyword
def first_id(kw):
    h = df[df["樣品名稱"].str.contains(kw, na=False)]
    if len(h) == 0:
        return None, None
    return h.iloc[0]["整合編號"], h.iloc[0]["樣品名稱"]

print("\n=== MACROS for samples ===")
KEY = ["熱量", "粗蛋白", "粗脂肪", "總碳水化合物", "膳食纖維", "鈉", "水分"]
for kw in ["白飯", "雞胸", "牛肉麵", "滷", "雞蛋"]:
    fid, name = first_id(kw)
    if not fid:
        print(f"--- {kw}: NOT FOUND ---")
        continue
    sub = df[(df["整合編號"] == fid) & (df["分析項"].isin(KEY))]
    macros = {r["分析項"]: f'{r["每100克含量"].strip()} {r["含量單位"]}' for _, r in sub.iterrows()}
    print(f"--- {kw} -> {fid} {name} ---")
    print(json.dumps(macros, ensure_ascii=False, indent=2))

# missingness: among foods (整合編號 unique), how many have a 熱量 value?
foods = df["整合編號"].nunique()
e_have = df[(df["分析項"].str.contains("熱量", na=False)) & (df["每100克含量"].str.strip() != "")]["整合編號"].nunique()
print(f"\n熱量 coverage: {e_have}/{foods} = {e_have/foods:.1%}")

# duplicate names
name_counts = df.drop_duplicates("整合編號")["樣品名稱"].value_counts()
dups = name_counts[name_counts > 1]
print(f"重複名稱: {len(dups)} 個樣品名出現多次, 最多 {dups.head(5).to_dict()}")

# english name fill rate
en = df.drop_duplicates("整合編號")
en_filled = (en["樣品英文名稱"].str.strip() != "").sum()
print(f"英文名 fill: {en_filled}/{len(en)} = {en_filled/len(en):.1%}")
