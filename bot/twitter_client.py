"""Twitter client using twikit for 100% free posting via internal web API."""

import asyncio
import json
import os
import time
from typing import Dict, Any, Tuple, Optional
from twikit import Client as TwikitClient

from bot.config import paths, twitter_config
from bot.ai_generator import format_tweet_1, format_tweet_2

COOKIES_FILE = os.path.join(paths.base_dir, "cookies.json")


def _apply_twikit_runtime_patch():
    """Ensure handle_x_migration routes to https://x.com/home where Twitter serves ondemand.s."""
    try:
        import twikit.x_client_transaction.utils as tu
        import bs4
        import re

        orig_handler = tu.handle_x_migration

        async def patched_handle_x_migration(session, headers):
            migration_redirection_regex = re.compile(
                r"""(http(?:s)?://(?:www\.)?(twitter|x){1}\.com(/x)?/migrate([/?])?tok=[a-zA-Z0-9%\-_]+)+""", re.VERBOSE)
            response = await session.request(method="GET", url="https://x.com/home", headers=headers)
            if "ondemand.s" not in response.text:
                response = await session.request(method="GET", url="https://x.com", headers=headers)
            home_page = bs4.BeautifulSoup(response.content, "lxml")
            migration_url = home_page.select_one("meta[http-equiv=\"refresh\"]")
            migration_redirection_url = re.search(migration_redirection_regex, str(migration_url)) or re.search(migration_redirection_regex, str(response.content))
            if migration_redirection_url:
                response = await session.request(method="GET", url=migration_redirection_url.group(0), headers=headers)
                home_page = bs4.BeautifulSoup(response.content, "lxml")
            migration_form = home_page.select_one("form[name=\"f\"]") or home_page.select_one("form[action=\"https://x.com/x/migrate\"]")
            if migration_form:
                url = migration_form.attrs.get("action", "https://x.com/x/migrate") + "/?mx=2"
                method = migration_form.attrs.get("method", "POST")
                request_payload = {input_field.get("name"): input_field.get("value") for input_field in migration_form.select("input")}
                response = await session.request(method=method, url=url, data=request_payload, headers=headers)
                home_page = bs4.BeautifulSoup(response.content, "lxml")
            return home_page

        tu.handle_x_migration = patched_handle_x_migration
    except Exception as e:
        print(f"[Twitter Warning] Could not apply twikit runtime patch: {e}")


# Apply patch immediately on import
_apply_twikit_runtime_patch()


