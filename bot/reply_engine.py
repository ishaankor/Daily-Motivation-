"""
Stealth Engagement Reply Engine
Discovers relevant organic tweets, filters for high-quality human targets,
generates fruitful, non-bot peer replies via Groq LLM, and posts safely.
"""

import asyncio
import datetime
import email.utils
import random
import re
import time
from typing import Dict, Any, List, Optional, Tuple

from bot.config import twitter_config
from bot.ai_generator import (
    generate_human_reply,
    generate_quote_tweet_commentary,
    generate_author_back_reply
)
from bot.database import db_manager


# High-recall Boolean cluster queries: packs multiple natural phrases into 1 API call
# so a single search returns 20+ fresh, high-intent human posts from the last 1-4 hours.
NICHE_QUERIES = [
    '("procrastinating" OR "doomscrolling") (study OR studying OR work OR coding OR assignment OR exam OR essay OR project)',
    '("need to lock in" OR "gotta lock in" OR "trying to lock in" OR "time to lock in")',
    '("cant focus" OR "can\'t focus" OR "zero motivation" OR "no motivation") (study OR studying OR work OR coding OR today)',
    '("building in public" OR "side project" OR "indie hacker" OR "solo founder") (bug OR css OR shipping OR launch OR landing page OR stuck)',
    '("instead of studying" OR "instead of working" OR "supposed to be studying" OR "supposed to be working")',
    '("due tomorrow" OR "due tonight" OR "midterm tomorrow") (study OR studying OR essay OR lecture OR assignment)',
    '("academic comeback" OR "lock in for" OR "rot day" OR "brain is fried") (study OR work OR coding OR exam OR semester)'
]

BLACKLIST_TERMS = [
    "crypto", "bitcoin", "btc", "eth", "solana", "airdrop", "nft", "token",
    "giveaway", "win $", "free cash", "presale", "whitelist", "telegram",
    "whatsapp", "dm me", "affiliate", "trading", "forex", "scalp", "scalping",
    "signals", "long signal", "short signal", "sqqq", "tqqq", "pnl",
    "send money", "amount of money", "need money", "send cash", "cash app",
    "cashapp", "venmo", "paypal", "gofundme", "donate to",
    "meet the", "shop now", "discount", "coupon", "use code", "free shipping",
    "pre-order", "special offer", "buy now", "link in bio", "sponsored", "#ad",
    "deals", "todays deals", "today's deals", "flash sale", "on sale", "clearance",
    "order now", "dm to order", "dm to buy", "dm for pricing", "pricing:",
    "tarot", "psychic", "tarot reading", "natal chart", "horoscope", "spell casting",
    "astrology reading", "energy reading", "soulmate reading", "love reading",
    "bet", "bets", "betting", "parlay", "sportsbook", "gambling", "casino",
    "stake now", "on stake", "stake.com", "stake casino",
    "laliga", "premier league", "nfl pick", "nba pick",
    "onlyfans", "porn", "nsfw", "sex", "sexy", "bitch", "fuck", "horny",
    "erotica", "smut", "kink", "bdsm", "fetish", "[mf]", "[ff]", "[mm]",
    "18+", "🔞", "dating", "hookup", "sugar daddy", "findom", "lewd",
    "trump", "biden", "democrat", "republican", "election", "kamala",
    "war in", "israel", "palestine", "gaza", "ukraine", "russia"
]


