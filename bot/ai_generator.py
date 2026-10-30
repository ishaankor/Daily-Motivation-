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
    "The Research Rabbit Hole (Wikipedia articles on obscure logistics or history instead of starting)",
    "Aesthetic Organization (Sorting desktop files, download folders, and color-coding tabs instead of working)",
    "The Gear & Setup Trap (Researching mechanical keyboards, ultra-wide monitors, and mouse DPI settings instead of coding)",
    "The Infinite Tutorial Loop (Watching 2 hours of YouTube tutorials on 'how to write' before typing a single sentence)",
    "The Fake Urgent Errand (Inventing urgent domestic chores like deep-cleaning the air fryer or sorting spices)",
    "The Dopamine Loop (Checking notifications, Twitter feeds, and bookmark managers under the guise of 'inspiration')",
    "The Planning Delusion (Spending 4 hours building a color-coded Notion dashboard instead of actually doing the work)",
    "The Spotify Playlist Trap (Spending 45 minutes curating a lo-fi focus playlist for a 10-minute task)",
    "The Fake Perfection Trap (Refactoring working button shadows and CSS padding instead of building the checkout flow)",
    "The Desk Cable Management Trap (Crawling under the desk routing monitor cords through velcro sleeves to avoid phone calls)",
    "The Tool Hopping Habit (Migrating all personal notes into Obsidian for an interactive graph view instead of writing)",
    "The Ritual Delusion (Weighing coffee beans to the tenth of a gram and dialing in grinder clicks before opening a document)",
    "The Font Pairing Paralysis (Testing 15 Google Fonts to find the 'most authoritative sans-serif' for a routine memo)",
    "The Digital Purge (Deleting 3,000 blurry screenshots from smartphone camera rolls right when deep focus is demanded)",
    "The Inbox Zero Obsession (Unsubscribing from 40 promotional newsletters to feel productive without producing anything)",
    "The IDE Theme Quest (Testing 12 VS Code dark themes because syntax highlighting 'doesn't feel inspiring enough')",
    "The Ambience Trap (Tweaking smart bulb hues and candle placement for 30 minutes before opening a notebook)",
    "The Shell Script Tinkering (Writing bash aliases to save 0.3 seconds on git commands while ignoring an urgent bug)",
    "The Download Folder Sorting (Categorizing 300 random PDFs and installers into subfolders instead of analyzing data)",
    "The Workout Blueprint Delusion (Building a 12-week lifting spreadsheet with formulas instead of doing 20 pushups)",
    "The Domain Name Hoarder (Buying 2 new domain names for 'future businesses' instead of finishing the MVP you started)",
    "The Hardware Spec Comparison (Watching 3 hours of M-series chip speed comparisons when your job is Google Docs)",
    "The Desktop Wallpaper Search (Browsing minimal wallpaper subreddits for 45 minutes looking for 'focus imagery')",
    "The Water Bottle Deep Clean (Soaking and bleaching reusable water bottles to avoid drafting a difficult email)",
    "The Slack Message Agony (Re-drafting a simple 2-sentence Slack message 7 times to sound casual yet professional)",
    "The Git Commit History Cleanse (Rebasing and crafting poetic commit messages instead of opening the pull request)",
    "The Noise-Canceling Gear Trap (Researching decibel ratings of headphones to block out your own wandering mind)",
    "The Pomodoro Timer Trap (Testing 4 different productivity timer apps with animated trees for an 8-minute task)",
    "The Phone App Declutter (Reorganizing mobile apps into color-coordinated folders to feel in control of your life)",
    "The Framework Novelty Loop (Reading documentation for cutting-edge web frameworks you will never use in production)",
    "The Ergonomic Posture Trap (Adjusting chair lumbar support, desk height, and footrest angles for 35 minutes before typing)",
    "The Smart Home Automation Trap (Configuring home automation routines for 2 hours instead of finishing your taxes)",
    "The Book Buying Delusion (Ordering 3 discipline books on Amazon while 5 unread books sit on your nightstand)",
    "The Chrome Tab Graveyard (Hoarding 42 open tabs as 'future reading material' for a project untouched in weeks)",
    "The Cold Brew Science (Sterilizing glass jars and calculating steep ratios instead of drafting a project proposal)"
]


