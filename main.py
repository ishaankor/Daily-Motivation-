#!/usr/bin/env python3
"""
Daily Motivation Twitter Bot - Main Orchestrator & CLI

Usage:
    python main.py --dry-run               # Test today's post and generate card preview without tweeting
    python main.py --post-today            # Post today's quote + card + backstory live to Twitter
    python main.py --test-auth             # Verify Twitter, Supabase DB, and Groq AI credentials
    python main.py --generate-quotes 5     # Pre-generate 5 upcoming quotes into quotes_catalog.json
    python main.py --preview-card cosmic   # Generate a sample card preview (cosmic or obsidian)
    python main.py --history               # View recently posted tweets from database
"""

import argparse
import datetime
import os
import sys

from bot.config import paths, twitter_config, ai_config
from bot.ai_generator import QuotesCatalog, DAY_THEMES
from bot.graphics import render_card_for_today, render_cosmic_card, render_obsidian_card, WEEKDAY_STYLES
from bot.database import db_manager
from bot.twitter_client import twitter_client


def run_test_auth():
    """Verify connectivity to Twitter API, Supabase Database, and Groq AI."""
    print("=" * 60)
    print("       DIAGNOSTIC & CREDENTIAL VERIFICATION")
    print("=" * 60)

    # 1. Twitter Verification
    print("\n[1/3] Testing Twitter Authentication...")
    twitter_ok = twitter_client.verify()

    # 2. Database Verification
    print("\n[2/3] Testing Database Connection...")
    pg_conn = db_manager.get_postgres_connection()
    if pg_conn:
        print("  ✓ Supabase PostgreSQL Connection: SUCCESSFUL")
        pg_conn.close()
        db_ok = True
    else:
        print("  ⚠ PostgreSQL failed; local SQLite fallback is ACTIVE at:")
        print(f"    {paths.base_dir}/bot_history.db")
        db_ok = True

    # 3. Groq AI Verification
    print("\n[3/3] Testing Groq AI API...")
    if not ai_config.groq_api_key:
        print("  ✗ GROQ_API_KEY is missing in .env")
        ai_ok = False
    else:
        try:
            import requests
            headers = {"Authorization": f"Bearer {ai_config.groq_api_key}"}
            r = requests.get("https://api.groq.com/openai/v1/models", headers=headers, timeout=5)
            if r.status_code == 200:
                print(f"  ✓ Groq API Connection: SUCCESSFUL (Model: {ai_config.groq_model})")
                ai_ok = True
            else:
                print(f"  ✗ Groq API returned status {r.status_code}: {r.text}")
                ai_ok = False
        except Exception as e:
            print(f"  ✗ Groq connection failed: {e}")
            ai_ok = False

    print("\n" + "=" * 60)
    if twitter_ok and db_ok and ai_ok:
        print("🎉 ALL SYSTEMS OPERATIONAL! The bot is fully ready to run.")
    else:
        print("⚠ Some components reported warnings. Review output above.")
    print("=" * 60)


