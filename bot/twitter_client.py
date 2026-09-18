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
    """Handles image uploads and threaded tweet creation via twikit (100% free, no API credits)."""

    def __init__(self):
        self.twikit_client: Optional[TwikitClient] = None
        self._authenticate()

    def _authenticate(self):
        """Initialize twikit client from cookies.json or environment."""
        if os.path.exists(COOKIES_FILE):
            try:
                client = TwikitClient("en-US")
                client.load_cookies(COOKIES_FILE)
                self.twikit_client = client
                print(f"[Twitter] Authenticated via {COOKIES_FILE} (twikit engine).")
                return
            except Exception as e:
                print(f"[Twitter] Error loading cookies.json: {e}")

        # Check for auth_token and ct0 directly in .env
        env_auth_token = os.getenv("TWITTER_AUTH_TOKEN")
        env_ct0 = os.getenv("TWITTER_CT0")
        if env_auth_token and env_ct0:
            try:
                client = TwikitClient("en-US")
                client.set_cookies({
                    "auth_token": env_auth_token,
                    "ct0": env_ct0
                })
                client.save_cookies(COOKIES_FILE)
                self.twikit_client = client
                print(f"[Twitter] Authenticated via .env cookies and saved {COOKIES_FILE}.")
                return
            except Exception as e:
                print(f"[Twitter] Error setting cookies from .env: {e}")

        print("[Twitter Info] No active session cookies found.")
        print("  -> Run './venv/bin/python3 login.py' once to log in and save cookies.json for free posting.")

    def verify(self) -> bool:
        """Verify that the twikit session is valid and active."""
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
        Tweet 2: Threaded reply with Historical Backstory
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

        if not self.twikit_client:
            print("\n[Twitter Error] Not logged in. Cannot post live.")
            print("Please run './venv/bin/python3 login.py' to authenticate once.")
            return None, None

        async def _execute_post():
            try:
                # 1. Upload Media Card Image
                print(f"[Twitter] Uploading card image via twikit: {image_path}...")
                media_id = await self.twikit_client.upload_media(image_path)
                print(f"[Twitter] Media uploaded successfully! ID: {media_id}")

                # 2. Post Tweet 1 (Main Post with Media)
                print("[Twitter] Posting Tweet 1 with quote card...")
                tweet_1 = await self.twikit_client.create_tweet(
                    text=t1_text,
                    media_ids=[media_id]
                )
                tweet_1_id = tweet_1.id
                print(f"[Twitter] Tweet 1 is live! ID: {tweet_1_id}")

                # 3. Wait 5 seconds before reply
                print("[Twitter] Waiting 5 seconds before posting threaded backstory...")
                await asyncio.sleep(5)

                # 4. Post Tweet 2 (Threaded Reply)
                print(f"[Twitter] Posting Tweet 2 in reply to {tweet_1_id}...")
                tweet_2 = await self.twikit_client.create_tweet(
                    text=t2_text,
                    reply_to=tweet_1_id
                )
                tweet_2_id = tweet_2.id
                print(f"[Twitter] Tweet 2 is live! ID: {tweet_2_id}")

                tweet_url = f"https://x.com/{twitter_config.handle.strip('@')}/status/{tweet_1_id}"
                print(f"\n🚀 Thread successfully published on Twitter: {tweet_url}")
                return tweet_1_id, tweet_2_id

            except Exception as e:
                print(f"\n[Twitter Error] Failed posting thread via twikit: {e}")
                return None, None

        return asyncio.run(_execute_post())


twitter_client = TwitterClient()
