"""把使用者菜單既有 ID 複製成 library row（資料來自最相近的 free-exercise-db 條目）。"""
import os, psycopg

# user_id → canonical library id (from free-exercise-db)
# None = 沒有合適 free-exercise-db 對應，需手寫 custom row
ALIAS = {
    'ab_wheel_rollout':       'ab_roller',
    'back_extension':         'hyperextensions_back_extensions',
    'back_squat':             'barbell_full_squat',
    'cable_fly':              'flat_bench_cable_flyes',
    'lat_pulldown':           'wide_grip_lat_pulldown',
    'leg_curl':               'seated_leg_curl',
    'leg_extension':          'leg_extensions',
    'machine_lateral_raise':  'side_lateral_raise',
    'machine_row':            'lying_t_bar_row',
    'reverse_pec_deck':       'reverse_flyes',
    'rope_triceps_pushdown':  'triceps_pushdown___rope_attachment',
    'seated_cable_row':       'seated_cable_rows',
    'smith_deadlift':         'romanian_deadlift',
    'standing_calf_raise':    'standing_calf_raises',
    'bulgarian_split_squat':  'split_squat_with_dumbbells',
}

# 沒對應的：自寫 row（zh_only，無圖）
CUSTOM = {
    'serratus_punch': {
        'name_en': 'Serratus Punch',
        'name_cn': '前鋸肌推',
        'aliases': ['前鋸肌啟動'],
        'category': 'strength',
        'level': 'beginner',
        'equipment': 'body only',
        'primary_muscles': ['serratus'],
        'secondary_muscles': ['shoulders'],
        'instructions_en': [
            'Stand with arms straight in front, shoulders down.',
            'Keeping arms locked, protract shoulder blades — push hands forward without bending elbows.',
            'Hold 1 second, then retract slowly back. Repeat for reps.',
        ],
        'instructions_cn': [
            '站姿，雙手伸直前舉，肩膀放鬆下沉。',
            '手肘鎖死，做肩胛前突 — 把雙手往前推、肩胛骨拉開（不靠手肘彎）。',
            '頂點停 1 秒後慢慢收回。重複指定次數。',
        ],
    },
    'ytw_raise': {
        'name_en': 'YTW Raise',
        'name_cn': 'YTW 肩胛訓練',
        'aliases': ['YTW', '肩胛三式'],
        'category': 'strength',
        'level': 'beginner',
        'equipment': 'dumbbell',
        'primary_muscles': ['shoulders'],
        'secondary_muscles': ['traps', 'middle back'],
        'instructions_en': [
            'Lie face-down on an incline bench holding light dumbbells.',
            'Y position: raise arms in a Y shape overhead, thumbs up.',
            'T position: bring arms out to sides at shoulder height, thumbs up.',
            'W position: bend elbows 90°, pull elbows back and down forming a W.',
            'Each shape counts as one rep; perform consecutively.',
        ],
        'instructions_cn': [
            '俯臥於上斜板上，雙手各持輕啞鈴。',
            'Y 位：雙臂在頭上方呈 Y 字形上抬，大拇指朝上。',
            'T 位：雙臂往兩側打開到肩高，大拇指朝上。',
            'W 位：手肘彎曲 90°，向後下方夾肩成 W 字。',
            '每個位置算一下；連續執行。',
        ],
    },
}

UPSERT_ALIAS = """
insert into exercise_library
  (id, source, source_ref, name_en, name_cn, aliases, category, force, level, mechanic, equipment,
   primary_muscles, secondary_muscles, instructions_en, instructions_cn, image_urls, updated_at)
select
  %s as id,
  'free_exercise_db_alias' as source,
  source_ref,
  name_en, name_cn, aliases, category, force, level, mechanic, equipment,
  primary_muscles, secondary_muscles, instructions_en, instructions_cn, image_urls, now()
from exercise_library where id = %s
on conflict (id) do update set
  name_en = excluded.name_en, name_cn = excluded.name_cn, aliases = excluded.aliases,
  category = excluded.category, force = excluded.force, level = excluded.level,
  mechanic = excluded.mechanic, equipment = excluded.equipment,
  primary_muscles = excluded.primary_muscles, secondary_muscles = excluded.secondary_muscles,
  instructions_en = excluded.instructions_en, instructions_cn = excluded.instructions_cn,
  image_urls = excluded.image_urls, updated_at = now();
"""

UPSERT_CUSTOM = """
insert into exercise_library
  (id, source, name_en, name_cn, aliases, category, level, equipment,
   primary_muscles, secondary_muscles, instructions_en, instructions_cn, updated_at)
values (%s, 'custom', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now())
on conflict (id) do update set
  source='custom', name_en=excluded.name_en, name_cn=excluded.name_cn, aliases=excluded.aliases,
  category=excluded.category, level=excluded.level, equipment=excluded.equipment,
  primary_muscles=excluded.primary_muscles, secondary_muscles=excluded.secondary_muscles,
  instructions_en=excluded.instructions_en, instructions_cn=excluded.instructions_cn, updated_at=now();
"""

def main():
    db = os.environ['SUPABASE_DB_URL']
    with psycopg.connect(db, prepare_threshold=None, autocommit=False) as conn:
        cur = conn.cursor()
        for uid, ref in ALIAS.items():
            cur.execute(UPSERT_ALIAS, (uid, ref))
            print(f'aliased {uid} ← {ref}')
        for uid, c in CUSTOM.items():
            cur.execute(UPSERT_CUSTOM, (
                uid, c['name_en'], c['name_cn'], c['aliases'], c['category'], c['level'], c['equipment'],
                c['primary_muscles'], c['secondary_muscles'], c['instructions_en'], c['instructions_cn'],
            ))
            print(f'custom  {uid}')
        conn.commit()
        n = conn.execute("select count(*) from exercise_library").fetchone()[0]
    print(f'\n✅ done. total rows: {n}')

if __name__ == '__main__':
    main()
