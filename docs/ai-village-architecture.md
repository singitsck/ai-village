# AI Village Civilization — System Architecture

**Version:** 1.0  
**Date:** 2026-03-24  
**Author:** PM Agent (Research Task)

---

## 1. Overview

A browser-based AI village civilization simulation driven by a multi-agent system. The game state lives in a JSON file (`village-state.json`) hosted on GitHub Pages. A scheduled GitHub Actions workflow (cron) triggers OpenClaw agents to process the world's turn, updating the state JSON. The frontend reads and renders the JSON state in real-time.

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Repository                          │
│  ┌──────────────┐    ┌─────────────────┐    ┌───────────┐  │
│  │ village-state│◄───│  GitHub Actions  │───►│  OpenClaw │  │
│  │   .json      │    │  Cron Workflow   │    │  Agents   │  │
│  └──────┬───────┘    └─────────────────┘    └───────────┘  │
│         │                                                     │
│         │ push (on merge)                                     │
│         ▼                                                     │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              GitHub Pages (Static Host)                  │  │
│  │         https://username.github.io/village/              │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ fetch / raw
                              ▼
              ┌───────────────────────────────┐
              │       Browser Frontend        │
              │   (Reads & renders state)      │
              │   Auto-refresh every N seconds │
              └───────────────────────────────┘
```

---

## 2. Components

### 2.1 State File (`village-state.json`)

The single source of truth for the entire simulation. Hosted as a raw file in the GitHub repository, accessible at:

```
https://raw.githubusercontent.com/{owner}/{repo}/main/data/village-state.json
```

**Access via GitHub Pages (user-friendly):**
```
https://{owner}.github.io/{repo}/data/village-state.json
```

#### State Schema

```json
{
  "meta": {
    "version": "1.0.0",
    "tick": 142,
    "lastUpdated": "2026-03-24T10:00:00Z",
    "tickIntervalSeconds": 300,
    "paused": false
  },
  "village": {
    "name": "Willowbrook",
    "population": 47,
    "resources": {
      "gold": 1200,
      "food": 340,
      "wood": 210,
      "stone": 85
    },
    "buildings": [
      { "id": "b1", "type": "town_hall", "x": 0, "y": 0, "hp": 100, "level": 2 },
      { "id": "b2", "type": "farm", "x": 1, "y": 0, "hp": 80, "level": 1 }
    ],
    "technology": {
      "irrigation": { "level": 1, "unlocked": true },
      "mining": { "level": 0, "unlocked": false }
    }
  },
  "agents": [
    {
      "id": "agent_001",
      "name": "Elder Miriam",
      "role": "leader",
      "x": 0,
      "y": 0,
      "traits": ["wise", "diplomatic"],
      "goals": ["expand_population", "build_infrastructure"],
      "memory": ["Decided to build new farm at (2,3)", "Met with trader from north village"]
    }
  ],
  "events": [
    {
      "id": "evt_089",
      "tick": 141,
      "type": "resource_gain",
      "message": "Farm produced +15 food",
      "data": { "resource": "food", "amount": 15 }
    },
    {
      "id": "evt_090",
      "tick": 142,
      "type": "agent_action",
      "message": "Elder Miriam proposed building a marketplace",
      "data": { "agentId": "agent_001", "action": "propose_building", "target": "marketplace" }
    }
  ],
  "map": {
    "width": 32,
    "height": 32,
    "tiles": [
      { "x": 0, "y": 0, "type": "grass", "owner": null },
      { "x": 1, "y": 0, "type": "forest", "owner": "village" }
    ]
  }
}
```

### 2.2 GitHub Actions Cron Workflow

Location: `.github/workflows/village-tick.yml`

```yaml
name: Village Tick

on:
  schedule:
    # Every 5 minutes: */5 * * * *
    # Adjust to match tickIntervalSeconds in meta
    - cron: '*/5 * * * *'
  workflow_dispatch:
    # Manual trigger for testing

permissions:
  contents: write
  pull-requests: write

jobs:
  process-village-turn:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repo
        uses: actions/checkout@v4

      - name: Read current state
        run: |
          curl -s https://raw.githubusercontent.com/${{ github.repository }}/main/data/village-state.json -o village-state.json
          cat village-state.json

      - name: Trigger OpenClaw agent
        env:
          OPENCLAW_API_KEY: ${{ secrets.OPENCLAW_API_KEY }}
        run: |
          curl -X POST https://api.openclaw.example/v1/agents/trigger \
            -H "Authorization: Bearer $OPENCLAW_API_KEY" \
            -H "Content-Type: application/json" \
            -d '{
              "agent": "village-simulation-agent",
              "payload": {
                "stateFile": "village-state.json",
                "tick": 142
              }
            }'

      - name: Commit updated state
        run: |
          git config user.name "Village Bot"
          git config user.email "bot@village.ai"
          git add data/village-state.json
          git diff --staged --stat
          git commit -m "Tick 142: Auto-simulation update [skip ci]" || echo "No changes to commit"
          git push
