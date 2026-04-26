"""TFND 2025-12 -> Supabase food_library 匯入腳本。

用法:
    source ../.env && .venv/bin/python import_foods.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pandas as pd
import psycopg
from psycopg.types.json import Jsonb

CSV_PATH = Path(__file__).parent / "tfnd" / "20_2.csv"
SOURCE_REF = "TFND-2025-12"

# 分析項中文 -> food_library 欄位
ITEM_TO_COL = {
    "熱量": "kcal",
    "水分": "water_g",
    "粗蛋白": "protein_g",
    "粗脂肪": "fat_g",
    "飽和脂肪": "sat_fat_g",
    "反式脂肪": "trans_fat_g",
    "總碳水化合物": "carb_g",
    "膳食纖維": "fiber_g",
    "糖質總量": "sugar_g",
    "灰分": "ash_g",
    "鈉": "sodium_mg",
    "鉀": "potassium_mg",
    "鈣": "calcium_mg",
    "鐵": "iron_mg",
}

DDL = """
create table if not exists food_library (
  id            text primary key,
  name_cn       text not null,
  name_alt      text,
  name_en       text,
  category      text not null,
  description   text,
  refuse_pct    numeric,
  kcal          numeric,
  water_g       numeric,
  protein_g     numeric,
  fat_g         numeric,
  sat_fat_g     numeric,
  trans_fat_g   numeric,
  carb_g        numeric,
  fiber_g       numeric,
  sugar_g       numeric,
  ash_g         numeric,
  sodium_mg     numeric,
  potassium_mg  numeric,
  calcium_mg    numeric,
  iron_mg       numeric,
  source_ref    text not null default 'TFND-2025-12',
  raw           jsonb,
  updated_at    timestamptz default now()
);
create index if not exists food_library_category_idx on food_library (category);
create index if not exists food_library_search_idx on food_library using gin (to_tsvector('simple', name_cn || ' ' || coalesce(name_en,'')));
alter table food_library enable row level security;
"""

POLICY_SQL = """
drop policy if exists "anon read foods" on food_library;
create policy "anon read foods" on food_library for select to anon using (true);
"""

UPSERT_COLS = [
    "id", "name_cn", "name_alt", "name_en", "category", "description", "refuse_pct",
    "kcal", "water_g", "protein_g", "fat_g", "sat_fat_g", "trans_fat_g",
    "carb_g", "fiber_g", "sugar_g", "ash_g",
    "sodium_mg", "potassium_mg", "calcium_mg", "iron_mg",
    "source_ref", "raw",
]


def to_num(x):
    if x is None or pd.isna(x):
        return None
    if isinstance(x, str):
        x = x.strip()
        if x == "" or x == "-":
            return None
    try:
        v = float(x)
        if pd.isna(v):
            return None
        return v
    except (TypeError, ValueError):
        return None


def to_str(x):
    if x is None or pd.isna(x):
        return None
    s = str(x).strip()
    return s if s else None


def build_rows(df: pd.DataFrame):
    df["每100克含量"] = df["每100克含量"].astype(str).str.strip()
    # 同一 id × 分析項 應該唯一；保留第一筆
    df = df.drop_duplicates(subset=["整合編號", "分析項"], keep="first")

    # meta：每個 id 的基本欄
    meta_cols = ["整合編號", "樣品名稱", "俗名", "樣品英文名稱", "食品分類", "內容物描述", "廢棄率"]
    meta = (
        df[meta_cols]
        .drop_duplicates(subset=["整合編號"], keep="first")
        .set_index("整合編號")
    )

    rows = []
    for fid, group in df.groupby("整合編號", sort=False):
        if fid not in meta.index:
            continue
        m = meta.loc[fid]
        record: dict = {
            "id": fid,
            "name_cn": to_str(m["樣品名稱"]) or fid,
            "name_alt": to_str(m["俗名"]),
            "name_en": to_str(m["樣品英文名稱"]),
            "category": to_str(m["食品分類"]) or "未分類",
            "description": to_str(m["內容物描述"]),
            "refuse_pct": to_num(m["廢棄率"]),
            "source_ref": SOURCE_REF,
        }
        for c in [
            "kcal", "water_g", "protein_g", "fat_g", "sat_fat_g", "trans_fat_g",
            "carb_g", "fiber_g", "sugar_g", "ash_g",
            "sodium_mg", "potassium_mg", "calcium_mg", "iron_mg",
        ]:
            record[c] = None

        raw_map: dict = {}
        for _, r in group.iterrows():
            item = to_str(r["分析項"])
            val = to_num(r["每100克含量"])
            if not item:
                continue
            raw_map[item] = val
            col = ITEM_TO_COL.get(item)
            if col is not None:
                record[col] = val

        record["raw"] = Jsonb(raw_map)
        rows.append(tuple(record[c] for c in UPSERT_COLS))
    return rows


def main():
    db_url = os.environ.get("SUPABASE_DB_URL")
    if not db_url:
        print("SUPABASE_DB_URL not set", file=sys.stderr)
        sys.exit(1)

    print(f"Reading {CSV_PATH} ...")
    df = pd.read_csv(CSV_PATH, dtype=str)
    print(f"  rows={len(df)}  unique ids={df['整合編號'].nunique()}")

    rows = build_rows(df)
    print(f"Built {len(rows)} food rows")

    placeholders = "(" + ",".join(["%s"] * len(UPSERT_COLS)) + ")"
    update_set = ",".join(f"{c}=excluded.{c}" for c in UPSERT_COLS if c != "id")
    update_set += ",updated_at=now()"
    upsert_sql = (
        f"insert into food_library ({','.join(UPSERT_COLS)}) values {placeholders} "
        f"on conflict (id) do update set {update_set}"
    )

    with psycopg.connect(db_url, prepare_threshold=None, autocommit=False) as conn:
        with conn.cursor() as cur:
            print("Creating table & indexes...")
            cur.execute(DDL)
            cur.execute(POLICY_SQL)
            conn.commit()

            print("Upserting...")
            BATCH = 500
            for i in range(0, len(rows), BATCH):
                cur.executemany(upsert_sql, rows[i:i + BATCH])
                conn.commit()
                print(f"  {min(i+BATCH, len(rows))}/{len(rows)}")

            cur.execute("select count(*) from food_library")
            total = cur.fetchone()[0]
            print(f"\nfood_library total = {total}")

            cur.execute(
                "select id,name_cn,kcal,protein_g,fat_g,carb_g from food_library "
                "where name_cn like any(%s) limit 10",
                (["%白米飯%", "%雞胸%", "%高麗菜%", "%鮭魚%", "%香蕉%"],),
            )
            print("\nsample rows:")
            for row in cur.fetchall():
                print(" ", row)

            cur.execute(
                "select category,count(*) from food_library group by category order by 2 desc"
            )
            print("\ncategory distribution:")
            for row in cur.fetchall():
                print(" ", row)

            for col in [
                "kcal", "protein_g", "fat_g", "carb_g", "fiber_g", "sugar_g",
                "sodium_mg", "potassium_mg", "calcium_mg", "iron_mg",
            ]:
                cur.execute(f"select count(*) from food_library where {col} is null")
                miss = cur.fetchone()[0]
                print(f"  null {col}: {miss}/{total}")

    print("Done.")


if __name__ == "__main__":
    main()
