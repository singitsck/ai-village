# AI Village — System Architecture

**Version:** 2.0  
**Date:** 2026-03-24  
**Author:** PM Agent

---

## 1. Overview

AI Village 是一個智能村民模擬系統，每個村民有自己的 LLM Brain，會記住過去的事件並影響未來決定。

**核心特點：**
- Per-Villager LLM Brain - 每個村民獨立思考
- 情感記憶系統 - 記住帶有情緒的事件
- 關係追蹤 - 好感/反感會影響互動
- 自然故事產生 - 故事從村民互動中自然浮現

---

## 2. 當前架構

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (GitHub Pages)                   │
│         https://singitsck.github.io/ai-village/           │
│                    ↕ Polling (3s)                          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Supabase (Source of Truth)                │
│              village_state (單一 JSONB 文檔)                 │
│  • meta: tick, weather, lastUpdated                      │
│  • agents[]: 村民（含 memory, relationships）            │
│  • events[]: 事件日誌                                     │
└─────────────────────────────────────────────────────────────┘
                              ↑
┌─────────────────────────────────────────────────────────────┐
│                 OpenClaw Cron (每 15 分鐘)                   │
│                                                             │
│  ai-village-multiagent                                     │
│  └── PM Agent → Spawn 3 Villager Agents                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 組件

### 3.1 Supabase State

**Table:** `village_state` (單一 JSONB 文檔)

```json
{
  "id": "main",
  "meta": {
    "tick": 13,
    "weather": {
      "type": "sunny",
      "emoji": "☀️",
      "mood_modifier": 0.2,
      "work_efficiency": 1.2
    },
    "lastUpdated": "2026-03-24T12:00:00Z",
    "tickIntervalSeconds": 900
  },
  "village": {
    "name": "AI Village",
    "population": 3
  },
  "agents": [
    {
      "id": "alice",
      "name": "Alice",
      "role": "farmer",
      "state": "idle",
      "position": {"x": 5, "y": 5},
      "personality": {
        "openness": 0.3,
        "conscientiousness": 0.7,
        "extraversion": 0.8,
        "agreeableness": 0.9,
        "neuroticism": 0.2
      },
      "memory": {
        "currentGoal": "tend to farm",
        "observations": [
          {
            "tick": 10,
            "content": "決定working：天氣很好想要工作",
            "emotional_valence": 0.2,
            "intensity": 0.5,
            "importance": 0.6,
            "is_pivotal": false
          }
        ],
        "reflections": []
      },
      "relationships": {
        "bob": {
          "affinity": 0.3,
          "trust": 0.5,
          "active_emotions": [],
          "last_interaction": 0
        }
      }
    }
  ],
  "events": [
    {
      "tick": 13,
      "type": "weather",
      "agent": "system",
      "message": "天氣變為 ☀️ sunny"
    }
  ]
}
```

### 3.2 OpenClaw Cron

**Job:** `ai-village-multiagent`  
**Schedule:** 每 15 分鐘 (`*/15 * * * *`)  
**觸發流程：**

```
Cron 觸發
    ↓
PM Agent 收到消息
    ↓
運行 villager-tick-multiagent.py
    ↓
Spawn 3 個 Villager Agents (並行)
    ↓
收集決策 → 更新 Supabase
```

### 3.3 Per-Villager LLM Brain

每個村民是一個獨立的 AI Agent，收到：

```
你是 Alice，一個 30 歲的 farmer。

【性格特徵】開放性:0.3, 盡責性:0.7, 外向性:0.8, 友善性:0.9, 神經質:0.2

你的重要記憶：
- 😊 和 Bob 一起工作很愉快（importance: 0.7）
- 🤔 決定idle：想要休息一下

你對其他村民的態度：
- Bob: 有好感，想要親近

當前天氣：☀️ Sunny（工作動機 120%）

請決定你接下來要做什麼。

回應格式：
ACTION: [行動]
REASON: [原因]
```

---

## 4. 村民系統

### 4.1 村民列表

| ID | 名稱 | 職業 | 性格特點 |
|-----|------|------|----------|
| alice | Alice | 農夫 (farmer) | 友善性高 (0.9), 外向 (0.8) |
| bob | Bob | 鐵匠 (blacksmith) | 盡責性高 (0.9), 內向 (0.2) |
| carol | Carol | 學徒 (apprentice) | 開放性高 (0.9), 好奇 (0.6) |

### 4.2 性格系統 (Big Five)

```typescript
interface Personality {
  openness: number;           // 0-1 好奇心、創造力
  conscientiousness: number;  // 0-1 紀律性、工作態度
  extraversion: number;       // 0-1 社交活躍度
  agreeableness: number;     // 0-1 合作意願
  neuroticism: number;       // 0-1 情緒穩定性
}
```

### 4.3 狀態類型