def _init_fallback_catalog() -> List[Dict[str, Any]]:
    """Load default 32-entry catalog from quotes_catalog.json with failsafe backup."""
    if os.path.exists(paths.catalog_path):
        try:
            with open(paths.catalog_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) >= 10 and data[0].get("tweet_1"):
                    return data
        except Exception as e:
            print(f"[Catalog] Note loading fallback from {paths.catalog_path}: {e}")
    return [
        {
            "id": "sq_cleaning_1",
            "tweet_1": (
                "Just spent 35 minutes completely reorganizing my kitchen spice rack alphabetically to avoid writing one proposal.\n\n"
                "The paprika is in alphabetical order. The client is still waiting.\n\n"
                "Step away from the seasonings. Open the document. Finish the draft."
            ),
            "tweet_2": (
                "The sudden urge to reorganize your kitchen is just anxiety wearing an apron. "
                "Do the scary 5-minute task first."
            ),
            "hook": "Just spent 35 minutes completely reorganizing my kitchen spice rack alphabetically to avoid writing one proposal.",
            "quote": "Just spent 35 minutes completely reorganizing my kitchen spice rack alphabetically to avoid writing one proposal.",
            "author": "Field Notes",
            "category": "FAKE CHORES",
            "theme": "Aesthetic Organization",
            "times_posted": 0,
            "last_posted": None
        }
    ]


FALLBACK_CATALOG = _init_fallback_catalog()


def format_tweet_1(entry: Dict[str, Any]) -> str:
    """Format primary tweet: Formula 2 conversational narrative (NO BULLETS, NO QUOTES)."""
    t1 = entry.get("tweet_1")
    if t1:
        return t1.strip()
    return entry.get("hook", "").strip()


REPLY_MAGNET_QUESTIONS = [
    "Be honest: what side quest are you using to avoid your real work today?",
    "What is the one tab or chore you're using to procrastinate right now?",
    "What's the 5-minute task you've been putting off all afternoon?",
    "Which fake-productive habit is winning on your screen today?"
]


def format_tweet_2(entry: Dict[str, Any]) -> str:
    """
    Format secondary tweet: Formula 2 thread reply + low-friction confession hook
    to convert profile visitors into thread commenters (27x-150x Heavy Ranker boost).
    """
    t2 = (entry.get("tweet_2") or entry.get("backstory") or "").strip()
    if not t2:
        return ""
    if "?" not in t2:
        entry_id = str(entry.get("id") or t2)
        hook_q = REPLY_MAGNET_QUESTIONS[sum(ord(c) for c in entry_id) % len(REPLY_MAGNET_QUESTIONS)]
        combined = f"{t2}\n\n{hook_q}"
        if len(combined) <= 250:
            return combined
    return t2


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


COMMON_STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by",
    "could", "did", "do", "does", "doing", "down", "during", "each", "few", "for", "from", "further",
    "had", "has", "have", "having", "he", "her", "here", "hers", "herself", "him", "himself", "his",
    "how", "i", "if", "in", "into", "is", "it", "its", "itself", "just", "me", "more", "most", "my",
    "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our",
    "ours", "ourselves", "out", "over", "own", "same", "she", "should", "so", "some", "such", "than",
    "that", "the", "their", "theirs", "them", "themselves", "then", "there", "these", "they", "this",
    "those", "through", "to", "too", "under", "until", "up", "very", "was", "we", "were", "what",
    "when", "where", "which", "while", "who", "whom", "why", "with", "would", "you", "your", "yours",
    "yourself", "yourselves", "spent", "minutes", "hours", "avoid", "one", "first", "still", "open",
    "write", "start", "doing", "instead", "project", "task", "work", "day", "today"
}


def tokenize_and_filter(text: str) -> set:
    """Extract meaningful lowercase tokens without punctuation and stopwords."""
    import re
    words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
    return {w for w in words if w not in COMMON_STOPWORDS}