def run_daily_workflow(dry_run: bool = False, weekday_override: int = None):
    """Execute the full workflow for today's post (or specified weekday)."""
    now = datetime.datetime.now()
    weekday_idx = weekday_override if weekday_override is not None else now.weekday()
    theme_name, theme_desc = DAY_THEMES.get(weekday_idx, ("Daily Wisdom", "Inspiration"))
    style_name = WEEKDAY_STYLES.get(weekday_idx, "obsidian")

    day_label = "Sunday (Reset Mode)" if weekday_idx == 6 else now.strftime('%A, %B %d, %Y')
    print("=" * 60)
    print(f"  DAILY MOTIVATION BOT — {day_label}")
    print(f"  Theme: {theme_name} | Visual Style: {style_name.upper()}")
    print("=" * 60)

    # 1. Fetch or generate today's quote entry
    catalog = QuotesCatalog()
    print("\n[Step 1] Sourcing quote entry for today...")
    entry = catalog.get_entry_for_today(weekday_idx)
    print(f"  Quote: \"{entry['quote']}\"")
    print(f"  Author: {entry['author']}")
    print(f"  Category: {entry.get('category', 'WISDOM')}")

    # 2. Render Quote Card Graphic
    print("\n[Step 2] Rendering visual quote card...")
    output_filename = f"card_{now.strftime('%Y%m%d')}_{style_name}.png"
    output_path = os.path.join(paths.output_dir, output_filename)
    card_path = render_card_for_today(entry, weekday_idx, output_path=output_path)
    print(f"  Card generated at: {card_path}")

    # 3. Post (or simulate) the 2-tweet thread
    print("\n[Step 3] Publishing 2-tweet thread...")
    tweet_1_id, tweet_2_id = twitter_client.post_quote_thread(
        entry=entry,
        image_path=card_path,
        dry_run=dry_run
    )

    # 4. Log to Database and update catalog
    if tweet_1_id:
        print("\n[Step 4] Logging post history to database...")
        db_manager.log_post(
            tweet_id=tweet_1_id,
            reply_tweet_id=tweet_2_id,
            entry=entry,
            style_used=style_name
        )

        if not dry_run:
            catalog.mark_posted(entry.get("id", ""))
            print(f"  Marked quote '{entry.get('id')}' as posted in catalog.")

    print("\n" + "=" * 60)
    if dry_run:
        print("✅ DRY RUN COMPLETE. Review the card image in output/ folder.")
    elif tweet_1_id:
        print("🚀 TODAY'S MOTIVATION HAS BEEN POSTED LIVE TO TWITTER!")
    else:
        print("❌ POSTING FAILED. Check the error log above.")
    print("=" * 60)


def preview_card_sample(style: str):
    """Generate a sample card image for manual review."""
    sample = {
        "quote": "We suffer more often in imagination than in reality. True mastery is learning to quiet the storms you invent in your own mind.",
        "author": "Seneca",
        "category": "STOIC WISDOM"
    }
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    if style.lower() == "obsidian":
        out = os.path.join(paths.output_dir, f"sample_obsidian_{timestamp}.png")
        path = render_obsidian_card(sample, out)
    else:
        out = os.path.join(paths.output_dir, f"sample_cosmic_{timestamp}.png")
        path = render_cosmic_card(sample, out)
    print(f"Preview card generated: {path}")


def view_history():
    """Display recent tweets logged in the database."""
    history = db_manager.get_recent_history(limit=10)
    print("=" * 60)
    print("          RECENT POST HISTORY")
    print("=" * 60)
    if not history:
        print("No post history recorded yet.")
        return

    for i, item in enumerate(history, 1):
        print(f"[{i}] Date: {item['created_at']} | Style: {item['style']}")
        print(f"    Tweet ID: {item['tweet_id']}")
        print(f"    Quote: \"{item['quote']}\" — {item['author']}")
        print("-" * 60)


def test_ai_generator(theme: str = None):
    """Test Groq AI quote generation live and display character count verification."""
    from bot.ai_generator import generate_quote_with_groq, format_tweet_1, format_tweet_2
    import json

    theme_name = theme if theme else "Focus Friday"
    theme_desc = "Deep Work, Craftsmanship, and Execution"

    print("=" * 60)
    print(f"       TESTING GROQ AI GENERATOR")
    print(f"       Theme: {theme_name}")
    print("=" * 60)
    print("Calling Groq API (openai/gpt-oss-20b)...")

    entry = generate_quote_with_groq(theme_name, theme_desc)
    if not entry:
        print("\n❌ Failed to generate quote from Groq. Check your GROQ_API_KEY in .env.")
        return

    print("\n✅ Groq Response Received Successfully!\n")
    print("--- RAW STRUCTURED DATA ---")
    print(json.dumps(entry, indent=2))

    t1 = format_tweet_1(entry)
    t2 = format_tweet_2(entry)

    print("\n" + "=" * 60)
    print(f"--- TWEET 1 ({len(t1)}/280 chars) ---")
    print(t1)
    print("\n" + "=" * 60)
    print(f"--- TWEET 2 (THREAD REPLY) ({len(t2)}/280 chars) ---")
    print(t2)
    print("=" * 60)

    if len(t1) <= 280 and len(t2) <= 280:
        print("🎉 VALIDATION PASSED: Both tweets are strictly under the 280-char limit!")
    else:
        print("⚠ Character limit warning detected.")


