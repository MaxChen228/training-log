"""Merge free-exercise-db + Chinese translation parts → upsert to exercise_library."""
import os, json, glob, sys
from pathlib import Path
import psycopg

ROOT = Path(__file__).parent
RAW  = ROOT / "exercises_raw.json"
PARTS_GLOB = str(ROOT / "translations_part_*.json")

GH_BASE = "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises"

def normalize_id(orig: str) -> str:
    return orig.lower().replace("-", "_")

def load_translations() -> dict:
    merged = {}
    files = sorted(glob.glob(PARTS_GLOB))
    if not files:
        print("⚠ no translations_part_*.json found — running with English only", file=sys.stderr)
        return merged
    for f in files:
        with open(f) as fh:
            d = json.load(fh)
        # detect collisions
        dup = set(merged) & set(d)
        if dup:
            print(f"⚠ duplicate keys in {f}: {dup}", file=sys.stderr)
        merged.update(d)
    print(f"loaded translations: {len(merged)} entries from {len(files)} parts")
    return merged

def build_rows(raw: list[dict], tr: dict) -> list[tuple]:
    rows = []
    miss_tr = 0
    bad_inst_len = []
    for e in raw:
        new_id = normalize_id(e["id"])
        t = tr.get(new_id, {})
        name_cn = t.get("name_cn")
        instructions_cn = t.get("instructions_cn") or []
        aliases = t.get("aliases") or []
        if not t:
            miss_tr += 1
        elif len(instructions_cn) != len(e.get("instructions") or []):
            bad_inst_len.append(new_id)
        image_urls = [f"{GH_BASE}/{e['id']}/{img.split('/')[-1]}" for img in (e.get("images") or [])]
        rows.append((
            new_id,                                       # id
            "free_exercise_db",                           # source
            e["id"],                                      # source_ref
            e["name"],                                    # name_en
            name_cn,                                      # name_cn
            aliases,                                      # aliases
            e.get("category"),                            # category
            e.get("force"),                               # force
            e.get("level"),                               # level
            e.get("mechanic"),                            # mechanic
            e.get("equipment"),                           # equipment
            e.get("primaryMuscles") or [],                # primary_muscles
            e.get("secondaryMuscles") or [],              # secondary_muscles
            e.get("instructions") or [],                  # instructions_en
            instructions_cn,                              # instructions_cn
            image_urls,                                   # image_urls
        ))
    if miss_tr:
        print(f"⚠ {miss_tr} entries missing Chinese translation (will store English only)")
    if bad_inst_len:
        print(f"⚠ {len(bad_inst_len)} entries have instructions_cn length ≠ original (e.g., {bad_inst_len[:5]})")
    return rows

UPSERT = """
insert into exercise_library
  (id, source, source_ref, name_en, name_cn, aliases, category, force, level, mechanic, equipment,
   primary_muscles, secondary_muscles, instructions_en, instructions_cn, image_urls, updated_at)
values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, now())
on conflict (id) do update set
  source            = excluded.source,
  source_ref        = excluded.source_ref,
  name_en           = excluded.name_en,
  name_cn           = coalesce(excluded.name_cn, exercise_library.name_cn),
  aliases           = excluded.aliases,
  category          = excluded.category,
  force             = excluded.force,
  level             = excluded.level,
  mechanic          = excluded.mechanic,
  equipment         = excluded.equipment,
  primary_muscles   = excluded.primary_muscles,
  secondary_muscles = excluded.secondary_muscles,
  instructions_en   = excluded.instructions_en,
  instructions_cn   = case when array_length(excluded.instructions_cn,1) > 0
                           then excluded.instructions_cn
                           else exercise_library.instructions_cn end,
  image_urls        = excluded.image_urls,
  updated_at        = now();
"""

def main():
    raw = json.load(open(RAW))
    tr = load_translations()
    rows = build_rows(raw, tr)
    print(f"prepared {len(rows)} rows")

    db_url = os.environ["SUPABASE_DB_URL"]
    with psycopg.connect(db_url, autocommit=False) as conn:
        with conn.cursor() as cur:
            cur.executemany(UPSERT, rows)
        conn.commit()
        n = conn.execute("select count(*) from exercise_library").fetchone()[0]
        n_cn = conn.execute("select count(*) from exercise_library where name_cn is not null").fetchone()[0]
        cats = conn.execute("select category, count(*) from exercise_library group by category order by 2 desc").fetchall()
    print(f"\n✅ done. total rows in DB: {n}, with name_cn: {n_cn}")
    print("by category:", dict(cats))

if __name__ == "__main__":
    main()
