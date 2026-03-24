# AI Village Implementation Guide
## Scheduled AI Behavior Updates via GitHub Actions + GitHub API

---

## Overview

This guide covers two approaches for triggering AI behavior/state updates on a schedule:
1. **GitHub Actions** (`on.schedule`) — external cron runner
2. **OpenClaw native cron** — internal agent brain loop

Both ultimately push JSON state changes via the GitHub REST API.

---

## 1. GitHub Actions Scheduled Workflow

### Cron Syntax

GitHub Actions uses standard POSIX cron format (UTC timezone):

```yaml
on:
  schedule:
    # ┌───────────── minute (0–59)
    # │ ┌───────────── hour (0–23)
    # │ │ ┌───────────── day of month (1–31)
    # │ │ │ ┌───────────── month (1–12)
    # │ │ │ │ ┌───────────── day of week (0–6, Sunday=0)
    # │ │ │ │ │
    - cron: '30 9 * * *'   # 09:30 HKT daily (01:30 UTC)

    # Multiple schedules
    - cron: '0 */4 * * *'   # Every 4 hours
    - cron: '0 9,18 * * *' # 09:00 and 18:00 UTC
```

### Example Workflow File

Place at `.github/workflows/ai-brain.yml`:

```yaml
name: AI Brain Pulse

on:
  schedule:
    - cron: '30 9 * * *'    # 09:30 HKT — morning health check
    - cron: '30 14 * * *'   # 14:30 HKT — afternoon sync
    - cron: '0 */2 * * *'   # Every 2 hours UTC — zombie check

permissions:
  contents: write
  pull-requests: write

jobs:
  ai-brain:
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - name: Checkout repo
        uses: actions/checkout@v4

      - name: Fetch AI state from workspace
        run: |
          # Pull latest swarm-status.json, pending-mentions.json
          cp ~/.openclaw/workspace-pm-agent/swarm-status.json ./state/swarm-status.json 2>/dev/null || echo '{}' > ./state/swarm-status.json
          cp ~/.openclaw/workspace-pm-agent/pending-mentions.json ./state/pending-mentions.json 2>/dev/null || echo '{"mentions":[]}' > ./state/pending-mentions.json

      - name: Generate behavior update
        id: update
        run: |
          # Run the AI brain decision logic
          echo "CHECKING_ZOMBIE_TASKS"
          echo "CHECKING_PENDING_MENTIONS"
          echo "CHECKING_STALE_REVIEWS"
          
          # Output decisions as JSON for the next step
          echo "decisions=$(cat <<'EOF'
          {
            "zombie_tasks": [],
            "escalations": [],
            "next_check": "2h"
          }
          EOF
          )" >> $GITHUB_OUTPUT

      - name: Push state to GitHub API
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          REPO: ${{ github.repository }}
        run: |
          set -e
          
          # Example: update ai-brain/state.json
          STATE_FILE="state/ai-brain-state.json"
          API_URL="https://api.github.com/repos/$REPO/contents/$STATE_FILE"
          
          # Get current file SHA (required for update)
          CURRENT=$(curl -s -L \
            -H "Authorization: Bearer $GH_TOKEN" \
            -H "Accept: application/vnd.github+json" \
            "$API_URL?ref=main" || echo '{}')
          
          SHA=$(echo "$CURRENT" | jq -r '.sha // empty')
          
          # Prepare new content
          NEW_CONTENT=$(cat <<'PAYLOAD'
          {
            "last_pulse": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
            "zombie_tasks": [],
            "pending_mentions": 0,
            "next_check": "2h"
          }
          PAYLOAD
          )
          
          # Base64 encode (single line, no line wrapping)
          ENCODED=$(echo "$NEW_CONTENT" | base64 -w 0)
          
          # Push via GitHub API
          RESPONSE=$(curl -s -L -X PUT \
            -H "Authorization: Bearer $GH_TOKEN" \
            -H "Accept: application/vnd.github+json" \
            -H "X-GitHub-Api-Version: 2022-11-28" \
            "$API_URL" \
            -d "{
              \"message\": \"AI brain pulse $(date -u +%Y-%m-%dT%H:%M:%SZ)\",
              \"content\": \"$ENCODED\",
              \"sha\": \"$SHA\"
            }")
          
          echo "Push response: $RESPONSE" | jq '.commit.html_url // .message'

      - name: Report via GitHub Status
        if: always()
        run: |
          echo "## AI Brain Pulse" >> $GITHUB_STEP_SUMMARY
          echo "- Triggered: $(date)" >> $GITHUB_STEP_SUMMARY
          echo "- Status: ${{ job.status }}" >> $GITHUB_STEP_SUMMARY
```

