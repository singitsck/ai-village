# AI Village - 詳細架構文檔

## 🎭 Per-Villager LLM Brain 設計

### 核心理念

每個村民是一個獨立的 "Agent"，擁有自己的：
1. **性格** - 決定行為傾向
2. **記憶** - 影響未來決定
3. **關係** - 改變互動方式
4. **情緒** - 受天氣和事件影響

### 數據模型

```typescript
interface Villager {
  id: string;
  name: string;
  role: 'farmer' | 'blacksmith' | 'apprentice';
  
  // 性格 (Big Five)
  personality: {
    openness: number;           // 0-1
    conscientiousness: number;  // 0-1
    extraversion: number;        // 0-1
    agreeableness: number;      // 0-1
    neuroticism: number;         // 0-1
  };
  
  // 狀態
  state: 'idle' | 'moving' | 'working' | 'talking' | 'resting';
  position: { x: number; y: number };
  
  // 記憶系統
  memory: {
    currentGoal: string;
    observations: Memory[];     // 觀察記憶
    reflections: Reflection[];  // 反思
  };
  
  // 關係系統
  relationships: {
    [villagerId: string]: Relationship
  };
}

interface Memory {
  tick: number;
  content: string;
  emotional_valence: number;  // -1 to 1
  intensity: number;           // 0 to 1
  importance: number;           // 0 to 1
  is_pivotal: boolean;        // 重要事件不衰減
}

interface Relationship {
  affinity: number;            // -1 to 1
  trust: number;              // 0 to 1
  active_emotions: string[];   // 情緒殘留
  last_interaction: number;    // tick
}
```

## 🧠 LLM Prompt 結構

```
你是 {Villager Name}，一個 {age} 歲的 {role}。

【性格特徵】開放性:0.x, 盡責性:0.x, 外向性:0.x, 友善性:0.x, 神經質:0.x

你的重要記憶：
- 😊 和 Bob 一起工作很愉快（importance: 0.7）
- 😠 和 Carol 吵架了（importance: 0.8, is_pivotal: true）

你對其他村民的態度：
- Bob: 有好感，想要親近
- Carol: 有反感，想要避開（還感受到: anger）

當前天氣：☀️ Sunny（工作動機 120%）

你的目標：{goal}

其他村民：
- Bob (blacksmith): working
- Carol (apprentice): talking

請根據以上所有信息，決定你接下來要做什麼。

回應格式：
ACTION: [行動]
REASON: [原因]
```

## 📝 決策類型

| 行動 | 描述 | 對關係的影響 |
|------|------|--------------|
| `move_to` | 移動到新位置 | 無 |
| `work` | 執行工作 | 視情況 |
| `talk_to [name]` | 和某人交談 | 更新 affinity |
| `rest` | 休息 | 無 |
| `idle` | 保持現狀 | 無 |

## 🔗 關係更新規則

### 互動時
```
talk (正面) → affinity +0.1, trust +0.05, 添加 "gratitude"
talk (負面) → affinity -0.15, 添加 "anger"
work_together (正面) → affinity +0.15, trust +0.1
work_together (負面) → affinity -0.1, 添加 "frustration"
```

### 情緒殘留
- 每次互動可能留下情緒 ("anger", "gratitude", "joy", "frustration")
- 情緒會影響下次互動的初始態度
- 最多保留 3 個最新情緒

## 📊 記憶衰減

```
每 Tick:
  if not is_pivotal:
    importance *= 0.98  // 2% 衰減
    
  if (current_tick - memory.tick) < 3:
    importance *= 1.1   // 近距離 boost
```

## 🌤️ 天氣系統

天氣會影響：
1. **心情修改器** - 直接加到 mood
2. **工作效率** - 影響 work 行動的產出

天氣生成規則：
- 70% 機會保持現有天氣（持續性）
- 30% 機會變化

## 🔄 Multi-Agent 協調流程

```
Cron (每15分鐘)
    ↓
PM Agent 收到消息
    ↓
運行 villager-tick-multiagent.py
    ↓
獲取所有村民的上下文
    ↓
Spawn 3 個 Villager Agents (並行)
    ↓
每個 Villager Agent:
  - 收到自己的上下文
  - 用 LLM 思考決策
  - 返回 ACTION + REASON
    ↓
PM Agent 收集決策
    ↓
更新 Supabase:
  - 每個村民的 state
  - 添加新記憶
  - 更新關係（如有互動）
  - 添加事件到 events[]
    ↓
前端 Polling 自動刷新
```

## 🎯 決策質量標準

好的 Villager 決策應該：
1. **符合性格** - 内向的人不會總是想聊天
2. **考慮記憶** - 上次吵架了，今天不想見到那人
3. **反映關係** - 對好朋友更願意幫助
4. **響應天氣** - 暴風雨天不想出去
5. **有個人特色** - 每個村民的決策風格不同

## 🚀 擴展计划

### Phase 1: 基礎 (完成)
- [x] Per-Villager LLM Brain
- [x] 記憶系統
- [x] 關係系統
- [x] 天氣系統

### Phase 2: 故事系統 (規劃中)
- [ ] 故事線追蹤 (Romance/Rivalry/Mystery)
- [ ] 角色成長記錄
- [ ] 村莊編年史

### Phase 3: 經濟系統 (規劃中)
- [ ] 資源 (food, gold, wood, stone)
- [ ] 交易系統
- [ ] 村莊升級

### Phase 4: 事件系統 (規劃中)
- [ ] 節慶活動
- [ ] 訪客系統
- [ ] 災難事件

---

*最後更新: 2026-03-24*