```

### 2.3 OpenClaw Agent System

Each agent is a specialized AI that processes a specific aspect of the village.

#### Agent Roster

| Agent | Role | Responsibility |
|-------|------|----------------|
| `village-leader-agent` | Leader | Makes high-level decisions, assigns tasks to other agents |
| `resource-agent` | Resource Manager | Calculates production, consumption, trade |
| `builder-agent` | Construction | Proposes/plans building construction |
| `diplomat-agent` | Diplomacy | Handles village relations, events, negotiations |
| `event-logger-agent` | Historian | Logs events, maintains event timeline |

#### Agent Communication Pattern

Agents communicate via the shared `village-state.json`. Each agent:
1. Reads the current state
2. Processes its domain (e.g., calculate resource production)
3. Writes proposed changes to a `proposals/` directory
4. A final merge agent consolidates proposals and writes back to `village-state.json`

```json
// proposals/resource-proposal.json
{
  "agent": "resource-agent",
  "tick": 142,
  "actions": [
    { "type": "consume", "resource": "food", "amount": 47, "reason": "population_consumption" },
    { "type": "produce", "resource": "food", "amount": 15, "reason": "farm_output", "source": "b2" }
  ]
}
```

### 2.4 Frontend — Read/Refresh Pattern

The frontend is a static site (React/Vue/Vanilla JS) hosted on GitHub Pages. It polls the JSON state file and re-renders on changes.

#### Auto-Refresh Options

**Option A: Polling (Simple)**
```javascript
// Refresh every 30 seconds
setInterval(async () => {
  const res = await fetch('https://raw.githubusercontent.com/{owner}/{repo}/main/data/village-state.json');
  const state = await res.json();
  renderVillage(state);
}, 30000);
```

**Option B: GitHub Pages with Jekyll**  
Use Jekyll's `relative_include` or a custom plugin to serve the JSON.

**Option C: Dedicated API Proxy**  
A lightweight serverless function (Cloudflare Workers, Vercel Edge) proxies the raw file with caching headers to avoid GitHub rate limits.

#### Recommended Frontend Stack

- **Framework:** React 18 + Vite (lightweight, fast builds)
- **Styling:** Tailwind CSS or plain CSS
- **Map Rendering:** Canvas API or a lightweight library like `leaflet`
- **State Management:** React hooks (useState, useEffect)
- **Hosting:** GitHub Pages (via `peaceiris/actions-gh-pages`)

#### Frontend Features

1. **Village Map** — Grid showing tiles, buildings, agent positions
2. **Resource Panel** — Current gold, food, wood, stone with production rates
3. **Agent Roster** — List of agents with traits, goals, and current actions
4. **Event Log** — Scrollable feed of recent events
5. **Tech Tree** — Visual representation of researched technologies
6. **Controls** — Pause/Resume simulation, manual "Advance Turn" button

---

## 3. Data Flow

```
Tick T:

  [1] GitHub Actions Cron fires (every 5 min)
         │
         ▼
  [2] Check if meta.paused === true
         │  Yes → Skip processing
         │  No  → Continue
         ▼
  [3] OpenClaw agents read village-state.json
         │
         ├──► Resource Agent → proposals/resource-proposal.json
         ├──► Builder Agent  → proposals/builder-proposal.json
         ├──► Diplomat Agent → proposals/diplomat-proposal.json
         └──► Leader Agent   → proposals/leader-proposal.json
                │
                ▼
  [4] Merge Agent reads all proposals
         │  Validates & merges into single update
         │  Writes new village-state.json
         │  Increments meta.tick
         │  Sets meta.lastUpdated
         │
         ▼
  [5] Git push triggers GitHub Pages rebuild
         │
         ▼
  [6] Frontend polls & re-renders
         │
         ▼
  Tick T+1