def calculate_jaccard_similarity(text1: str, text2: str) -> float:
    """Calculate Jaccard similarity between two texts based on informative tokens."""
    tokens1 = tokenize_and_filter(text1)
    tokens2 = tokenize_and_filter(text2)
    if not tokens1 or not tokens2:
        return 0.0
    intersection = tokens1.intersection(tokens2)
    union = tokens1.union(tokens2)
    return len(intersection) / len(union)


KEY_SUBJECT_GROUPS = [
    {"keyboard", "switches", "mouse", "monitor", "cables", "desk", "chair", "lighting", "webcam"},
    {"spotify", "playlist", "lo-fi", "music", "podcast", "audio", "headphones", "noise-canceling"},
    {"youtube", "tutorial", "tutorials", "video", "videos", "course", "courses", "lecture"},
    {"notion", "dashboard", "obsidian", "notes", "planner", "calendar", "timeblock", "todo"},
    {"tabs", "browser", "chrome", "bookmark", "wikipedia", "reddit", "articles"},
    {"spice", "spices", "kitchen", "pantry", "fridge", "dishes", "laundry", "socks", "bottles", "cleaning"},
    {"code", "refactoring", "css", "shadows", "buttons", "terminal", "aliases", "git", "commits", "vscode"},
    {"coffee", "grind", "beans", "espresso"},
    {"books", "amazon", "reading", "library"},
    {"workout", "gym", "lifting", "spreadsheet", "fitness"},
    {"domains", "domain", "saas", "namecheap"},
    {"downloads", "folder", "files", "desktop", "screenshots", "photos"},
    {"email", "inbox", "newsletters", "receipts", "slack"}
]


def shares_subject_cluster(text1: str, text2: str) -> bool:
    """Check if two texts share a specific subject cluster (e.g. both talking about keyboards or spices)."""
    tokens1 = tokenize_and_filter(text1)
    tokens2 = tokenize_and_filter(text2)
    for group in KEY_SUBJECT_GROUPS:
        overlap1 = tokens1.intersection(group)
        overlap2 = tokens2.intersection(group)
        if overlap1 and overlap2:
            return True
    return False


def is_entry_unique(
    candidate: Dict[str, Any],
    recent_entries: List[Dict[str, Any]],
    similarity_threshold: float = 0.28
) -> tuple:
    """
    Strictly verify that candidate post is completely unique and not similar to any recent post.
    Checks:
    1. Direct duplicate / substring match.
    2. Token Jaccard similarity against any post in last 30 days (< threshold).
    3. Shared subject cluster / domain with posts in the last 7 days.
    4. Category repetition against yesterday's post.
    """
    c_t1 = format_tweet_1(candidate)
    c_hook = candidate.get("hook", "")
    c_cat = candidate.get("category", "").upper()

    if not recent_entries:
        return True, "OK (no recent history)"

    # 1. Category check against immediately preceding post (index 0 is most recent)
    if recent_entries:
        last_cat = (recent_entries[0].get("category") or "").upper()
        if c_cat and last_cat and c_cat == last_cat:
            return False, f"Category '{c_cat}' repeats yesterday's category"

    # 2. Check against recent history (up to last 30 posts)
    for idx, past in enumerate(recent_entries[:30]):
        past_text = past.get("quote") or past.get("tweet_1") or past.get("hook") or ""
        if not past_text:
            continue

        # Exact hook or substring match
        if c_hook and (c_hook.lower() in past_text.lower() or past_text.lower() in c_hook.lower()):
            return False, f"Hook duplicates past post #{idx+1}: '{past_text[:50]}...'"

        # Jaccard word similarity
        sim = calculate_jaccard_similarity(c_t1, past_text)
        if sim >= similarity_threshold:
            return False, f"Word similarity {sim:.2f} >= {similarity_threshold} with post #{idx+1}: '{past_text[:50]}...'"

        # Subject cluster collision within last 7 posts
        if idx < 7 and shares_subject_cluster(c_t1, past_text):
            return False, f"Shares subject cluster with recent post #{idx+1}: '{past_text[:50]}...'"

    return True, "OK"