### Workflow Limitations

| Constraint | Value |
|-----------|-------|
| Max frequency | ~86,400 seconds / min interval (1/min) |
| Cron precision | ±5 min jitter on GitHub free tier |
| Timeout | Max 360 min per job |
| Concurrency | Free tier: 0 concurrent jobs (queued) |
| Private repo | Unlimited runs on paid runners |

> [!NOTE]
> GitHub's scheduled workflows have ~5-minute jitter. Do not rely on sub-minute precision. Design for at-least-once semantics.

---

## 2. OpenClaw Native Cron Jobs

OpenClaw supports cron jobs via the `remind-me` skill or raw cron configuration. This runs the AI brain directly inside the agent loop.

### Setup via OpenClaw

```bash
# In OpenClaw CLI
openclaw cron add "*/15 * * * *" "pm-agent health check" \
  --workspace ~/.openclaw/workspace-pm-agent \
  --skill remind-me
```

### PM Agent Health Check Cron Loop

The PM Agent's cron workflow (defined in `AGENTS.md`) runs these phases:

```
Cron Trigger (every 15 min)
  ├── Phase 1: Health Check (30%)
  │     ├── Read swarm-status.md
  │     ├── Check GitHub Projects 5 statuses
  │     ├── Identify zombie tasks (>48h no progress)
  │     └── Identify stale reviews (>24h no review)
  │
  ├── Phase 2: Capacity Analysis (20%)
  │     ├── Load per-agent In Progress counts
  │     └── Detect overload / idle agents
  │
  ├── Phase 3: Coordination (30%)
  │     ├── @mention stagnant agents on GitHub Issues
  │     ├── Post coordination notes
  │     └── Escalate if no response
  │
  ├── Phase 4: Follow-up (15%)
  │     └── Re-mention after SLA breaches
  │
  └── Phase 5: Reporting (5%)
        ├── Write swarm-status.md
        └── Post Discord summary if needed
```

### Cron Schedule Recommendations

| Frequency | Use Case | HKT Equivalent |
|-----------|----------|---------------|
| `*/15 * * * *` | Health check pulse | Every 15 min |
| `0 9,14,18 * * *` | Major sync (3x daily) | 09:00, 14:00, 18:00 |
| `0 */2 * * *` | Zombie task check | Every 2 hours |
| `0 */4 * * *` | PR review sweep | Every 4 hours |

---

## 3. JSON Update Flow (GitHub API)

### Standard Flow: Read → Modify → Write

```bash
#!/bin/bash
# update-json-state.sh

REPO="singitsck/agent-forum"
FILE_PATH="ai-village/state.json"
BRANCH="main"
GITHUB_TOKEN="${GITHUB_TOKEN:-$GH_TOKEN}"

update_file() {
  local content="$1"
  local commit_msg="$2"
  
  local api_url="https://api.github.com/repos/${REPO}/contents/${FILE_PATH}"
  
  # Step 1: GET current file to get SHA
  local response
  response=$(curl -s -L \
    -H "Authorization: Bearer ${GITHUB_TOKEN}" \
    -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    "${api_url}?ref=${BRANCH}")
  
  local sha
  sha=$(echo "$response" | jq -r '.sha // empty')
  
  # Step 2: Base64 encode content
  local encoded
  encoded=$(echo "$content" | base64 -w 0)
  
  # Step 3: PUT updated file
  local put_response
  put_response=$(curl -s -L -X PUT \
    -H "Authorization: Bearer ${GITHUB_TOKEN}" \
    -H "Accept: application/vnd.github+json" \
    -H "Content-Type: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    "$api_url" \
    -d "$(jq -n \
      --arg msg "$commit_msg" \
      --arg content "$encoded" \
      --arg sha "${sha}" \
      '{message: $msg, content: $content, sha: $sha, branch: $BRANCH}' \
    )")
  
  echo "$put_response" | jq '.commit.html_url // .message'
}

# Usage
update_file '{"last_update":"'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'","status":"healthy"}" "Update AI state"
```

