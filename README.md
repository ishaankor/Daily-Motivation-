# Daily Motivation Twitter/X Bot 🎯

An automated, modern AI-driven Twitter bot engineered to maximize impressions, algorithmic retention, and bookmarks for [@MotivationFTD](https://x.com/MotivationFTD).

Built with **Groq AI (Llama 3 / OSS 20B)**, a high-resolution **Obsidian Luxury Visual Framework** engine, dual **Supabase PostgreSQL / SQLite** persistence, and a 100% free cloud deployment pipeline on **Render**.

---

## Key Features

- **Obsidian Luxury Visual Framework**: Generates 4:5 portrait (1080×1350) mobile-optimized framework cards featuring the day's hero quote, 3 tactical execution principles, a highlighted Core Law, and an algorithmic retention cue (`🔖 BOOKMARK TO REVISIT`).
- **Bundled Open-Source Editorial Fonts**: Ships with Google Fonts (*Playfair Display*, *Lora*, *Inter*) in `assets/fonts/` ensuring 100% pixel-perfect visual parity between macOS and Linux (Render) environments.
- **Strict 280-Character Validation**: Automated character counter guarantees that Tweet 1 (Quote + 3 shifts + hook question) and Tweet 2 (Historical backstory) never exceed Twitter's strict character limits.
- **Sunday Reset Experience**: Specialized Sunday edition featuring weekly reflection, realignment principles, and weekly planning frameworks.
- **Zero Paid API Fees**: Bypasses Twitter's $100–$5,000/mo API paywall using authenticated web sessions via `twifork`.
- **Dual Database Persistence**: Logs tweet IDs, categories, themes, and timestamps to Supabase PostgreSQL with an automatic fallback to local SQLite (`bot_history.db`).
- **Zero-Sleep Cloud Automation**: Pre-configured for deployment on Render Free Web Services with scheduled webhook triggers via [cron-job.org](https://cron-job.org) or GitHub Actions.

---

## Weekly Theme Schedule

| Day | Theme | Focus |
| :--- | :--- | :--- |
| **Monday** | Motivation Monday | Relentless Ambition, Grit, and Momentum |
| **Tuesday** | Stoic Tuesday | Stoic Wisdom, Composure, and Mental Discipline |
| **Wednesday** | Wisdom Wednesday | Timeless Life Lessons, Humility, and Truth |
| **Thursday** | Tenacity Thursday | Perseverance, Overcoming Obstacles, and Resilience |
| **Friday** | Focus Friday | Deep Work, Craftsmanship, and Execution |
| **Saturday** | Success Saturday | Leadership, Innovation, and Entrepreneurship |
| **Sunday** | Sunday Reset | Reflection, Clarity, and Weekly Mental Renewal |

---

## Project Structure

```text
├── assets/
│   ├── fonts/               # Bundled editorial fonts (Playfair Display, Lora, Inter)
│   ├── purple-nebula.jpg    # Cosmic background asset
│   └── starry-night-sky...  # Starry background asset
├── bot/
│   ├── __init__.py
│   ├── ai_generator.py      # Groq AI generation + character validation
│   ├── config.py            # Centralized settings & environment loader
│   ├── database.py          # Supabase PostgreSQL + SQLite dual logging
│   ├── graphics.py          # Obsidian Luxury Framework card rendering engine
│   ├── scheduler.py         # Automated daily scheduler (schedule package)
│   └── twitter_client.py    # Authenticated posting engine with twifork
├── .github/workflows/
│   └── daily_bot.yml        # GitHub Actions scheduled cron trigger
├── .env.example             # Template for required environment variables
├── login.py                 # One-time browser cookie authentication helper
├── main.py                  # Primary CLI orchestrator
├── quotes_catalog.json      # Persistent queue preventing quote repetition
├── render.yaml              # Render Free Web Service deployment blueprint
├── requirements.txt         # Pinned Python dependencies
└── server.py                # Flask web service with webhook cron endpoints
```

---

## License

MIT License. See [LICENSE](LICENSE) for details.