def generate_quote_with_groq(
    theme_name: str,
    theme_desc: str,
    recent_history: Optional[List[Dict[str, Any]]] = None,
    retries: int = 3
) -> Optional[Dict[str, Any]]:
    """Call Groq API to generate a natural, witty, deadpan human tweet (relatable observation + grounded motivation)."""
    if not ai_config.groq_api_key:
        print("[AI Generator] No GROQ_API_KEY set. Falling back to local catalog.")
        return None

    headers = {
        "Authorization": f"Bearer {ai_config.groq_api_key}",
        "Content-Type": "application/json"
    }

    # Build negative context to explicitly forbid repetition
    avoid_snippets = []
    if recent_history:
        for item in recent_history[:10]:
            q = item.get("quote") or item.get("tweet_1") or ""
            if q:
                first_sent = q.split(". ")[0].split("\n")[0].strip()
                avoid_snippets.append(f"- \"{first_sent}\"")
    
    avoid_block = ""
    if avoid_snippets:
        avoid_block = (
            "\nRECENTLY COVERED TOPICS (YOU ARE STRICTLY FORBIDDEN FROM REPEATING OR IMITATING THESE):\n"
            + "\n".join(avoid_snippets)
            + "\nCRITICAL MANDATE: Write about a completely different, fresh avoidance scenario. "
            "Do NOT touch the same items, apps, chores, or objects listed above.\n\n"
        )

    system_prompt = (
        "You are a witty, observational writer (think Jerry Seinfeld, Tim Urban, or David Sedaris) writing relatable, honest tweets about modern procrastination.\n\n"
        "CORE VOICE RULES — WRITE LIKE A REAL HUMAN:\n"
        "- Write naturally in clean, standard English. Use normal sentence structure, capitalization, and punctuation (periods, commas).\n"
        "- NO FORCED SLANG: Never use cringe internet buzzwords ('sparkle', 'close the mop', 'stop the shine', 'diabolical', 'cooked', 'slay').\n"
        "- NO RHYMING OR SLAM POETRY: Do NOT string together rhyming lists of commands. Talk like a normal person making a dry, deadpan observation.\n"
        "- NO NUMBERED LISTS, BULLET POINTS, OR QUOTATION MARKS.\n\n"
        "STRUCTURE OF TWEET 1 (Must be 3 short, distinct paragraphs):\n"
        "Paragraph 1 (The Setup): A specific, funny, deadpan description of an avoidance behavior you caught yourself doing (e.g. cleaning, researching gear, tweaking playlists, organizing Notion).\n"
        "Paragraph 2 (The Reality Check): A short, dry 1-sentence truth showing why it didn't solve anything (e.g. 'The paprika is in alphabetical order. The client is still waiting.').\n"
        "Paragraph 3 (The Motivation): A grounded, practical call to action (e.g. 'Step away from the seasonings. Open the document. Finish the draft.').\n\n"
        "TWEET 2 (Thread Reply & Engagement Hook): 1 calm, natural sentence delivering an insight on why we avoid uncomfortable work, followed by a casual 1-sentence question asking readers what 'side quest' they are using to procrastinate today.\n\n"
        "GOLD-STANDARD HUMAN EXAMPLES:\n\n"
        "Example 1:\n"
        "{\n"
        '  "tweet_1": "Just spent 35 minutes completely reorganizing my kitchen spice rack alphabetically to avoid writing one proposal.\\n\\nThe paprika is in alphabetical order. The client is still waiting.\\n\\nStep away from the seasonings. Open the document. Finish the draft.",\n'
        '  "tweet_2": "The sudden urge to reorganize your kitchen is just anxiety wearing an apron. Do the scary 5-minute task first.",\n'
        '  "category": "FAKE CHORES",\n'
        '  "hook": "Just spent 35 minutes completely reorganizing my kitchen spice rack alphabetically to avoid writing one proposal."\n'
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
        f"{avoid_block}"
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

                    if not validate_character_limits(parsed):
                        print(f"[AI Generator] Generation failed validation on model {model}, retrying (attempt {attempt+1}/{retries})...")
                        continue

                    # Uniqueness verification against recent history
                    if recent_history:
                        is_unique, reason = is_entry_unique(parsed, recent_history)
                        if not is_unique:
                            print(f"[AI Generator] Generation failed uniqueness check: {reason}. Retrying (attempt {attempt+1}/{retries})...")
                            continue

                    return parsed
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
        """Fetch or generate a 100% unique side quest post that avoids past topics & repetition."""
        # 0. Retrieve recent history from database if available
        recent_history = []
        try:
            from bot.database import db_manager
            recent_history = db_manager.get_recent_history(limit=30)
        except Exception as e:
            print(f"[Catalog] Note reading db_manager history: {e}")

        # Combine with recent catalog posted entries
        catalog_recent = [e for e in self.catalog if e.get("last_posted")]
        catalog_recent.sort(key=lambda x: x.get("last_posted") or "", reverse=True)
        combined_recent = recent_history + catalog_recent

        # Pick a topic whose domain wasn't covered recently
        available_topics = list(SIDE_QUEST_TOPICS)
        random.shuffle(available_topics)
        chosen_topic = available_topics[0]
        for t in available_topics:
            topic_core = t.split("(")[0].strip().lower()
            if not any(topic_core in (p.get("theme") or "").lower() for p in combined_recent[:7]):
                chosen_topic = t
                break

        # 1. Try to generate a fresh one via Groq with negative context & uniqueness verification
        generated = generate_quote_with_groq("Side Quest", chosen_topic, recent_history=combined_recent)
        if generated:
            self.catalog.append(generated)
            self.save()
            return generated

        # 2. Offline / Fallback: Filter catalog for entries that are 100% unique compared to recent history
        unique_candidates = []
        for entry in self.catalog:
            unique, reason = is_entry_unique(entry, combined_recent)
            if unique:
                unique_candidates.append(entry)

        if not unique_candidates:
            # If all 32 have been used recently, relax to those not used in the last 14 entries
            print("[Catalog] Relaxing uniqueness filter to last 14 days...")
            for entry in self.catalog:
                unique, _ = is_entry_unique(entry, combined_recent[:14], similarity_threshold=0.35)
                if unique:
                    unique_candidates.append(entry)

        if not unique_candidates:
            unique_candidates = list(self.catalog)

        # Prioritize completely unposted entries (times_posted == 0)
        unposted = [e for e in unique_candidates if e.get("times_posted", 0) == 0]
        if unposted:
            choice = random.choice(unposted)
            return choice

        # If all candidates have been posted at least once, pick the least recently posted among unique candidates
        sorted_candidates = sorted(
            unique_candidates,
            key=lambda x: (x.get("times_posted", 0), x.get("last_posted") or "")
        )
        return sorted_candidates[0]

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
    "dear friend", "hello", "hey there", "great post", "love this"
)

