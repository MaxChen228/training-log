import pandas as pd
import json

CSV = "/Users/chenliangyu/Desktop/active/training-log/etl/tfnd/20_2.csv"

df = pd.read_csv(CSV, dtype=str, keep_default_na=False)
print("=== SHAPE ===")
print(df.shape)
print("\n=== COLUMNS ===")
for i, c in enumerate(df.columns):
    print(f"{i:2d}  {c!r}")

print("\n=== FIRST 3 ROWS (json) ===")
for i in range(3):
    print(json.dumps(df.iloc[i].to_dict(), ensure_ascii=False))

# guess name column
name_cols = [c for c in df.columns if "樣品名稱" in c or "食品名稱" in c or "中文名稱" in c]
print("\n=== name col candidates ===", name_cols)

print("\n=== CATEGORIES (資料類別) ===")
if "資料類別" in df.columns:
    print(df["資料類別"].value_counts().head(30).to_string())
if "整合編號" in df.columns:
    print("\n整合編號 unique:", df["整合編號"].nunique(), "/ rows:", len(df))

# unique sample names
if "樣品名稱" in df.columns:
    print("\n樣品名稱 unique:", df["樣品名稱"].nunique())

print("\n=== SAMPLE SEARCH ===")
for kw in ["滷肉飯", "牛肉麵", "白飯", "雞胸肉"]:
    if "樣品名稱" in df.columns:
        hits = df[df["樣品名稱"].str.contains(kw, na=False)]
        print(f"\n--- {kw}: {len(hits)} 筆 ---")
        if len(hits):
            print(json.dumps(hits.iloc[0].to_dict(), ensure_ascii=False))

# energy / kcal column
print("\n=== ENERGY-LIKE COLS ===")
for c in df.columns:
    if "熱量" in c or "kcal" in c.lower() or "kJ" in c or "kj" in c.lower() or "能量" in c:
        print(repr(c))

# missingness on a few key numeric cols
def miss(col):
    if col not in df.columns:
        return f"[no col {col}]"
    s = df[col]
    n = len(s)
    blank = (s.str.strip() == "").sum()
    return f"{col}: blank={blank}/{n} = {blank/n:.1%}"

print()
for c in ["熱量(kcal)", "熱量", "粗蛋白", "粗脂肪", "總碳水化合物", "膳食纖維", "鈉"]:
    print(miss(c))
