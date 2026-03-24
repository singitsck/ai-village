# AI Village - 智能村民模擬項目

> 每個村民有自己的 LLM Brain，會記住過去、影響未來決定

## 🎯 願景

村民會有真正個性化的記憶：
- 「我上次和 Bob 吵架了，所以今天不想幫他蓋房子」
- 「Carol 是我的好朋友，我總是想和她一起工作」

會自然產生故事：有人談戀愛、有人偷懶、有人發起革命、有人因為天氣心情差而遷移。世界感覺極度「活」。

## 🏛️ 當前架構

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (GitHub Pages)                   │
│         https://singitsck.github.io/ai-village/            │
│                    ↕ Polling (3s)                         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Supabase (Source of Truth)               │
│              village_state (單一 JSONB 文檔)                │
│  • meta: tick, weather, lastUpdated                       │
│  • agents[]: 村民（含 memory, relationships）             │
│  • events[]: 事件日誌                                     │
└─────────────────────────────────────────────────────────────┘
                              ↑
┌─────────────────────────────────────────────────────────────┐
│                 Cron Jobs (OpenClaw)                        │
│                                                             │
│  ai-village-multiagent (每 15 分鐘)                        │
│  └── PM Agent 協調 → Spawn 3 Villager Agents               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              Per-Villager LLM Brain System                  │
│                                                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐                   │
│  │  Alice  │  │   Bob   │  │  Carol  │                   │
│  │  Brain  │  │  Brain  │  │  Brain  │                   │
│  └─────────┘  └─────────┘  └─────────┘                   │
│       ↓            ↓            ↓                           │
│  獨立 LLM 思考 → 個性化決策 → 情感記憶                      │
└─────────────────────────────────────────────────────────────┘
```

## 👥 村民

| 村民 | 職業 | 性格特點 |
|------|------|----------|
| **Alice** | 農夫 (farmer) | 友善性高 (0.9), 外向 (0.8) |
| **Bob** | 鐵匠 (blacksmith) | 盡責性高 (0.9), 內向 (0.2) |
| **Carol** | 學徒 (apprentice) | 開放性高 (0.9), 好奇 (0.6) |

## 🧠 LLM Brain 系統

每個村民的大腦包含：

### 1. 性格系統 (Big Five)
- **開放性**: 好奇心、創造力
- **盡責性**: 纪律性、工作態度
- **外向性**: 社交活躍度
- **友善性**: 合作意願
- **神經質**: 情緒穩定性

### 2. 情感記憶系統
```json
{
  "content": "決定working：天氣很好想要工作",
  "emotional_valence": 0.2,  // -1 (負面) to 1 (正面)
  "intensity": 0.5,          // 0 to 1
  "importance": 0.3,          // 會衰減，除了重要事件
  "is_pivotal": false         // true = 不會衰減
}
```

### 3. 關係系統
```json
{
  "affinity": 0.3,            // -1 (反感) to 1 (好感)
  "trust": 0.5,              // 0 to 1
  "active_emotions": ["anger"], // 情緒殘留
  "last_interaction": 12      // 上次互動的 tick
}
```

### 4. 天氣影響
| 天氣 | 心情修正 | 工作效率 |
|------|----------|----------|
| ☀️ Sunny | +0.2 | 120% |
| ☁️ Cloudy | 0.0 | 100% |
| 🌧️ Rainy | -0.1 | 70% |
| ⛈️ Stormy | -0.3 | 30% |
| ❄️ Snowy | -0.2 | 50% |

## 🔄 Tick 流程

每 15 分鐘執行一次：

```
1. Cron 觸發 → PM Agent
2. PM Agent Spawn 3 個 Villager Agents
3. 每個 Villager Agent 收到：
   - 性格描述
   - 最近記憶
   - 對其他村民的態度
   - 天氣狀況
   - 當前狀態
4. Villager Agent 用 LLM 思考並回應
5. 決策格式：
   ACTION: work
   REASON: 因為我的盡責性很高，而且天氣不錯
6. PM Agent 收集決策 → 更新 Supabase
```

## 📁 項目結構

```
ai-village/
├── index.html           # 前端顯示頁面
├── state/
│   └── village-state.json  # 本地狀態（備份）
├── scripts/
│   ├── villager-tick-multiagent.py  # 多 Agent 協調腳本
│   ├── villager-tick-llm.py         # LLM 版本腳本
│   └── villager-tick.py              # 基礎版本
└── docs/
    ├── README.md        # 本文件
    └── ARCHITECTURE.md  # 詳細架構文檔
```

## 🌐 技術棧

| 組件 | 技術 |
|------|------|
| 前端 | HTML + JavaScript + Polling |
| 數據庫 | Supabase (JSONB) |
| Agent | OpenClaw + MiniMax LLM |
| 部署 | GitHub Pages (前端) + OpenClaw Cron |

## 🚀 運行方式

### 本地運行
```bash
# 克隆項目
git clone https://github.com/singitsck/ai-village.git
cd ai-village

# 運行 villager tick（需要 OpenClaw）
python3 scripts/villager-tick-multiagent.py
```

### 查看狀態
```bash
# 直接查詢 Supabase
curl "https://yqwcxushplzodbnqwqxn.supabase.co/rest/v1/village_state?id=eq.main" \
  -H "apikey: <your-key>"
```

## 📊 當前狀態

- **Tick**: 13
- **天氣**: ❄️ Snowy
- **村民**:
  - Alice: idle
  - Bob: working
  - Carol: working

## 🔮 未來計劃

- [ ] 實現故事線追蹤系統
- [ ] 添加更多村民
- [ ] 實現資源經濟系統
- [ ] 添加訪客和事件系統
- [ ] 實現村莊設施建築

---

*最後更新: 2026-03-24*
