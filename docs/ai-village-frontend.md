# AI Village Simulation — Frontend Specification

**Version:** 2.0  
**Date:** 2026-03-24

---

## 1. Overview

前端是一個簡單的 HTML + JavaScript 頁面，通過 Polling 從 Supabase 讀取村莊狀態並實時顯示。

**特點：**
- 純前端（無需後端）
- Polling 刷新（每 3 秒）
- 實時顯示村民狀態
- 響應式設計

---

## 2. 技術棧

| 組件 | 技術 |
|------|------|
| 頁面 | HTML5 + CSS + Vanilla JS |
| 數據獲取 | Fetch API |
| 刷新頻率 | 3 秒一次 |
| 部署 | GitHub Pages |
| 圖標 | Emoji |

---

## 3. 數據獲取

```javascript
const SUPABASE_URL = 'https://yqwcxushplzodbnqwqxn.supabase.co';
const SUPABASE_KEY = 'sb_publishable_wCLebgvM4KNlSkqyevXhWA_DHOO92Lh';

async function fetchVillageState() {
  const response = await fetch(
    `${SUPABASE_URL}/rest/v1/village_state?id=eq.main`,
    {
      headers: {
        'apikey': SUPABASE_KEY,
        'Authorization': `Bearer ${SUPABASE_KEY}`
      }
    }
  );
  const data = await response.json();
  return data[0];
}
```

---

## 4. 顯示內容

### 4.1 村莊頭部

```
┌─────────────────────────────────────────┐
│  🏘️ AI Village — Tick 13               │
│  🌤️ Sunny ☀️  |  🕐 12:00              │
└─────────────────────────────────────────┘
```

### 4.2 村民面板

每個村民顯示：
- 名字和職業
- 當前狀態（idle/working/talking）
- 表情圖標
- 最近記憶（可選）

### 4.3 事件日誌

滾動顯示最近的事件：
- 狀態變化
- 天氣變化
- 重要記憶

---

## 5. Polling 實現

```javascript
// 3 秒刷新一次
setInterval(async () => {
  const state = await fetchVillageState();
  render(state);
}, 3000);

function render(state) {
  // 更新 Tick
  document.getElementById('tick').textContent = state.meta.tick;
  
  // 更新天氣
  document.getElementById('weather').textContent = 
    `${state.meta.weather.emoji} ${state.meta.weather.type}`;
  
  // 更新村民列表
  state.agents.forEach(agent => {
    // 更新每個村民的顯示
  });
}
```

---

## 6. 文件結構

```
ai-village/
├── index.html           # 主頁面
├── index-realtime.html  # 即時版本（使用 Supabase Realtime）
└── docs/
    └── ai-village-frontend.md
```

---

## 7. 當前實現

當前前端 (`index.html`) 是一個簡單的 Polling 版本：
- 每 3 秒從 Supabase 獲取狀態
- 顯示村民名稱、狀態、職業
- 顯示天氣和 Tick
- 滾動事件日誌

---

## 8. 未來改進

- [ ] 使用 Canvas 渲染村莊地圖
- [ ] 添加村民頭像/Sprite
- [ ] 顯示村莊資源 (gold, food, wood)
- [ ] 添加設置面板
- [ ] 使用 Realtime 訂閱（替代 Polling）

---

*最後更新: 2026-03-24*
