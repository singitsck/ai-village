#!/usr/bin/env python3
"""
AI Village - LLM-Powered Villager Tick
使用真實 LLM 決策 + Grok 風格 Prompt
"""

import json
import os
import random
import urllib.request
from datetime import datetime

# 配置
SUPABASE_URL = "https://yqwcxushplzodbnqwqxn.supabase.co"
SUPABASE_KEY = "sb_publishable_wCLebgvM4KNlSkqyevXhWA_DHOO92Lh"

# MiniMax API 配置
MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY", "")
MINIMAX_BASE_URL = "https://api.minimax.chat/v1"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

# ============================================================
# 天氣系統
# ============================================================
WEATHER_TYPES = [
    {"type": "sunny", "emoji": "☀️", "mood_modifier": 0.2, "work_efficiency": 1.2},
    {"type": "cloudy", "emoji": "☁️", "mood_modifier": 0.0, "work_efficiency": 1.0},
    {"type": "rainy", "emoji": "🌧️", "mood_modifier": -0.1, "work_efficiency": 0.7},
    {"type": "stormy", "emoji": "⛈️", "mood_modifier": -0.3, "work_efficiency": 0.3},
    {"type": "snowy", "emoji": "❄️", "mood_modifier": -0.2, "work_efficiency": 0.5},
]

def generate_weather(current_weather, tick):
    if current_weather and random.random() < 0.7:
        return current_weather
    return random.choice(WEATHER_TYPES)

# ============================================================
# Prompt 構建（Grok 風格）
# ============================================================
def build_villager_prompt(villager, all_villagers, weather, tick):
    """為村民構建 Grok 風格 Prompt"""
    p = villager.get("personality", {})
    
    # 性格
    personality_text = f"""- 開放性: {p.get('openness', 0.5):.1f}（對新事物好奇程度）
- 盡責性: {p.get('conscientiousness', 0.5):.1f}（做事認真程度）
- 外向性: {p.get('extraversion', 0.5):.1f}（喜歡社交程度）
- 友善性: {p.get('agreeableness', 0.5):.1f}（待人溫暖程度）
- 神經質: {p.get('neuroticism', 0.5):.1f}（情緒穩定程度）"""
    
    # 個人檔案
    profile_text = f"""- 生日：{villager.get('birthday', '待發掘')}
- 目前興趣：{', '.join(villager.get('hobbies', [])) or '待發掘'}
- 目前專長：{villager.get('specialty', '待發掘')}
- 家庭情況：{villager.get('family_status', '待發掘')}"""
    
    # 記憶
    memories = villager.get("memory", {}).get("observations", [])
    if memories:
        recent = list(reversed(memories[-5:]))
        memory_lines = []
        for m in recent:
            valence = m.get("emotional_valence", 0)
            emoji = "😊" if valence > 0.3 else "😠" if valence < -0.3 else "🤔"
            memory_lines.append(f"{emoji} {m['content']} (Tick {m.get('tick', '?')})")
        memory_text = "\n".join(memory_lines)
    else:
        memory_text = "目前沒有重要記憶。"
    
    # 關係
    rel_lines = []
    relationships = villager.get("relationships", {})
    for other in all_villagers:
        if other["id"] == villager["id"]:
            continue
        if other["id"] in relationships:
            rel = relationships[other["id"]]
            affinity = rel.get("affinity", 0)
            att = "有好感，想要親近" if affinity > 0.3 else "有反感，想要避開" if affinity < -0.3 else "一般關係"
            emotions = rel.get("active_emotions", [])
            emotion_str = f"（還感受到: {', '.join(emotions[-2:])})" if emotions else ""
            rel_lines.append(f"- {other['name']}: {att} {emotion_str}")
    rel_text = "\n".join(rel_lines) if rel_lines else "目前對其他人都保持中立。"
    
    # 其他村民狀態
    others_parts = []
    for v in all_villagers:
        if v["id"] != villager["id"]:
            others_parts.append(f"- {v['name']} ({v.get('role', 'unknown')}): {v.get('state', 'idle')}")
    others_text = "\n".join(others_parts) or "沒有其他村民"
    
    # 全村概況
    working = [v['name'] for v in all_villagers if v.get('state') == 'working']
    talking = [v['name'] for v in all_villagers if 'talk' in v.get('state', '')]
    idle = [v['name'] for v in all_villagers if v.get('state') == 'idle']
    village_parts = []
    if working: village_parts.append(f"{', '.join(working)}正在工作")
    if talking: village_parts.append(f"{', '.join(talking)}在聊天")
    if idle: village_parts.append(f"{', '.join(idle)}在休息")
    village_summary = "；".join(village_parts) if village_parts else "村莊很平靜"
    
    # 目標
    goal = villager.get("memory", {}).get("currentGoal", villager.get("goal", "快樂生活"))
    
    # 位置
    pos = villager.get("position", {})
    x, y = pos.get("x", 5), pos.get("y", 5)
    current_state = villager.get("state", "idle")
    
    # 天氣文本
    weather_text = f"{weather.get('emoji', '☀️')} {weather.get('type', 'sunny')}"
    
    prompt = f"""你是 {villager['name']}，一位 {villager.get('age', 30)} 歲的 {villager.get('role', 'village member')}，生活在 Willowbrook 村莊。

### 你的核心人格（Big Five）
{personality_text}

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

### 回應格式（必須嚴格遵守）
ACTION: [行動]
REASON: [用第一人稱，詳細解釋你為什麼要做這個行動，包含人格、天氣、記憶的影響，最多 2-3 句]
DISCOVERY: [如果這次有新發現就填寫，格式為「類型: 內容」，否則留空]

現在，請根據以上所有資訊，決定你接下來要做的行動。"""
    
    return prompt

