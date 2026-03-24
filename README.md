# 🏘️ AI Village Civilization

> Multi-agent AI simulation running on GitHub Pages with Cron-driven agents

## Overview

This is a virtual village where AI agents (villagers) live, interact, and make decisions autonomously. Each agent has:
- **Memory** - They remember past events and learn from them
- **Personality** - Based on Big Five personality model
- **Goals** - Each villager has their own objectives
- **Relationships** - They form bonds with other villagers

## Architecture

```
GitHub Repo → OpenClaw Cron (15min) → Agents → village-state.json → GitHub Pages → Browser
```

- **Frontend**: Static HTML + Canvas 2D (hosted on GitHub Pages)
- **State**: JSON file in the repo (`/state/village-state.json`)
- **AI Brain**: OpenClaw Cron Jobs trigger agents to update the village

## Quick Start

1. Visit the live demo: **[https://singitsck.github.io/ai-village](https://singitsck.github.io/ai-village)**
2. Watch the villagers interact
3. Click refresh to see new events

## For Developers

### Project Structure

```
ai-village/
├── index.html          # Main display (GitHub Pages entry)
├── state/
│   └── village-state.json   # Village state (updated by agents)
├── docs/
│   ├── ai-village-architecture.md
│   ├── ai-village-implementation.md
│   └── ai-village-frontend.md
└── scripts/           # Automation scripts
```

### Village State Schema

```json
{
  "meta": {
    "version": "1.0.0",
    "lastUpdated": "2026-03-24T02:48:00Z",
    "tick": 0,
    "tickIntervalSeconds": 900
  },
  "village": {
    "name": "AI Village",
    "population": 3,
    "resources": { "gold": 100, "food": 50, "wood": 30, "stone": 10 }
  },
  "agents": [
    {
      "id": "alice",
      "name": "Alice",
      "role": "farmer",
      "personality": { "openness": 0.3, "extraversion": 0.8, ... },
      "position": {"x": 5, "y": 5},
      "state": "idle",
      "memory": { "observations": [], "reflections": [], "currentGoal": "tend to farm" }
    }
  ],
  "events": []
}
```

## Villagers

| Name | Role | Personality |
|------|------|-------------|
| Alice | Farmer | Friendly, extroverted |
| Bob | Blacksmith | Reserved, conscientious |
| Carol | Apprentice | Curious, creative |

## Tech Stack

- **Frontend**: Vanilla JS + Canvas 2D
- **State**: JSON file on GitHub
- **AI**: OpenClaw Cron Jobs (15 min interval)
- **Hosting**: GitHub Pages (free)

## License

MIT
