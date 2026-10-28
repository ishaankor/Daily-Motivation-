"""AI Content & Human Engagement Generator using Groq with strict Twitter 280-character validation.
Engineered for Formula 2: "The Absurdly Specific Side Quest" (Pure conversational narrative, NO bullets, NO quotes).
"""

import json
import os
import random
import time
from typing import Dict, Any, List, Optional
import requests

from bot.config import ai_config, paths

SIDE_QUEST_TOPICS = [
    "The Research Rabbit Hole (Wikipedia and obscure rabbit holes instead of starting)",
    "Aesthetic Organization (Cleaning your room, sorting files, and color-coding tabs instead of working)",
    "The Gear & Setup Trap (Researching keyboards, monitors, and productivity apps instead of writing code)",
    "The Infinite Tutorial Loop (Watching YouTube tutorials before writing a single sentence)",
    "The Fake Urgent Errand (Inventing urgent minor errands like wiping baseboards to avoid hard tasks)",
    "The Dopamine Loop (Checking notifications and doomscrolling under the guise of 'inspiration')",
    "The Planning Delusion (Spending 4 hours building a Notion dashboard instead of actually doing the work)",
    "The Spotify Playlist Trap (Spending 45 minutes curating a lo-fi playlist for a 10-minute work session)",
    "The Fake Perfection Trap (Refactoring working code instead of starting the new scary feature)"
]


FALLBACK_CATALOG = [
    {
        "id": "sq_research_1",
        "tweet_1": (
            "my brain convinced me that before i could study for this exam, "
            "i needed to reorganize my google drive and learn the history of liechtenstein.\n\n"
            "cleaning baseboards to avoid opening a pdf is diabolical behavior.\n\n"
            "stop faking productivity. write the first terrible paragraph."
        ),
        "tweet_2": (
            "the sudden urge to deep-clean your room is just anxiety wearing rubber gloves. "
            "sit down and do 10 minutes of the ugly work."
        ),
        "hook": "my brain convinced me that before i could study for this exam, i needed to reorganize my google drive and learn the history of liechtenstein.",
        "quote": "my brain convinced me that before i could study for this exam, i needed to reorganize my google drive and learn the history of liechtenstein.",
        "author": "Field Notes",
        "category": "RABBIT HOLE",
        "theme": "The Research Rabbit Hole",
        "times_posted": 0,
        "last_posted": None
    },
    {
        "id": "sq_cleaning_1",
        "tweet_1": (
            "cleaning the baseboards behind your couch with an alcohol wipe to avoid sending one email is diabolical behavior.\n\n"
            "the cleaning spray will not solve the uncomfortable draft.\n\n"
            "put down the sponge. open the tab. hit send."
        ),
        "tweet_2": (
            "cleaning your apartment won't make the scary task disappear. "
            "sit down, open the draft, and do the 5-minute task."
        ),
        "hook": "cleaning the baseboards behind your couch with an alcohol wipe to avoid sending one email is diabolical behavior.",
        "quote": "cleaning the baseboards behind your couch with an alcohol wipe to avoid sending one email is diabolical behavior.",
        "author": "Field Notes",
        "category": "FAKE CHORES",
        "theme": "Aesthetic Organization",
        "times_posted": 0,
        "last_posted": None
    },
    {
        "id": "sq_gear_1",
        "tweet_1": (
            "spent two hours researching mechanical keyboard switches when i haven't written a line of code in 4 days.\n\n"
            "my brain will do literally anything to avoid facing an empty text editor.\n\n"
            "a $200 keyboard won't write the function for you. open the editor."
        ),
        "tweet_2": (
            "tweaking your setup gives you cheap dopamine without shipping anything. "
            "ship the ugly version first, customize your desk later."
        ),
        "hook": "spent two hours researching mechanical keyboard switches when i haven't written a line of code in 4 days.",
        "quote": "spent two hours researching mechanical keyboard switches when i haven't written a line of code in 4 days.",
        "author": "Field Notes",
        "category": "GEAR TRAP",
        "theme": "The Gear & Setup Trap",
        "times_posted": 0,
        "last_posted": None
    },
    {
        "id": "sq_spotify_1",
        "tweet_1": (
            "spent 45 minutes curating the 'perfect deep work focus playlist' for a study session that lasted 11 minutes.\n\n"
            "you don't need 3 hours of lo-fi rain sounds to write a 2-page essay.\n\n"
            "close the 30 tabs. put the phone across the room. lock in."
        ),
        "tweet_2": (
            "fiddling with your aesthetic is just procrastination in a trench coat. "
            "you're not waiting for inspiration, you're avoiding friction."
        ),
        "hook": "spent 45 minutes curating the perfect deep work focus playlist for a study session that lasted 11 minutes.",
        "quote": "spent 45 minutes curating the perfect deep work focus playlist for a study session that lasted 11 minutes.",
        "author": "Field Notes",
        "category": "SPOTIFY TRAP",
        "theme": "Aesthetic Organization",
        "times_posted": 0,
        "last_posted": None
    },
    {
        "id": "sq_notion_1",
        "tweet_1": (
            "spent 4 hours designing an aesthetic notion dashboard for next week instead of doing anything today.\n\n"
            "color-coding your calendar will not execute your monday for you.\n\n"
            "close the dashboard. pick one hard task for tomorrow. go to sleep on time."
        ),
        "tweet_2": (
            "over-planning is the illusion of control. "
            "the best plan in the world is useless if you don't build the stomach for daily friction."
        ),
        "hook": "spent 4 hours designing an aesthetic notion dashboard for next week instead of doing anything today.",
        "quote": "spent 4 hours designing an aesthetic notion dashboard for next week instead of doing anything today.",
        "author": "Field Notes",
        "category": "PLANNING TRAP",
        "theme": "The Sunday Planning Delusion",
        "times_posted": 0,
        "last_posted": None
    }
]