def get_tweet_created_at(tweet) -> Optional[datetime.datetime]:
    """
    Extract the UTC creation timestamp for a tweet across various client formats:
    1. tweet.created_at_datetime (twikit's native datetime property)
    2. tweet.created_at (Twitter timestamp string or ISO format)
    3. Snowflake ID bitwise decoding (guaranteed fallback for valid numeric tweet IDs)
    """
    # 1. Check created_at_datetime property
    dt = getattr(tweet, "created_at_datetime", None)
    if isinstance(dt, datetime.datetime):
        if dt.tzinfo is None:
            return dt.replace(tzinfo=datetime.timezone.utc)
        return dt.astimezone(datetime.timezone.utc)

    # 2. Check created_at string
    raw_created = getattr(tweet, "created_at", None)
    if isinstance(raw_created, str) and raw_created.strip():
        # Try standard Twitter format: "Wed Sep 22 15:00:00 +0000 2026"
        try:
            parsed = datetime.datetime.strptime(raw_created.strip(), "%a %b %d %H:%M:%S %z %Y")
            return parsed.astimezone(datetime.timezone.utc)
        except Exception:
            pass

        # Try RFC 2822 / email format
        try:
            parsed = email.utils.parsedate_to_datetime(raw_created.strip())
            if parsed:
                if parsed.tzinfo is None:
                    return parsed.replace(tzinfo=datetime.timezone.utc)
                return parsed.astimezone(datetime.timezone.utc)
        except Exception:
            pass

        # Try ISO 8601
        try:
            parsed = datetime.datetime.fromisoformat(raw_created.strip())
            if parsed:
                if parsed.tzinfo is None:
                    return parsed.replace(tzinfo=datetime.timezone.utc)
                return parsed.astimezone(datetime.timezone.utc)
        except Exception:
            pass

    # 3. Twitter Snowflake ID calculation
    # Snowflake ID timestamp (ms) = (id >> 22) + 1288834974657
    raw_id = getattr(tweet, "id", None)
    if raw_id is not None:
        try:
            numeric_id = int(str(raw_id).strip())
            if numeric_id > 10000000000:
                ts_ms = (numeric_id >> 22) + 1288834974657
                return datetime.datetime.fromtimestamp(ts_ms / 1000.0, tz=datetime.timezone.utc)
        except Exception:
            pass

    return None


def is_tweet_eligible(
    tweet,
    bot_handle: str,
    max_age_hours: Optional[float] = None
) -> Tuple[bool, str]:
    """
    Apply strict anti-bot, freshness, and quality filters to determine if a tweet
    is safe, organic, and recent enough for a fruitful human peer reply.
    """
    # 0. Check tweet recency / age (ensure we only reply to fresh tweets, never days-old)
    effective_max_age = max_age_hours if max_age_hours is not None else twitter_config.engagement_max_age_hours
    created_at_dt = get_tweet_created_at(tweet)
    if created_at_dt is None:
        return False, "Cannot verify tweet creation timestamp"

    now_utc = datetime.datetime.now(datetime.timezone.utc)
    age_seconds = (now_utc - created_at_dt).total_seconds()
    age_hours = max(0.0, age_seconds / 3600.0)
    if age_hours > effective_max_age:
        return False, f"Tweet is too old ({age_hours:.1f}h ago, max allowed: {effective_max_age:.1f}h)"

    # 1. Check Twitter's sensitive content flag
    if getattr(tweet, "possibly_sensitive", False):
        return False, "Twitter flagged tweet as possibly sensitive"

    # 1. Check for replies or retweets
    if getattr(tweet, "in_reply_to", None) is not None:
        return False, "Tweet is a reply to someone else"

    if getattr(tweet, "is_quote_status", False):
        return False, "Tweet is a quote tweet"

    if hasattr(tweet, "retweeted_tweet") and tweet.retweeted_tweet is not None:
        return False, "Tweet is a retweet"

    # 2. Check author
    user = getattr(tweet, "user", None)
    if not user:
        return False, "Missing user object"

    screen_name = getattr(user, "screen_name", "") or ""
    display_name = getattr(user, "name", "") or ""
    clean_bot = bot_handle.lstrip("@").lower()
    if screen_name.lower() == clean_bot:
        return False, "Cannot reply to self"

    # Check user display name for adult / scam markers
    combined_user_info = f"{screen_name} {display_name}".lower()
    for adult_marker in ["18+", "nsfw", "onlyfans", "🔞", "erotica", "smut", "findom"]:
        if adult_marker in combined_user_info:
            return False, f"User profile contains adult marker: '{adult_marker}'"

    # 3. Follower bounds (avoid bot farms with <10 followers and mega-accounts >40k with high spam-report density)
    followers = getattr(user, "followers_count", 0) or 0
    if followers < 10:
        return False, f"User follower count too low ({followers}) - likely a bot or dormant"
    if followers > 40000:
        return False, f"User follower count too high ({followers}) - high risk of spam filters"

    # 4. Reply count (we want threads where our reply will actually be read, not buried in hundreds)
    reply_count = getattr(tweet, "reply_count", 0) or 0
    if reply_count > 10:
        return False, f"Too many replies ({reply_count}) - reply would get buried"

    # 5. Text length and blacklist
    text = getattr(tweet, "text", "") or getattr(tweet, "full_text", "") or ""
    text_clean = text.strip()
    if len(text_clean) < 25:
        return False, "Tweet text too short (< 25 chars)"
    if len(text_clean) > 500:
        return False, "Tweet text too long"

    # Check if tweet is mostly a link
    links = re.findall(r"https?://\S+", text_clean)
    text_without_links = re.sub(r"https?://\S+", "", text_clean).strip()
    if links and len(text_without_links) < 25:
        return False, "Tweet is primarily a link or promo"

    # Ensure tweet is predominantly English text
    ascii_chars = sum(1 for c in text_clean if ord(c) < 128)
    if len(text_clean) > 0 and (ascii_chars / len(text_clean)) < 0.75:
        return False, "Tweet is not predominantly in English"

    text_lower = text_clean.lower()
    for term in BLACKLIST_TERMS:
        # Use word-boundary matching for standard word/phrase terms so "eth" never matches "something"/"better"
        if re.match(r"^[a-z0-9\s']+$", term):
            if re.search(rf"\b{re.escape(term)}\b", text_lower):
                return False, f"Contains blacklisted keyword: '{term}'"
        else:
            if term in text_lower:
                return False, f"Contains blacklisted keyword: '{term}'"

    # Check for commercial pricing patterns (e.g. $28, $19.99, $500)
    if re.search(r"\$\s*\d+", text_clean):
        return False, "Tweet contains monetary price / commercial offer ($XX)"

    # 6. Database deduplication (have we already engaged with this user or tweet?)
    tweet_id = str(getattr(tweet, "id", ""))
    if db_manager.has_replied_to_tweet(tweet_id):
        return False, "Already replied to this tweet ID in database"

    if db_manager.has_replied_to_user(screen_name, days=30):
        return False, f"Already replied to @{screen_name} within the last 30 days"

    return True, "Eligible"


