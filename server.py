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
from bot.ai_generator import QuotesCatalog, DAY_THEMES
from bot.graphics import render_card_for_today, WEEKDAY_STYLES
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
    weekday_idx = now.weekday()
    theme_name, _ = DAY_THEMES.get(weekday_idx, ("Daily Wisdom", ""))
    style_name = WEEKDAY_STYLES.get(weekday_idx, "cosmic")

    return jsonify({
        "status": "online",
        "bot": twitter_config.handle,
        "engine": "twikit (100% Free)",
        "today": {
            "day": now.strftime("%A, %B %d, %Y"),
            "theme": theme_name,
            "style": style_name
        },
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

    try:
        now = datetime.datetime.now()
        weekday_idx = now.weekday()
        style_name = WEEKDAY_STYLES.get(weekday_idx, "cosmic")

        catalog = QuotesCatalog()
        entry = catalog.get_entry_for_today(weekday_idx)

        output_filename = f"card_{now.strftime('%Y%m%d')}_{style_name}.png"
        output_path = os.path.join(paths.output_dir, output_filename)
        card_path = render_card_for_today(entry, weekday_idx, output_path=output_path)

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
                style_used=style_name
            )
            catalog.mark_posted(entry.get("id", ""))

            return jsonify({
                "success": True,
                "tweet_1_id": tweet_1_id,
                "tweet_2_id": tweet_2_id,
                "quote": entry["quote"],
                "author": entry["author"],
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
    """
    Dedicated webhook endpoint for Sunday Reset execution.
    Can be scheduled for Sunday evenings (e.g. 6:00 PM EST).
    Usage: GET /cron/sunday?secret=YOUR_SECRET (or GET /sunday?secret=YOUR_SECRET)
    """
    if request.method == "HEAD":
        return "", 200

    secret = request.args.get("secret", "")
    if CRON_SECRET and secret != CRON_SECRET:
        return jsonify({"error": "Unauthorized. Invalid secret."}), 401

    try:
        now = datetime.datetime.now()
        weekday_idx = 6  # Force Sunday Reset
        style_name = "obsidian"

        catalog = QuotesCatalog()
        entry = catalog.get_entry_for_today(weekday_idx)

        output_filename = f"card_{now.strftime('%Y%m%d')}_sunday_reset.png"
        output_path = os.path.join(paths.output_dir, output_filename)
        card_path = render_card_for_today(entry, weekday_idx, output_path=output_path)

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
                style_used=style_name
            )
            catalog.mark_posted(entry.get("id", ""))

            return jsonify({
                "success": True,
                "theme": "Sunday Reset",
                "tweet_1_id": tweet_1_id,
                "tweet_2_id": tweet_2_id,
                "quote": entry["quote"],
                "author": entry["author"],
                "url": f"https://x.com/{twitter_config.handle.strip('@')}/status/{tweet_1_id}"
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "Failed to post Sunday Reset thread. Check server logs."
            }), 500

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/preview", methods=["GET"])
def preview_card():
    """Generate and return today's card (or Sunday Reset if ?day=sunday) directly in the browser."""
    now = datetime.datetime.now()
    day_param = request.args.get("day", "").lower()
    if day_param in ["sunday", "sun", "6"]:
        weekday_idx = 6
    else:
        weekday_idx = now.weekday()

    style_name = WEEKDAY_STYLES.get(weekday_idx, "obsidian")

    catalog = QuotesCatalog()
    entry = catalog.get_entry_for_today(weekday_idx)

    output_filename = f"preview_{now.strftime('%Y%m%d')}_{style_name}.png"
    output_path = os.path.join(paths.output_dir, output_filename)
    card_path = render_card_for_today(entry, weekday_idx, output_path=output_path)

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

    try:
        count_param = request.args.get("count", "2")
        try:
            count = min(max(int(count_param), 1), 3)  # Hard cap between 1 and 3 per run for safety
        except ValueError:
            count = 2

        dry_run_param = request.args.get("dry_run", "false").lower()
        dry_run = dry_run_param in ["true", "1", "yes"]
        query_override = request.args.get("query", None)

        result = twitter_client.run_engagement(
            count=count,
            dry_run=dry_run,
            query_override=query_override
        )

        status_code = 200 if result.get("success") else 500
        return jsonify(result), status_code

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
