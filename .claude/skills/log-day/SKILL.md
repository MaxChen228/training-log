---
name: log-day
description: 將使用者當日的訓練 / 飲食 / 舒緩活動寫入 training-log 的 Supabase logs 表。當使用者用自然語言敘述「今天做了 X」「午餐吃了 Y」「拉伸了 Z」「補昨天的紀錄」等需要持久化到訓練日誌時觸發。包含解析、結構化預覽、確認、upsert 的完整工作流。
---

# log-day — 對話式訓練日誌寫入

使用者懶得開 app 點擊就直接口述今日活動，由 Claude 解析後寫進 Supabase `logs` 表，下次手機開 app 就看得到。

## 不在範圍內
- 純查詢（「上週訓練量？」）→ 用 `sbFetch` 直接 GET 就好，不用走這個 skill
- 改菜單 / 改 config → 那是 `settings` 表的事，本 skill 只動 `logs`

## 1. 取得認證

每次寫入前先讀 `.env`（在工作目錄根，gitignore 已護住）：

```bash
set -a && source /Users/chenliangyu/Desktop/active/training-log/.env && set +a
```

需要的變數：`SUPABASE_URL`、`SUPABASE_ANON_KEY`（RLS 全開，anon 即可寫）。

## 2. logs 表結構

PK = `date`（YYYY-MM-DD 字串），其他欄位：

| 欄位 | 型別 | 說明 |
|---|---|---|
| `date` | text | PK |
| `blocks` | jsonb (陣列) | 當日所有活動 block |
| `updated_at` | timestamptz | upsert 時帶 `new Date().toISOString()` |

## 3. block jsonb shape

通用欄位：
```jsonc
{
  "id": "<隨機字串>",            // crypto.randomUUID() 或 nanoid 風格
  "type": "lift" | "volleyball" | "recovery",
  "start": "HH:MM",
  "end":   "HH:MM",
  "collapsed": false,
  "note": ""
}
```

### type=`lift`（重訓，**現有 schema**）
```jsonc
{
  ...通用,
  "type": "lift",
  "splits": ["upper"],            // 子集：upper | lower | core | prep
  "sets": {
    "lat_pulldown": [
      { "weight": 50, "reps": 10 },
      { "weight": 55, "reps": 8 }
    ]
  }
}
```
`exerciseId` 取自 `index.html` 內 `DEFAULT_CONFIG.splits.*.exercises[].id`（L745-786）。
**未知動作不要瞎掰 ID** — 詢問使用者要對應到哪個既有動作，或標記 `note` 暫存。

### type=`volleyball`
```jsonc
{ ...通用, "type": "volleyball" }
```
（時長從 start/end 推算，無額外 payload）

### type=`recovery`（規劃中，jsonb shape 預定義；UI 未上線）
```jsonc
{
  ...通用,
  "type": "recovery",
  "items": [
    { "id": "child_pose", "duration_sec": 60, "note": "" }
  ]
}
```
recovery 動作可從 `exercise_library` 查 `category='stretching'` 取 id（已有 123 筆中文化好的 stretching/mobility 動作）。

## 4. 工作流（口述 → upsert）

**步驟必須照順序，不可跳過確認步驟。**

### Step 1：解析

使用者輸入範例：
> 「今天下午 4-5 點做了上半身，深蹲沒做，做了高位下拉 4 組 50/55/55/60 kg 各 8-10 下，還有面拉 3 組」

解析時：
- 推日期：未指定 → 今天（local TZ）；說「昨天」→ today-1；具體日期照填
- 推時段：未指定 → 詢問或先省略 start/end（保留 null）
- exerciseId 對照：用既有 DEFAULT_CONFIG 對照表（必要時 Read [index.html:741-786](index.html)）
- 不確定的部分**全部標出來問**，不要靜默猜

### Step 2：顯示預覽（強制）

把要寫入的 JSON 顯示給使用者，**等明確 OK 才寫**。範例：
```
要寫入 2026-04-26 一個新 block：
- type: lift, splits: [upper]
- 17:00-18:00（時間我假設的，要改說）
- 高位下拉 4 組：50×10 / 55×10 / 55×8 / 60×8
- 繩索面拉 3 組：（重量 reps 沒講，先當 ?×?）

確認寫入嗎？
```

### Step 3：讀當日現有 blocks（避免覆蓋）

```bash
curl -s "$SUPABASE_URL/rest/v1/logs?date=eq.2026-04-26&select=blocks" \
  -H "apikey: $SUPABASE_ANON_KEY" -H "Authorization: Bearer $SUPABASE_ANON_KEY"
```

**append 到現有陣列**，不要直接替換 — 使用者可能已經在 app 裡記過東西。
若回傳 `[]`（當日無 row），直接用新 blocks 陣列。

### Step 4：upsert

```bash
curl -s -X POST "$SUPABASE_URL/rest/v1/logs" \
  -H "apikey: $SUPABASE_ANON_KEY" \
  -H "Authorization: Bearer $SUPABASE_ANON_KEY" \
  -H "Content-Type: application/json" \
  -H "Prefer: resolution=merge-duplicates,return=minimal" \
  -d '{
    "date": "2026-04-26",
    "blocks": [...完整合併後陣列...],
    "updated_at": "2026-04-26T09:30:00.000Z"
  }'
```

成功回 `201`（return=minimal 會空 body）。

### Step 5：回報

「已寫入 2026-04-26，當日總 blocks: N」。**不要**重述整份 JSON。

## 5. 編輯既有 block

若使用者說「改一下剛剛那個」「把面拉改成 4 組」：
- 重讀當日 blocks
- 用 `id` 定位（不要靠 index）
- 改完整個陣列重新 upsert

## 6. 刪除

使用者明確說「刪掉今天 X」：
- 從 blocks 陣列移掉該 id 後 upsert
- 若整天清空 → `DELETE` 該 row：
  ```bash
  curl -X DELETE "$SUPABASE_URL/rest/v1/logs?date=eq.2026-04-26" \
    -H "apikey: $SUPABASE_ANON_KEY" -H "Authorization: Bearer $SUPABASE_ANON_KEY"
  ```

## 7. 常見坑

- **時區**：使用者在台灣（UTC+8），date 用本地日期，不要用 UTC 日期算（凌晨會差一天）
- **id 必填**：blocks 陣列每個元素一定要有唯一 `id`，不要省略
- **collapsed 預設 false**：app 預期此欄位存在
- **未知 exerciseId 絕不亂塞**：menu 視圖會根據 ID 查不到而顯示空白
