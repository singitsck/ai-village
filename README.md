# AI Village 🌾

> 每個村民是一個獨立的 AI Agent，會記住過去、影響未來決定

## 🎯 願景

村民會有真正個性化的記憶：
- 「我上次和 Bob 吵架了，所以今天不想幫他蓋房子」
- 「Carol 是我的好朋友，我總是想和她一起工作」

會自然產生故事：有人談戀愛、有人偷懶、有人發起革命、有人因為天氣心情差而遷移。世界感覺極度「活」。

## 🏛️ 當前架構

```
Frontend (GitHub Pages)
    ↕ Polling (3s)
Supabase (village_state)
    ↑
PM Agent → Spawn 3 Villager Agents
    ↑
OpenClaw Cron (每 15 分鐘)
```

## 🌐 當前狀態

**Live Demo:** https://singitsck.github.io/ai-village/

| 村民 | 職業 | 決策 |
|------|------|------|
| Alice | 農夫 | rest |
| Bob | 鐵匠 | talk_to Alice |
| Carol | 學徒 | talk_to Alice |

## 📁 文檔

- [Architecture](docs/ai-village-architecture.md) - 系統架構
- [Frontend](docs/ai-village-frontend.md) - 前端說明
- [Implementation](docs/ai-village-implementation.md) - 實現指南

## 🚀 技術棧

| 組件 | 技術 |
|------|------|
| 前端 | HTML + JS + Polling |
| 數據庫 | Supabase |
| Agent | OpenClaw (PM + 3 Villagers) |
| Cron | OpenClaw Cron |

## 📊 當前功能

- [x] Per-Villager LLM Brain
- [x] 情感記憶系統
- [x] 關係追蹤系統
- [x] 天氣系統
- [x] Multi-Agent 協調
- [x] 自然故事產生
- [ ] 故事線追蹤
- [ ] 資源經濟系統
- [ ] 訪客系統

---

*最後更新: 2026-03-26*
