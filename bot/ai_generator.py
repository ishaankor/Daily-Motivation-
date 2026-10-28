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
        "id": "sq_cleaning_1",
        "tweet_1": (
            "Just spent 25 minutes scrubbing the baseboards behind my couch to avoid sending one proposal.\n\n"
            "The baseboards are spotless. The client is still waiting.\n\n"
            "Put down the sponge. Open the document. Finish the draft."
        ),
        "tweet_2": (
            "The sudden urge to clean your entire apartment is just anxiety wearing rubber gloves. "
            "Do the scary 5-minute task first."
        ),
        "hook": "Just spent 25 minutes scrubbing the baseboards behind my couch to avoid sending one proposal.",
        "quote": "Just spent 25 minutes scrubbing the baseboards behind my couch to avoid sending one proposal.",
        "author": "Field Notes",
        "category": "FAKE CHORES",
        "theme": "Aesthetic Organization",
        "times_posted": 0,
        "last_posted": None
    },
    {
        "id": "sq_spotify_1",
        "tweet_1": (
            "Spent 40 minutes building the \"ultimate focus playlist\" on Spotify for a task that took 8 minutes.\n\n"
            "You do not need a movie soundtrack to reply to three emails.\n\n"
            "Pause the playlist. Open your inbox. Get it done."
        ),
        "tweet_2": (
            "Waiting for the perfect mood or environment is the easiest way to lose an entire afternoon. Just start ugly."
        ),
        "hook": "Spent 40 minutes building the ultimate focus playlist on Spotify for a task that took 8 minutes.",
        "quote": "Spent 40 minutes building the ultimate focus playlist on Spotify for a task that took 8 minutes.",
        "author": "Field Notes",
        "category": "SPOTIFY TRAP",
        "theme": "Aesthetic Organization",
        "times_posted": 0,
        "last_posted": None
    },
    {
        "id": "sq_gear_1",
        "tweet_1": (
            "Spent an hour reading reviews on mechanical keyboard switches instead of working on the report due tomorrow.\n\n"
            "A quieter spacebar will not write your financial summary.\n\n"
            "Use the laptop keyboard you already have. Open the file. Get the first draft done."
        ),
        "tweet_2": (
            "Researching gear gives you the feeling of progress without any of the work. Build with what you have."
        ),
        "hook": "Spent an hour reading reviews on mechanical keyboard switches instead of working on the report due tomorrow.",
        "quote": "Spent an hour reading reviews on mechanical keyboard switches instead of working on the report due tomorrow.",
        "author": "Field Notes",
        "category": "GEAR TRAP",
        "theme": "The Gear & Setup Trap",
        "times_posted": 0,
        "last_posted": None
    },
    {
        "id": "sq_notion_1",
        "tweet_1": (
            "Spent 3 hours color-coding a Notion dashboard for next week to avoid doing anything today.\n\n"
            "An aesthetic calendar does not do the work for you.\n\n"
            "Close the planner. Pick the single hardest task on your list. Start it now."
        ),
        "tweet_2": (
            "Over-planning is just comfortable hiding. The only plan that matters is what you execute in the next 30 minutes."
        ),
        "hook": "Spent 3 hours color-coding a Notion dashboard for next week to avoid doing anything today.",
        "quote": "Spent 3 hours color-coding a Notion dashboard for next week to avoid doing anything today.",
        "author": "Field Notes",
        "category": "PLANNING TRAP",
        "theme": "The Sunday Planning Delusion",
        "times_posted": 0,
        "last_posted": None
    },
    {
        "id": "sq_research_1",
        "tweet_1": (
            "Went to Google to look up one statistic, and somehow ended up reading the entire Wikipedia page on medieval siege weapons.\n\n"
            "The trebuchet is fascinating. Your deadline is in two hours.\n\n"
            "Close the 12 tabs. Open the document. Write the first paragraph."
        ),
        "tweet_2": (
            "Curiosity rabbit holes are just anxiety in an academic costume. Close the browser and do the real work."
        ),
        "hook": "Went to Google to look up one statistic, and somehow ended up reading the entire Wikipedia page on medieval siege weapons.",
        "quote": "Went to Google to look up one statistic, and somehow ended up reading the entire Wikipedia page on medieval siege weapons.",
        "author": "Field Notes",
        "category": "RABBIT HOLE",
        "theme": "The Research Rabbit Hole",
        "times_posted": 0,
        "last_posted": None
    },
    {
        "id": "sq_errand_1",
        "tweet_1": (
            "Convinced myself I couldn't start my taxes until I sharpened every pencil in the house and organized my sock drawer.\n\n"
            "The sock drawer is beautiful. The deadline didn't move.\n\n"
            "Sit down. Open the form. Finish page one."
        ),
        "tweet_2": (
            "Urgent trivial errands always show up when important work is on the line. Ignore the sudden urge to clean."
        ),
        "hook": "Convinced myself I couldn't start my taxes until I sharpened every pencil in the house and organized my sock drawer.",
        "quote": "Convinced myself I couldn't start my taxes until I sharpened every pencil in the house and organized my sock drawer.",
        "author": "Field Notes",
        "category": "FAKE CHORES",
        "theme": "The Fake Urgent Errand",
        "times_posted": 0,
        "last_posted": None
    },
    {
        "id": "sq_tutorial_1",
        "tweet_1": (
            "Watched two hours of YouTube tutorials on 'how to write clearly' before writing a single sentence.\n\n"
            "Watching other people work does not produce your work.\n\n"
            "Close YouTube. Write the first messy paragraph. You can edit it later."
        ),
        "tweet_2": (
            "Passive consumption feels like productivity, but it's just comfortable procrastination. Jump into the friction."
        ),
        "hook": "Watched two hours of YouTube tutorials on 'how to write clearly' before writing a single sentence.",
        "quote": "Watched two hours of YouTube tutorials on 'how to write clearly' before writing a single sentence.",
        "author": "Field Notes",
        "category": "TUTORIAL LOOP",
        "theme": "The Infinite Tutorial Loop",
        "times_posted": 0,
        "last_posted": None
    },
    {
        "id": "sq_refactor_1",
        "tweet_1": (
            "Spent 2 hours tweaking the button shadows on my app's landing page instead of testing the checkout flow.\n\n"
            "Subtle drop-shadows will not process payments.\n\n"
            "Leave the CSS alone. Test the checkout. Ship the product."
        ),
        "tweet_2": (
            "Perfectionism is usually just fear of putting your work out there. Ship the imperfect version first."
        ),
        "hook": "Spent 2 hours tweaking the button shadows on my app's landing page instead of testing the checkout flow.",
        "quote": "Spent 2 hours tweaking the button shadows on my app's landing page instead of testing the checkout flow.",
        "author": "Field Notes",
        "category": "PERFECTION TRAP",
        "theme": "The Fake Perfection Trap",
        "times_posted": 0,
        "last_posted": None
    },
    {
        "id": "sq_reading_1",
        "tweet_1": (
            "Bought 3 new books on focus and discipline while 5 unread books are already sitting on my desk.\n\n"
            "Buying the book does not download the discipline into your brain.\n\n"
            "Close Amazon. Pick up the book on your desk. Read 10 pages right now."
        ),
        "tweet_2": (
            "Buying tools gives you a cheap hit of progress without any effort. Use what you already own."
        ),
        "hook": "Bought 3 new books on focus and discipline while 5 unread books are already sitting on my desk.",
        "quote": "Bought 3 new books on focus and discipline while 5 unread books are already sitting on my desk.",
        "author": "Field Notes",
        "category": "RESEARCH TRAP",
        "theme": "The Research Rabbit Hole",
        "times_posted": 0,
        "last_posted": None
    },
    {
        "id": "sq_tab_1",
        "tweet_1": (
            "Currently have 38 Chrome tabs open as 'reading material' for a project I haven't touched in a week.\n\n"
            "A crowded tab bar is not a project management system.\n\n"
            "Bookmark the tabs. Close the browser. Write one page in peace."
        ),
        "tweet_2": (
            "Information overload is often just avoidance in disguise. You don't need more tabs; you need 15 minutes of uninterrupted focus."
        ),
        "hook": "Currently have 38 Chrome tabs open as 'reading material' for a project I haven't touched in a week.",
        "quote": "Currently have 38 Chrome tabs open as 'reading material' for a project I haven't touched in a week.",
        "author": "Field Notes",
        "category": "DOPAMINE LOOP",
        "theme": "The Dopamine Loop",
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
    """Ensure both tweets meet character limits, have proper punctuation, and sound like real human speech."""
    t1 = format_tweet_1(entry)
    t2 = format_tweet_2(entry)
    len_t1 = len(t1)
    len_t2 = len(t2)

    if not (0 < len_t1 <= 275 and 0 < len_t2 <= 250):
        print(f"[Validation Warning] Length invalid: Tweet 1 ({len_t1}/275), Tweet 2 ({len_t2}/250)")
        return False

    # Check for paragraph structure (must have blank lines separating setup, reality check, and motivation)
    paras = [p.strip() for p in t1.split("\n\n") if p.strip()]
    if len(paras) < 2:
        print("[Validation Warning] Tweet 1 missing multi-paragraph structure (need setup + reality check + motivation).")
        return False

    # Enforce punctuation: human writing uses periods or question marks, not unpunctuated run-on strings
    if "." not in t1 and "?" not in t1 and "!" not in t1:
        print("[Validation Warning] Tweet 1 missing standard punctuation. Rejecting unpunctuated AI run-on.")
        return False

    # Ban forced slang / AI glitches
    banned_phrases = ["close the mop", "stop the shine", "wait for your sparkle", "shine on", "lock in for your"]
    t1_lower = t1.lower()
    for bp in banned_phrases:
        if bp in t1_lower:
            print(f"[Validation Warning] Tweet 1 contains cringe forced slang: '{bp}'. Rejecting.")
            return False

    # Check for motivational call-to-action / punchy kick in the last paragraph
    action_keywords = [
        "close", "open", "put down", "sit down", "write", "send",
        "finish", "start", "stop", "do the", "pick", "delete", "step away",
        "clean", "execute", "hit send", "pause", "get back", "turn off", "shut down",
        "draft", "ship", "toss", "leave", "drop", "face the", "get it done", "knock out"
    ]
    last_para = paras[-1].lower()
    has_action = any(kw in last_para for kw in action_keywords)
    if not has_action:
        print(f"[Validation Warning] Final paragraph lacks motivational action kick: '{paras[-1]}'")
        return False

    return True


def generate_quote_with_groq(theme_name: str, theme_desc: str, retries: int = 3) -> Optional[Dict[str, Any]]:
    """Call Groq API to generate a natural, witty, deadpan human tweet (relatable observation + grounded motivation)."""
    if not ai_config.groq_api_key:
        print("[AI Generator] No GROQ_API_KEY set. Falling back to local catalog.")
        return None

    headers = {
        "Authorization": f"Bearer {ai_config.groq_api_key}",
        "Content-Type": "application/json"
    }

    system_prompt = (
        "You are a witty, observational writer (think Jerry Seinfeld, Tim Urban, or David Sedaris) writing relatable, honest tweets about modern procrastination.\n\n"
        "CORE VOICE RULES — WRITE LIKE A REAL HUMAN:\n"
        "- Write naturally in clean, standard English. Use normal sentence structure, capitalization, and punctuation (periods, commas).\n"
        "- NO FORCED SLANG: Never use cringe internet buzzwords ('sparkle', 'close the mop', 'stop the shine', 'diabolical', 'cooked', 'slay').\n"
        "- NO RHYMING OR SLAM POETRY: Do NOT string together rhyming lists of commands. Talk like a normal person making a dry, deadpan observation.\n"
        "- NO NUMBERED LISTS, BULLET POINTS, OR QUOTATION MARKS.\n\n"
        "STRUCTURE OF TWEET 1 (Must be 3 short, distinct paragraphs):\n"
        "Paragraph 1 (The Setup): A specific, funny, deadpan description of an avoidance behavior you caught yourself doing (e.g. cleaning, researching gear, tweaking playlists, organizing Notion).\n"
        "Paragraph 2 (The Reality Check): A short, dry 1-sentence truth showing why it didn't solve anything (e.g. 'The baseboards are clean. The client is still waiting.').\n"
        "Paragraph 3 (The Motivation): A grounded, practical call to action (e.g. 'Put down the sponge. Open the document. Finish the draft.').\n\n"
        "TWEET 2 (Thread Reply): 1-2 calm, natural sentences delivering a thoughtful insight on why we avoid uncomfortable work.\n\n"
        "GOLD-STANDARD HUMAN EXAMPLES:\n\n"
        "Example 1:\n"
        "{\n"
        '  "tweet_1": "Just spent 25 minutes scrubbing the baseboards behind my couch to avoid sending one proposal.\\n\\nThe baseboards are spotless. The client is still waiting.\\n\\nPut down the sponge. Open the document. Finish the draft.",\n'
        '  "tweet_2": "The sudden urge to clean your entire apartment is just anxiety wearing rubber gloves. Do the scary 5-minute task first.",\n'
        '  "category": "FAKE CHORES",\n'
        '  "hook": "Just spent 25 minutes scrubbing the baseboards behind my couch to avoid sending one proposal."\n'
        "}\n\n"
        "Example 2:\n"
        "{\n"
        '  "tweet_1": "Spent 40 minutes building the \\"ultimate focus playlist\\" on Spotify for a task that took 8 minutes.\\n\\nYou do not need a movie soundtrack to reply to three emails.\\n\\nPause the playlist. Open your inbox. Get it done.",\n'
        '  "tweet_2": "Waiting for the perfect mood or environment is the easiest way to lose an entire afternoon. Just start ugly.",\n'
        '  "category": "SPOTIFY TRAP",\n'
        '  "hook": "Spent 40 minutes building the ultimate focus playlist on Spotify for a task that took 8 minutes."\n'
        "}\n\n"
        "Example 3:\n"
        "{\n"
        '  "tweet_1": "Spent an hour reading reviews on mechanical keyboard switches instead of working on the report due tomorrow.\\n\\nA quieter spacebar will not write your financial summary.\\n\\nUse the laptop keyboard you already have. Open the file. Get the first draft done.",\n'
        '  "tweet_2": "Researching gear gives you the feeling of progress without any of the work. Build with what you have.",\n'
        '  "category": "GEAR TRAP",\n'
        '  "hook": "Spent an hour reading reviews on mechanical keyboard switches instead of working on the report due tomorrow."\n'
        "}\n\n"
        "Example 4:\n"
        "{\n"
        '  "tweet_1": "Spent 3 hours color-coding a Notion dashboard for next week to avoid doing anything today.\\n\\nAn aesthetic calendar does not do the work for you.\\n\\nClose the planner. Pick the single hardest task on your list. Start it now.",\n'
        '  "tweet_2": "Over-planning is just comfortable hiding. The only plan that matters is what you execute in the next 30 minutes.",\n'
        '  "category": "PLANNING TRAP",\n'
        '  "hook": "Spent 3 hours color-coding a Notion dashboard for next week to avoid doing anything today."\n'
        "}\n\n"
        "Length limits: \"tweet_1\" strictly under 270 chars (3 paragraphs). \"tweet_2\" strictly under 240 chars.\n"
        "Return a JSON object with keys: \"tweet_1\", \"tweet_2\", \"category\", \"hook\", \"quote\" (duplicate of hook), \"author\" ('Field Notes')."
    )

    user_prompt = (
        f"Write an authentic, deadpan, and naturally MOTIVATING tweet pair about: '{theme_name}' ({theme_desc}).\n\n"
        f"Remember: Write like a real person, NOT an AI trying to sound cool. Use proper punctuation (periods and commas).\n"
        f"Paragraph 1: The absurd avoidance behavior.\n"
        f"Paragraph 2: The deadpan reality check.\n"
        f"Paragraph 3: The grounded call to action (e.g. 'Put down the sponge. Open the document. Finish the draft.').\n\n"
        f"tweet_2: A thoughtful, conversational observation with normal punctuation.\n"
        f"Strictly under 270 chars for tweet_1 and under 240 chars for tweet_2. Respond ONLY in valid JSON."
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
                        print(f"[AI Generator] Generation failed validation on model {model}, retrying (attempt {attempt+1}/{retries})...")
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