def format_tweet_1(entry: Dict[str, Any]) -> str:
    """Format primary tweet: Formula 2 conversational narrative (NO BULLETS, NO QUOTES)."""
    t1 = entry.get("tweet_1")
    if t1:
        return t1.strip()
    return entry.get("hook", "").strip()


def format_tweet_2(entry: Dict[str, Any]) -> str:
    """Format secondary tweet: Formula 2 thread reply (NO GURU JARGON)."""
    t2 = entry.get("tweet_2")
    if t2:
        return t2.strip()
    return entry.get("backstory", "").strip()


def validate_character_limits(entry: Dict[str, Any]) -> bool:
    """Ensure both tweets strictly fit within Twitter's 280-character limit."""
    t1 = format_tweet_1(entry)
    t2 = format_tweet_2(entry)
    len_t1 = len(t1)
    len_t2 = len(t2)

    valid = (0 < len_t1 <= 280) and (0 < len_t2 <= 280)
    if not valid:
        print(f"[Validation Warning] Tweet 1: {len_t1}/280 chars, Tweet 2: {len_t2}/280 chars")
    return valid


def generate_quote_with_groq(theme_name: str, theme_desc: str, retries: int = 3) -> Optional[Dict[str, Any]]:
    """Call Groq API to generate a pure Formula 2 narrative tweet (conversational, funny, NO bullets)."""
    if not ai_config.groq_api_key:
        print("[AI Generator] No GROQ_API_KEY set. Falling back to local catalog.")
        return None

    headers = {
        "Authorization": f"Bearer {ai_config.groq_api_key}",
        "Content-Type": "application/json"
    }

    system_prompt = (
        "You write hilarious, self-aware, brutally relatable tweets about modern procrastination.\n"
        "Style: Formula 2 — 'The Absurdly Specific Side Quest'.\n\n"
        "CRITICAL RULES:\n"
        "- NO BULLET POINTS. NO NUMBERED LISTS (no '1. 2. 3.', no '•').\n"
        "- NO QUOTES. NEVER CITE AUTHORS. NO QUOTATION MARKS.\n"
        "- Pure, natural conversational flow. 2 to 3 short paragraphs separated by blank lines.\n"
        "- Relaxed human lowercase or natural casing (like someone typing on their phone at 2 PM).\n"
        "- Witty, self-deprecating, calling out absurd mental gymnastics (cleaning baseboards, Spotify playlists, mechanical keyboards).\n"
        "- Total length of \"tweet_1\" MUST BE strictly under 275 characters!\n"
        "- Total length of \"tweet_2\" MUST BE strictly under 250 characters!\n\n"
        "Return a JSON object with these EXACT keys:\n"
        "- \"tweet_1\": The main tweet text (2-3 short conversational paragraphs, max 270 chars)\n"
        "- \"tweet_2\": The punchline follow-up thread reply (1-2 sentences, max 240 chars)\n"
        "- \"category\": 2-word uppercase theme (e.g. 'SIDE QUEST', 'FAKE CHORES', 'RABBIT HOLE')\n"
        "- \"hook\": The first paragraph of tweet_1\n"
        "- \"quote\": Duplicate of hook\n"
        "- \"author\": 'Field Notes'"
    )

    user_prompt = (
        f"Generate a Formula 2 Side Quest tweet pair for topic: '{theme_name}' ({theme_desc}). "
        f"Remember: NO BULLET POINTS. NO QUOTES. Natural, funny, conversational paragraphs. "
        f"Respond ONLY in valid JSON."
    )

    primary = ai_config.groq_model
    if primary == "openai/gpt-oss-20b":
        primary = "openai/gpt-oss-120b"

    candidate_models = [primary, "openai/gpt-oss-120b", "qwen/qwen3.8-27b", "groq/compound-mini"]
    seen = set()
    models_to_try = [m for m in candidate_models if not (m in seen or seen.add(m))]

    for model in models_to_try:
        for attempt in range(retries):
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.85
            }

            try:
                response = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=15
                )

                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    parsed = json.loads(content)

                    parsed["id"] = f"sq_{int(time.time())}_{random.randint(100, 999)}"
                    parsed["theme"] = theme_name
                    parsed["author"] = "Field Notes"
                    parsed["times_posted"] = 0
                    parsed["last_posted"] = None

                    if validate_character_limits(parsed):
                        return parsed
                    else:
                        print(f"[AI Generator] Generation exceeded 280 chars on model {model}, retrying (attempt {attempt+1}/{retries})...")
                elif response.status_code == 400 and "json_validate_failed" in response.text:
                    print(f"[AI Generator] Model '{model}' failed JSON schema validation; switching models immediately.")
                    break
                else:
                    print(f"[AI Generator] API error ({response.status_code}): {response.text}")
                    time.sleep(1)

            except Exception as e:
                print(f"[AI Generator] Exception calling Groq ({model}): {e}")
                time.sleep(1)

    print("[AI Generator] Failed to generate compliant entry via Groq; using fallback.")
    return None


