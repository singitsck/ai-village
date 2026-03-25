#!/usr/bin/env python3
"""
AI Village - Multi-Agent Villager Brain System
PM Agent 使用這個腳本協調多個 Villager Agents
"""

import json
import sys
import os
from datetime import datetime

# 這個腳本會被 PM Agent 調用
# 它會讀取狀態，然後 PM Agent 會 Spawn 3 個 sub-agents

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
        record = data[0] if data else None
        # The Supabase row IS the state (no nested 'state' key)
        return record

def build_villager_context(villager, all_villagers, weather, tick):
    """為村民構建上下文"""
    p = villager.get("personality", {})
    personality = f"開放性:{p.get('openness', 0.5):.1f}, 盡責性:{p.get('conscientiousness', 0.5):.1f}, 外向性:{p.get('extraversion', 0.5):.1f}, 友善性:{p.get('agreeableness', 0.5):.1f}, 神經質:{p.get('neuroticism', 0.5):.1f}"
    
    # 記憶
    memories = villager.get("memory", {}).get("observations", [])
    if memories:
        recent = memories[-5:]
        memory_lines = ["你的重要記憶："]
        for m in recent:
            emoji = "😊" if m.get("emotional_valence", 0) > 0.3 else "😠" if m.get("emotional_valence", 0) < -0.3 else "🤔"
            memory_lines.append(f"- {emoji} {m['content']}")
        memory_text = "\n".join(memory_lines)
    else:
        memory_text = "你最近沒有特殊的記憶。"
    
    # 關係
    rel_lines = []
    relationships = villager.get("relationships", {})
    for other in all_villagers:
        if other["id"] == villager["id"]:
            continue
        if other["id"] in relationships:
            rel = relationships[other["id"]]
            if rel.get("affinity", 0) > 0.3:
                att = "有好感，想要親近"
            elif rel.get("affinity", 0) < -0.3:
                att = "有反感，想要避開"
            else:
                att = "一般關係"
            emotions = f"（還感受到: {', '.join(rel.get('active_emotions', [])[-2:])})" if rel.get("active_emotions") else ""
            rel_lines.append(f"- {other['name']}: {att} {emotions}")
    rel_text = "你對其他村民的態度：\n" + "\n".join(rel_lines) if rel_lines else "你還沒有建立深厚的友誼。"
    
    # 其他村民
    others = [f"- {v['name']} ({v.get('role', 'unknown')}): {v.get('state', 'idle')}" 
              for v in all_villagers if v["id"] != villager["id"]]
    others_text = "\n".join(others) or "沒有其他村民"
    
    goal = villager.get("memory", {}).get("currentGoal", villager.get("goal", "快樂生活"))
    
    # 新發現的屬性
    birthday = villager.get("birthday", "未知")
    hobbies = villager.get("hobbies", [])
    specialty = villager.get("specialty", "未知")
    family = villager.get("family_status", "未知")
    
    # 構建已知屬性
    known_attrs = []
    if birthday:
        known_attrs.append(f"生日: {birthday}")
    if hobbies:
        known_attrs.append(f"興趣: {', '.join(hobbies)}")
    if specialty and specialty != "未知":
        known_attrs.append(f"專長: {specialty}")
    if family and family != "未知":
        known_attrs.append(f"家庭: {family}")
    
    attrs_text = "\n".join(known_attrs) if known_attrs else "你還在探索自己的特質..."
    
    return f"""你是 {villager['name']}，一個 {villager.get('age', 30)} 歲的 {villager.get('role', 'village member')}。

【性格特徵】{personality}

【個人特質】（你已經發現的）
{attrs_text}

{memory_text}

{rel_text}

【當前天氣】{weather['emoji']} {weather['type']}（工作動機 {weather['work_efficiency']:.0%}）

【你的目標】{goal}

【其他村民】
{others_text}

【你的位置】({villager.get('position', {}).get('x', 5)}, {villager.get('position', {}).get('y', 5)})
【你當前狀態】{villager.get('state', 'idle')}

請根據以上所有信息，決定你接下來要做什麼。

重要原則：
- 你的性格會影響你的行為
- 過去的記憶會影響你的決定
- 你對其他村民的態度會影響你和誰互動
- 天氣也會影響你的心情

【特殊發現】（如果發生了有意義的事，你可以「發現」自己的新特質）
- 興趣愛好：如果某件事讓你感到快樂，可能成為你的愛好
- 專長：如果某件事你做得特別好，可能是你的專長
- 家庭：如果談到了家鄉或家人，分享你的家庭狀況

可選行動：move_to / work / talk_to [村民名] / rest / idle / discover [類型] [內容]

回應格式：
ACTION: [行動]
REASON: [原因]
DISCOVERY: [可選 - 如果你有新發現，格式：類型:內容 例如 "興趣:我喜歡在河邊畫畫"]"""

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
4. 用以下格式回應（只回一行）：
   ACTION: [行動]
   REASON: [原因]

請為以下每個村民做出決定："""
    }
    
    # 打印輸出（PM Agent 會處理這個）
    print(json.dumps(output, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