```

---

## 4. GitHub Integration Pattern

### Repository Structure

```
ai-village/
├── .github/
│   └── workflows/
│       ├── village-tick.yml       # Cron job
│       └── deploy-pages.yml       # GitHub Pages deploy
├── data/
│   ├── village-state.json         # Game state (main)
│   └── village-state.backup.json  # Previous tick backup
├── proposals/
│   ├── resource-proposal.json
│   ├── builder-proposal.json
│   ├── diplomat-proposal.json
│   └── leader-proposal.json
├── src/
│   ├── main.js                    # Entry point
│   ├── state.js                   # State fetching & parsing
│   ├── render.js                  # DOM rendering
│   ├── map.js                     # Map rendering (Canvas)
│   └── styles.css
├── index.html
├── package.json
└── vite.config.js
```

### GitHub Actions Secrets

| Secret | Purpose |
|--------|---------|
| `OPENCLAW_API_KEY` | Auth for OpenClaw agent API |
| `OPENCLAW_WEBHOOK_SECRET` | Verify webhook authenticity |

### Rate Limiting Considerations

- GitHub raw content: **60 requests/hour** for unauthenticated
- Use a token for higher limits: `${{ secrets.GITHUB_TOKEN }}`
- Frontend should cache with `no-cache, must-revalidate` headers
- Consider using GitHub's API with ETag support for conditional fetches

---

## 5. Agent Responsibilities (Detailed)

### 5.1 Leader Agent
- Reads full village state
- Evaluates overall village health (population growth, resource balance, building needs)
- Proposes high-level goals for the tick
- Delegates tasks to specialized agents via proposals
- Decides final action when proposals conflict

### 5.2 Resource Agent
- Calculates resource production (farms, mines, forests)
- Calculates resource consumption (population, buildings)
- Detects resource shortages or surpluses
- Proposes trade actions or storage expansion
- Tracks resource history for trend analysis

### 5.3 Builder Agent
- Monitors building health and decay
- Proposes new construction sites
- Plans building upgrades based on available resources
- Coordinates with Resource Agent to ensure materials available
- Tracks construction progress across ticks

### 5.4 Diplomat Agent
- Generates random world events (visitors, disasters, opportunities)
- Processes village relationships
- Creates narrative/story for the simulation
- Logs interesting events to the event log
- Handles random encounters and village reputation

### 5.5 Event Logger Agent
- Maintains the canonical event log
- Formats events for frontend display
- Prunes old events (keep last 100 events)
- Generates tick summary
- Archives significant milestones

---

## 6. State Update Concurrency

Since multiple agents write proposals simultaneously, use file-based locking:

```bash
# Create a lock file before writing
echo "agent_001" > .proposals/.lock
git add .proposals/.lock
git commit -m "Lock proposals for tick 142"
# ... write proposals ...
git commit -m "Commit proposals for tick 142"
git push
```

Or use a **merge-first** approach:
- All agents write to their own numbered proposal file: `proposals/agent_001_tick142.json`
- Merge agent collects all and applies changes sequentially

---

## 7. Error Handling

| Scenario | Handling |
|----------|----------|
| OpenClaw API timeout | Keep current state, retry next tick, log error |
| GitHub push conflict | Pull latest, rebase proposals, push |
| Malformed proposal | Reject proposal, log warning, continue with others |
| Rate limit hit | Wait 1 minute, retry (GitHub Actions has built-in retry) |
| Frontend can't fetch | Show last cached state with "Stale data" warning |

---

## 8. Tick Interval Recommendations

| Interval | Use Case |
|----------|----------|
| `*/5 * * * *` (5 min) | Fast simulation, active development |
| `*/15 * * * *` (15 min) | Balanced, default recommendation |
| `*/30 * * * *` (30 min) | Relaxed pace, casual viewing |
| Manual only | Debugging or one-shot mode |

Match `meta.tickIntervalSeconds` to the cron schedule:
- 5 min cron → `tickIntervalSeconds: 300`
- 15 min cron → `tickIntervalSeconds: 900`

---

## 9. Scaling to Multiple Villages

For multiple simultaneous villages, use subdirectories:

```
data/
├── village-willowbrook/
│   └── state.json
├── village-oakvale/
│   └── state.json
└── meta.json
```

Frontend can switch between villages via URL parameter:
```
?village=willowbrook
```

---

## 10. Quick Start Checklist

- [ ] Create GitHub repository with GitHub Pages enabled
- [ ] Add `OPENCLAW_API_KEY` secret to repo settings
- [ ] Create `.github/workflows/village-tick.yml`
- [ ] Initialize `data/village-state.json` with initial state
- [ ] Deploy frontend to GitHub Pages
- [ ] Verify cron fires and state updates
- [ ] Add OpenClaw agent webhooks for processing
- [ ] Configure frontend polling interval

---

*This document is a living specification. Update as the system evolves.*