class QuotesCatalog:
    """Manages the local side quest catalog and persistence."""

    def __init__(self, file_path: str = paths.catalog_path):
        self.file_path = file_path
        self.catalog: List[Dict[str, Any]] = []
        self.load()

    def load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self.catalog = json.load(f)
                if not self.catalog or not self.catalog[0].get("tweet_1"):
                    self.catalog = list(FALLBACK_CATALOG)
                    self.save()
            except Exception as e:
                print(f"[Catalog] Error loading {self.file_path}: {e}")
                self.catalog = list(FALLBACK_CATALOG)
        else:
            self.catalog = list(FALLBACK_CATALOG)
            self.save()

    def save(self):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.catalog, f, indent=2, ensure_ascii=False)

    def get_entry_for_today(self, weekday_idx: Optional[int] = None) -> Dict[str, Any]:
        """Fetch or generate a fresh side quest post from the dynamic pool (no rigid day themes)."""
        topic = random.choice(SIDE_QUEST_TOPICS)

        # 1. Try to generate a fresh one via Groq
        generated = generate_quote_with_groq("Side Quest", topic)
        if generated:
            self.catalog.append(generated)
            self.save()
            return generated

        # 2. Look for an unposted entry in catalog
        unposted = [e for e in self.catalog if e.get("times_posted", 0) == 0]
        if unposted:
            choice = random.choice(unposted)
            return choice

        # 3. If all posted, pick the least recently posted
        sorted_by_recent = sorted(self.catalog, key=lambda x: (x.get("times_posted", 0), x.get("last_posted") or ""))
        return sorted_by_recent[0]

    def mark_posted(self, entry_id: str):
        for entry in self.catalog:
            if entry.get("id") == entry_id:
                entry["times_posted"] = entry.get("times_posted", 0) + 1
                entry["last_posted"] = time.strftime("%Y-%m-%d %H:%M:%S")
                break
        self.save()

    def prefill_batch(self, count: int = 5) -> int:
        """Pre-generate N original side quest posts using Groq."""
        added = 0
        for i in range(count):
            topic = SIDE_QUEST_TOPICS[i % len(SIDE_QUEST_TOPICS)]
            print(f"[Prefill] Generating side quest post {i+1}/{count} for {topic}...")
            entry = generate_quote_with_groq("Side Quest", topic)
            if entry:
                self.catalog.append(entry)
                added += 1
            time.sleep(1)
        self.save()
        print(f"[Prefill] Successfully added {added} new side quest posts to catalog!")
        return added


BANNED_REPLY_STARTERS = (
    "honestly,", "honestly ", "totally,", "totally ", "so true,", "so true ",
    "i agree,", "i completely agree,", "it sounds like", "as someone who",
    "remember,", "remember that", "take a deep breath", "as they say",
    "dear friend", "hello", "hey there"
)

BANNED_REPLY_CLICHES = [
    "future self", "listen to your body", "give yourself permission",
    "heavy mental load", "take a deep breath", "it's okay to not be okay",
    "mental static", "prescription for", "nourish the soul", "doormat",
    "crush it", "delve"
]