def score_candidate_tweet(tweet, now_utc: Optional[datetime.datetime] = None) -> float:
    """
    Score an eligible candidate tweet (0-100) to prioritize targets most likely
    to produce genuine author engagement (likes/replies back) and build Tweepcred:
    1. Recency (up to 40 pts): <30m = 40, <1h = 34, <2h = 26, <4h = 16, else 8
    2. Follower sweet spot (up to 25 pts): 30-1,500 = 25 (highest reply-back rate), 1,500-5,000 = 18
    3. Low reply competition (up to 15 pts): 0 replies = 15, 1-2 replies = 10, 3-5 replies = 5
    4. First-person personal authenticity (up to 20 pts): "i ", "my ", "i'm", struggle/builder markers
    """
    if now_utc is None:
        now_utc = datetime.datetime.now(datetime.timezone.utc)

    score = 0.0

    # 1. Recency score (0-40)
    created_dt = get_tweet_created_at(tweet)
    if created_dt:
        age_hours = max(0.0, (now_utc - created_dt).total_seconds() / 3600.0)
        if age_hours <= 0.5:
            score += 40.0
        elif age_hours <= 1.0:
            score += 34.0
        elif age_hours <= 2.0:
            score += 26.0
        elif age_hours <= 4.0:
            score += 16.0
        else:
            score += 8.0

    # 2. Follower sweet spot (0-25)
    user = getattr(tweet, "user", None)
    followers = getattr(user, "followers_count", 0) or 0
    if 30 <= followers <= 1500:
        score += 25.0
    elif 1500 < followers <= 5000:
        score += 18.0
    else:
        score += 10.0

    # 3. Reply competition (0-15)
    reply_count = getattr(tweet, "reply_count", 0) or 0
    if reply_count == 0:
        score += 15.0
    elif reply_count <= 2:
        score += 10.0
    else:
        score += 5.0

    # 4. Personal authenticity & conversational hooks (0-20)
    text = (getattr(tweet, "text", "") or getattr(tweet, "full_text", "") or "").lower()
    if any(fp in f" {text} " for fp in (" i ", " i'm ", " im ", " my ", " me ", " ive ", " i've ")):
        score += 12.0
    if any(kw in text for kw in ("instead of", "supposed to", "procrastinat", "lock in", "shipping", "coding", "studying", "exam", "essay", "app", "project")):
        score += 8.0

    # 5. Early Velocity Bonus (up to +10 pts): tweets <90m old that already have 1-25 likes
    # are actively being pushed by X's Heavy Ranker into "For You" feeds.
    raw_fav = getattr(tweet, "favorite_count", 0)
    fav_count = int(raw_fav) if isinstance(raw_fav, (int, float)) else 0
    if created_dt and ((now_utc - created_dt).total_seconds() / 3600.0) <= 1.5 and 1 <= fav_count <= 25:
        score = min(100.0, score + 8.0)

    return round(score, 1)