| 狀態 | 描述 |
|------|------|
| `idle` | 保持現狀 |
| `moving` | 移動到新位置 |
| `working` | 執行工作 |
| `talking` | 和某人交談 |
| `resting` | 休息 |

---

## 5. 記憶系統

### 5.1 記憶結構

```typescript
interface Memory {
  tick: number;
  content: string;           // 記憶內容
  emotional_valence: number; // -1 (負面) to 1 (正面)
  intensity: number;         // 0 to 1 強度
  importance: number;        // 0 to 1 重要性
  is_pivotal: boolean;     // true = 不會衰減
}
```

### 5.2 記憶衰減

```
每 Tick:
  if not is_pivotal:
    importance *= 0.98  // 2% 衰減
```

### 5.3 記憶影響決策

```python
# 檢索相關記憶時的評分
score = (
    relevance * 0.3 +      # 內容相關性
    recency * 0.2 +        # 時間新近度
    importance * 0.3 +     # 重要性
    emotion_bonus * 0.2    # 情緒強度
)
```

---

## 6. 關係系統

### 6.1 關係結構

```typescript
interface Relationship {
  affinity: number;         // -1 (反感) to 1 (好感)
  trust: number;           // 0 to 1
  respect: number;         // 0 to 1
  familiarity: number;     // 0 to 1
  active_emotions: string[]; // ["anger", "gratitude"]
  last_interaction: number;  // tick
}
```

### 6.2 關係更新規則

| 互動 | 效果 |
|------|------|
| talk (正面) | affinity +0.1, trust +0.05 |
| talk (負面) | affinity -0.15, 添加 "anger" |
| work_together | affinity +0.15, trust +0.1 |

---

## 7. 天氣系統

### 7.1 天氣類型

| 天氣 | Emoji | 心情修正 | 工作效率 |
|------|-------|----------|----------|
| Sunny | ☀️ | +0.2 | 120% |
| Cloudy | ☁️ | 0.0 | 100% |
| Rainy | 🌧️ | -0.1 | 70% |
| Stormy | ⛈️ | -0.3 | 30% |
| Snowy | ❄️ | -0.2 | 50% |

### 7.2 天氣生成

- 70% 機會保持現有天氣（持續性）
- 30% 機會變化為新天氣

---

## 8. Multi-Agent 協調流程

```
[1] Cron 觸發 (每 15 分鐘)
         │
         ▼
[2] PM Agent 收到消息
         │
         ▼
[3] 運行 villager-tick-multiagent.py
         │
         ▼
[4] 獲取所有村民的上下文
         │
         ├──► Spawn Alice Agent
         ├──► Spawn Bob Agent
         └──► Spawn Carol Agent
                │
                ▼
[5] 每個 Villager Agent 用 LLM 思考
         │
         ▼
[6] 返回決策 (ACTION + REASON)
         │
         ▼
[7] PM Agent 收集並更新 Supabase
         │
         ├──► 更新每個村民的 state
         ├──► 添加新記憶
         ├──► 更新關係（如有互動）
         └──► 添加事件到 events[]
         │
         ▼
[8] 前端 Polling 自動刷新
```

---

## 9. 項目結構

```
ai-village/
├── index.html              # 前端頁面
├── state/
│   └── village-state.json  # 本地備份
├── scripts/
│   ├── villager-tick-multiagent.py  # 多 Agent 協調
│   ├── villager-tick-llm.py         # LLM 版本
│   └── villager-tick.py              # 基礎版本
├── docs/
│   ├── ai-village-architecture.md    # 本文件
│   ├── ai-village-frontend.md       # 前端文檔
│   └── ai-village-implementation.md  # 實現文檔
└── .env                      # 環境配置
```

---

## 10. 技術棧

| 組件 | 技術 |
|------|------|
| 前端 | HTML + JavaScript + Polling |
| 數據庫 | Supabase (JSONB) |
| Agent | OpenClaw + MiniMax LLM |
| Cron | OpenClaw Cron |
| 部署 | GitHub Pages (前端) |

---

## 11. 與舊架構的區別

| 項目 | 舊架構 (v1) | 新架構 (v2) |
|------|-------------|-------------|
| 數據存儲 | GitHub JSON | Supabase |
| Agent 數量 | 5+ (資源/建築/外交等) | 3 (每村民一個) |
| 決策方式 | 多 Agent 提案合併 | Per-Villager LLM Brain |
| 更新頻率 | Cron → GitHub Actions | Cron → OpenClaw Agent |
| 記憶系統 | 簡單陣列 | 情感記憶 + 關係追蹤 |

---

## 12. 未來計劃

- [ ] 實現故事線追蹤系統
- [ ] 添加更多村民
- [ ] 實現資源經濟系統
- [ ] 添加訪客和事件系統
- [ ] 實現村莊設施建築

---

*最後更新: 2026-03-24*