BANNED_REPLY_CLICHES = [
    "future self", "listen to your body", "give yourself permission",
    "heavy mental load", "take a deep breath", "it's okay to not be okay",
    "mental static", "prescription for", "nourish the soul", "doormat",
    "crush it", "delve", "insane work bro", "put the phone in another room",
    "toss the phone", "canonical builder experience", "rise and grind",
    "schadenfreude", "smugly", "rite of passage", "masterclass", "humbles a",
    "what are you building anyway", "classic trap", "foreign language"
]


def _extract_word_trigrams(text: str) -> set:
    """Extract lowercase 3-word sequences to prevent repetitive n-gram signatures across replies."""
    import re
    words = re.findall(r"\b[a-zA-Z']+\b", text.lower())
    if len(words) < 3:
        return set()
    return {" ".join(words[i:i + 3]) for i in range(len(words) - 2)}


def is_reply_unique(
    candidate_reply: str,
    recent_replies: List[Dict[str, Any]],
    similarity_threshold: float = 0.25
) -> tuple:
    """
    Ensure an outgoing reply does not share repetitive n-grams or token overlap
    with recently sent replies (crucial for avoiding X's automated spam filter).
    """
    if not recent_replies:
        return True, "OK"

    cand_clean = candidate_reply.strip().lower()
    cand_trigrams = _extract_word_trigrams(cand_clean)

    for idx, item in enumerate(recent_replies[:20]):
        past_reply = (item.get("reply_text") or "").strip()
        if not past_reply:
            continue

        past_clean = past_reply.lower()
        if cand_clean == past_clean:
            return False, f"Exact duplicate of recent reply #{idx + 1}"

        # Check 3-word phrase overlap
        past_trigrams = _extract_word_trigrams(past_clean)
        shared_trigrams = cand_trigrams.intersection(past_trigrams)
        if shared_trigrams:
            sample_trigram = next(iter(shared_trigrams))
            return False, f"Shares 3-word phrase '{sample_trigram}' with recent reply #{idx + 1}"

        # Check Jaccard token similarity
        sim = calculate_jaccard_similarity(cand_clean, past_clean)
        if sim >= similarity_threshold:
            return False, f"Token similarity {sim:.2f} >= {similarity_threshold} with recent reply #{idx + 1}"

    return True, "OK"