async def process_inbound_thread_comments(
    twikit_client,
    tweepy_client: Optional[Any] = None,
    dry_run: bool = False
) -> Optional[Dict[str, Any]]:
    """
    STAGE 1 OF GROWTH LOOP (Inbound Author-Reply Flywheel — 150x Algorithmic Boost):
    Checks our most recent published threads for reader comments we haven't replied to yet,
    and replies back to 1 comment. Author-replies on our own thread carry 0% ghost-ban risk.
    """
    if not twikit_client:
        return None

    recent_posts = db_manager.get_recent_history(limit=2)
    if not recent_posts:
        return None

    clean_bot = twitter_config.handle.lstrip("@").lower()

    for post in recent_posts:
        own_tweet_id = str(post.get("tweet_id") or "")
        if not own_tweet_id or own_tweet_id.startswith("sim_"):
            continue

        try:
            if not hasattr(twikit_client, "get_tweet_by_id"):
                continue
            own_tweet = await twikit_client.get_tweet_by_id(own_tweet_id)
            replies_list = getattr(own_tweet, "replies", None) or []

            for comment in replies_list:
                comment_id = str(getattr(comment, "id", ""))
                comment_user = getattr(comment, "user", None)
                commenter_handle = (getattr(comment_user, "screen_name", "") or "").strip()
                commenter_name = (getattr(comment_user, "name", "") or commenter_handle).strip()
                comment_text = (getattr(comment, "text", "") or getattr(comment, "full_text", "") or "").strip()

                if not comment_id or not commenter_handle or not comment_text:
                    continue
                if commenter_handle.lower() == clean_bot:
                    continue
                if len(comment_text) < 4:
                    continue
                if db_manager.has_replied_to_tweet(comment_id):
                    continue

                print(f"\n🔥 [Growth Loop Stage 1] Found un-replied reader comment on our thread ({own_tweet_id})!")
                print(f"  Reader: @{commenter_handle} -> \"{comment_text}\"")

                back_reply = generate_author_back_reply(
                    parent_tweet_text=post.get("quote", ""),
                    comment_text=comment_text,
                    commenter_name=commenter_name
                )
                if not back_reply:
                    continue

                print(f"  💬 Author Back-Reply: \"{back_reply}\"")

                if dry_run:
                    return {
                        "type": "inbound_author_reply",
                        "target_tweet_id": comment_id,
                        "target_screen_name": commenter_handle,
                        "reply_text": back_reply,
                        "reply_tweet_id": f"sim_inbound_{int(time.time())}"
                    }

                # Like the reader's comment and reply back
                try:
                    if hasattr(comment, "favorite"):
                        await comment.favorite()
                except Exception:
                    pass

                await asyncio.sleep(random.uniform(4.0, 9.0))
                reply_id = ""
                if tweepy_client is not None:
                    try:
                        resp = tweepy_client.create_tweet(
                            text=back_reply,
                            in_reply_to_tweet_id=comment_id,
                            user_auth=True
                        )
                        if resp and getattr(resp, "data", None) and resp.data.get("id"):
                            reply_id = str(resp.data["id"])
                    except Exception:
                        pass

                if not reply_id:
                    posted = await twikit_client.create_tweet(text=back_reply, reply_to=comment_id)
                    reply_id = str(getattr(posted, "id", ""))

                db_manager.log_reply(
                    target_tweet_id=comment_id,
                    target_user_id=str(getattr(comment_user, "id", "")),
                    target_screen_name=commenter_handle,
                    original_tweet_text=comment_text,
                    reply_tweet_id=reply_id,
                    reply_text=back_reply
                )
                print(f"  ✓ Replied to reader @{commenter_handle} (150x Heavy Ranker thread boost active!)")
                return {
                    "type": "inbound_author_reply",
                    "target_tweet_id": comment_id,
                    "target_screen_name": commenter_handle,
                    "reply_text": back_reply,
                    "reply_tweet_id": reply_id
                }
        except Exception:
            continue

    return None


