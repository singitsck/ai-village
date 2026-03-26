#!/usr/bin/env python3
"""
AI Village - Agent-Based Tick System
每個村民是一個獨立的 Agent
"""

import json
import urllib.request
from datetime import datetime

SUPABASE_URL = "https://yqwcxushplzodbnqwqxn.supabase.co"
SUPABASE_KEY = "sb_publishable_wCLebgvM4KNlSkqyevXhWA_DHOO92Lh"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def fetch_state():
    url = f"{SUPABASE_URL}/rest/v1/village_state?id=eq.main"
    req = urllib.request.Request(url)
    req.add_header("apikey", SUPABASE_KEY)
    req.add_header("Authorization", f"Bearer {SUPABASE_KEY}")
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
        return data[0] if data else None

def update_state(state):
    url = f"{SUPABASE_URL}/rest/v1/village_state?id=eq.main"
    data = json.dumps(state).encode()
    req = urllib.request.Request(url, data=data, method="PATCH")
    req.add_header("apikey", SUPABASE_KEY)
    req.add_header("Authorization", f"Bearer {SUPABASE_KEY}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=10):
            return True
    except Exception as e:
        log(f"更新失敗: {e}")
        return False

def build_prompt(villager, all_villagers, weather, tick):
    """為村民構建 Prompt"""
    p = villager.get("personality", {})
    
    # 記憶
    memories = villager.get("memory", {}).get("observations", [])
    if memories:
        recent = list(reversed(memories[-5:]))
        mem_lines = []
        for m in recent:
            emoji = "😊" if m.get("emotional_valence", 0) > 0.3 else "😠" if m.get("emotional_valence", 0) < -0.3 else "🤔"
            mem_lines.append(f"{emoji} {m['content']} (Tick {m.get('tick', '?')})")
        mem_text = "\n".join(mem_lines)
    else:
        mem_text = "目前沒有重要記憶。"
    
    # 關係
    rel_lines = []
    for other in all_villagers:
        if other["id"] == villager["id"]:
            continue
        rel = villager.get("relationships", {}).get(other["id"], {})
        aff = rel.get("affinity", 0)
        att = "有好感" if aff > 0.3 else "有反感" if aff < -0.3 else "一般"
        emotions = rel.get("active_emotions", [])
        emotion_str = f"（還感受到: {', '.join(emotions[-2:])})" if emotions else ""
        rel_lines.append(f"- {other['name']}: {att} {emotion_str}")
    rel_text = "\n".join(rel_lines) if rel_lines else "目前對其他人都保持中立。"
    
    # 全村概況
    working = [v['name'] for v in all_villagers if v.get('state') == 'working']
    talking = [v['name'] for v in all_villagers if 'talk' in v.get('state', '')]
    idle = [v['name'] for v in all_villagers if v.get('state') == 'idle']
    parts = []
    if working: parts.append(f"{', '.join(working)}正在工作")
    if talking: parts.append(f"{', '.join(talking)}在聊天")
    if idle: parts.append(f"{', '.join(idle)}在休息")
    village_summary = "；".join(parts) if parts else "村莊很平靜"
    
    prompt = f"""你是 {villager['name']}，一位 {villager.get('age', 30)} 歲的 {villager.get('role', 'village member')}，生活在 Willowbrook 村莊。

### 你的核心人格（Big Five）
- 開放性: {p.get('openness', 0.5):.1f}（對新事物好奇程度）
- 盡責性: {p.get('conscientiousness', 0.5):.1f}（做事認真程度）
- 外向性: {p.get('extraversion', 0.5):.1f}（喜歡社交程度）
- 友善性: {p.get('agreeableness', 0.5):.1f}（待人溫暖程度）
- 神經質: {p.get('neuroticism', 0.5):.1f}（情緒穩定程度）

### 個人檔案
- 生日：{villager.get('birthday', '待發掘')}
- 目前興趣：{', '.join(villager.get('hobbies', [])) or '待發掘'}
- 目前專長：{villager.get('specialty', '待發掘')}
- 家庭情況：{villager.get('family_status', '待發掘')}

### 重要記憶
{mem_text}

### 你對其他村民的當前態度
{rel_text}

### 當前環境資訊
- 天氣：{weather.get('emoji', '☀️')} {weather.get('type', 'sunny')}（影響心情和工作意願）
- 全村概況：{village_summary}

### 你的目標
{villager.get('memory', {}).get('currentGoal', villager.get('goal', '快樂生活'))}

### 行動原則
1. 你的決定要符合人格特質
2. 過去記憶會影響當前決定
3. 天氣會影響心情和工作意願

### 可使用的行動
- move_to (x,y) → 移動
- work → 工作
- talk_to [村民名] → 交談
- rest → 休息
- idle → 觀察
- discover [類型] [內容] → 發現新事物
- propose [行動] → 向其他村民提建議

### 回應格式
ACTION: [行動]
REASON: [原因]

請根據以上所有資訊，決定你接下來要做的行動。"""
    
    return prompt

def main():
    log("=" * 50)
    log("🤖 AI Village - Agent Tick 系統")
    
    state = fetch_state()
    if not state:
        log("❌ 無法獲取狀態")
        return
    
    tick = state["meta"]["tick"] + 1
    state["meta"]["tick"] = tick
    log(f"📊 Tick: {tick}")
    
    weather = state["meta"].get("weather", {"type": "sunny", "emoji": "☀️"})
    log(f"🌤️ 天氣: {weather['emoji']} {weather['type']}")
    
    # 為每個村民生成 prompt
    prompts = {}
    for agent in state["agents"]:
        prompts[agent["id"]] = build_prompt(agent, state["agents"], weather, tick)
    
    # 輸出 JSON 供 Agent 處理
    output = {
        "tick": tick,
        "weather": weather,
        "villagers": {
            agent["id"]: {
                "name": agent["name"],
                "prompt": build_prompt(agent, state["agents"], weather, tick)
            }
            for agent in state["agents"]
        }
    }
    
    print("\n" + "=" * 50)
    print("📋 VILLAGER PROMPTS")
    print("=" * 50)
    print(json.dumps(output, ensure_ascii=False, indent=2))
    print("\n💡 PM Agent 應為每個村民 Spawn 一個 sub-agent，讓它們根據 prompt 做出決策。")
    
    # 這裡 PM Agent 會 Spawn 3 個 sub-agents
    # 每個 sub-agent 會收到對應的 prompt 並做出決策
    # 然後 PM Agent 收集決策並更新 Supabase
    
    # 更新狀態
    state["meta"]["lastUpdated"] = datetime.now().isoformat() + "Z"
    update_state(state)
    log(f"✅ Tick {tick} 完成！")
    
    return output

if __name__ == "__main__":
    main()
