"""Automated Cron Scheduler for Daily Motivation Bot.

Runs automatically at a designated time every day (default: 09:00 AM local time).
Handles daily Formula 2 side quest posts seamlessly.
"""

import argparse
import datetime
import os
import sys
import time
import schedule

from bot.config import paths, twitter_config
from bot.twitter_client import twitter_client
import random
from main import run_daily_workflow

DEFAULT_POST_TIME = os.getenv("SCHEDULE_TIME", "09:00")
ENGAGEMENT_SLOTS = ["11:30", "15:30", "19:30"]


def scheduled_engagement_job():
    """Execute one Cohesive Growth Loop cycle with organic human timing jitter."""
    if not twitter_config.engagement_enabled:
        print("[Scheduler] Engagement loop is disabled (ENABLE_ENGAGEMENT=false). Skipping slot.")
        return

    now = datetime.datetime.now()
    jitter_sec = random.randint(45, 720)
    print(f"\n⏰ GROWTH LOOP TRIGGER: {now.strftime('%I:%M %p')} (waiting {jitter_sec // 60}m {jitter_sec % 60}s human jitter)...")
    time.sleep(jitter_sec)

    try:
        twitter_client.run_engagement(count=1, dry_run=False, mode="auto")
    except Exception as e:
        print(f"[Scheduler Error] Growth loop execution failed: {e}")

    print_next_run()


def scheduled_job():
    """Execute today's scheduled posting workflow with organic timing jitter."""
    now = datetime.datetime.now()
    day_name = now.strftime("%A")

    # Organic human timing jitter (random delay 1 to 18 minutes) to mask robotic clock regularity
    jitter_sec = random.randint(60, 1080)
    print(f"\n⏰ CRON TRIGGER RECEIVED: {day_name}, {now.strftime('%I:%M %p')}")
    print(f"🎲 Applying organic human timing jitter ({jitter_sec // 60}m {jitter_sec % 60}s delay)...")
    time.sleep(jitter_sec)

    now = datetime.datetime.now()
    print("\n" + "=" * 60)
    print(f"🚀 Launching Daily Workflow at {now.strftime('%I:%M %p')} for {day_name}...")
    print("=" * 60)

    try:
        run_daily_workflow(dry_run=False)
    except Exception as e:
        print(f"[Scheduler Error] Job execution failed: {e}")

    print_next_run()


def print_next_run():
    """Display when the next job will run."""
    next_run = schedule.next_run()
    if next_run:
        now = datetime.datetime.now()
        delta = next_run - now
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        print(f"⏳ Next post scheduled for: {next_run.strftime('%A, %B %d, %Y at %I:%M %p')} "
              f"(in {hours}h {minutes}m {seconds}s)")
    print("-" * 60)


def start_scheduler(post_time: str = DEFAULT_POST_TIME, run_immediately: bool = False):
    """Start the blocking scheduler loop."""
    print("=" * 60)
    print("       DAILY MOTIVATION BOT — CRON SCHEDULER")
    print("=" * 60)
    print(f"• Target Handle:   {twitter_config.handle}")
    print(f"• Daily Post Time: {post_time}")
    print(f"• Engine:          twikit web session (100% Free)")
    print(f"• Current Time:    {datetime.datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}")
    print("=" * 60)

    if run_immediately:
        print("⚡ --run-now flag passed: Executing workflow immediately before scheduling...")
        scheduled_job()

    schedule.every().day.at(post_time).do(scheduled_job)
    print(f"✓ Daily post job registered at {post_time}")

    for slot in ENGAGEMENT_SLOTS:
        schedule.every().day.at(slot).do(scheduled_engagement_job)
    print(f"✓ Growth Loop slots registered at: {', '.join(ENGAGEMENT_SLOTS)} (Active: {twitter_config.engagement_enabled})")
    print_next_run()

    print("Scheduler running. Press Ctrl+C to stop.\n")
    try:
        while True:
            schedule.run_pending()
            time.sleep(30)
    except KeyboardInterrupt:
        print("\n[Scheduler] Stopped by user. Exiting cleanly.")
        sys.exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Daily Motivation Cron Scheduler")
    parser.add_argument("--time", type=str, default=DEFAULT_POST_TIME, help="Daily post time in 24h format (e.g. 09:00)")
    parser.add_argument("--run-now", action="store_true", help="Run today's workflow immediately on launch, then resume schedule")
    parser.add_argument("--dry-run", action="store_true", help="Simulate scheduled run without posting")
    args = parser.parse_args()

    if args.dry_run:
        print("[Scheduler] Running simulated dry-run workflow...")
        run_daily_workflow(dry_run=True)
    else:
        start_scheduler(post_time=args.time, run_immediately=args.run_now)
