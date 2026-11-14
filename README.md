# Daily Motivation Twitter/X Bot 🎯 (Apple Notes Edition)

An automated, modern AI-driven Twitter bot engineered for high organic retention, bookmarks, and relatable engagement for [@MotivationFTD](https://x.com/MotivationFTD).

Built with **Groq AI (Llama 3 / OSS 120B)**, a pixel-perfect **Apple Notes Card Rendering Engine**, dual **Supabase PostgreSQL / SQLite** persistence, and a cloud-ready deployment pipeline for **Render**.

---

## 📱 Concept: Brutal Ego-Bruisers & Absurd Side Quests

Rather than generic, cliché motivational quotes that get ignored, the bot delivers sharp, brutally relatable **Ego-Bruiser** reality checks and **Absurd Side Quests** formatted as authentic iOS Apple Notes cards.

### Core Archetypes
- **Self-Handicapping Excuses**: Exposing elaborate preparation designed to delay starting.
- **Wasted Potential Addiction**: Calling out daydreams of future glory that replace present execution.
- **Ambition Cosplay Checklists**: Interactive checklists (`○` / `●`) where the fake preparation is checked off while the single uncomfortable task remains untouched.
- **Perfectionism Cope**: Showing how "polishing" and "research" are often just fear of looking messy.
- **Excuse vs. Reality Receipts**: Direct side-by-side contrasts between what we say is stopping us vs. what's actually happening.

---

## ⚡ Key Features

- **Authentic Apple Notes UI**: Renders 100% vector-accurate iOS Apple Notes cards with dynamic content-aware height, `< Notes` chevron, `Done` header, centered `Today at ...` timestamps, checklist bullets (`○` pending / `●` completed), and clean system typography.
- **AI-Powered Generation**: Leverages Groq LLM (`openai/gpt-oss-120b` with fallback to `qwen/qwen3.8-27b`) to craft unique, non-formulaic micro-essays, punchy one-liners, and contextual commentary.
- **Dual Database Persistence**: Logs tweet IDs, action types, card styles, and timestamps to **Supabase PostgreSQL** with automatic, zero-config failover to local SQLite (`bot_history.db`).
- **Hybrid Twitter Client**: Supports both the **Official X API v2 (OAuth 1.0a)** for safe writes and authenticated session management via `twikit` for media uploads and rich tweet reading.
- **Smart Engagement Engine**: Includes a rotation engine designed for quote-tweet commentary and contextual interaction with strict velocity guardrails.
- **Safety & Pause Guardrails**: Centralized kill-switches (`ENABLE_DAILY_POSTING=false`, `ENABLE_ENGAGEMENT=false`) that safely short-circuit cron webhooks with `200 OK` responses during account cooling-off periods.

---

## 🛠 Project Structure

```text
├── assets/
│   ├── fonts/               # Bundled editorial fonts (SF Pro / Inter / Lora)
│   └── backgrounds/         # Fallback visual assets
├── bot/
│   ├── __init__.py
│   ├── ai_generator.py      # Groq AI generator, quote catalog & prompt archetypes
│   ├── config.py            # Centralized settings & environment loader
│   ├── database.py          # Supabase PostgreSQL + SQLite dual logging
│   ├── graphics.py          # Dynamic Apple Notes card rendering engine (Pillow)
│   ├── reply_engine.py      # Wave-surfing engagement & quote-tweet engine
│   ├── scheduler.py         # Local cron scheduler with organic human timing jitter
│   └── twitter_client.py    # Hybrid Twitter client (Official API v2 + twikit)
├── .github/workflows/
│   ├── daily_bot.yml        # GitHub Actions backup cron trigger
│   └── engagement_bot.yml   # Engagement workflow (paused)
├── .env.example             # Template for all environment variables & API keys
├── login.py                 # One-time browser cookie authentication helper
├── main.py                  # Primary CLI orchestrator & diagnostic suite
├── quotes_catalog.json      # Persistent queue preventing repetitive content
├── render.yaml              # Render Free Web Service deployment blueprint
├── requirements.txt         # Pinned Python dependencies
└── server.py                # Flask web service with health & webhook cron endpoints
```

---

## 🚀 Getting Started

### 1. Environment Setup

Clone the repository and create a Python 3.11+ virtual environment:

```bash
git clone https://github.com/ishaankor/Daily-Motivation-.git
cd Daily-Motivation-
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configuration (`.env`)

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Key environment variables:
```ini
# Account Handle
HANDLE=@MotivationFTD

# Safety Switches
ENABLE_DAILY_POSTING=false
ENABLE_ENGAGEMENT=false

# AI Engine
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-120b

# Database (Supabase PostgreSQL)
DB_HOST=aws-1-us-west-1.pooler.supabase.com
DB_PORT=6543
DB_NAME=postgres
DB_USER=postgres.your_project_id
DB_PASSWORD=your_db_password

# Official Twitter API v2 (OAuth 1.0a)
API_KEY=your_api_key
API_SECRET_KEY=your_api_secret_key
API_ACCESS_TOKEN=your_access_token
API_SECRET_ACCESS_TOKEN=your_access_token_secret

# Webhook Security
CRON_SECRET=your_random_secret_string
```

### 3. CLI Commands

```bash
# Verify all credentials (Twitter API, Supabase, Groq)
python main.py --test-auth

# Preview today's Apple Notes card locally (saves to output/)
python main.py --preview-card

# Run dry-run simulation of today's post
python main.py --dry-run

# View recent post history from Supabase / SQLite
python main.py --history
```

---

## ☁️ Deployment (Render + Webhooks)

1. **Deploy to Render**:
   - Push to GitHub and link the repo to Render as a **Web Service** using `render.yaml`.
   - Add your secret environment variables in the Render Dashboard (`GROQ_API_KEY`, `DB_PASSWORD`, `TWITTER_AUTH_TOKEN`, `TWITTER_CT0`, etc.).

2. **Automate with cron-job.org**:
   - **Daily Post**: `GET https://your-service.onrender.com/cron/daily?secret=YOUR_CRON_SECRET` (e.g. 09:00 AM daily).
   - **Status & Health**: `GET https://your-service.onrender.com/status` for live health telemetry.

---

## 🛡 Account Health & Safety Protocol

If the account receives an algorithmic flag or restriction interstitial from X:
1. **Pause Automation**: Ensure `ENABLE_DAILY_POSTING=false` and `ENABLE_ENGAGEMENT=false`.
2. **Clear Challenges**: Log in via official mobile app on a residential IP and complete any human verification prompts (SMS/Email/CAPTCHA).
3. **Cooling-Off Window**: Allow 3–7 days of zero automated actions for spam scores to decay.
4. **Avoid Cold Replies**: Never automate unsolicited replies into strangers' threads. Limit outbound activity to standalone daily posts and high-context quote-tweets.

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