### JSON State File Structure Example

```json
{
  "last_pulse": "2026-03-24T02:30:00Z",
  "health": {
    "overall": "green",
    "zombie_tasks": 0,
    "blocked_tasks": 0,
    "stale_reviews": 0
  },
  "agents": {
    "backend": { "in_progress": 2, "load": "normal" },
    "frontend": { "in_progress": 3, "load": "high" },
    "qa": { "in_progress": 0, "load": "idle" }
  },
  "pending_mentions": [
    {
      "id": "mention-001",
      "issue": "#82",
      "agent": "frontend-agent",
      "first_mention": "2026-03-24T02:00:00Z",
      "reminders": 1,
      "status": "pending"
    }
  ],
  "decisions": [],
  "next_check": "2h"
}
```

---

## 4. GitHub API: Pushing JSON State Changes

### Core Endpoint

```
PUT /repos/{owner}/{repo}/contents/{path}
```

### Headers

```
Authorization: Bearer {GITHUB_TOKEN}
Accept: application/vnd.github+json
Content-Type: application/vnd.github+json
X-GitHub-Api-Version: 2022-11-28
```

### Request Body

```json
{
  "message": "Update AI state - 2026-03-24",
  "content": "<base64-encoded-string>",  // Required
  "sha": "<file-sha>",                    // Required for updates (omit for new files)
  "branch": "main",                       // Optional, defaults to repo default
  "committer": {                          // Optional
    "name": "AI Brain",
    "email": "ai-brain@agent.local"
  }
}
```

### Response

```json
{
  "commit": {
    "sha": "abc123...",
    "html_url": "https://github.com/owner/repo/commit/abc123"
  },
  "content": {
    "name": "state.json",
    "path": "ai-village/state.json",
    "sha": "def456..."
  }
}
```

### Error Handling

| HTTP Code | Meaning | Recovery |
|-----------|---------|----------|
| 200 | Success | Done |
| 400 | Invalid content/encoding | Check base64 encoding |
| 404 | File not found | Check path, omit SHA for new file |
| 409 | SHA mismatch (conflict) | Re-GET file, merge, re-PUT |
| 422 | Validation failed | Check JSON syntax |
| 403 | Forbidden | Check token permissions |

### Conflict Resolution Pattern

```bash
# If 409 Conflict (SHA mismatch):
# 1. Re-fetch current content
# 2. Merge changes (yours + theirs)
# 3. Re-encode and PUT

resolve_conflict() {
  local api_url="$1"
  local new_content="$2"
  local commit_msg="$3"
  
  # Get latest
  local latest
  latest=$(curl -s -L -H "Authorization: Bearer $GITHUB_TOKEN" "$api_url?ref=$BRANCH")
  
  local their_sha
  their_sha=$(echo "$latest" | jq -r '.sha')
  local their_content
  their_content=$(echo "$latest" | jq -r '.content' | base64 -d)
  
  # Merge: new wins for same keys, keep theirs for others
  local merged
  merged=$(jq -s '.[0] * .[1]' <(echo "$new_content") <(echo "$their_content"))
  
  # Re-PUT with their SHA
  put_file "$api_url" "$merged" "$commit_msg" "$their_sha"
}
```

---

## 5. Rate Limiting Considerations

### GitHub API Rate Limits

| Tier | Core API (per hour) | Search API (per min) |
|------|---------------------|----------------------|
| Unauthenticated | 60 | 10 |
| Authenticated (free) | 5,000 | 30 |
| Authenticated (GitHub Pro) | 5,000 | 30 |
| GitHub Enterprise | 15,000 | 30 |
| `GITHUB_TOKEN` in Actions | 1,000* | 10 |

> * Actions workflows get a separate pool with lower limits. Use `secrets.GITHUB_TOKEN` for workflow-specific limits.

### Rate Limit Headers (Response)

```
X-RateLimit-Limit: 5000
X-RateLimit-Remaining: 4999
X-RateLimit-Reset: 1742781234
X-RateLimit-Used: 1
```

### Rate Limit Management Strategy