class TwitterClient:
    """
    Handles image uploads, threaded tweet creation, and hybrid anti-ghost-ban outreach replies.
    Uses twikit for 100% free read/search/media, and supports Official X API v2 (OAuth 1.0a)
    for write replies to avoid datacenter web-cookie deboosting.
    """

    def __init__(self):
        self.twikit_client: Optional[TwikitClient] = None
        self.tweepy_client: Optional[Any] = None
        self.tweepy_api: Optional[Any] = None
        self._authenticate()
        self._init_official_api()

    def _create_twikit_instance(self) -> TwikitClient:
        """Create TwikitClient with optional residential proxy to protect IP reputation."""
        proxy = twitter_config.proxy_url.strip() if twitter_config.proxy_url else None
        if proxy:
            try:
                return TwikitClient("en-US", proxy=proxy)
            except TypeError:
                client = TwikitClient("en-US")
                if hasattr(client, "proxy"):
                    client.proxy = proxy
                return client
        return TwikitClient("en-US")

    def _init_official_api(self):
        """
        Initialize Official X API v2 client (OAuth 1.0a User Context) and v1.1 media API
        if keys are configured. Official API v2 write calls (Free tier allows 1,500 tweets/month)
        are exempt from datacenter web-cookie fingerprint penalties.
        """
        if all([
            twitter_config.api_key,
            twitter_config.api_secret_key,
            twitter_config.access_token,
            twitter_config.access_token_secret
        ]):
            try:
                import tweepy
                self.tweepy_client = tweepy.Client(
                    consumer_key=twitter_config.api_key,
                    consumer_secret=twitter_config.api_secret_key,
                    access_token=twitter_config.access_token,
                    access_token_secret=twitter_config.access_token_secret,
                    wait_on_rate_limit=False
                )
                auth = tweepy.OAuth1UserHandler(
                    twitter_config.api_key,
                    twitter_config.api_secret_key,
                    twitter_config.access_token,
                    twitter_config.access_token_secret
                )
                self.tweepy_api = tweepy.API(auth)
                print("[Twitter] Official X API v2 OAuth 1.0a client initialized (hybrid write protection active).")
            except Exception as e:
                print(f"[Twitter] Could not initialize Official X API v2 client: {e}")

    def _authenticate(self, quiet: bool = False):
        """
        Initialize a fresh twikit client from cookies.json or environment.
        Called before each asyncio.run() invocation so httpx.AsyncClient is always
        bound to the current active event loop (prevents 'Event loop is closed' on Render).
        """
        if os.path.exists(COOKIES_FILE):
            try:
                client = self._create_twikit_instance()
                client.load_cookies(COOKIES_FILE)
                self.twikit_client = client
                if not quiet:
                    print(f"[Twitter] Authenticated via {COOKIES_FILE} (twikit engine).")
                return
            except Exception as e:
                if not quiet:
                    print(f"[Twitter] Error loading cookies.json: {e}")

        # Check for auth_token and ct0 directly in .env
        env_auth_token = os.getenv("TWITTER_AUTH_TOKEN")
        env_ct0 = os.getenv("TWITTER_CT0")
        if env_auth_token and env_ct0:
            try:
                client = self._create_twikit_instance()
                client.set_cookies({
                    "auth_token": env_auth_token,
                    "ct0": env_ct0
                })
                client.save_cookies(COOKIES_FILE)
                self.twikit_client = client
                if not quiet:
                    print(f"[Twitter] Authenticated via .env cookies and saved {COOKIES_FILE}.")
                return
            except Exception as e:
                if not quiet:
                    print(f"[Twitter] Error setting cookies from .env: {e}")

        if not quiet:
            print("[Twitter Info] No active session cookies found.")
            print("  -> Run './venv/bin/python3 login.py' once to log in and save cookies.json for free posting.")

    async def _close_twikit_http(self):
        """Persist updated session cookies and cleanly close httpx.AsyncClient before event loop exits."""
        if not self.twikit_client:
            return
        try:
            self.twikit_client.save_cookies(COOKIES_FILE)
        except Exception:
            pass
        try:
            http_client = getattr(self.twikit_client, "http", None)
            if http_client and hasattr(http_client, "aclose"):
                await http_client.aclose()
        except Exception:
            pass

    def verify(self) -> bool:
        """Verify that the twikit session is valid and active."""
        self._authenticate(quiet=True)
        if not self.twikit_client:
            print("[Twitter] Session not authenticated. Run 'python login.py' first.")
            return False

        async def _verify():
            try:
                user = await self.twikit_client.user()
                print(f"[Twitter] Verified session for @{user.screen_name} ({user.name}) | Followers: {user.followers_count}")
                return True
            except Exception as e:
                print(f"[Twitter] Session verification failed: {e}")
                return False
            finally:
                await self._close_twikit_http()

        return asyncio.run(_verify())

    def post_quote_thread(
        self,
        entry: Dict[str, Any],
        image_path: str,
        dry_run: bool = False
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Post the 2-tweet thread:
        Tweet 1: Quote + 3 Takeaways + Hook + Attached Image Card
        Tweet 2: Threaded reply with Historical Backstory + Reply-Magnet Question
        """
        t1_text = format_tweet_1(entry)
        t2_text = format_tweet_2(entry)

        print("\n" + "=" * 50)
        print("          PREPARING TWEET THREAD")
        print("=" * 50)
        print(f"Attached Card Image: {image_path}")
        print(f"\n--- TWEET 1 ({len(t1_text)}/280 chars) ---")
        print(t1_text)
        print(f"\n--- TWEET 2 (REPLY) ({len(t2_text)}/280 chars) ---")
        print(t2_text)
        print("=" * 50)

        if dry_run:
            print("\n[DRY RUN ACTIVE] No tweets were posted to Twitter.")
            simulated_id_1 = f"sim_tweet_{int(time.time())}"
            simulated_id_2 = f"sim_reply_{int(time.time())}"
            return simulated_id_1, simulated_id_2

        # Re-bind twikit httpx.AsyncClient to a fresh instance for this event loop
        self._authenticate(quiet=True)

        if not self.twikit_client and not self.tweepy_client:
            print("\n[Twitter Error] Not logged in. Cannot post live.")
            print("Please run './venv/bin/python3 login.py' to authenticate once.")
            return None, None

        async def _execute_post():
            try:
                media_id = None

                # 1. Upload Media Card Image (Try twikit first, fallback to Official X API v1.1 media_upload)
                if self.twikit_client:
                    try:
                        print(f"[Twitter] Uploading card image via twikit: {image_path}...")
                        media_id = await self.twikit_client.upload_media(image_path)
                        print(f"[Twitter] Media uploaded via twikit! ID: {media_id}")
                    except Exception as tw_media_err:
                        print(f"[Twitter Warning] twikit media upload failed ({tw_media_err}); trying Official X API...")

                if not media_id and self.tweepy_api:
                    try:
                        print(f"[Twitter] Uploading card image via Official X API v1.1: {image_path}...")
                        media_obj = self.tweepy_api.media_upload(filename=image_path)
                        media_id = str(media_obj.media_id_string)
                        print(f"[Twitter] Media uploaded via Official X API! ID: {media_id}")
                    except Exception as api_media_err:
                        print(f"[Twitter Error] Official X API media upload failed: {api_media_err}")

                if not media_id:
                    print("[Twitter Error] Could not upload card image via any engine.")
                    return None, None

                # 2. Post Tweet 1 (Main Post with Media — try Official X API v2 first, fallback to twikit)
                tweet_1_id = None
                if self.tweepy_client:
                    try:
                        print("[Twitter] Posting Tweet 1 with quote card via Official X API v2...")
                        resp_1 = self.tweepy_client.create_tweet(
                            text=t1_text,
                            media_ids=[media_id],
                            user_auth=True
                        )
                        if resp_1 and getattr(resp_1, "data", None) and resp_1.data.get("id"):
                            tweet_1_id = str(resp_1.data["id"])
                            print(f"[Twitter] Tweet 1 is live via Official X API v2! ID: {tweet_1_id}")
                    except Exception as api_t1_err:
                        print(f"[Twitter Warning] Official X API v2 Tweet 1 failed ({api_t1_err}); falling back to twikit...")

                if not tweet_1_id and self.twikit_client:
                    print("[Twitter] Posting Tweet 1 with quote card via twikit...")
                    tweet_1 = await self.twikit_client.create_tweet(
                        text=t1_text,
                        media_ids=[media_id]
                    )
                    tweet_1_id = str(tweet_1.id)
                    print(f"[Twitter] Tweet 1 is live via twikit! ID: {tweet_1_id}")

                if not tweet_1_id:
                    return None, None

                # 3. Wait 5 seconds before reply
                print("[Twitter] Waiting 5 seconds before posting threaded backstory...")
                await asyncio.sleep(5)

                # 4. Post Tweet 2 (Threaded Reply — try Official X API v2 first, fallback to twikit)
                tweet_2_id = None
                if self.tweepy_client:
                    try:
                        print(f"[Twitter] Posting Tweet 2 in reply to {tweet_1_id} via Official X API v2...")
                        resp_2 = self.tweepy_client.create_tweet(
                            text=t2_text,
                            in_reply_to_tweet_id=tweet_1_id,
                            user_auth=True
                        )
                        if resp_2 and getattr(resp_2, "data", None) and resp_2.data.get("id"):
                            tweet_2_id = str(resp_2.data["id"])
                            print(f"[Twitter] Tweet 2 is live via Official X API v2! ID: {tweet_2_id}")
                    except Exception as api_t2_err:
                        print(f"[Twitter Warning] Official X API v2 Tweet 2 failed ({api_t2_err}); falling back to twikit...")

                if not tweet_2_id and self.twikit_client:
                    print(f"[Twitter] Posting Tweet 2 in reply to {tweet_1_id} via twikit...")
                    tweet_2 = await self.twikit_client.create_tweet(
                        text=t2_text,
                        reply_to=tweet_1_id
                    )
                    tweet_2_id = str(tweet_2.id)
                    print(f"[Twitter] Tweet 2 is live via twikit! ID: {tweet_2_id}")

                tweet_url = f"https://x.com/{twitter_config.handle.strip('@')}/status/{tweet_1_id}"
                print(f"\n🚀 Thread successfully published on Twitter: {tweet_url}")
                return tweet_1_id, tweet_2_id

            except Exception as e:
                print(f"\n[Twitter Error] Failed posting thread: {e}")
                return None, None
            finally:
                await self._close_twikit_http()

        return asyncio.run(_execute_post())

    def run_engagement(
        self,
        count: int = 1,
        dry_run: bool = False,
        query_override: Optional[str] = None,
        max_age_hours: Optional[float] = None,
        mode: str = "auto"
    ) -> Dict[str, Any]:
        """
        Execute cohesive growth loop:
        Inbound thread comment replies + Scored discovery + Quote-Tweet/Reply outreach.
        """
        from bot.reply_engine import run_engagement_cycle
        # Re-bind twikit httpx.AsyncClient to a fresh instance for this event loop
        self._authenticate(quiet=True)

        async def _execute_engagement():
            try:
                return await run_engagement_cycle(
                    twikit_client=self.twikit_client,
                    tweepy_client=self.tweepy_client,
                    count=count,
                    dry_run=dry_run,
                    query_override=query_override,
                    max_age_hours=max_age_hours,
                    mode=mode
                )
            finally:
                await self._close_twikit_http()

        return asyncio.run(_execute_engagement())


twitter_client = TwitterClient()
