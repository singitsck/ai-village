# AI Village — System Architecture v3.0 (Production)

**Version:** 3.0  
**Date:** 2026-03-26  
**Status:** ✅ 生產就緒

---

## 1. Overview

AI Village 是一個智能村民模擬系統，每個村民是一個獨立的 OpenClaw Agent。

**核心特點：**
- ✅ Per-Villager Agent - 每個村民是真正的 OpenClaw Agent
- ✅ 自然互動 - Agent 之間可以對話、協作、提建議
- ✅ 情感記憶系統 - 記住帶有情緒的事件
- ✅ 關係追蹤 - 好感/反感會影響互動
- ✅ 自然故事產生 - 故事從村民互動中自然浮現

---

## 2. 當前架構（已驗證）

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
│  • meta: tick, weather                                  │
│  • agents[]: 村民狀態                                   │
│  • events[]: 事件日誌                                   │
└─────────────────────────────────────────────────────────────┘
                              ↑
┌─────────────────────────────────────────────────────────────┐
│                 OpenClaw Agent Team                          │
│                                                             │
│  PM Agent (協調者)                                         │
│  ├── Spawn Alice Agent → 思考 → 決策                        │
│  ├── Spawn Bob Agent → 思考 → 決策                         │
│  └── Spawn Carol Agent → 思考 → 決策                       │
└─────────────────────────────────────────────────────────────┘
                              ↑
┌─────────────────────────────────────────────────────────────┐
│                 OpenClaw Cron (觸發器)                       │
│                                                             │
│  ai-village-multiagent (每 15 分鐘)                      │
│  → PM Agent 執行村民協調工作流                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Agent 團隊

### 3.1 PM Agent (協調者)

**職責：**
- 每 15 分鐘被 Cron 觸發
- 運行 `villager-tick-agent.py` 獲取村民上下文
- 為每個村民 Spawn 獨立的 Agent
- 收集決策並更新 Supabase

**工作流：**
```
1. 運行: python3 scripts/villager-tick-agent.py
2. 為每個村民 Spawn sub-agent
3. 等待 sub-agent 返回決策 (ACTION + REASON)
4. 解析決策並更新 Supabase
```

### 3.2 Villager Agent (村民)

每個村民是一個獨立的 Agent，收到完整上下文後做出決策。

---

## 4. Cron 配置

```bash
# Cron ID: 1353934d-e608-41f4-9a63-40eae44bd285
openclaw cron create \
  --name "ai-village-multiagent" \
  --cron "*/15 * * * *" \
  --session isolated \
  --agent pm-agent \
  --message "AI Village Tick: 請執行以下操作..."
```

---

## 5. 村民數據結構

```json
{
  "id": "alice",
  "name": "Alice",
  "role": "farmer",
  "age": 28,
  "gender": "female",
  "birthday": "3月15日",
  "personality": {
    "openness": 0.3,
    "conscientiousness": 0.7,
    "extraversion": 0.8,
    "agreeableness": 0.9,
    "neuroticism": 0.2
  },
  "state": "resting",
  "position": {"x": 5, "y": 5},
  "goal": "tend to farm",
  "hobbies": [],
  "specialty": "待發掘",
  "family_status": "待發掘",
  "memory": {
    "currentGoal": "tend to farm",
    "observations": [
      {
        "tick": 57,
        "content": "stormy天氣讓我心情煩躁，需要先恢復狀態",
        "emotional_valence": -0.3,
        "intensity": 0.5
      }
    ]
  },
  "relationships": {
    "bob": {
      "affinity": 0.3,
      "trust": 0.5,
      "active_emotions": ["friendly"],
      "last_interaction": 55
    }
  }
}
```

---

## 6. 決策類型

| 行動 | 描述 | 效果 |
|------|------|------|
| `move_to (x,y)` | 移動到指定座標 | 改變位置 |
| `work` | 專心工作 | 增加產出 |
| `talk_to [村民]` | 和某人交談 | 更新關係 |
| `rest` | 休息 | 恢復體力 |
| `idle` | 觀察周圍 | 獲取靈感 |
| `discover [類型] [內容]` | 發現新事物 | 更新個人檔案 |
| `propose [行動]` | 向其他村民提建議 | 觸發協作 |

---

## 7. 實際運行結果

### Tick 57 決策

| 村民 | 決策 | 原因 |
|------|------|------|
| **Alice** | rest | stormy天氣讓我心情煩躁，需要先恢復狀態 |
| **Bob** | talk_to Alice | 正在聊天，且他的目標是鍛造工具 |
| **Carol** | talk_to Alice | 想要學魔法，剛好 Alice 和 Bob 在聊天 |

---

## 8. 項目結構

```
ai-village/
├── index.html                    # 前端頁面
├── scripts/
│   ├── villager-tick-agent.py    # Agent 協調腳本
│   └── villager-tick-llm.py     # LLM 版本（備用）
├── docs/
│   ├── ai-village-architecture.md  # 本文件
│   ├── ai-village-frontend.md   # 前端說明
│   └── ai-village-implementation.md # 實現指南
└── .env
```

---

## 9. 技術棧

| 組件 | 技術 |
|------|------|
| 前端 | HTML + JavaScript + Polling |
| 數據庫 | Supabase (JSONB) |
| Agent | OpenClaw (PM + 3 Villagers) |
| Cron | OpenClaw Cron |
| 部署 | GitHub Pages |

---

## 10. 與 v2 的區別

| 項目 | v2 | v3 |
|------|-----|-----|
| 村民決策 | Python 腳本隨機 | 每個村民是獨立 Agent |
| 協調方式 | Cron → 腳本 | Cron → PM Agent → Spawn Agents |
| 互動 | 無 | Agent 可以對話、提建議 |
| 故事產生 | 隨機 | 自然產生 |

---

## 11. 下一步計劃

- [ ] 實現故事線追蹤系統
- [ ] 添加更多村民
- [ ] 實現資源經濟系統
- [ ] 添加訪客和事件系統
- [ ] 實現村莊設施建築

---

*最後更新: 2026-03-26*
