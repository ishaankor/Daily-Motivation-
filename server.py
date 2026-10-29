#!/usr/bin/env python3
"""
Web Server for Render Free Web Service Deployment.
Provides health checks, browser card previews, and webhook cron triggers.
"""

import datetime
import os
import sys
from flask import Flask, jsonify, request, send_file

from bot.config import paths, twitter_config, db_config
from bot.ai_generator import QuotesCatalog
from bot.graphics import render_card_for_today, render_apple_notes_card
from bot.database import db_manager
from bot.twitter_client import twitter_client
from main import run_daily_workflow

app = Flask(__name__)
CRON_SECRET = os.getenv("CRON_SECRET", "")


@app.route("/ping", methods=["GET", "HEAD"])
@app.route("/warmup", methods=["GET", "HEAD"])
def ping():
    """Ultra-lightweight ping/warmup endpoint returning 2 bytes to prevent cold starts."""
    if request.method == "HEAD":
        return "", 200
    return "OK", 200, {"Content-Type": "text/plain"}


@app.route("/", methods=["GET", "HEAD"])
@app.route("/health", methods=["GET", "HEAD"])
def health():
    """Health check endpoint for Render and uptime monitoring."""
    if request.method == "HEAD":
        return "", 200
    now = datetime.datetime.now()

    return jsonify({
        "status": "online",
        "bot": twitter_config.handle,
        "engine": "twikit (100% Free)",
        "format": "Formula 2 (Absurd Side Quests)",
        "card_style": "Apple Notes",
        "today": now.strftime("%A, %B %d, %Y"),
        "server_time": now.isoformat()
    }), 200


@app.route("/daily", methods=["GET", "POST", "HEAD"])
@app.route("/cron/daily", methods=["GET", "POST", "HEAD"])
def cron_trigger():
    """
    Webhook endpoint triggered daily by cron-job.org or UptimeRobot.
    Usage: GET /cron/daily?secret=YOUR_SECRET (or GET /daily?secret=YOUR_SECRET)
    """
    if request.method == "HEAD":
        return "", 200

    secret = request.args.get("secret", "")
    if CRON_SECRET and secret != CRON_SECRET:
        return jsonify({"error": "Unauthorized. Invalid secret."}), 401

    if not twitter_config.daily_posting_enabled:
        return jsonify({
            "success": False,
            "paused": True,
            "message": "Daily posting is paused for account safety during cooling-off period. Set ENABLE_DAILY_POSTING=true to re-enable."
        }), 200

    try:
        now = datetime.datetime.now()
        catalog = QuotesCatalog()
        entry = catalog.get_entry_for_today()

        output_filename = f"card_{now.strftime('%Y%m%d')}_apple_notes.png"
        output_path = os.path.join(paths.output_dir, output_filename)
        card_path = render_card_for_today(entry, 0, output_path=output_path)

        tweet_1_id, tweet_2_id = twitter_client.post_quote_thread(
            entry=entry,
            image_path=card_path,
            dry_run=False
        )

        if tweet_1_id:
            db_manager.log_post(
                tweet_id=tweet_1_id,
                reply_tweet_id=tweet_2_id,
                entry=entry,
                style_used="apple_notes"
            )
            catalog.mark_posted(entry.get("id", ""))

            return jsonify({
                "success": True,
                "tweet_1_id": tweet_1_id,
                "tweet_2_id": tweet_2_id,
                "quote": entry.get("quote", ""),
                "category": entry.get("category", "SIDE QUEST"),
                "url": f"https://x.com/{twitter_config.handle.strip('@')}/status/{tweet_1_id}"
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "Failed to post thread via twikit. Check server logs."
            }), 500

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/sunday", methods=["GET", "POST", "HEAD"])
@app.route("/cron/sunday", methods=["GET", "POST", "HEAD"])
def cron_sunday_trigger():
    """Alias for cron_trigger: day themes removed in favor of dynamic side quest pool."""
    return cron_trigger()


@app.route("/preview", methods=["GET"])
def preview_card():
    """Generate and return an Apple Notes card directly in the browser."""
    now = datetime.datetime.now()
    catalog = QuotesCatalog()
    entry = catalog.get_entry_for_today()

    output_filename = f"preview_{now.strftime('%Y%m%d')}_apple_notes.png"
    output_path = os.path.join(paths.output_dir, output_filename)
    card_path = render_card_for_today(entry, output_path=output_path)

    return send_file(card_path, mimetype="image/png")


@app.route("/history", methods=["GET"])
def history():
    """View recent post history from Supabase / SQLite."""
    posts = db_manager.get_recent_history(limit=10)
    return jsonify({"count": len(posts), "posts": posts}), 200


@app.route("/replies", methods=["GET"])
def replies_history():
    """View recent engagement replies from Supabase / SQLite."""
    replies = db_manager.get_recent_replies(limit=15)
    return jsonify({"count": len(replies), "replies": replies}), 200


@app.route("/engage", methods=["GET", "POST", "HEAD"])
@app.route("/cron/engage", methods=["GET", "POST", "HEAD"])
def cron_engage_trigger():
    """
    Webhook endpoint to trigger stealth engagement reply run.
    Usage: GET /cron/engage?secret=YOUR_SECRET&count=2
    """
    if request.method == "HEAD":
        return "", 200

    secret = request.args.get("secret", "")
    if CRON_SECRET and secret != CRON_SECRET:
        return jsonify({"error": "Unauthorized. Invalid secret."}), 401

    if not twitter_config.engagement_enabled:
        return jsonify({
            "success": False,
            "disabled": True,
            "message": "Stealth engagement engine is paused for account safety. Set ENABLE_ENGAGEMENT=true to re-enable."
        }), 200

    try:
        count_param = request.args.get("count", "1")
        try:
            count = min(max(int(count_param), 1), 2)  # Hard cap between 1 and 2 per run for anti-ghost-ban safety
        except ValueError:
            count = 1

        dry_run_param = request.args.get("dry_run", "false").lower()
        dry_run = dry_run_param in ["true", "1", "yes"]
        query_override = request.args.get("query", None)

        max_age_param = request.args.get("max_age", None) or request.args.get("max_age_hours", None)
        max_age_hours = None
        if max_age_param:
            try:
                max_age_hours = float(max_age_param)
            except ValueError:
                max_age_hours = None

        result = twitter_client.run_engagement(
            count=count,
            dry_run=dry_run,
            query_override=query_override,
            max_age_hours=max_age_hours,
            mode=request.args.get("mode", "auto")
        )

        status_code = 200 if result.get("success") else 500
        return jsonify(result), status_code

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
