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
            "close the dashboard. pick one hard task for tomorrow. lock in."
        ),
        "tweet_2": (
            "over-planning is the illusion of control. "
            "the best plan is useless if you don't build the stomach for daily friction."
        ),
        "hook": "spent 4 hours designing an aesthetic notion dashboard for next week instead of doing anything today.",
        "quote": "spent 4 hours designing an aesthetic notion dashboard for next week instead of doing anything today.",
        "author": "Field Notes",
        "category": "PLANNING TRAP",
        "theme": "The Sunday Planning Delusion",
        "times_posted": 0,
        "last_posted": None
    },
    {
        "id": "sq_tutorial_1",
        "tweet_1": (
            "watched 3 hours of youtube tutorials on 'how to build an audience' before writing a single sentence.\n\n"
            "watching other people build things is not building.\n\n"
            "close youtube. write the first embarrassing post. ship it."
        ),
        "tweet_2": (
            "passive consumption feels like work, but it's just comfortable hiding. do the ugly friction."
        ),
        "hook": "watched 3 hours of youtube tutorials on 'how to build an audience' before writing a single sentence.",
        "quote": "watched 3 hours of youtube tutorials on 'how to build an audience' before writing a single sentence.",
        "author": "Field Notes",
        "category": "TUTORIAL LOOP",
        "theme": "The Infinite Tutorial Loop",
        "times_posted": 0,
        "last_posted": None
    },
    {
        "id": "sq_errand_1",
        "tweet_1": (
            "convinced myself i couldn't start my taxes until i sharpened all the pencils and watered a fake plant.\n\nthe fake plant is hydrated. the deadline did not move.\n\nsit down. open the document. knock out the first form."
        ),
        "tweet_2": (
            "urgent trivial tasks always show up when important scary tasks are due. ignore the sudden chores."
        ),
        "hook": "convinced myself i couldn't start my taxes until i sharpened all the pencils and watered a fake plant.",
        "quote": "convinced myself i couldn't start my taxes until i sharpened all the pencils and watered a fake plant.",
        "author": "Field Notes",
        "category": "FAKE CHORES",
        "theme": "The Fake Urgent Errand",
        "times_posted": 0,
        "last_posted": None
    },
    {
        "id": "sq_refactor_1",
        "tweet_1": (
            "spent 3 hours tweaking button padding and css shadows to avoid testing the payment checkout flow.\n\nthe border-radius will not charge credit cards.\n\nleave the css alone. test the scary flow. ship the mvp."
        ),
        "tweet_2": (
            "perfectionism is just cowardice with high standards. ship the broken thing and fix it live."
        ),
        "hook": "spent 3 hours tweaking button padding and css shadows to avoid testing the payment checkout flow.",
        "quote": "spent 3 hours tweaking button padding and css shadows to avoid testing the payment checkout flow.",
        "author": "Field Notes",
        "category": "PERFECTION TRAP",
        "theme": "The Fake Perfection Trap",
        "times_posted": 0,
        "last_posted": None
    },
    {
        "id": "sq_reading_1",
        "tweet_1": (
            "bought 4 productivity books on amazon to feel productive instead of reading the 6 sitting on my nightstand.\n\nbuying the book does not download the knowledge into your skull.\n\nput down the card. open chapter one. read 10 pages."
        ),
        "tweet_2": (
            "collecting solutions is not solving problems. start with the friction right in front of you."
        ),
        "hook": "bought 4 productivity books on amazon to feel productive instead of reading the 6 sitting on my nightstand.",
        "quote": "bought 4 productivity books on amazon to feel productive instead of reading the 6 sitting on my nightstand.",
        "author": "Field Notes",
        "category": "RESEARCH TRAP",
        "theme": "The Research Rabbit Hole",
        "times_posted": 0,
        "last_posted": None
    },
    {
        "id": "sq_tab_1",
        "tweet_1": (
            "currently have 47 chrome tabs open as 'research' for a project i have not touched in 3 weeks.\n\nthe tab graveyard is not a project manager.\n\nbookmark all tabs into a folder you will never open. close the browser. write 1 page."
        ),
        "tweet_2": (
            "information hoarding is anxiety in disguise. you don't need more data, you need to execute."
        ),
        "hook": "currently have 47 chrome tabs open as 'research' for a project i have not touched in 3 weeks.",
        "quote": "currently have 47 chrome tabs open as 'research' for a project i have not touched in 3 weeks.",
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
    """Ensure both tweets meet character limits AND contain the Formula 2 motivational structure."""
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

    # Check for motivational call-to-action / punchy kick in the last paragraph
    action_keywords = [
        "close", "open", "lock in", "put down", "sit down", "write", "send",
        "finish", "start", "stop", "do the", "pick one", "delete", "step away",
        "clean", "execute", "hit send", "pause", "get back", "turn off", "shut down",
        "draft", "ship", "toss", "leave", "drop", "face the"
    ]
    last_para = paras[-1].lower()
    has_action = any(kw in last_para for kw in action_keywords)
    if not has_action:
        print(f"[Validation Warning] Final paragraph lacks motivational action kick: '{paras[-1]}'")
        return False

    return True


def generate_quote_with_groq(theme_name: str, theme_desc: str, retries: int = 3) -> Optional[Dict[str, Any]]:
    """Call Groq API to generate an authentic Formula 2 tweet (relatable humor + sharp motivational turnaround)."""
    if not ai_config.groq_api_key:
        print("[AI Generator] No GROQ_API_KEY set. Falling back to local catalog.")
        return None

    headers = {
        "Authorization": f"Bearer {ai_config.groq_api_key}",
        "Content-Type": "application/json"
    }

    system_prompt = (
        "You are the voice of an elite modern writer who writes viral, hilarious, and genuinely MOTIVATING tweets calling out procrastination.\n"
        "Formula 2: 'The Absurdly Specific Side Quest' (Call out the avoidance -> reality check -> informal motivation to lock in).\n\n"
        "EVERY POST (tweet_1) MUST FOLLOW THIS EXACT 3-PARAGRAPH STRUCTURE:\n"
        "Paragraph 1 (The Absurd Setup): Call out an absurdly specific avoidance rabbit hole (cleaning baseboards, curating 3-hour playlists, Notion dashboards, mechanical keyboards, Wikipedia dives) with self-aware internet humor.\n"
        "Paragraph 2 (The Reality Check): A witty, brutal reality check showing why the side quest won't save you.\n"
        "Paragraph 3 (The Informal Motivation): A punchy, sharp, informal kick to snap out of it, stop stalling, and LOCK IN right now (e.g. 'close the tab. open the doc. lock in for 15 minutes.').\n\n"
        "TWEET 2 (Thread Reply): 1-2 punchy sentences delivering a memorable, grounded truth about doing hard things instead of hiding in fake productivity.\n\n"
        "STRICT CONSTRAINTS:\n"
        "- NO BULLET POINTS. NO NUMBERED LISTS (never use '1.', '2.', '•').\n"
        "- NO QUOTES. NO AUTHOR CITATIONS. NO QUOTATION MARKS.\n"
        "- MUST INCLUDE MOTIVATION: Do NOT just complain or ramble. Always end paragraph 3 with the kick to close tabs and do the work!\n"
        "- Relaxed, conversational casing (lowercase or relaxed phone typing).\n"
        "- Length: \"tweet_1\" MUST be strictly between 160 and 270 characters (3 short paragraphs separated by blank lines).\n"
        "- Length: \"tweet_2\" MUST be strictly between 60 and 220 characters.\n\n"
        "GOLD-STANDARD EXAMPLES:\n\n"
        "Example 1 (Spotify / Music Trap):\n"
        "{\n"
        '  "tweet_1": "spent 45 minutes curating a 3-hour synthwave playlist for a task that took 8 minutes.\\n\\nyou do not need movie soundtrack tension to update a spreadsheet.\\n\\npause the queue. open the sheet. finish it before track two.",\n'
        '  "tweet_2": "you do not need the perfect frequency to do average tasks. put the headphones on, open the tab, and do the ugly work.",\n'
        '  "category": "SPOTIFY TRAP",\n'
        '  "hook": "spent 45 minutes curating a 3-hour synthwave playlist for a task that took 8 minutes."\n'
        "}\n\n"
        "Example 2 (Cleaning / Chores Trap):\n"
        "{\n"
        '  "tweet_1": "cleaning the baseboards behind your couch with an alcohol wipe to avoid sending one email is diabolical behavior.\\n\\nthe cleaning spray will not solve the uncomfortable draft.\\n\\nput down the sponge. open the tab. hit send.",\n'
        '  "tweet_2": "cleaning your apartment will not make the scary task disappear. sit down and do 10 minutes of the friction.",\n'
        '  "category": "FAKE CHORES",\n'
        '  "hook": "cleaning the baseboards behind your couch with an alcohol wipe to avoid sending one email is diabolical behavior."\n'
        "}\n\n"
        "Example 3 (Research / Wikipedia Dive):\n"
        "{\n"
        '  "tweet_1": "my brain convinced me that before i could study for this exam, i needed to reorganize my google drive and learn the history of liechtenstein.\\n\\nwikipedia dives are just anxiety wearing an academic costume.\\n\\nclose the 14 tabs. write the first terrible paragraph.",\n'
        '  "tweet_2": "stop waiting to feel ready. you do not need inspiration, you just need 15 minutes of uninterrupted focus.",\n'
        '  "category": "RABBIT HOLE",\n'
        '  "hook": "my brain convinced me that before i could study for this exam, i needed to reorganize my google drive and learn the history of liechtenstein."\n'
        "}\n\n"
        "Example 4 (Gear & Setup Trap):\n"
        "{\n"
        '  "tweet_1": "spent two hours researching mechanical keyboard switches when i have not written a line of code in 4 days.\\n\\na $200 keyboard will not write the function for you.\\n\\nuse your ugly laptop keyboard. open the editor. lock in.",\n'
        '  "tweet_2": "tweaking your setup gives you cheap dopamine without shipping anything. make the first version look like garbage.",\n'
        '  "category": "GEAR TRAP",\n'
        '  "hook": "spent two hours researching mechanical keyboard switches when i have not written a line of code in 4 days."\n'
        "}\n\n"
        "Return a JSON object with keys: \"tweet_1\", \"tweet_2\", \"category\", \"hook\", \"quote\" (duplicate of hook), \"author\" ('Field Notes')."
    )

    user_prompt = (
        f"Write a hilarious, relatable, and MOTIVATIONAL Formula 2 Side Quest tweet pair for topic: '{theme_name}' ({theme_desc}).\n\n"
        f"STRUCTURE REQUIRED:\n"
        f"Paragraph 1: The funny, absurd avoidance side quest call-out.\n"
        f"Paragraph 2: The brutal, witty reality check.\n"
        f"Paragraph 3: The punchy, informal motivational kick to snap out of it and do the work right now (e.g. 'close the tab. open the doc. lock in.').\n\n"
        f"tweet_2: The follow-up thread reply with a memorable, dry truth about discipline and friction.\n"
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