def generate_human_reply(
    tweet_text: str,
    author_name: str = "",
    recent_replies: Optional[List[Dict[str, Any]]] = None,
    retries: int = 3
) -> Optional[str]:
    """
    Generate an organic, non-repetitive peer reply designed to spark genuine
    author engagement (likes/replies) and avoid X spam/ghost-ban heuristics.
    """
    if not ai_config.groq_api_key:
        print("[AI Reply] No GROQ_API_KEY set.")
        return None

    if recent_replies is None:
        try:
            from bot.database import db_manager
            recent_replies = db_manager.get_recent_replies(limit=15)
        except Exception:
            recent_replies = []

    avoid_replies_block = ""
    if recent_replies:
        snippets = [
            f"- \"{r.get('reply_text', '').strip()}\""
            for r in recent_replies[:8]
            if r.get("reply_text")
        ]
        if snippets:
            avoid_replies_block = (
                "\nRECENT REPLIES YOU ALREADY SENT (DO NOT REUSE ANY PHRASES, SLANG, OR SENTENCE STRUCTURES FROM THESE):\n"
                + "\n".join(snippets)
                + "\n"
            )

    headers = {
        "Authorization": f"Bearer {ai_config.groq_api_key}",
        "Content-Type": "application/json"
    }

    system_prompt = (
        "You are a supportive, funny, relatable 20-something friend on X.\n"
        "Your signature style is HUMOROUS + MOTIVATIONAL at the same time (like a friend in the library who makes you laugh about procrastinating and then hypes you up to knock out 15 minutes of work).\n\n"
        "STEP 1 — RELEVANCE GATE:\n"
        "If the tweet is NOT a personal post about studying, working, coding, building a project, procrastinating, or trying to focus "
        "(for example, if it's about sports, video games, politics, fan cams, celebrity drama, selling something, or tragedy), output the exact single word: SKIP\n\n"
        "STEP 2 — THE 2-PART FORMULA (HUMOR + MOTIVATION):\n"
        "Write 1 to 2 short, natural sentences (45 to 145 characters total):\n"
        "  1. The Funny Observation: React with light, everyday humor to the exact thing that happened in their tweet.\n"
        "  2. The Grounded Motivational Push: Give them a warm, bite-sized nudge that makes starting feel easy right now (e.g. 'knock out just 15 minutes', 'write one messy page', 'ship the ugly version first, you got this').\n\n"
        "CRITICAL VOICE RULES:\n"
        "- Use simple, everyday conversational English. NEVER use pretentious SAT/thesaurus words ('schadenfreude', 'smugly', 'canonical', 'poetic', 'rite of passage', 'masterclass', 'peak').\n"
        "- STAY 100% ON THEIR EXACT TOPIC: Never ask 'what are you building?' unless their tweet explicitly mentions coding or building an app.\n"
        "- Output ONLY the reply text (or SKIP). NO quotes, NO hashtags, NO links, NO @mentions, NO emojis.\n\n"
        "GOLD-STANDARD EXAMPLES (HUMOROUS + MOTIVATIONAL):\n"
        "- Tweet: 'dropped my phone on my nose this is what I get for not studying and doomscrolling instead'\n"
        "  Reply: 'even gravity is telling you it\\'s time to start. knock out just 15 minutes of notes and call it a win, you got this'\n"
        "- Tweet: 'procrastinating by organizing my spotify playlist instead of studying for this midterm'\n"
        "  Reply: 'the soundtrack is officially ready. press play and just get through one chapter tonight, future you will be hyped'\n"
        "- Tweet: 'why do i always deep clean my room the night before a huge deadline'\n"
        "  Reply: 'nothing makes a room cleaner than a terrifying deadline. ride that momentum into just 20 minutes on the actual draft'\n"
        "- Tweet: 'spent 4 hours fighting css padding instead of finishing the feature'\n"
        "  Reply: 'css has humbled every developer alive. ship the messy version first and fix the pixels later, you\\'re closer than you think'"
    )

    clean_tweet = tweet_text.strip()
    user_prompt = (
        f"Tweet:\n\"{clean_tweet}\"\n"
        f"{avoid_replies_block}\n"
        f"Write a humorous yet genuinely motivating 1-2 sentence reply reacting directly to this tweet (45-145 chars), or output SKIP if off-topic:"
    )

    primary_model = ai_config.groq_model or "openai/gpt-oss-120b"
    candidate_models = [primary_model, "openai/gpt-oss-120b", "qwen/qwen3.8-27b"]
    seen_models = set()
    models_to_try = [m for m in candidate_models if not (m in seen_models or seen_models.add(m))]

    for model in models_to_try:
        for attempt in range(retries):
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.68,
                "max_tokens": 80
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

                    if reply.upper() == "SKIP" or reply.upper().startswith("SKIP"):
                        print("[AI Reply] LLM relevance gate marked tweet as off-topic (SKIP).")
                        return None

                    reply_lower = reply.lower().strip()

                    if any(reply_lower.startswith(starter) for starter in BANNED_REPLY_STARTERS):
                        print(f"[AI Reply] Rejected banned starter in reply: '{reply}'. Retrying...")
                        continue

                    if any(cliche in reply_lower for cliche in BANNED_REPLY_CLICHES):
                        print(f"[AI Reply] Rejected cliché in reply: '{reply}'. Retrying...")
                        continue

                    if any(bad_emoji in reply for bad_emoji in ("🚀", "🤖", "🧵", "🔥", "💯")):
                        print(f"[AI Reply] Rejected bot emoji in reply: '{reply}'. Retrying...")
                        continue

                    unique_ok, unique_reason = is_reply_unique(reply, recent_replies or [])
                    if not unique_ok:
                        print(f"[AI Reply] Rejected non-unique reply ({unique_reason}): '{reply}'. Retrying...")
                        continue

                    if 30 <= len(reply) <= 180 and "#" not in reply and "http" not in reply and "@" not in reply:
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


