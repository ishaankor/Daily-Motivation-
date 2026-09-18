#!/usr/bin/env python3
"""
Simple Browser Cookie Importer for Twitter Bot (twikit engine).
Twitter blocks automated password logins, so importing your browser session cookies
is the 100% reliable, official way to authenticate for free posting.
"""

import asyncio
import json
import os
import sys

from twikit import Client

COOKIES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cookies.json")


def main():
    print("=" * 65)
    print("      AUTHENTICATE TWITTER BOT (One-Time Cookie Setup)")
    print("=" * 65)
    print("Twitter/X requires session cookies to authenticate without API fees.\n")
    print("Follow these 3 quick steps in your browser (Chrome/Safari/Brave):")
    print("1. Open https://x.com and make sure you are logged in as @MotivationFTD.")
    print("   (If already logged in, REFRESH the page once to get fresh cookies).")
    print("2. Open Developer Tools (Press F12, or Cmd + Option + I on Mac).")
    print("3. Click 'Application' (or 'Storage') -> 'Cookies' -> 'https://x.com':")
    print("   - Find 'auth_token' and copy its value (approx 40 characters)")
    print("   - Find 'ct0' and copy its value (approx 160 characters)\n")

    auth_token = input("Paste 'auth_token': ").strip()
    ct0 = input("Paste 'ct0': ").strip()

    if not auth_token or not ct0:
        print("\n❌ Error: Both auth_token and ct0 are required.")
        sys.exit(1)

    cookies = {
        "auth_token": auth_token,
        "ct0": ct0
    }

    with open(COOKIES_PATH, "w", encoding="utf-8") as f:
        json.dump(cookies, f, indent=2)

    print(f"\nSaved session to: {COOKIES_PATH}")
    print("Verifying session with Twitter...")

    async def verify():
        client = Client("en-US")
        client.set_cookies(cookies)

        try:
            user = await client.user()
            print("\n" + "=" * 65)
            print(f"🎉 AUTHENTICATION SUCCESSFUL!")
            print(f"Logged in as: @{user.screen_name} ({user.name})")
            print("=" * 65)
            print("\nThe bot is now fully authorized to post for free.")
            print("Run './venv/bin/python3 main.py --post-today' to post your first tweet!")
        except Exception as e:
            print(f"\n❌ Verification failed: {e}")
            print("\nPlease make sure you refreshed https://x.com right before copying the cookies.")

    asyncio.run(verify())


if __name__ == "__main__":
    main()