async def search_engagement_candidates(
    twikit_client,
    max_candidates: int = 4,
    query_override: Optional[str] = None,
    max_age_hours: Optional[float] = None
) -> List[Any]:
    """
    Search Twitter using high-recall Boolean cluster queries, score all eligible
    candidates by author-engagement probability, and print diagnostic filter telemetry.
    """
    effective_max_age = max_age_hours if max_age_hours is not None else twitter_config.engagement_max_age_hours
    now_utc = datetime.datetime.now(datetime.timezone.utc)

    # Try up to 2 Boolean cluster queries (stops after the 1st query if eligible tweets are found)
    queries_to_try = [query_override] if query_override else random.sample(NICHE_QUERIES, min(2, len(NICHE_QUERIES)))
    candidates = []
    seen_ids = set()

    for q_idx, raw_query in enumerate(queries_to_try):
        if not raw_query:
            continue
        # Note: -filter:links strips external promo links at X's search index level;
        # we avoid -filter:replies in raw query syntax because X GraphQL search often drops valid posts when combined with OR clusters.
        search_query = f"{raw_query} -filter:retweets -filter:links lang:en"
        print(f"\n[Engagement Search] Query [{q_idx+1}/{len(queries_to_try)}]: {search_query}")

        try:
            results = await twikit_client.search_tweet(search_query, product="Latest", count=20)
            if not results:
                print("  -> 0 raw tweets returned by X for this query.")
            else:
                raw_batch = list(results)
                skip_reasons: Dict[str, int] = {}
                batch_candidates = []

                for tweet in raw_batch:
                    tweet_id = str(getattr(tweet, "id", ""))
                    if tweet_id in seen_ids:
                        continue
                    seen_ids.add(tweet_id)

                    eligible, reason = is_tweet_eligible(
                        tweet,
                        twitter_config.handle,
                        max_age_hours=effective_max_age
                    )
                    if eligible:
                        batch_candidates.append(tweet)
                    else:
                        # Group skip reasons for clean diagnostic output
                        short_reason = reason.split("(")[0].split(":")[0].strip()
                        skip_reasons[short_reason] = skip_reasons.get(short_reason, 0) + 1

                # Adaptive Age Fallback: if X returned tweets on this query, none met effective_max_age,
                # and max_age_hours wasn't explicitly forced, relax age window up to 8.0h on the ALREADY fetched batch
                # so we don't waste an extra search API call!
                if not batch_candidates and max_age_hours is None and effective_max_age < 8.0:
                    relaxed_age = 8.0
                    for tweet in raw_batch:
                        eligible_rel, _ = is_tweet_eligible(
                            tweet,
                            twitter_config.handle,
                            max_age_hours=relaxed_age
                        )
                        if eligible_rel:
                            batch_candidates.append(tweet)
                    if batch_candidates:
                        print(f"  ℹ Relaxed age window to {relaxed_age:.1f}h on fetched batch ({len(batch_candidates)} found).")

                for tweet in batch_candidates:
                    screen_name = getattr(getattr(tweet, "user", None), "screen_name", "unknown")
                    followers = getattr(getattr(tweet, "user", None), "followers_count", 0) or 0
                    created_dt = get_tweet_created_at(tweet)
                    if created_dt:
                        age_h = max(0.0, (now_utc - created_dt).total_seconds() / 3600.0)
                        age_str = f"{age_h:.1f}h ago" if age_h >= 1.0 else f"{int(age_h * 60)}m ago"
                    else:
                        age_str = "recent"
                    cand_score = score_candidate_tweet(tweet, now_utc=now_utc)
                    print(f"  ✓ Candidate: @{screen_name} ({age_str} | {followers} flw | Score: {cand_score}/100)")
                    candidates.append(tweet)

                if skip_reasons:
                    summary_str = ", ".join(f"{v}× {k}" for k, v in sorted(skip_reasons.items(), key=lambda item: -item[1]))
                    print(f"  [Filter Telemetry] Checked {len(raw_batch)} tweets -> {len(batch_candidates)} eligible | Skipped: {summary_str}")

        except Exception as e:
            print(f"[Engagement Search] Error searching query '{raw_query}': {e}")

        # Stop immediately after the first query if we found at least 1 candidate (no multi-query burst)
        if candidates:
            break

        # Only pause if we need to try the fallback query
        if q_idx < len(queries_to_try) - 1:
            pause_sec = random.uniform(4.0, 7.5)
            print(f"  -> 0 eligible candidates on first query; pausing {pause_sec:.1f}s before fallback cluster...")
            await asyncio.sleep(pause_sec)

    # Sort discovered candidates by composite quality score descending (tie-broken by newest timestamp)
    def _candidate_sort_key(t):
        dt = get_tweet_created_at(t)
        ts = dt.timestamp() if dt else 0.0
        return (score_candidate_tweet(t, now_utc=now_utc), ts)

    candidates.sort(key=_candidate_sort_key, reverse=True)
    return candidates[:max_candidates]


