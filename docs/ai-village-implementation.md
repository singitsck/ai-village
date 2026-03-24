# AI Village Implementation Guide

**Version:** 2.0  
**Date:** 2026-03-24

---

## 1. 概述

AI Village 使用 OpenClaw Cron 觸發多 Agent 系統，每個村民有獨立的 LLM Brain。

**核心流程：**
```
Cron (每 15 分鐘) → PM Agent → Spawn Villager Agents → 決策 → Supabase
```

---

## 2. 腳本結構

### 2.1 villager-tick-multiagent.py

主腳本，負責：
1. 從 Supabase 讀取狀態
2. 為每個村民生成上下文
3. 輸出 JSON 供 PM Agent 處理

```bash
python3 scripts/villager-tick-multiagent.py
```

輸出示例：
```json
{
  "tick": 13,
  "weather": {"type": "sunny", "emoji": "☀️"},
  "villagers": {
    "Alice": {"context": "...", "villager_id": "alice"},
    "Bob": {"context": "...", "villager_id": "bob"},
    "Carol": {"context": "...", "villager_id": "carol"}
  }
}
```

### 2.2 villager-tick-llm.py

使用 MiniMax API 的版本（需要 API Key）。

### 2.3 villager-tick.py

基礎版本（隨機決策）。

---

## 3. OpenClaw Cron 設置

### 3.1 創建 Cron Job

```bash
openclaw cron create \
  --name "ai-village-multiagent" \
  --cron "*/15 * * * *" \
  --exact \
  --session isolated \
  --agent pm-agent \
  --message "AI Village Villager Brain..." \
  --timeout-seconds 180
```

### 3.2 Cron 消息格式

PM Agent 收到的消息包含：
- 運行腳本的指令
- 為每個村民 Spawn sub-agent 的指引
- 收集決策並更新 Supabase 的指示

---

## 4. PM Agent 工作流程

當 Cron 觸發時，PM Agent 執行：

```
1. 運行 villager-tick-multiagent.py
2. 讀取輸出 JSON
3. 對於每個村民 (Alice, Bob, Carol)：
   - sessions_spawn 創建 sub-agent
   - task: 村民上下文
   - runtime: subagent
   - mode: run
   - timeout: 60秒
4. 收集每個 sub-agent 的回應
5. 解析決策 (ACTION: 和 REASON:)
6. 更新 Supabase village_state
```

---

## 5. Supabase 操作

### 5.1 讀取狀態

```bash
curl "https://yqwcxushplzodbnqwqxn.supabase.co/rest/v1/village_state?id=eq.main" \
  -H "apikey: sb_publishable_wCLebgvM4KNlSkqyevXhWA_DHOO92Lh" \
  -H "Authorization: Bearer sb_publishable_wCLebgvM4KNlSkqyevXhWA_DHOO92Lh"
```

### 5.2 更新狀態

```bash
curl -X PATCH \
  "https://yqwcxushplzodbnqwqxn.supabase.co/rest/v1/village_state?id=eq.main" \
  -H "apikey: sb_publishable_wCLebgvM4KNlSkqyevXhWA_DHOO92Lh" \
  -H "Authorization: Bearer sb_publishable_wCLebgvM4KNlSkqyevXhWA_DHOO92Lh" \
  -H "Content-Type: application/json" \
  -d '{"meta": {"tick": 14}, "agents": [...]}'
```

---

## 6. 決策格式

Villager Agent 返回：

```
ACTION: work
REASON: 因為我的盡責性很高，而且天氣不錯想要工作
```

PM Agent 解析後更新 Supabase。

---

## 7. 記憶更新

每次決策後，自動添加記憶：

```json
{
  "tick": 14,
  "content": "決定working：因為天氣不錯想要工作",
  "emotional_valence": 0.2,
  "intensity": 0.5,
  "importance": 0.6,
  "is_pivotal": false
}
```

---

## 8. 本地測試

```bash
# 測試腳本
cd ~/.openclaw/workspace-ai-village
python3 scripts/villager-tick-multiagent.py

# 手動觸發 cron
openclaw cron run ai-village-multiagent
```

---

## 9. 常見問題

### Q: Cron 顯示 error 狀態？
A: 通常是 announce 失敗，不影響實際功能。檢查 sessions 中的實際執行結果。

### Q: 如何查看執行日誌？
A: 查看 `/Users/singit/.openclaw/workspace-ai-village/logs/villager-tick.log`

### Q: 如何添加新村民？
A: 
1. 在 Supabase 添加新 agent
2. 更新前端顯示
3. 更新 PM Agent 的 spawn 邏輯

---

## 10. 環境變量

```
SUPABASE_URL=https://yqwcxushplzodbnqwqxn.supabase.co
SUPABASE_KEY=sb_publishable_wCLebgvM4KNlSkqyevXhWA_DHOO92Lh
MINIMAX_API_KEY=... (可選)
```

---

*最後更新: 2026-03-24*