def generate_quote_tweet_commentary(
    tweet_text: str,
    author_name: str = "",
    recent_replies: Optional[List[Dict[str, Any]]] = None,
    retries: int = 3
) -> Optional[str]:
    """
    Generate a deadpan 'Field Note / Procrastination Archive' observation for Quote-Tweeting
    a relatable post. Quote Tweets appear on the main timeline, notify the author, and carry
    zero cold-reply deboosting risk.
    """
    if not ai_config.groq_api_key:
        return None

    if recent_replies is None:
        try:
            from bot.database import db_manager
            recent_replies = db_manager.get_recent_replies(limit=15)
        except Exception:
            recent_replies = []

    headers = {
        "Authorization": f"Bearer {ai_config.groq_api_key}",
        "Content-Type": "application/json"
    }

    system_prompt = (
        "You run 'The Procrastination Archive' on X — a humorous and motivating account about how students and builders avoid their work.\n"
        "You are Quote-Tweeting someone's post about procrastinating, coding struggles, or studying.\n\n"
        "STEP 1 — RELEVANCE GATE:\n"
        "If the tweet is NOT a genuine personal post about procrastinating, studying, coding, building, or avoiding work, output the exact single word: SKIP\n\n"
        "STEP 2 — QUOTE-TWEET FORMULA (HUMOR + MOTIVATION):\n"
        "- Write 1-2 short sentences in plain everyday English: first a funny, relatable observation about their specific procrastination, followed by a grounded, encouraging push to start small.\n"
        "- Never use big thesaurus words ('schadenfreude', 'rite of passage', 'canonical').\n"
        "- Strictly between 45 and 145 characters. No hashtags, no links, no @mentions, no quotes around the output.\n\n"
        "EXAMPLES:\n"
        "- Tweet: 'just cleaned my entire kitchen from top to bottom instead of starting my 5 page paper'\n"
        "  Quote: 'Nothing makes an apartment cleaner than a 5-page paper due tomorrow. Kitchen is spotless, now just get the ugly first paragraph down.'\n"
        "- Tweet: 'spent 3 hours tweaking my editor theme instead of writing the code'\n"
        "  Quote: 'Three hours picking a font to avoid ten minutes of coding happens to all of us. Write one messy function and let momentum take over.'"
    )

    user_prompt = (
        f"Tweet:\n\"{tweet_text.strip()}\"\n\n"
        f"Write a humorous yet motivating Quote-Tweet (45-145 chars), or output SKIP:"
    )

    primary_model = ai_config.groq_model or "openai/gpt-oss-120b"
    candidate_models = [primary_model, "openai/gpt-oss-120b", "qwen/qwen3.8-27b"]
    seen_models = set()
    models_to_try = [m for m in candidate_models if not (m in seen_models or seen_models.add(m))]

    for model in models_to_try:
        for _ in range(retries):
            try:
                response = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.68,
                        "max_tokens": 80
                    },
                    timeout=15
                )
                if response.status_code == 200:
                    qt_text = response.json()["choices"][0]["message"]["content"].strip().strip("\"'")
                    if qt_text.upper().startswith("SKIP"):
                        return None
                    unique_ok, _ = is_reply_unique(qt_text, recent_replies or [])
                    if unique_ok and 35 <= len(qt_text) <= 160 and "#" not in qt_text and "http" not in qt_text:
                        return qt_text
            except Exception:
                time.sleep(1)

    return None