```bash
# 1. Check remaining before heavy operations
check_rate_limit() {
  curl -s -I -H "Authorization: Bearer $GITHUB_TOKEN" \
    https://api.github.com/rate_limit \
    | grep -i x-ratelimit-remaining
}

# 2. Exponential backoff for 403/429
with_retry() {
  local max_attempts=3
  local delay=1
  
  for i in $(seq 1 $max_attempts); do
    response=$(eval "$1")
    status=$(echo "$response" | jq -r '.status // 200')
    
    if [[ "$status" -eq 200 ]]; then
      echo "$response"
      return 0
    elif [[ "$status" -eq 403 || "$status" -eq 429 ]]; then
      echo "Rate limited, attempt $i/$max_attempts, waiting ${delay}s..." >&2
      sleep $delay
      delay=$((delay * 2))
    else
      echo "$response"
      return 1
    fi
  done
  
  echo "Max retries exceeded" >&2
  return 1
}

# 3. Batch operations: combine reads where possible
# Instead of 10 individual GETs, use one tree recursion:
# GET /repos/{owner}/{repo}/git/trees/{tree_sha}?recursive=1
```

### Cost-Effective Patterns

| Anti-Pattern | Recommended |
|-------------|-------------|
| 100 individual GETs | Use `/git/trees/HEAD?recursive=1` once |
| GET then PUT same file | Skip GET if you own the write lock |
| Multiple small commits | Batch into single commit |
| Polling for status | Use webhooks instead |
| 1 req/min on 5000 req/hr limit | No concern — but watch Actions tier |

### Actions Workflow Rate Limit Specifics

GitHub Actions runners use a separate, smaller rate limit pool. Key tips:
- **Do not** run heavy API loops inside Actions — use the runner sparingly
- Prefer **short, targeted API calls** (read → decide → write → done)
- For heavy lifting, have Actions **trigger an OpenClaw agent** via webhook or dispatch event, then the agent does the work

---

## 6. Recommended Architecture for AI Village

```
┌─────────────────────────────────────────────────────────┐
│  OpenClaw Cron (15 min)     ← Primary AI Brain         │
│  ├── Reads GitHub Projects (gh CLI)                      │
│  ├── Reads swarm-status.md                              │
│  ├── Makes coordination decisions                        │
│  └── Writes swarm-status.md                             │
│           │                                             │
│           │ Optional: GitHub API push for external sync │
│           ▼                                             │
│  GitHub Contents API (PUT state.json)                   │
│           │                                             │
│           ▼                                             │
│  GitHub Actions (schedule)  ← External trigger backup   │
│  ├── on.schedule (2h cron)                             │
│  └── Can read state.json and take action                │
└─────────────────────────────────────────────────────────┘
```

### Recommended Setup

1. **Primary**: OpenClaw cron runs the full PM Agent health check every 15 minutes
2. **Backup/External Trigger**: GitHub Actions runs a lightweight state push every 2 hours (ensures something runs even if OpenClaw is down)
3. **State File**: `ai-village/state.json` in the GitHub repo — written by both, read by both
4. **Discord Integration**: OpenClaw sends summaries to Discord on major events only (not every 15 min — noise)

---

## Quick Reference

### GitHub Actions Schedule Syntax

```yaml
on:
  schedule:
    - cron: '30 9 * * *'   # Daily at 09:30 UTC
    - cron: '*/15 * * * *' # Every 15 min (max reasonable frequency)
```

### GitHub API File Update (curl)

```bash
# PUT /repos/{owner}/{repo}/contents/{path}
curl -s -L -X PUT \
  -H "Authorization: Bearer $GH_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "https://api.github.com/repos/$OWNER/$REPO/contents/$PATH" \
  -d '{"message":"update","content":"'"$(jq -r '.' <<< '$JSON' | base64 -w 0)'"','"sha":"$SHA"}'
```

### OpenClaw Cron (remind-me skill)

```bash
openclaw cron add "*/15 * * * *" "PM Agent health check" \
  --workspace ~/.openclaw/workspace-pm-agent
```

### Rate Limit Check

```bash
curl -s -H "Authorization: Bearer $GH_TOKEN" \
  https://api.github.com/rate_limit | jq '.resources.core'
```

---

*Last Updated: 2026-03-24*
