"""Automated Cron Scheduler for Daily Motivation Bot.

Runs automatically at a designated time every day (default: 09:00 AM local time).
Handles weekday themed mindset posts and Sunday Reset threads seamlessly.
"""

import argparse
import datetime
import os
import sys
import time
import schedule

from bot.config import paths, twitter_config
from main import run_daily_workflow

DEFAULT_POST_TIME = os.getenv("SCHEDULE_TIME", "09:00")


def scheduled_job():
    """Execute today's scheduled posting workflow."""
    now = datetime.datetime.now()
    weekday_idx = now.weekday()
    day_name = now.strftime("%A")
    
    print("\n" + "=" * 60)
    print(f"⏰ CRON TRIGGER FIRED: {day_name}, {now.strftime('%B %d, %Y %I:%M %p')}")
    if weekday_idx == 6:
        print("🌅 TODAY IS SUNDAY: Launching Sunday Reset Workflow...")
    else:
        print(f"🚀 Launching Daily Workflow for {day_name}...")
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
    print(f"✓ Daily job registered at {post_time}")
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
