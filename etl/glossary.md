# 健身動作中文翻譯 Glossary（強制術語統一）

## 使用者現有菜單譯名（**最高優先，遇到必須採用**）

| EN | 中文 |
|---|---|
| Lat Pulldown | 高位下拉 |
| Seated Cable Row | 坐姿繩索划船 |
| Machine Row | 機械划船 |
| Reverse Pec Deck | 反向飛鳥 |
| Face Pull | 繩索面拉 |
| Cable Fly / Cable Crossover | 繩索夾胸 |
| Machine Lateral Raise | 機械側平舉 |
| Rope Triceps Pushdown | 繩索三頭下壓 |
| Back Squat / Barbell Squat | 槓鈴深蹲 |
| Smith Machine Deadlift | 史密斯機硬拉 |
| Leg Extension | 坐姿腿伸 |
| Leg Curl / Seated Leg Curl | 坐姿腿彎舉 |
| Standing Calf Raise | 站姿提踵 |
| Bulgarian Split Squat | 保加利亞分腿蹲 |
| Ab Wheel Rollout | 健腹輪 |
| Torso Rotation | 機械轉體 |
| Back Extension | 背部伸展 |
| External Rotation | 肩外旋 |
| Serratus Punch | 前鋸肌推 |
| YTW Raise | YTW 肩胛訓練 |

## 器材術語

| EN | 中文 |
|---|---|
| Barbell | 槓鈴 |
| Dumbbell | 啞鈴 |
| Cable | 繩索 |
| Machine | 機械 |
| Smith Machine | 史密斯機 |
| Kettlebell / Kettlebells | 壺鈴 |
| Bands | 彈力帶 |
| Medicine Ball | 藥球 |
| Exercise Ball / Stability Ball | 抗力球 |
| Foam Roll / Foam Roller | 滾筒 |
| E-Z Curl Bar | EZ 曲槓 |
| Body Only / Bodyweight | 徒手 |
| Bench | 臥推椅 / 板凳（看上下文） |
| Pull-up Bar | 引體向上桿 |
| Dip Bar | 雙槓 |

## 動作模式術語（核心動詞）

| EN | 中文 |
|---|---|
| Squat | 深蹲 |
| Deadlift | 硬拉 |
| Press | 推（bench press 臥推 / overhead press 過頭推 / shoulder press 肩推） |
| Row | 划船 |
| Pulldown | 下拉 |
| Pull-up | 引體向上 |
| Chin-up | 反握引體向上 |
| Curl | 彎舉 |
| Extension | 伸展 / 伸（leg extension 腿伸 / triceps extension 三頭伸展） |
| Fly | 飛鳥 / 夾胸（看上下文） |
| Raise | 平舉 / 抬（lateral raise 側平舉 / front raise 前平舉 / calf raise 提踵） |
| Lunge | 弓步 / 箭步蹲 |
| Step-up | 登階 |
| Crunch | 捲腹 |
| Sit-up | 仰臥起坐 |
| Plank | 棒式 |
| Bridge | 橋式 |
| Twist | 轉體 |
| Rotation | 轉體 / 旋轉 |
| Pushdown | 下壓 |
| Push-up | 伏地挺身 |
| Dip | 雙槓撐體 |
| Shrug | 聳肩 |
| Hip Thrust | 臀推 |
| Clean | 上膊 |
| Snatch | 抓舉 |
| Jerk | 挺舉 |
| Swing | 擺盪（kettlebell swing 壺鈴擺盪） |
| Stretch | 伸展 |
| Hold | 維持 |

## 肌群術語（出現在動作名與步驟中）

| EN | 中文 |
|---|---|
| Chest | 胸 |
| Back | 背 |
| Shoulders | 肩 |
| Lats | 闊背肌 |
| Traps | 斜方肌 |
| Rhomboids | 菱形肌 |
| Deltoids | 三角肌 |
| Biceps | 二頭肌 |
| Triceps | 三頭肌 |
| Forearms | 前臂 |
| Abdominals / Abs | 腹肌 |
| Obliques | 腹斜肌 |
| Lower Back | 下背 |
| Glutes | 臀肌 |
| Quadriceps / Quads | 股四頭肌 |
| Hamstrings | 大腿後側 / 腿後肌 |
| Calves | 小腿 |
| Adductors | 內收肌 |
| Abductors | 外展肌 |
| Hip Flexors | 髖屈肌 |
| Serratus | 前鋸肌 |
| Rotator Cuff | 肩旋轉肌群 |

## 姿勢/方向術語

| EN | 中文 |
|---|---|
| Seated | 坐姿 |
| Standing | 站姿 |
| Lying / Supine | 仰臥 |
| Prone | 俯臥 |
| Incline | 上斜 |
| Decline | 下斜 |
| Flat | 平板 |
| Wide-grip | 寬握 |
| Close-grip | 窄握 |
| Reverse-grip | 反握 |
| Neutral-grip | 中立握 |
| Underhand | 反手 |
| Overhand | 正手 |
| Single-leg / One-leg | 單腿 |
| Single-arm / One-arm | 單手 |
| Alternating | 交替 |

## 翻譯規則

1. **動作名（name_cn）**：簡潔，台灣健身房口語，3-10 字為主。範例 `Barbell Bench Press` → `槓鈴臥推`。
2. **指令（instructions_cn）**：逐條翻譯，每條一個 string，**順序與英文 array 一致、長度相同**。語氣口語但完整。
3. **別名（aliases）**：**選填**，只在常見口語別名才加（如 `back_squat` → `["後蹲", "槓鈴蹲"]`）。沒明顯別名就空陣列 `[]`。**絕不音譯亂湊。**
4. **未知動作名**：若是冷門動作（strongman、奧舉細項）找不到標準譯名，直接意譯 + 保留英文括號，如 `Atlas Stones` → `阿特拉斯石（Atlas Stones）`。
5. **品牌/特定器械**：保留英文（如 `Bosu Ball` → `Bosu 球`、`TRX` 不翻譯）。
6. **方位詞**：always 用繁體中文，**不可用簡體**。
