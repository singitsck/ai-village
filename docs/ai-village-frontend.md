# AI Village Simulation — Frontend Specification

## 1. Recommended Tech Stack

### Core Stack
| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Hosting** | GitHub Pages | Free, Git-integrated, custom domain support, automatic HTTPS |
| **Rendering** | HTML5 Canvas 2D | Best for pixel art — direct pixel control, hardware accelerated, low overhead |
| **Animation** | CSS Animations + requestAnimationFrame | Smooth sprite frame cycling, GPU composited |
| **Data Fetch** | Fetch API + setInterval | Lightweight JSON polling, no build step required |
| **State** | Plain JS modules | No framework overhead; keeps bundle zero for GitHub Pages |
| **Build** | None (vanilla) | GitHub Pages serves static files directly; easier CI/CD |

### Optional Enhancements
- **p5.js** — if rapid prototyping is needed; wraps Canvas with helpful utilities
- **Phaser** — if the simulation grows complex (physics, tilemaps, sound)
- **Google Fonts** — `Press Start 2P` for authentic pixel art typography

---

## 2. Visual Design Approach

### Pixel Art / Retro Game Style

```
Color Palette (16-color NES-inspired):
  Background:   #1a1c2c (deep navy)
  Ground:       #5d275d (dark purple-brown)
  Grass:        #38b764 (pixel green)
  Wood/Buildings: #b13e53 (brick red)
  Water:        #29366f (deep blue)
  Villager skin: #f4cca1 (warm peach)
  Villager clothes: #3b5dc9 / #e07020 / #73eff7 (classic NES palette)
  UI Text:      #f4f4f4 (off-white)
  UI Accent:    #ffcd75 (gold)
```

**Font:** `Press Start 2P` (Google Fonts) — authentic 8-bit feel.

**Grid:** 16×16 or 32×32 pixel tiles. Each villager ~16×16 sprite. Buildings ~32×32.

**Layout:**
```
┌─────────────────────────────────────────┐
│  🏘️ AI Village — Day 3  ⏱ 14:32         │  ← HUD bar (top)
├─────────────────────────────────────────┤
│                                         │
│    [grass tiles]                        │
│    [villagers]  [buildings]             │  ← Canvas game area
│    [trees]      [paths]                 │
│                                         │
├─────────────────────────────────────────┤
│  👤 12 villagers | 🏠 4 buildings | 🔄  │  ← Status bar (bottom)
└─────────────────────────────────────────┘
```

---

## 3. Auto-Refresh Pattern

### Strategy: Polling with Fetch + setInterval

```javascript
// config
const POLL_INTERVAL_MS = 5000;  // 5 seconds — adjust based on simulation speed
const JSON_URL = 'data/village.json';

// state
let villageData = null;
let animationFrameId = null;

async function loadVillageJSON() {
  const res = await fetch(JSON_URL + '?t=' + Date.now(), { cache: 'no-store' });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

async function tick() {
  const fresh = await loadVillageJSON();
  if (JSON.stringify(fresh) !== JSON.stringify(villageData)) {
    villageData = fresh;
    render(villageData);
  }
}

// start polling
let intervalId = setInterval(tick, POLL_INTERVAL_MS);

// start render loop (60fps for smooth animation)
function gameLoop(timestamp) {
  update(timestamp);   // advance villager walk cycles
  render(villageData);
  animationFrameId = requestAnimationFrame(gameLoop);
}
requestAnimationFrame(gameLoop);

// stop on page hide
document.addEventListener('visibilitychange', () => {
  if (document.hidden) clearInterval(intervalId);
  else intervalId = setInterval(tick, POLL_INTERVAL_MS);
});
```

### JSON Structure Expected
```json
{
  "meta": { "day": 3, "time": "14:32", "tick": 86400 },
  "villagers": [
    {
      "id": "v1",
      "name": "Elder Mira",
      "role": "farmer",
      "x": 128, "y": 96,
      "direction": "south",
      "animation": "idle",
      "inventory": ["wheat", 3]
    }
  ],
  "buildings": [
    { "id": "b1", "type": "house", "x": 64, "y": 32, "name": "Cottage" }
  ],
  "map": {
    "width": 320, "height": 240,
    "tiles": [ 0,0,1,1,... ]   // tile type indices
  }
}
```

### CORS Note
If the simulation backend is on a different origin, either:
1. Enable CORS on the backend (`Access-Control-Allow-Origin: *`)
2. Proxy via GitHub Actions / Netlify Functions
3. Embed JSON directly in the repo (best for GitHub Pages simplicity)

---

## 4. Village Display Components

### A. Canvas Layers (render order, back → front)

| Layer | Z-index | Description |
|-------|---------|-------------|
| Ground tiles | 0 | Grass, water, path tiles |
| Buildings | 1 | Houses, farms, walls (sorted by Y) |
| Villagers | 2 | Characters (sorted by Y for depth) |
| Effects | 3 | Smoke, sparkles, particles |
| UI Overlay | 4 | HUD drawn on canvas OR HTML overlay |

### B. Tile Map Renderer
```javascript
const TILE_SIZE = 16;
const TILESET = {
  0: { color: '#38b764', label: 'grass' },
  1: { color: '#5d275d', label: 'path' },
  2: { color: '#29366f', label: 'water' },
  3: { color: '#b13e53', label: 'wall' },
};

function drawTileMap(ctx, map) {
  for (let y = 0; y < map.height / TILE_SIZE; y++) {
    for (let x = 0; x < map.width / TILE_SIZE; x++) {
      const tile = map.tiles[y * (map.width / TILE_SIZE) + x];
      ctx.fillStyle = TILESET[tile]?.color ?? '#1a1c2c';
      ctx.fillRect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE);
      // optional: draw tile borders for grid effect
      ctx.strokeStyle = 'rgba(0,0,0,0.15)';
      ctx.strokeRect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE);
    }
  }
}
```