async def run_engagement_cycle(
    twikit_client,
    count: int = 1,
    dry_run: bool = False,
    query_override: Optional[str] = None,
    max_age_hours: Optional[float] = None,
    tweepy_client: Optional[Any] = None,
    mode: str = "auto"
) -> Dict[str, Any]:
    """
    Execute the Cohesive Growth Loop:
    Stage 1: Inbound Thread Comment Responder (150x Heavy Ranker boost, 0% ban risk).
    Stage 2: High-Recall Boolean Search + Velocity Candidate Scoring (0-100).
    Stage 3: Dual-Mode Execution ('reply', 'quote', or 'auto' mix of Quote-Tweet Field Notes & Stealth Replies).
    """
    effective_max_age = max_age_hours if max_age_hours is not None else twitter_config.engagement_max_age_hours
    effective_count = max(1, min(count, 2)) if not dry_run else max(1, count)
    clean_mode = (mode or "auto").strip().lower()

    print("=" * 60)
    mode_label = "DRY RUN (Preview Only)" if dry_run else "LIVE EXECUTION"
    write_engine = "Official X API v2 (OAuth 1.0a)" if tweepy_client else "twikit Web Session"
    print(f"      COHESIVE GROWTH LOOP — {mode_label}")
    print(f"      Target Count: {effective_count} | Mode: {clean_mode.upper()} | Max Age: {effective_max_age:.1f}h")
    print(f"      Write Engine: {write_engine}")
    print("=" * 60)

    if not twikit_client and not dry_run:
        return {
            "success": False,
            "error": "Twitter client not authenticated. Run login.py first.",
            "replies_posted": 0,
            "engagements": []
        }

    engagements = []

    # STAGE 1: Check for un-replied comments on our own recent threads first (0% ghost-ban risk, 150x boost)
    inbound_action = await process_inbound_thread_comments(
        twikit_client=twikit_client,
        tweepy_client=tweepy_client,
        dry_run=dry_run
    )
    if inbound_action:
        engagements.append(inbound_action)

    # STAGE 0: Database Velocity Guardrail before outbound outreach (Live Mode Only)
    if not dry_run:
        velocity = db_manager.get_reply_velocity_status(
            max_daily=twitter_config.engagement_max_daily_replies,
            min_cooldown_hours=twitter_config.engagement_min_cooldown_hours
        )
        if not velocity["can_reply"]:
            print(f"\n🛡 [Anti-Ghost-Ban Guardrail] {velocity['reason']}")
            return {
                "success": True,
                "skipped": True,
                "reason": velocity["reason"],
                "replies_posted": len(engagements),
                "engagements": engagements
            }

    # STAGE 2: Search & score outbound candidates
    candidates = await search_engagement_candidates(
        twikit_client,
        max_candidates=effective_count + 3,
        query_override=query_override,
        max_age_hours=effective_max_age
    )

    if not candidates:
        print("\n[Engagement Info] No suitable candidate tweets found meeting all quality and recency criteria.")
        return {
            "success": True,
            "replies_posted": len(engagements),
            "engagements": engagements,
            "message": "No eligible tweets found during search."
        }

    print(f"\n[Engagement Info] Selected {len(candidates)} scored candidates. Processing up to {effective_count}...\n")
    outbound_count = 0
    recent_replies_cache = db_manager.get_recent_replies(limit=20)

    for idx, tweet in enumerate(candidates):
        if outbound_count >= effective_count:
            break

        user = getattr(tweet, "user", None)
        screen_name = getattr(user, "screen_name", "user")
        name = getattr(user, "name", "")
        followers = getattr(user, "followers_count", 0)
        raw_fav = getattr(tweet, "favorite_count", 0)
        fav_count = int(raw_fav) if isinstance(raw_fav, (int, float)) else 0
        tweet_text = getattr(tweet, "text", "") or getattr(tweet, "full_text", "")
        tweet_id = str(getattr(tweet, "id", ""))
        cand_score = score_candidate_tweet(tweet)

        # Decide action type: 'quote' vs 'reply'
        # In 'auto' mode, if a tweet already has strong traction (fav_count >= 5) and good length,
        # we can Quote-Tweet it as a "Field Note" for main-feed reach & 0% reply-ban risk.
        use_quote_tweet = (
            clean_mode == "quote"
            or (clean_mode == "auto" and fav_count >= 5 and len(tweet_text.strip()) >= 55)
        )
        action_label = "QUOTE TWEET (Field Note)" if use_quote_tweet else "STEALTH PEER REPLY"

        print(f"--- CANDIDATE [{idx+1}] ({action_label} | Score: {cand_score}/100) ---")
        print(f"Author:    @{screen_name} ({name}) | Followers: {followers} | Likes: {fav_count}")
        print(f"Tweet ID:  {tweet_id}")
        print(f"Content:   \"{tweet_text.strip()}\"")

        # Generate contextual text via Groq
        if use_quote_tweet:
            print("\nGenerating deadpan Quote-Tweet Field Note via Groq...")
            reply_text = generate_quote_tweet_commentary(
                tweet_text,
                author_name=name or screen_name,
                recent_replies=recent_replies_cache
            )
        else:
            print("\nGenerating organic peer reply via Groq...")
            reply_text = generate_human_reply(
                tweet_text,
                author_name=name or screen_name,
                recent_replies=recent_replies_cache
            )

        if not reply_text:
            print("❌ Candidate skipped by LLM relevance/uniqueness gate. Trying next candidate...\n")
            continue

        print(f"\nProposed {action_label} ({len(reply_text)} chars):")
        print(f"💬 \"{reply_text}\"\n")

        # Append to in-memory cache so subsequent candidates in the same run cannot repeat trigrams
        recent_replies_cache.insert(0, {"reply_text": reply_text})
        target_url = f"https://x.com/{screen_name}/status/{tweet_id}"

        engagement_record = {
            "action_type": "quote_tweet" if use_quote_tweet else "reply",
            "score": cand_score,
            "target_tweet_id": tweet_id,
            "target_screen_name": screen_name,
            "original_text": tweet_text.strip(),
            "reply_text": reply_text,
            "tweet_url": target_url
        }

        if dry_run:
            print(f"[DRY RUN ACTIVE] Simulated {action_label} for @{screen_name}. No actions sent to Twitter.")
            engagement_record["reply_tweet_id"] = f"sim_{int(time.time())}_{idx}"
            engagements.append(engagement_record)
            outbound_count += 1
            print("-" * 60 + "\n")
            continue

        # Live Execution Steps
        try:
            # Step A: Simulate opening TweetDetail & reading thread (avoids raw search-to-reply anomaly)
            read_dwell = random.uniform(8.0, 16.0)
            print(f"[Twitter] Opening tweet detail & reading thread ({read_dwell:.1f}s dwell)...")
            try:
                if hasattr(twikit_client, "get_tweet_by_id"):
                    await twikit_client.get_tweet_by_id(tweet_id)
            except Exception:
                pass
            await asyncio.sleep(read_dwell)

            # Step B: Probabilistic Like (~45% chance — avoids 100% mechanical like+reply signature)
            should_like = random.random() < twitter_config.engagement_like_probability
            if should_like:
                print(f"[Twitter] Liking tweet from @{screen_name} (probabilistic human like)...")
                try:
                    if hasattr(tweet, "favorite"):
                        await tweet.favorite()
                    elif hasattr(twikit_client, "favorite_tweet"):
                        await twikit_client.favorite_tweet(tweet_id)
                    print("  ✓ Liked target tweet.")
                except Exception as e:
                    print(f"  ⚠ Could not favorite tweet (continuing anyway): {e}")
            else:
                print("[Twitter] Skipping like on this tweet to maintain natural human telemetry.")

            # Step C: Human typing delay scaled by reply length (15 to 35 seconds)
            typing_sec = len(reply_text) * random.uniform(0.12, 0.22) + random.uniform(8.0, 16.0)
            print(f"[Twitter] Human typing delay: waiting {typing_sec:.1f}s before publishing...")
            await asyncio.sleep(typing_sec)

            # Step D: Publish Quote-Tweet or Reply (Prefer Official X API v2 OAuth 1.0a)
            reply_id = ""
            used_official_api = False
            if tweepy_client is not None:
                try:
                    if use_quote_tweet:
                        print(f"[Twitter] Publishing Quote-Tweet of @{screen_name} via Official X API v2...")
                        resp = tweepy_client.create_tweet(
                            text=reply_text,
                            quote_tweet_id=tweet_id,
                            user_auth=True
                        )
                    else:
                        print(f"[Twitter] Posting reply to @{screen_name} via Official X API v2 (OAuth 1.0a)...")
                        resp = tweepy_client.create_tweet(
                            text=reply_text,
                            in_reply_to_tweet_id=tweet_id,
                            user_auth=True
                        )
                    if resp and getattr(resp, "data", None) and resp.data.get("id"):
                        reply_id = str(resp.data["id"])
                        used_official_api = True
                except Exception as api_err:
                    print(f"  ⚠ Official API v2 write failed ({api_err}); falling back to twikit...")

            if not reply_id:
                if use_quote_tweet:
                    print(f"[Twitter] Publishing Quote-Tweet of @{screen_name} via twikit...")
                    posted_reply = await twikit_client.create_tweet(text=reply_text, attachment_url=target_url)
                    reply_id = str(getattr(posted_reply, "id", ""))
                else:
                    print(f"[Twitter] Posting reply to @{screen_name} via twikit...")
                    if hasattr(tweet, "reply"):
                        posted_reply = await tweet.reply(text=reply_text)
                        reply_id = str(getattr(posted_reply, "id", ""))
                    else:
                        posted_reply = await twikit_client.create_tweet(text=reply_text, reply_to=tweet_id)
                        reply_id = str(getattr(posted_reply, "id", ""))

            engine_tag = "Official API v2" if used_official_api else "twikit"
            print(f"  🎉 {action_label} live via {engine_tag}! ID: {reply_id}")
            reply_url = f"https://x.com/{twitter_config.handle.strip('@')}/status/{reply_id}"
            print(f"  URL: {reply_url}")

            # Step E: Log to database
            db_manager.log_reply(
                target_tweet_id=tweet_id,
                target_user_id=str(getattr(user, "id", "")),
                target_screen_name=screen_name,
                original_tweet_text=tweet_text,
                reply_tweet_id=reply_id,
                reply_text=reply_text
            )

            engagement_record["reply_tweet_id"] = reply_id
            engagement_record["reply_url"] = reply_url
            engagement_record["engine"] = engine_tag
            engagements.append(engagement_record)
            outbound_count += 1

            # Step F: Cooldown pause before next candidate if processing more
            if outbound_count < effective_count:
                cooldown = random.uniform(35.0, 65.0)
                print(f"[Twitter] Cooldown delay: waiting {cooldown:.1f}s before next interaction...")
                await asyncio.sleep(cooldown)

        except Exception as e:
            print(f"❌ Error during live engagement with @{screen_name}: {e}")

        print("-" * 60 + "\n")

    return {
        "success": True,
        "replies_posted": len(engagements),
        "engagements": engagements
    }
