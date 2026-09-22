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
from bot.ai_generator import generate_human_reply
from bot.database import db_manager


NICHE_QUERIES = [
    # Burnout & Exhaustion
    '"feeling burnt out"',
    '"mentally exhausted"',
    '"drained from work"',
    '"so tired of working so hard"',
    
    # Consistency, Discipline & Habits
    '"struggling to stay consistent"',
    '"struggling with consistency"',
    '"procrastinating on my"',
    '"hard to stay focused"',
    '"need some discipline"',
    '"trying to build good habits"',
    
    # Building, Indie Work & Ambition
    '"building in public is tough"',
    '"building in public is hard"',
    '"imposter syndrome hitting"',
    '"building a startup is tough"',
    
    # Life Perspective & Overcoming Slumps
    '"feeling stuck in life"',
    '"hard lesson I learned"',
    '"overwhelmed with everything going on"'
]

BLACKLIST_TERMS = [
    # Financial/Scam/Crypto/Trading/Solicitation
    "crypto", "bitcoin", "btc", "eth", "solana", "airdrop", "nft", "token",
    "giveaway", "win $", "free cash", "presale", "whitelist", "telegram",
    "whatsapp", "dm me", "affiliate", "trading", "forex", "scalp", "scalping",
    "signals", "long signal", "short signal", "sqqq", "tqqq", "pnl",
    "send money", "amount of money", "need money", "send cash", "cash app",
    "cashapp", "venmo", "paypal", "gofundme", "donate to",
    # Commercial Ads / Product Pitches
    "meet the", "shop now", "discount", "coupon", "use code", "free shipping",
    "pre-order", "special offer", "buy now", "link in bio", "sponsored", "#ad",
    # Sports Betting / Gambling
    "bet", "bets", "betting", "parlay", "sportsbook", "gambling", "casino",
    "stake now", "on stake", "stake.com", "stake casino",
    "laliga", "premier league", "nfl pick", "nba pick",
    # Adult / Erotica / Dating / Smut
    "onlyfans", "porn", "nsfw", "sex", "sexy", "bitch", "fuck", "horny",
    "erotica", "smut", "kink", "bdsm", "fetish", "[mf]", "[ff]", "[mm]",
    "18+", "🔞", "dating", "hookup", "sugar daddy", "findom", "lewd",
    # Political / Controversy / Divisive
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
    if created_at_dt is not None:
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

    # 3. Follower bounds (avoid bot farms with <10 followers and mega-influencers/brands >40k)
    followers = getattr(user, "followers_count", 0) or 0
    if followers < 10:
        return False, f"User follower count too low ({followers}) - likely a bot or dormant"
    if followers > 40000:
        return False, f"User follower count too high ({followers}) - high risk of spam filters"

    # 4. Reply count (we want threads where our reply will actually be read, not buried in hundreds)
    reply_count = getattr(tweet, "reply_count", 0) or 0
    if reply_count > 6:
        return False, f"Too many replies ({reply_count}) - reply would get buried"

    # 5. Text length and blacklist
    text = getattr(tweet, "text", "") or getattr(tweet, "full_text", "") or ""
    text_clean = text.strip()
    if len(text_clean) < 35:
        return False, "Tweet text too short (< 35 chars)"
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
        if term in text_lower:
            return False, f"Contains blacklisted keyword: '{term}'"

    # 6. Database deduplication (have we already engaged with this user or tweet?)
    tweet_id = str(getattr(tweet, "id", ""))
    if db_manager.has_replied_to_tweet(tweet_id):
        return False, "Already replied to this tweet ID in database"

    if db_manager.has_replied_to_user(screen_name, days=30):
        return False, f"Already replied to @{screen_name} within the last 30 days"

    return True, "Eligible"


async def search_engagement_candidates(
    twikit_client,
    max_candidates: int = 5,
    query_override: Optional[str] = None,
    max_age_hours: Optional[float] = None
) -> List[Any]:
    """
    Search Twitter for organic candidate tweets matching reflective/struggle queries,
    filtering strictly for recent (under max_age_hours) high-signal authentic human posts.
    """
    effective_max_age = max_age_hours if max_age_hours is not None else twitter_config.engagement_max_age_hours
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    # Ensure Twitter search query only scans recent 24-48h window
    since_date = (now_utc - datetime.timedelta(days=1)).strftime("%Y-%m-%d")

    queries_to_try = [query_override] if query_override else random.sample(NICHE_QUERIES, min(4, len(NICHE_QUERIES)))
    candidates = []
    seen_ids = set()

    for raw_query in queries_to_try:
        if not raw_query:
            continue
        search_query = f"{raw_query} -filter:retweets lang:en since:{since_date}"
        print(f"\n[Engagement Search] Searching X with query: {search_query}...")

        try:
            results = await twikit_client.search_tweet(search_query, product="Latest", count=20)
            if not results:
                print("  -> No results returned for this query.")
                continue

            for tweet in results:
                tweet_id = str(getattr(tweet, "id", ""))
                if tweet_id in seen_ids:
                    continue
                seen_ids.add(tweet_id)

                eligible, reason = is_tweet_eligible(
                    tweet,
                    twitter_config.handle,
                    max_age_hours=effective_max_age
                )
                screen_name = getattr(getattr(tweet, "user", None), "screen_name", "unknown")
                created_dt = get_tweet_created_at(tweet)
                if created_dt:
                    age_h = max(0.0, (now_utc - created_dt).total_seconds() / 3600.0)
                    age_str = f"{age_h:.1f}h ago" if age_h >= 1.0 else f"{int(age_h * 60)}m ago"
                else:
                    age_str = "recent"

                if eligible:
                    print(f"  ✓ Candidate found: @{screen_name} ({age_str} | ID: {tweet_id})")
                    candidates.append(tweet)
                    if len(candidates) >= max_candidates * 2:
                        break
                else:
                    # Debug logging for skipped tweets
                    pass

        except Exception as e:
            print(f"[Engagement Search] Error searching query '{raw_query}': {e}")

        # If we have enough fresh candidates, we can stop querying
        if len(candidates) >= max_candidates * 2:
            break

        # Small pause between searches
        await asyncio.sleep(2)

    # Sort all discovered candidates strictly by creation time descending (newest tweets first)
    def _tweet_timestamp(t):
        dt = get_tweet_created_at(t)
        return dt.timestamp() if dt else 0.0

    candidates.sort(key=_tweet_timestamp, reverse=True)
    return candidates[:max_candidates]


async def run_engagement_cycle(
    twikit_client,
    count: int = 2,
    dry_run: bool = False,
    query_override: Optional[str] = None,
    max_age_hours: Optional[float] = None
) -> Dict[str, Any]:
    """
    Execute a stealth engagement run:
    1. Finds strictly recent candidate tweets matching human struggle/reflection queries.
    2. Generates an authentic, fruitful, human-sounding peer reply via Groq.
    3. (In live mode) Likes tweet, waits human jitter delay, posts reply, and logs to database.
    """
    effective_max_age = max_age_hours if max_age_hours is not None else twitter_config.engagement_max_age_hours
    print("=" * 60)
    mode_label = "DRY RUN (Preview Only)" if dry_run else "LIVE EXECUTION"
    print(f"      STEALTH ENGAGEMENT ENGINE — {mode_label}")
    print(f"      Target Count: {count} replies | Max Allowed Age: {effective_max_age:.1f}h")
    print("=" * 60)

    if not twikit_client and not dry_run:
        return {
            "success": False,
            "error": "Twitter client not authenticated. Run login.py first.",
            "replies_posted": 0,
            "engagements": []
        }

    # 1. Search candidates (prioritizing most recent)
    candidates = await search_engagement_candidates(
        twikit_client,
        max_candidates=count + 2,
        query_override=query_override,
        max_age_hours=effective_max_age
    )

    if not candidates:
        print("\n[Engagement Info] No suitable candidate tweets found meeting all quality and recency criteria.")
        return {
            "success": True,
            "replies_posted": 0,
            "engagements": [],
            "message": "No eligible tweets found during search."
        }

    print(f"\n[Engagement Info] Selected {len(candidates)} candidates. Processing up to {count}...\n")
    engagements = []
    replies_count = 0

    for idx, tweet in enumerate(candidates):
        if replies_count >= count:
            break

        user = getattr(tweet, "user", None)
        screen_name = getattr(user, "screen_name", "user")
        name = getattr(user, "name", "")
        followers = getattr(user, "followers_count", 0)
        tweet_text = getattr(tweet, "text", "") or getattr(tweet, "full_text", "")
        tweet_id = str(getattr(tweet, "id", ""))

        print(f"--- CANDIDATE [{idx+1}] ---")
        print(f"Author:    @{screen_name} ({name}) | Followers: {followers}")
        print(f"Tweet ID:  {tweet_id}")
        print(f"Content:   \"{tweet_text.strip()}\"")

        # Generate fruitful human reply
        print("\nGenerating organic peer reply via Groq...")
        reply_text = generate_human_reply(tweet_text, author_name=name or screen_name)

        if not reply_text:
            print("❌ Failed to generate human reply. Skipping candidate.\n")
            continue

        print(f"\nProposed Reply ({len(reply_text)} chars):")
        print(f"💬 \"{reply_text}\"\n")

        engagement_record = {
            "target_tweet_id": tweet_id,
            "target_screen_name": screen_name,
            "original_text": tweet_text.strip(),
            "reply_text": reply_text,
            "tweet_url": f"https://x.com/{screen_name}/status/{tweet_id}"
        }

        if dry_run:
            print(f"[DRY RUN ACTIVE] Simulated reply to @{screen_name}. No actions sent to Twitter.")
            engagement_record["reply_tweet_id"] = f"sim_reply_{int(time.time())}_{idx}"
            engagements.append(engagement_record)
            replies_count += 1
            print("-" * 60 + "\n")
            continue

        # Live Execution Steps
        try:
            # Step A: Like the tweet first (mimic real human reading flow)
            print(f"[Twitter] Liking tweet from @{screen_name}...")
            try:
                if hasattr(tweet, "favorite"):
                    await tweet.favorite()
                elif hasattr(twikit_client, "favorite_tweet"):
                    await twikit_client.favorite_tweet(tweet_id)
                print("  ✓ Liked target tweet.")
            except Exception as e:
                print(f"  ⚠ Could not favorite tweet (continuing anyway): {e}")

            # Step B: Human reading/typing jitter delay (20 to 45 seconds)
            jitter_sec = random.uniform(20.0, 45.0)
            print(f"[Twitter] Human jitter delay: waiting {jitter_sec:.1f}s before sending reply...")
            await asyncio.sleep(jitter_sec)

            # Step C: Send reply
            print(f"[Twitter] Posting reply to @{screen_name}...")
            if hasattr(tweet, "reply"):
                posted_reply = await tweet.reply(text=reply_text)
                reply_id = str(getattr(posted_reply, "id", ""))
            else:
                posted_reply = await twikit_client.create_tweet(text=reply_text, reply_to=tweet_id)
                reply_id = str(getattr(posted_reply, "id", ""))

            print(f"  🎉 Reply live! ID: {reply_id}")
            reply_url = f"https://x.com/{twitter_config.handle.strip('@')}/status/{reply_id}"
            print(f"  URL: {reply_url}")

            # Step D: Log to database
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
            engagements.append(engagement_record)
            replies_count += 1

            # Step E: Cooldown pause before next candidate if processing more
            if replies_count < count:
                cooldown = random.uniform(30.0, 60.0)
                print(f"[Twitter] Cooldown delay: waiting {cooldown:.1f}s before next interaction...")
                await asyncio.sleep(cooldown)

        except Exception as e:
            print(f"❌ Error during live engagement with @{screen_name}: {e}")

        print("-" * 60 + "\n")

    return {
        "success": True,
        "replies_posted": replies_count,
        "engagements": engagements
    }