### C. Villager Sprite Animation
```javascript
// Sprite sheet layout: each row = animation state, each col = frame
// States: idle, walk_up, walk_down, walk_left, walk_right
const SPRITE_COLS = 4;
const SPRITE_FRAME_W = 16;
const SPRITE_FRAME_H = 16;
const FRAME_DURATION_MS = 150;

const sprites = new Image();
sprites.src = 'sprites/villagers.png';
sprites.onload = () => render(villageData);

function drawVillager(ctx, villager, timestamp) {
  const animRow = { idle: 0, walk_down: 1, walk_left: 2, walk_right: 3, walk_up: 4 };
  const row = animRow[villager.animation] ?? 0;
  const frame = Math.floor((timestamp / FRAME_DURATION_MS) % SPRITE_COLS);

  ctx.drawImage(
    sprites,
    frame * SPRITE_FRAME_W, row * SPRITE_FRAME_H,
    SPRITE_FRAME_W, SPRITE_FRAME_H,
    villager.x, villager.y,
    SPRITE_FRAME_W, SPRITE_FRAME_H
  );
}
```

### D. Building Renderer
```javascript
const BUILDING_SPRITES = {
  house: { w: 32, h: 32, color: '#b13e53', roofColor: '#5d275d' },
  farm:  { w: 48, h: 32, color: '#5d275d', roofColor: '#38b764' },
  well:  { w: 16, h: 24, color: '#29366f', roofColor: '#5d275d' },
};

function drawBuilding(ctx, building) {
  const def = BUILDING_SPRITES[building.type];
  // Body
  ctx.fillStyle = def.color;
  ctx.fillRect(building.x, building.y, def.w, def.h);
  // Roof (simple triangle)
  ctx.fillStyle = def.roofColor;
  ctx.beginPath();
  ctx.moveTo(building.x, building.y);
  ctx.lineTo(building.x + def.w / 2, building.y - 12);
  ctx.lineTo(building.x + def.w, building.y);
  ctx.fill();
}
```

### E. HUD (HTML Overlay — simpler than canvas text)
```html
<div id="hud">
  <span>🏘️ AI Village</span>
  <span>Day <span id="day">—</span></span>
  <span>⏱ <span id="time">—</span></span>
</div>
<div id="statusbar">
  <span>👤 <span id="villager-count">0</span> villagers</span>
  <span>🏠 <span id="building-count">0</span> buildings</span>
  <button id="pause-btn">⏸ Pause</button>
</div>
```
```javascript
function updateHUD(data) {
  document.getElementById('day').textContent = data.meta.day;
  document.getElementById('time').textContent = data.meta.time;
  document.getElementById('villager-count').textContent = data.villagers.length;
  document.getElementById('building-count').textContent = data.buildings.length;
}
```

---

## 5. GitHub Pages Deployment

### Repository Structure
```
ai-village/
├── index.html          # Entry point
├── css/
│   └── style.css       # HUD styling, pixel-perfect layout
├── js/
│   ├── main.js         # Init, game loop, polling
│   ├── render.js       # Canvas drawing functions
│   ├── sprites.js      # Sprite loading & animation
│   └── state.js        # Village data management
├── data/
│   └── village.json    # Simulation output (updated by backend)
├── sprites/
│   ├── villagers.png   # 16×16 sprite sheet
│   └── buildings.png   # Building sprites
└── README.md
```

### GitHub Actions (auto-deploy + data pull)
```yaml
# .github/workflows/deploy.yml
name: Deploy to GitHub Pages
on:
  push:
    branches: [main]
  schedule:
    - cron: '*/5 * * * *'   # Pull new simulation data every 5 min

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Pull latest simulation data
        run: curl -s https://api.yoursim.com/village > data/village.json
      - name: Deploy
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./
```

### Custom Domain (optional)
Add `CNAME` file to repo root: `village.yourdomain.com`

---

## 6. Quick Start Checklist

- [ ] Create repo, enable GitHub Pages (Settings → Pages → Source: main branch)
- [ ] Add `index.html` with canvas element + HUD HTML overlay
- [ ] Create `data/village.json` with mock data (schema in §3)
- [ ] Add sprite sheet `sprites/villagers.png` (4 frames × 5 rows = 20 sprites)
- [ ] Wire up `loadVillageJSON()` polling + `requestAnimationFrame` render loop
- [ ] Verify Canvas renders tiles, buildings, villagers correctly
- [ ] Test auto-refresh (change JSON, verify canvas updates within 5s)
- [ ] Add `Press Start 2P` font from Google Fonts for HUD
- [ ] Enable GitHub Actions to pull live simulation data

---

## 7. Key Decision Summary

| Question | Recommendation |
|----------|---------------|
| Canvas vs SVG vs CSS Grid? | **Canvas 2D** — best for pixel art, performant at 60fps, simple sprite blitting |
| Framework or vanilla JS? | **Vanilla JS** — zero build step, GitHub Pages friendly |
| Auto-refresh strategy? | **Fetch + setInterval** (5s) + `cache: 'no-store'` + visibility API pause |
| Sprite animation? | **requestAnimationFrame** with frame-index cycling on sprite sheet |
| Hosting? | **GitHub Pages** — free, reliable, native Git integration |
| Real-time (WebSocket) vs polling? | **Polling** for now — simpler, GitHub Pages compatible. Upgrade to WebSocket only if latency matters. |

---

*Generated: 2026-03-24 | For AI Village Simulation Project*
