#!/usr/bin/env python3
"""
AI Village - Multi-Agent Villager Brain System
PM Agent 使用這個腳本協調多個 Villager Agents
基於 Grok 優化的 Prompt 架構
"""

import json
import sys
import os
from datetime import datetime

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", file=sys.stderr)

def fetch_state():
    """從 Supabase 獲取狀態"""
    import urllib.request
    SUPABASE_URL = "https://yqwcxushplzodbnqwqxn.supabase.co"
    SUPABASE_KEY = "sb_publishable_wCLebgvM4KNlSkqyevXhWA_DHOO92Lh"
    
    url = f"{SUPABASE_URL}/rest/v1/village_state?id=eq.main"
    req = urllib.request.Request(url)
    req.add_header("apikey", SUPABASE_KEY)
    req.add_header("Authorization", f"Bearer {SUPABASE_KEY}")
    
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
        return data[0] if data else None

def build_villager_context(villager, all_villagers, weather, tick):
    """為村民構建增強版上下文（基於 Grok 架構）"""
    
    # === 性格 ===
    p = villager.get("personality", {})
    
    # === 個人檔案 ===
    profile_text = f"""- 生日：{villager.get('birthday', '待發掘')}
- 目前興趣：{', '.join(villager.get('hobbies', [])) or '待發掘'}
- 目前專長：{villager.get('specialty', '待發掘')}
- 家庭情況：{villager.get('family_status', '待發掘')}"""
    
    # === 記憶（按時間倒序）===
    memories = villager.get("memory", {}).get("observations", [])
    if memories:
        # 取最近 5 條，並倒序（最新的在最前）
        recent = list(reversed(memories[-5:]))
        memory_lines = []
        for i, m in enumerate(recent):
            valence = m.get("emotional_valence", 0)
            emoji = "😊" if valence > 0.3 else "😠" if valence < -0.3 else "🤔"
            memory_lines.append(f"{emoji} {m['content']} (Tick {m.get('tick', '?')})")
        memory_text = "\n".join(memory_lines)
    else:
        memory_text = "目前沒有重要記憶。"
    
    # === 關係 ===
    rel_lines = []
    relationships = villager.get("relationships", {})
    for other in all_villagers:
        if other["id"] == villager["id"]:
            continue
        if other["id"] in relationships:
            rel = relationships[other["id"]]
            affinity = rel.get("affinity", 0)
            if affinity > 0.3:
                att = "有好感，想要親近"
            elif affinity < -0.3:
                att = "有反感，想要避開"
            else:
                att = "一般關係"
            emotions = rel.get("active_emotions", [])
            emotion_str = f"（還感受到: {', '.join(emotions[-2:])})" if emotions else ""
            rel_lines.append(f"- {other['name']}: {att} {emotion_str}")
    rel_text = "\n".join(rel_lines) if rel_lines else "目前對其他人都保持中立。"
    
    # === 其他村民狀態 ===
    others_parts = []
    for v in all_villagers:
        if v["id"] != villager["id"]:
            others_parts.append(f"- {v['name']} ({v.get('role', 'unknown')}): {v.get('state', 'idle')}")
    others_text = "\n".join(others_parts) or "沒有其他村民"
    
    # === 全村概況 ===
    working = [v['name'] for v in all_villagers if v.get('state') == 'working']
    talking = [v['name'] for v in all_villagers if 'talk' in v.get('state', '')]
    idle = [v['name'] for v in all_villagers if v.get('state') == 'idle']
    
    village_parts = []
    if working: village_parts.append(f"{', '.join(working)}正在工作")
    if talking: village_parts.append(f"{', '.join(talking)}在聊天")
    if idle: village_parts.append(f"{', '.join(idle)}在休息")
    village_summary = "；".join(village_parts) if village_parts else "村莊很平靜"
    
    # === 目標 ===
    goal = villager.get("memory", {}).get("currentGoal", villager.get("goal", "快樂生活"))
    
    # === 位置和狀態 ===
    pos = villager.get("position", {})
    x, y = pos.get("x", 5), pos.get("y", 5)
    current_state = villager.get("state", "idle")
    
    # === 天氣 ===
    weather_text = f"{weather.get('emoji', '☀️')} {weather.get('type', 'sunny')}"
    
    # === Prompt ===
    prompt = f"""你是 {villager['name']}，一位 {villager.get('age', 30)} 歲的 {villager.get('role', 'village member')}，生活在 Willowbrook 村莊。

### 你的核心人格（Big Five）
- 開放性: {p.get('openness', 0.5):.1f}（對新事物好奇程度）
- 盡責性: {p.get('conscientiousness', 0.5):.1f}（做事認真程度）
- 外向性: {p.get('extraversion', 0.5):.1f}（喜歡社交程度）
- 友善性: {p.get('agreeableness', 0.5):.1f}（待人溫暖程度）
- 神經質: {p.get('neuroticism', 0.5):.1f}（情緒穩定程度）

### 個人檔案
{profile_text}

### 重要記憶（按時間倒序，最新的最有影響力）
{memory_text}

### 你對其他村民的當前態度
{rel_text}

### 當前環境資訊
- 天氣：{weather_text}（這會明顯影響你的心情和工作意願）
- 你的當前位置：({x}, {y})
- 你目前的狀態：{current_state}
- 全村概況：{village_summary}

### 你的主要目標
{goal}

### 行動原則（必須嚴格遵守）
1. 你的所有決定都要符合你的人格特質（例如高神經質的人容易擔心，低外向性的人不愛主動找人聊天）。
2. 過去記憶會強烈影響當前決定，尤其是最近 3-5 條記憶。
3. 你會根據天氣調整心情與行動意願（晴天開心、雨天容易疲倦或焦慮）。
4. 你可以慢慢「發現」自己的新興趣、專長或家庭故事，但不要一次發現太多。
5. 你會自然與其他村民互動，但不會突然做出違反性格的極端行為。

### 可使用的行動類型（只能選其中一種）
- move_to (x,y) → 移動到指定座標
- work → 專心工作（農田、工坊、採集等）
- talk_to [村民名稱] → 主動找某人聊天
- rest → 休息、睡覺，放鬆
- idle → 短暫發呆或觀察周圍
- discover [類型] [內容] → 發現新事物（興趣/專長/家庭/地點等）
- propose [行動] → 向其他村民提出建議（僅限性格適合的人）

### 回應格式（必須嚴格遵守）
ACTION: [行動]
REASON: [用第一人稱，詳細解釋你為什麼要做這個行動，包含人格、天氣、記憶的影響，最多 2-3 句]
DISCOVERY: [如果這次有新發現就填寫，格式為「類型: 內容」，否則留空]

現在，請根據以上所有資訊，決定你接下來要做的行動。"""
    
    return prompt