def generate_human_reply(tweet_text: str, author_name: str = "", retries: int = 2) -> Optional[str]:
    """
    Generate an informal, witty, relatable 'lock-in' peer reply.
    Calls out procrastination or fear with dry humor and gives a 1-sentence reality check.
    """
    if not ai_config.groq_api_key:
        print("[AI Reply] No GROQ_API_KEY set.")
        return None

    headers = {
        "Authorization": f"Bearer {ai_config.groq_api_key}",
        "Content-Type": "application/json"
    }

    system_prompt = (
        "You are an ambitious, self-aware 20-something peer on Twitter/X (a builder/student locking in).\n"
        "Your tone is INFORMAL, CASUAL, WITTY, RELATABLE, and GROUNDED. NEVER PREACHY OR CORPORATE.\n\n"
        "MISSION: Call out procrastination or self-doubt with dry humor and offer a 1-sentence reality check like a friend in the library or co-working space.\n\n"
        "CRITICAL RULES:\n"
        "- Casual, conversational lowercase or relaxed casing (no formal capitalization).\n"
        "- Natural modern phrasing used authentically: 'lock in', 'cooked', 'doomscrolling', 'side quest', 'unserious', 'rot day', 'insane work', 'we\\'re so back'.\n"
        "- NO THERAPIST TALK: Never say 'listen to your body', 'give yourself permission', 'it\\'s okay to not be okay'.\n"
        "- NO CHEESY CORPORATE HUSTLE: Don't tell people to 'rise and grind' or 'crush it'. Keep it dry, funny, and realistic.\n"
        "- 1 to 2 short sentences (strictly between 50 and 140 characters).\n"
        "- Output ONLY the reply text itself. NO quotes, NO hashtags, NO links, NO @mentions.\n\n"
        "AUTHENTIC EXAMPLES:\n"
        "- Tweet: 'procrastinating by organizing my spotify playlist instead of studying for this midterm'\n"
        "  Reply: 'organizing playlists while your midterm is tomorrow is insane work bro close the tab and review 1 chapter'\n"
        "- Tweet: 'im cooked for this presentation tomorrow'\n"
        "  Reply: 'you\\'re not cooked yet. write down 3 bullet points per slide, do 1 practice run, and get some sleep'\n"
        "- Tweet: 'spent 4 hours fighting css padding instead of launching'\n"
        "  Reply: 'fighting css padding for 4 hours is a canonical builder experience. ship the ugly version, nobody will notice the 4px difference'\n"
        "- Tweet: 'zero motivation to lock in today'\n"
        "  Reply: 'motivation isn\\'t showing up today bro. put the phone in another room, set a 15 min timer, and just start'\n"
        "- Tweet: 'doomscrolling on tiktok when i have 3 assignments due'\n"
        "  Reply: 'tiktok algorithm currently winning the battle for your gpa. toss the phone across the bed and lock in for 30 mins'"
    )

    clean_tweet = tweet_text.strip()
    user_prompt = f"Tweet from {author_name or 'someone'}:\n\"{clean_tweet}\"\n\nWrite a witty, casual, relatable peer reply:"

    candidate_models = ["qwen/qwen3.8-27b", "openai/gpt-oss-120b", "groq/compound-mini"]

    for model in candidate_models:
        for attempt in range(retries):
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.85,
                "max_tokens": 100
            }

            try:
                response = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=15
                )

                if response.status_code == 200:
                    data = response.json()
                    reply = data["choices"][0]["message"]["content"].strip()
                    if (reply.startswith('"') and reply.endswith('"')) or (reply.startswith("'") and reply.endswith("'")):
                        reply = reply[1:-1].strip()

                    reply_lower = reply.lower().strip()

                    if any(reply_lower.startswith(starter) for starter in BANNED_REPLY_STARTERS):
                        print(f"[AI Reply] Rejected banned starter in reply: '{reply}'. Retrying...")
                        continue

                    if any(cliche in reply_lower for cliche in BANNED_REPLY_CLICHES):
                        print(f"[AI Reply] Rejected cliché in reply: '{reply}'. Retrying...")
                        continue

                    if 20 <= len(reply) <= 200 and "#" not in reply and "http" not in reply:
                        return reply
                    else:
                        print(f"[AI Reply] Reply failed quality/length check ({len(reply)} chars): '{reply}'. Retrying...")
                else:
                    print(f"[AI Reply] Groq error ({response.status_code}): {response.text}")
                    time.sleep(1)

            except Exception as e:
                print(f"[AI Reply] Exception calling Groq ({model}): {e}")
                time.sleep(1)

    return None