def view_replies_history():
    """Display recent engagement replies logged in the database."""
    replies = db_manager.get_recent_replies(limit=10)
    print("=" * 60)
    print("          RECENT ENGAGEMENT REPLIES")
    print("=" * 60)
    if not replies:
        print("No engagement replies recorded yet.")
        return

    for i, item in enumerate(replies, 1):
        print(f"[{i}] Date: {item['created_at']} | To: @{item['target_screen_name']}")
        print(f"    Target Tweet ID: {item['target_tweet_id']}")
        print(f"    Original: \"{item['original_tweet_text'][:80]}...\"")
        print(f"    Reply ID: {item['reply_tweet_id']}")
        print(f"    Our Reply: \"{item['reply_text']}\"")
        print("-" * 60)


def run_engagement_cli(count: int = 2, dry_run: bool = False, query: Optional[str] = None):
    """Run the stealth engagement reply engine from the command line."""
    results = twitter_client.run_engagement(
        count=count,
        dry_run=dry_run,
        query_override=query
    )
    print("\n" + "=" * 60)
    print("            ENGAGEMENT SUMMARY")
    print("=" * 60)
    print(f"Success:        {results.get('success', False)}")
    print(f"Replies Posted: {results.get('replies_posted', 0)}")
    if results.get("error"):
        print(f"Error:          {results.get('error')}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Daily Motivation Twitter Bot CLI")
    parser.add_argument("--test-ai", nargs="?", const="Focus Friday", metavar="THEME", help="Test Groq quote generator live and verify character limits")
    parser.add_argument("--dry-run", action="store_true", help="Simulate today's post and generate card preview without tweeting")
    parser.add_argument("--post-today", action="store_true", help="Post today's quote + card + backstory live to Twitter")
    parser.add_argument("--sunday-reset", action="store_true", help="Simulate Sunday Reset post and card preview")
    parser.add_argument("--post-sunday", action="store_true", help="Post Sunday Reset live to Twitter")
    parser.add_argument("--engage", action="store_true", help="Run stealth human engagement reply engine")
    parser.add_argument("--count", type=int, default=2, help="Number of replies for --engage (default: 2)")
    parser.add_argument("--query", type=str, default=None, help="Specific search query override for --engage")
    parser.add_argument("--replies", action="store_true", help="View recent engagement replies from database")
    parser.add_argument("--schedule", action="store_true", help="Start background daily scheduler (runs every day at --time)")
    parser.add_argument("--time", type=str, default="09:00", help="Posting time in 24h format for --schedule (default: 09:00)")
    parser.add_argument("--test-auth", action="store_true", help="Test Twitter, Database, and Groq AI credentials")
    parser.add_argument("--generate-quotes", type=int, metavar="N", help="Pre-generate N quotes using Groq into quotes_catalog.json")
    parser.add_argument("--preview-card", choices=["cosmic", "obsidian"], help="Generate a sample card of the specified style")
    parser.add_argument("--history", action="store_true", help="View recently posted tweets from database")

    args = parser.parse_args()

    if args.engage:
        run_engagement_cli(count=args.count, dry_run=args.dry_run, query=args.query)
    elif args.replies:
        view_replies_history()
    elif args.test_ai:
        test_ai_generator(args.test_ai)
    elif args.test_auth:
        run_test_auth()
    elif args.dry_run:
        run_daily_workflow(dry_run=True)
    elif args.post_today:
        run_daily_workflow(dry_run=False)
    elif args.sunday_reset:
        run_daily_workflow(dry_run=True, weekday_override=6)
    elif args.post_sunday:
        run_daily_workflow(dry_run=False, weekday_override=6)
    elif args.schedule:
        from bot.scheduler import start_scheduler
        start_scheduler(post_time=args.time)
    elif args.generate_quotes:
        catalog = QuotesCatalog()
        catalog.prefill_batch(args.generate_quotes)
    elif args.preview_card:
        preview_card_sample(args.preview_card)
    elif args.history:
        view_history()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