# ============================================================
# LLM 調用
# ============================================================
def call_llm(prompt, villager_name):
    """調用 MiniMax LLM"""
    if not MINIMAX_API_KEY:
        log(f"⚠️ {villager_name}: 沒有 API Key，使用隨機決策")
        return None
    
    try:
        url = f"{MINIMAX_BASE_URL}/text/chatcompletion_v2"
        
        payload = {
            "model": "MiniMax-M2",
            "messages": [
                {"role": "system", "content": "你是一個村莊模擬遊戲中的村民。請根據性格和記憶做出符合角色的決定。"},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 200,
            "temperature": 0.8
        }
        
        data = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Authorization", f"Bearer {MINIMAX_API_KEY}")
        req.add_header("Content-Type", "application/json")
        
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            content = result["choices"][0]["message"]["content"]
            return content
            
    except Exception as e:
        log(f"⚠️ {villager_name}: LLM 錯誤 - {e}")
        return None

def parse_decision(response, villager):
    """解析 LLM 回應"""
    if not response:
        actions = ["moving", "working", "talking", "idle"]
        reasons = [f"身為{villager.get('role')}想要工作", "想要探索村莊", "想找人聊天", "想要休息一下"]
        return random.choice(actions), random.choice(reasons), None
    
    action = "idle"
    reason = response
    discovery = None
    
    for line in response.strip().split("\n"):
        line = line.strip()
        if "ACTION:" in line.upper():
            action_text = line.split(":", 1)[1].strip().lower()
            if "move" in action_text:
                action = "moving"
            elif "work" in action_text:
                action = "working"
            elif "talk" in action_text:
                action = "talking"
            elif "rest" in action_text:
                action = "idle"
            else:
                action = "idle"
        elif "REASON:" in line.upper():
            reason = line.split(":", 1)[1].strip()
        elif "DISCOVERY:" in line.upper():
            disc = line.split(":", 1)[1].strip()
            if disc and disc != "空":
                discovery = disc
    
    return action, reason, discovery

# ============================================================
# 記憶系統
# ============================================================
def add_memory(villager, content, valence=0, intensity=0.3):
    """添加記憶"""
    if "memory" not in villager:
        villager["memory"] = {"observations": [], "reflections": [], "currentGoal": villager.get("goal", "")}
    if "observations" not in villager["memory"]:
        villager["memory"]["observations"] = []
    
    villager["memory"]["observations"].append({
        "tick": villager.get("current_tick", 0),
        "content": content,
        "emotional_valence": valence,
        "intensity": intensity
    })
    
    if len(villager["memory"]["observations"]) > 20:
        villager["memory"]["observations"] = villager["memory"]["observations"][-20:]

def apply_memory_decay(villager, current_tick):
    """應用記憶衰減"""
    if "memory" not in villager or "observations" not in villager["memory"]:
        return
    for memory in villager["memory"]["observations"]:
        if memory.get("is_pivotal"):
            continue
        if "importance" not in memory:
            memory["importance"] = 0.5
        memory["importance"] *= 0.98

def init_relationships(villager, all_villagers):
    """初始化關係"""
    if "relationships" not in villager:
        villager["relationships"] = {}
    for other in all_villagers:
        if other["id"] != villager["id"] and other["id"] not in villager["relationships"]:
            villager["relationships"][other["id"]] = {
                "affinity": 0.0,
                "trust": 0.3,
                "active_emotions": [],
                "last_interaction": 0
            }

# ============================================================
# Supabase 操作
# ============================================================
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
        with urllib.request.urlopen(req, timeout=10) as resp:
            resp.read()
            return True
    except Exception as e:
        log(f"⚠️ 更新失敗: {e}")
        return False

# ============================================================
# 主流程
# ============================================================
def run_tick():
    log("=" * 50)
    log("🌟 開始 Village Tick (LLM Powered)")
    
    state = fetch_state()
    if not state:
        log("❌ 無法獲取狀態")
        return
    
    current_tick = state["meta"]["tick"] + 1
    state["meta"]["tick"] = current_tick
    log(f"📊 Tick: {current_tick}")
    
    # 天氣
    current_weather = state["meta"].get("weather", WEATHER_TYPES[0])
    new_weather = generate_weather(current_weather, current_tick)
    state["meta"]["weather"] = new_weather
    log(f"🌤️ 天氣: {new_weather['emoji']} {new_weather['type']}")
    
    # 初始化關係
    for villager in state["agents"]:
        init_relationships(villager, state["agents"])
        villager["current_tick"] = current_tick
    
    events = state.get("events", [])
    
    # 為每個村民做決策
    for villager in state["agents"]:
        name = villager["name"]
        old_state = villager.get("state", "idle")
        
        apply_memory_decay(villager, current_tick)
        
        prompt = build_villager_prompt(villager, state["agents"], new_weather, current_tick)
        log(f"🤖 {name} 思考中...")
        
        response = call_llm(prompt, name)
        action, reason, discovery = parse_decision(response, villager)
        new_state = action
        
        villager["state"] = new_state
        
        if new_state != old_state:
            event = {
                "tick": current_tick,
                "type": "action",
                "agent": name,
                "message": f"{name}: {old_state} → {new_state}",
                "reason": reason,
                "timestamp": datetime.now().isoformat()
            }
            events.append(event)
            log(f"🤖 {name}: {old_state} → {new_state}")
            log(f"   原因: {reason}")
        
        # 添加記憶
        add_memory(villager, f"{reason}", valence=0.1, intensity=0.3)
        
        # 處理發現
        if discovery:
            log(f"✨ {name} 發現: {discovery}")
            parts = discovery.split(":", 1)
            if len(parts) == 2:
                disc_type, disc_content = parts
                disc_type = disc_type.strip().lower()
                disc_content = disc_content.strip()
                
                if disc_type == "興趣" or disc_type == "interest":
                    if "hobbies" not in villager:
                        villager["hobbies"] = []
                    if disc_content not in villager["hobbies"]:
                        villager["hobbies"].append(disc_content)
                elif disc_type == "專長" or disc_type == "specialty":
                    villager["specialty"] = disc_content
                elif disc_type == "家庭" or disc_type == "family":
                    villager["family_status"] = disc_content
        
        # 天氣影響
        if new_weather.get("mood_modifier", 0) < -0.1 and random.random() < 0.3:
            add_memory(villager, f"天氣{new_weather['type']}讓我有點煩躁", valence=-0.2, intensity=0.3)
    
    # 天氣事件
    events.append({
        "tick": current_tick,
        "type": "weather",
        "agent": "system",
        "message": f"天氣變為 {new_weather['emoji']} {new_weather['type']}",
        "timestamp": datetime.now().isoformat()
    })
    
    state["meta"]["lastUpdated"] = datetime.now().isoformat() + "Z"
    state["events"] = events[-50:]
    
    update_state(state)
    log(f"✅ Tick {current_tick} 完成！")
    
    return state

if __name__ == "__main__":
    run_tick()