def generate_author_back_reply(
    parent_tweet_text: str,
    comment_text: str,
    commenter_name: str = ""
) -> Optional[str]:
    """
    Generate a warm, witty author reply to someone who commented on OUR thread.
    In X's Heavy Ranker, Author-Reply-to-Comment carries a 75x-150x algorithmic boost
    and has 0% ghost-ban risk.
    """
    if not ai_config.groq_api_key:
        return None

    headers = {
        "Authorization": f"Bearer {ai_config.groq_api_key}",
        "Content-Type": "application/json"
    }

    system_prompt = (
        "You are the creator of a witty productivity/builder account on X.\n"
        "A reader just replied to your thread. Write a brief, warm, witty 1-sentence reply back to them.\n"
        "Keep it casual, appreciative, and grounded (25 to 120 characters). No hashtags, no links, no @mentions."
    )
    user_prompt = (
        f"Our original tweet: \"{parent_tweet_text.strip()}\"\n"
        f"Reader ({commenter_name or 'peer'}) commented: \"{comment_text.strip()}\"\n\n"
        f"Write a short, witty 1-sentence reply back:"
    )

    for model in ["qwen/qwen3.8-27b", "openai/gpt-oss-120b"]:
        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.85,
                    "max_tokens": 70
                },
                timeout=15
            )
            if response.status_code == 200:
                reply = response.json()["choices"][0]["message"]["content"].strip().strip("\"'")
                if 20 <= len(reply) <= 160 and "#" not in reply and "http" not in reply:
                    return reply
        except Exception:
            pass
    return None