def main():
    log("🤖 AI Village - 讀取狀態並準備 Villager Agents...")
    
    state = fetch_state()
    if not state:
        log("❌ 無法獲取狀態")
        sys.exit(1)
    
    current_tick = state["meta"]["tick"] + 1
    weather = state["meta"].get("weather", {"type": "sunny", "emoji": "☀️", "work_efficiency": 1.0})
    
    log(f"📊 Tick: {current_tick}")
    log(f"🌤️ 天氣: {weather['emoji']} {weather['type']}")
    
    # 為每個村民生成 context
    villager_contexts = {}
    for villager in state["agents"]:
        name = villager["name"]
        context = build_villager_context(villager, state["agents"], weather, current_tick)
        villager_contexts[name] = {
            "context": context,
            "villager_id": villager["id"],
            "current_state": villager.get("state", "idle")
        }
        log(f"✅ {name} 的大腦已準備好")
    
    # 輸出 JSON
    output = {
        "tick": current_tick,
        "weather": weather,
        "villagers": villager_contexts,
        "instruction": """對於每個村民，請：
1. 閱讀他們的上下文
2. 想像你就是這個村民
3. 根據他們的性格、記憶、關係和天氣做出決定
4. 用以下格式回應：
   ACTION: [行動]
   REASON: [用第一人稱解釋]
   DISCOVERY: [如有新發現]

請為每個村民做出決定："""
    }
    
    print(json.dumps(output, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
