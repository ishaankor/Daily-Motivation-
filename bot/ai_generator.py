"""AI Content & Human Engagement Generator using Groq with strict Twitter 280-character validation.
Engineered for Formula 2: "The Absurdly Specific Side Quest" (Pure conversational narrative, NO bullets, NO quotes).
"""

import json
import os
import random
import re
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

POST_ARCHETYPES = [
    {
        "id": "SELF_HANDICAPPING_EXCUSE",
        "name": "The Self-Handicapping Callout (Procrastination as Ego Insurance)",
        "card_length": "120 to 290 chars (Short bold first line under 45 chars + 1-2 brutal paragraphs)",
        "instructions": (
            "Expose the secret ego-defense mechanism behind last-minute procrastination: people wait until the last possible hour ON PURPOSE "
            "so that if the result is mediocre, they can tell themselves 'well, I did it in 30 minutes' instead of facing what their true 100% effort looks like. "
            "Start with a short punchy header line (like 'hard pill to swallow:' or 'why you actually wait until 11pm:'), then deliver the ego-bruiser."
        ),
        "example_card": (
            "hard pill to swallow:\n\n"
            "you procrastinate until the last minute on purpose so you have a built-in excuse if the result is mediocre.\n\n"
            "saying 'i threw this together in an hour' protects your ego. trying for 3 days and still coming up short doesn't."
        ),
        "example_caption": "nobody wants to find out what their actual 100% effort looks like.",
        "example_tweet_2": "The second you stop protecting your image and let yourself look like a beginner for an hour, the paralysis disappears. Where are you holding back just to keep an excuse handy?"
    },
    {
        "id": "WASTED_POTENTIAL_ADDICTION",
        "name": "The 'Untapped Potential' Addiction",
        "card_length": "120 to 290 chars (Short bold first line + 2 razor-sharp paragraphs)",
        "instructions": (
            "Call out how people are secretly addicted to feeling like 'wasted potential' because 'I could crush this if I actually tried' "
            "is a comfortable fantasy that never has to be tested against reality. Make the reader feel called out enough to prove it wrong today."
        ),
        "example_card": (
            "uncomfortable truth:\n\n"
            "a lot of you aren't scared of failing.\n\n"
            "you're scared of giving something 100% of your focus for 6 months and finding out you're just normal—because right now you still get to comfort yourself with 'i could do it if i actually tried.'"
        ),
        "example_caption": "'untapped potential' is the most comfortable lie in the world.",
        "example_tweet_2": "Potential expires the longer you hoard it to feel special. One messy, finished rep today beats another year of imaginary dominance. What have you been 'about to start' for months?"
    },
    {
        "id": "AMBITION_COSPLAY_CHECKLIST",
        "name": "The iOS Notes Checklist Callout (Ambition Cosplay)",
        "card_length": "130 to 310 chars (Short title line + 3 unchecked '○ ' fake-progress items + 1 checked '● ' real uncomfortable item)",
        "instructions": (
            "Format the note as a real iOS Apple Notes checklist using '○ ' for unchecked items and '● ' for the final checked item. "
            "Expose how buying gear, reorganizing Notion, or hoarding tabs is just 'ambition cosplay'—rehearsing what a disciplined person looks like "
            "to get free dopamine without risking embarrassment."
        ),
        "example_card": (
            "things that feel like progress but are just ambition cosplay:\n\n"
            "○ buying a new domain name at 1am\n"
            "○ rebuilding your notion dashboard from scratch\n"
            "○ watching 3 hours of productivity setups on youtube\n"
            "● doing the one uncomfortable task you've been dodging since tuesday"
        ),
        "example_caption": "we love the aesthetic of locking in way more than the actual work.",
        "example_tweet_2": "Your brain will happily let you 'prepare' for 10 hours if it saves you from 20 minutes of feeling stupid on a real task. Which piece of fake prep are you using to stall today?"
    },
    {
        "id": "PERFECTIONISM_COPE",
        "name": "The 'Perfectionism' Cope Destroyer",
        "card_length": "110 to 275 chars (Bold opening claim + brutal distinction between high standards and fragile pride)",
        "instructions": (
            "Destroy the favorite lie procrastinators tell themselves: 'I'm just a perfectionist.' Point out that you cannot be a perfectionist "
            "about something that doesn't exist yet—refusing to write an ugly first draft isn't high standards, it's fragile pride."
        ),
        "example_card": (
            "stop calling yourself a perfectionist when you haven't even started.\n\n"
            "perfectionism is obsessing over the final 5% of something you already built.\n\n"
            "staring at a blank page for four days because your first attempt might look rough isn't high standards. it's just fragile pride."
        ),
        "example_caption": "calling procrastination 'perfectionism' is the biggest cope on earth.",
        "example_tweet_2": "High standards never stopped anyone from starting; only ego does. Let the first page be embarrassing so you actually have something to sharpen. What draft are you refusing to write ugly?"
    },
    {
        "id": "EXCUSE_VS_REALITY_RECEIPT",
        "name": "The Excuse vs. Reality iOS Notes Receipt",
        "card_length": "130 to 300 chars (Two contrasting checklist sections using '○ ' for excuses and '● ' for the blunt truth)",
        "instructions": (
            "Write a two-part iOS Notes checklist contrasting 'what you say is holding you back:' (3 '○ ' items blaming time, systems, burnout, or mood) "
            "against 'what is actually holding you back:' (1 brutal '● ' item exposing the refusal to sit with 25 minutes of boredom or bruised ego)."
        ),
        "example_card": (
            "what you say is blocking you:\n"
            "○ not enough time in the day\n"
            "○ haven't found the right routine yet\n"
            "○ waiting until i feel locked in\n\n"
            "what is actually blocking you:\n"
            "● one 25-minute task that requires you to feel slightly incompetent without reaching for your phone"
        ),
        "example_caption": "your screen time report already knows the real answer.",
        "example_tweet_2": "People will spend three weeks shopping for a 'better system' just to avoid 25 minutes of quiet friction. What's the one task you'd finish today if your phone was in another room?"
    }
]


def _init_fallback_catalog() -> List[Dict[str, Any]]:
    """Load default Brutal Ego-Bruiser catalog from quotes_catalog.json with failsafe backup."""
    if os.path.exists(paths.catalog_path):
        try:
            with open(paths.catalog_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) >= 5 and data[0].get("card_text"):
                    return data
        except Exception as e:
            print(f"[Catalog] Note loading fallback from {paths.catalog_path}: {e}")
    return [
        {
            "id": "ego_handicap_1",
            "archetype": "SELF_HANDICAPPING_EXCUSE",
            "card_text": (
                "hard pill to swallow:\n\n"
                "you procrastinate until the last minute on purpose so you have a built-in excuse if the result is mediocre.\n\n"
                "saying 'i threw this together in an hour' protects your ego. trying for 3 days and still coming up short doesn't."
            ),
            "tweet_1": "nobody wants to find out what their actual 100% effort looks like.",
            "tweet_2": "The second you stop protecting your image and let yourself look like a beginner for an hour, the paralysis disappears. Where are you holding back just to keep an excuse handy?",
            "hook": "you procrastinate until the last minute on purpose so you have a built-in excuse if the result is mediocre.",
            "quote": (
                "hard pill to swallow:\n\n"
                "you procrastinate until the last minute on purpose so you have a built-in excuse if the result is mediocre.\n\n"
                "saying 'i threw this together in an hour' protects your ego. trying for 3 days and still coming up short doesn't."
            ),
            "author": "Field Notes",
            "category": "EGO INSURANCE",
            "theme": "The Fake Perfection Trap",
            "times_posted": 0,
            "last_posted": None
        }
    ]


FALLBACK_CATALOG = _init_fallback_catalog()


def format_tweet_1(entry: Dict[str, Any]) -> str:
    """Format primary tweet caption (short human observation above the Apple Notes card)."""
    t1 = entry.get("tweet_1")
    if t1:
        return t1.strip()
    return (entry.get("card_text") or entry.get("hook") or "").strip()


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
    """Ensure card_text, tweet_1 caption, and tweet_2 meet character limits and avoid robotic AI templates."""
    t1 = format_tweet_1(entry)
    t2 = format_tweet_2(entry)
    card_text = (entry.get("card_text") or entry.get("quote") or entry.get("hook") or t1).strip()

    len_t1 = len(t1)
    len_t2 = len(t2)
    len_card = len(card_text)

    if not (12 <= len_t1 <= 275 and 15 <= len_t2 <= 250 and 45 <= len_card <= 390):
        print(
            f"[Validation Warning] Length invalid: Card ({len_card}/390), "
            f"Tweet 1 ({len_t1}/275), Tweet 2 ({len_t2}/250)"
        )
        return False

    # Enforce punctuation or checklist structure in card_text
    if "." not in card_text and "?" not in card_text and "!" not in card_text and "●" not in card_text:
        print("[Validation Warning] card_text missing standard punctuation or checklist marker. Rejecting.")
        return False

    # Ban old Mad-Libs AI template phrases and soft therapist cliches
    banned_phrases = [
        "close the mop", "stop the shine", "wait for your sparkle", "shine on", "lock in for your",
        "close the doc", "close the tab", "close the planner", "open the document", "open the file",
        "put down the", "step away from the", "pause the playlist", "lock the phone in the other room",
        "study session was completely wasted", "sit down with your notes", "study for 25 minutes",
        "forgive yourself right now"
    ]
    combined_lower = f"{t1}\n{card_text}\n{t2}".lower()
    for bp in banned_phrases:
        if bp in combined_lower:
            print(f"[Validation Warning] Entry contains banned AI template phrase: '{bp}'. Rejecting.")
            return False

    # Ensure Tweet 1 caption and Apple Notes card_text aren't lazy verbatim duplicates when card_text is explicitly set
    if entry.get("card_text") and t1.strip().lower() == card_text.strip().lower():
        print("[Validation Warning] tweet_1 caption is an exact duplicate of card_text. Rejecting.")
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
    4. Category or structural archetype repetition against yesterday's post.
    """
    c_card = (candidate.get("card_text") or candidate.get("quote") or candidate.get("hook") or "").strip()
    c_t1 = format_tweet_1(candidate)
    c_combined = f"{c_card} {c_t1}".strip()
    c_hook = candidate.get("hook", "") or c_card
    c_cat = (candidate.get("category") or "").upper()
    c_arch = (candidate.get("archetype") or "").upper()

    if not recent_entries:
        return True, "OK (no recent history)"

    # 1. Category & Archetype check against immediately preceding post (index 0 is most recent)
    if recent_entries:
        last_cat = (recent_entries[0].get("category") or "").upper()
        if c_cat and last_cat and c_cat == last_cat:
            return False, f"Category '{c_cat}' repeats yesterday's category"
        last_arch = (recent_entries[0].get("archetype") or "").upper()
        if c_arch and last_arch and c_arch == last_arch:
            return False, f"Archetype '{c_arch}' repeats yesterday's structural archetype"

    # 2. Check against recent history (up to last 30 posts)
    for idx, past in enumerate(recent_entries[:30]):
        past_text = (
            past.get("card_text")
            or past.get("quote")
            or past.get("tweet_1")
            or past.get("hook")
            or ""
        )
        if not past_text:
            continue

        # Exact hook or substring match
        if c_hook and (c_hook.lower() in past_text.lower() or past_text.lower() in c_hook.lower()):
            return False, f"Hook duplicates past post #{idx+1}: '{past_text[:50]}...'"

        # Jaccard word similarity
        sim = calculate_jaccard_similarity(c_combined, past_text)
        if sim >= similarity_threshold:
            return False, f"Word similarity {sim:.2f} >= {similarity_threshold} with post #{idx+1}: '{past_text[:50]}...'"

        # Subject cluster collision within last 7 posts
        if idx < 7 and shares_subject_cluster(c_combined, past_text):
            return False, f"Shares subject cluster with recent post #{idx+1}: '{past_text[:50]}...'"

    return True, "OK"


def generate_quote_with_groq(
    theme_name: str,
    theme_desc: str,
    recent_history: Optional[List[Dict[str, Any]]] = None,
    retries: int = 3
) -> Optional[Dict[str, Any]]:
    """Call Groq API to generate a rotating Multi-Archetype Apple Notes card + non-duplicate tweet caption."""
    if not ai_config.groq_api_key:
        print("[AI Generator] No GROQ_API_KEY set. Falling back to local catalog.")
        return None

    headers = {
        "Authorization": f"Bearer {ai_config.groq_api_key}",
        "Content-Type": "application/json"
    }

    # Pick an archetype that does not repeat the most recent post's archetype
    last_arch = ""
    if recent_history:
        last_arch = (recent_history[0].get("archetype") or "").upper()
    eligible_archetypes = [a for a in POST_ARCHETYPES if a["id"] != last_arch] or POST_ARCHETYPES
    chosen_arch = random.choice(eligible_archetypes)

    # Build negative context to explicitly forbid repetition
    avoid_snippets = []
    if recent_history:
        for item in recent_history[:10]:
            q = item.get("card_text") or item.get("quote") or item.get("tweet_1") or ""
            if q:
                first_sent = q.split(". ")[0].split("\n")[0].strip()
                avoid_snippets.append(f"- \"{first_sent}\"")

    avoid_block = ""
    if avoid_snippets:
        avoid_block = (
            "\nRECENTLY COVERED TOPICS (YOU ARE STRICTLY FORBIDDEN FROM REPEATING OR IMITATING THESE):\n"
            + "\n".join(avoid_snippets)
            + "\nCRITICAL MANDATE: Write about a completely different, fresh psychological angle or scenario. "
            "Do NOT touch the same items, apps, chores, or objects listed above.\n\n"
        )

    system_prompt = (
        "You write viral, brutally honest Twitter/X posts for an account that shares raw iPhone Apple Notes screenshots exposing "
        "the hidden ego excuses behind procrastination, fake productivity, and 'untapped potential.'\n\n"
        "THE VIRAL 'X-FACTOR' — BRUTAL EGO-BRUISERS (NOT POLITE THERAPIST ADVICE):\n"
        "- Polite self-help advice ('you're just tired, forgive yourself') gets ignored. Viral posts expose the SECRET EXCUSE people use to protect their ego.\n"
        "- Call out uncomfortable truths that make readers quote-tweet with 'delete this right now' or 'i feel attacked':\n"
        "  * Waiting until the last minute on purpose so if you fail, you can say 'I barely tried'\n"
        "  * Being addicted to feeling like 'wasted potential' because trying 100% and finding out you're average is terrifying\n"
        "  * Using fake preparation (Notion templates, courses, desk setups) as 'ambition cosplay' to get free dopamine without risking embarrassment\n"
        "  * Calling yourself a 'perfectionist' when you haven't even started (it's not high standards, it's fragile pride)\n"
        "- Write `card_text` in raw, natural lowercase (like a real private note typed on an iPhone at 11:42 PM). Use '○ ' and '● ' when the archetype calls for an iOS Notes checklist.\n"
        "- NEVER use the old 3-paragraph AI template ('Spent X minutes doing Y -> Close X. Open Y.').\n"
        "- NEVER copy-paste `card_text` into `tweet_1`. `tweet_1` is the short, deadpan 1-sentence caption posted above the screenshot.\n\n"
        f"TODAY'S STRUCTURAL ARCHETYPE: {chosen_arch['name']} ({chosen_arch['id']})\n"
        f"- Card Format & Length: {chosen_arch['card_length']}\n"
        f"- Archetype Instructions: {chosen_arch['instructions']}\n\n"
        "WHAT YOU MUST GENERATE (JSON OBJECT):\n"
        "1. \"card_text\": The raw note rendered INSIDE the iOS Apple Notes screenshot (90 to 340 chars). Follow today's archetype strictly.\n"
        "2. \"tweet_1\": The short, deadpan 1-liner caption posted in the tweet body ABOVE the screenshot (25 to 115 chars). Must NOT repeat `card_text`.\n"
        "3. \"tweet_2\": A sharp 1-2 sentence follow-up reply beneath the image that turns the callout into immediate action + a pointed question (under 235 chars).\n"
        "4. \"category\": A short 2-word uppercase label (e.g., \"EGO INSURANCE\", \"AMBITION COSPLAY\", \"POTENTIAL COPE\", \"FRAGILE PRIDE\").\n\n"
        "GOLD-STANDARD EXAMPLE FOR TODAY'S ARCHETYPE:\n"
        "{\n"
        f'  "archetype": "{chosen_arch["id"]}",\n'
        f'  "card_text": {json.dumps(chosen_arch["example_card"])},\n'
        f'  "tweet_1": {json.dumps(chosen_arch["example_caption"])},\n'
        f'  "tweet_2": {json.dumps(chosen_arch["example_tweet_2"])},\n'
        '  "category": "EGO INSURANCE"\n'
        "}"
    )

    user_prompt = (
        f"Generate a brutal, scroll-stopping post using the '{chosen_arch['name']}' ({chosen_arch['id']}) archetype, exposing the ego excuse behind: '{theme_desc}'.\n\n"
        f"{avoid_block}"
        "Remember:\n"
        "- `card_text` goes inside the iOS Apple Notes screenshot (raw lowercase realism, sharp ego-bruiser, NO soft therapist cliches).\n"
        "- `tweet_1` is a short, deadpan 1-sentence caption for the tweet body (25-115 chars) that does NOT repeat `card_text`.\n"
        "- `tweet_2` is the follow-up reply under the post (under 235 chars) ending with a pointed question.\n"
        "Respond ONLY in valid JSON."
    )

    primary = ai_config.groq_model
    if primary == "openai/gpt-oss-20b":
        primary = "openai/gpt-oss-120b"

    candidate_models = [primary, "openai/gpt-oss-120b", "openai/gpt-oss-20b", "groq/compound-mini"]
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
            if model.startswith("openai/gpt-oss"):
                payload["reasoning_effort"] = "low"

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

                    card_text = (parsed.get("card_text") or parsed.get("quote") or parsed.get("hook") or "").strip()
                    parsed["card_text"] = card_text
                    parsed["hook"] = card_text
                    parsed["quote"] = card_text
                    parsed["archetype"] = parsed.get("archetype") or chosen_arch["id"]
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
                if not self.catalog or not self.catalog[0].get("card_text"):
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
    "what are you building anyway", "classic trap", "foreign language",
    "origin story", "mysterious mentor", "lurking in the shadows",
    "movie villain", "training arc", "isaac newton",
    "close the doc", "close the tab", "close the app", "open the doc",
    "open the file", "put down the", "step away from", "ugly first draft",
    "terrible paragraph", "messy function", "knock out one page", "call it a win",
    "once you get past", "gets way easier", "real relief only hits",
    "higher graduation rate", "how top grades are", "survival mode is undefeated",
    "clear finish line", "rest of the feature flies", "first ten minutes of boredom"
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
    retries: int = 3,
    media_urls: Optional[List[str]] = None
) -> Optional[str]:
    """
    Generate a 100% tweet-specific peer reply engineered for X's Heavy Ranker:
    - #1 Chameleon Mode: Matches the exact native energy of the tweet (zero forced motivational lectures).
    - #2 Author Reply-Bait (+150x Heavy Ranker boost): Uses hyper-specific follow-up questions or playful
      callouts about the exact detail in their tweet so the author replies back.
    - #3 Vision Easter-Egg Zoom-In: When a photo is attached, spots a specific background detail in the image.
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

    has_image = bool(media_urls and len(media_urls) > 0)
    clean_tweet = re.sub(r"https?://\S+", "", tweet_text).strip()

    system_prompt = (
        "You are a sharp, funny, deadpan peer on X replying directly to someone's post.\n"
        "CRITICAL RULE — NO FORCED MOTIVATIONAL TEMPLATES:\n"
        "- Do NOT act like a life coach, therapist, or LinkedIn motivational speaker.\n"
        "- NEVER tack a preachy moral or 'once you start it gets easier' lesson onto the end of your reply.\n"
        "- Write 100% FOR THIS SPECIFIC TWEET by matching its native energy (Chameleon Mode):\n\n"
        "STEP 1 — RELEVANCE GATE:\n"
        "If the tweet is a personal post about studying, homework, working, coding, building, procrastinating, burnout, or deadlines, it PASSED.\n"
        "Output the exact single word SKIP if the tweet is unrelated (sports, politics, fan cams, celebrity drama, crypto/forex, selling something, or HR layoffs).\n\n"
        "STEP 2 — PICK THE BEST REACTION FOR THIS SPECIFIC TWEET (35 to 140 chars, lowercase casual human style):\n"
        "Option A — THE +150x AUTHOR REPLY-BAIT QUESTION (Best when they are procrastinating, stuck, or crashing out):\n"
        "  Zoom in on the most specific detail in their tweet and ask a deadpan, low-effort question they can't resist answering.\n"
        "  * Tweet: 'procrastinating on this 10 page paper due at midnight'\n"
        "    Reply: 'wait how many pages do you actually have written right now or is the doc still just your name and the date'\n"
        "  * Tweet: 'spent 4 hours fighting css padding instead of finishing the feature'\n"
        "    Reply: 'did you finally fix it or did you just slap overflow hidden on it and walk away'\n"
        "  * Tweet: 'why do i always deep clean my room the night before a huge exam'\n"
        "    Reply: 'be honest how spotless is the floor right now compared to your study guide'\n"
        "Option B — THE PLAYFUL ROAST / ESCALATION (Best when they are joking, memeing, or flexing a sneaky move):\n"
        "  Skip the advice and escalate their exact joke one step further.\n"
        "  * Tweet: 'When bro says we\\'re cooked for the exam but I\\'ve been studying in secret'\n"
        "    Reply: 'lying to your own study partner\\'s face just to ruin the curve is nasty work'\n"
        "  * Tweet: 'dropped my phone on my nose this is what I get for doomscrolling instead of studying'\n"
        "    Reply: 'even gravity is intervening on behalf of your gpa at this point'\n\n"
        "STRICT CONSTRAINTS:\n"
        "- 1 sentence (or 2 very short clauses), 35 to 140 characters total.\n"
        "- Zero preachy advice, zero 'you got this' clichés, zero SAT words, zero hashtags, zero @mentions, zero emojis.\n"
        "- Output ONLY the raw reply text (or SKIP)."
    )

    # #3: Vision "Easter-Egg" Pass when the target tweet has an attached photo
    if has_image and media_urls:
        try:
            vision_resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json={
                    "model": "meta-llama/llama-4-scout-17b-16e-instruct",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": (
                                        f"Tweet caption: \"{clean_tweet}\"\n"
                                        f"{avoid_replies_block}\n"
                                        "Look closely at the attached image. Spot ONE specific detail in the photo (e.g., open tabs, "
                                        "what's on their screen/desk, drinks, handwriting, clock time, messy notes) and write a deadpan "
                                        "1-sentence reply or specific question about that detail (35-135 chars) that makes the author reply back, "
                                        "or output SKIP if off-topic:"
                                    )
                                },
                                {"type": "image_url", "image_url": {"url": media_urls[0]}}
                            ]
                        }
                    ],
                    "temperature": 0.68
                },
                timeout=15
            )
            if vision_resp.status_code == 200:
                v_reply = (vision_resp.json()["choices"][0]["message"].get("content") or "").strip().strip("\"'")
                if v_reply.upper().startswith("SKIP"):
                    print("[AI Reply Vision] Vision gate marked image tweet as off-topic (SKIP).")
                    return None
                v_lower = v_reply.lower()
                if (
                    not any(v_lower.startswith(s) for s in BANNED_REPLY_STARTERS)
                    and not any(c in v_lower for c in BANNED_REPLY_CLICHES)
                    and is_reply_unique(v_reply, recent_replies or [])[0]
                    and 25 <= len(v_reply) <= 180
                    and "#" not in v_reply
                    and "http" not in v_reply
                    and "@" not in v_reply
                ):
                    print("  👁 [Vision Peer Reply] Generated using live image detail inspection!")
                    return v_reply
        except Exception:
            pass

    user_prompt = (
        f"Tweet:\n\"{clean_tweet}\"\n"
        f"{avoid_replies_block}\n"
        "Write a sharp, tweet-specific 1-sentence peer reply (either a deadpan follow-up question about their exact situation "
        "that baits the author into replying back, or a playful escalation of their joke — ZERO motivational lecturing, 35-140 chars), "
        "or output SKIP if off-topic:"
    )

    # Use models enabled in the Groq project with separate TPM pools (120b -> 20b -> compound-mini)
    primary_model = ai_config.groq_model or "openai/gpt-oss-120b"
    if primary_model == "openai/gpt-oss-20b":
        primary_model = "openai/gpt-oss-120b"
    candidate_models = [primary_model, "openai/gpt-oss-120b", "openai/gpt-oss-20b", "groq/compound-mini"]
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
                "temperature": 0.72
            }
            if model.startswith("openai/gpt-oss"):
                payload["reasoning_effort"] = "low"

            try:
                response = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=15
                )

                if response.status_code == 200:
                    data = response.json()
                    reply = (data["choices"][0]["message"].get("content") or "").strip()
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

                    if 25 <= len(reply) <= 200 and "#" not in reply and "http" not in reply and "@" not in reply:
                        return reply
                    else:
                        print(f"[AI Reply] Reply failed quality/length check ({len(reply)} chars): '{reply}'. Retrying...")
                elif response.status_code == 429:
                    print(f"[AI Reply] Model '{model}' hit Groq 429 rate limit; switching to next model pool...")
                    time.sleep(2.0)
                    break
                else:
                    print(f"[AI Reply] Groq error on '{model}' ({response.status_code}): {response.text}")
                    break

            except Exception as e:
                print(f"[AI Reply] Exception calling Groq ({model}): {e}")
                time.sleep(1)

    return None


def generate_quote_tweet_commentary(
    tweet_text: str,
    author_name: str = "",
    recent_replies: Optional[List[Dict[str, Any]]] = None,
    retries: int = 3,
    media_urls: Optional[List[str]] = None
) -> Optional[str]:
    """
    Generate a scroll-stopping Quote-Tweet written 100% FOR the target tweet/photo:
    - #1 Chameleon Mode: Escalates the joke, calls out the unspoken behavior, or drops a sharp micro hot-take
      with ZERO forced motivational lecturing.
    - #3 Vision Easter-Egg Zoom-In: When quoting a photo, calls out one specific background detail in the image
      so viewers pause and tap/zoom into the photo (spiking Dwell Time + Photo Expands).
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

    has_image = bool(media_urls and len(media_urls) > 0)
    image_instruction = (
        "- This tweet has a photo attached below your text. Do NOT summarize their caption—write a punchy 1-liner "
        "that makes people look twice at the image.\n"
        if has_image else ""
    )

    system_prompt = (
        "You run a viral, deadpan X account that Quote-Tweets posts from students, developers, and procrastinators.\n\n"
        "CRITICAL RULE — NO FORCED MOTIVATIONAL LESSONS:\n"
        "- NEVER end your Quote-Tweet with a preachy motivational lesson ('survival mode is undefeated', 'how top grades are made', 'once the code runs').\n"
        "- Do NOT force every tweet into the same template. Write 100% FOR THIS SPECIFIC TWEET.\n\n"
        "STEP 1 — RELEVANCE GATE:\n"
        "If the tweet is a real personal post about procrastinating, studying, homework, coding, building, working, burnout, or deadlines, it PASSED.\n"
        "Output the exact single word SKIP if the tweet is unrelated or fake (sports, esports interviews, forex/crypto, fictional 'Lecturer: / Student:' skits, politics, or ads).\n\n"
        "STEP 2 — PICK THE SHARPEST VIRAL ANGLE FOR THIS TWEET (35 to 135 chars, casual lowercase human style):\n"
        "1. THE ESCALATION / PUNCHLINE (Best when the quoted tweet is a funny situation or meme):\n"
        "   Push their exact premise one step further without explaining the joke.\n"
        "   * Quoted: 'When bro says we\\'re cooked for the exam but I\\'ve been studying in secret'\n"
        "     Quote-Tweet: 'looking your friend dead in the eye and saying \"yeah man i haven\\'t started either\" when you\\'re on chapter 9 is cold blooded'\n"
        "2. THE 'IN YOUR WALLS' CALLOUT (Best when they are procrastinating or avoiding a task):\n"
        "   Call out the exact unspoken micro-behavior happening behind their tweet.\n"
        "   * Quoted: 'I should really keep catching up on my homework but I deadass have zero motivation'\n"
        "     Quote-Tweet: 'leaving the assignment tab open in the background for 6 hours so it spiritually counts as studying'\n"
        "   * Quoted: 'just cleaned my entire kitchen from top to bottom instead of starting my 5 page paper'\n"
        "     Quote-Tweet: 'nobody cleans their apartment faster than someone with a google doc titled Untitled document (3) open on their laptop'\n"
        "3. THE MICRO HOT-TAKE (Best when they mention a specific habit, tool, or study/work setup):\n"
        "   Drop a playfully opinionated observation about that exact activity that makes people quote-tweet or argue in the replies.\n"
        f"{image_instruction}"
        "STRICT CONSTRAINTS:\n"
        "- 1 sentence (35 to 135 chars). Casual, deadpan human phrasing.\n"
        "- Zero life-coach advice, zero hashtags, zero links, zero @mentions, no wrapping quotes.\n"
        "- Output ONLY the Quote-Tweet text (or SKIP)."
    )

    clean_tweet = re.sub(r"https?://\S+", "", tweet_text).strip()
    media_note = "\n[Note: This tweet has a photo attached right below your Quote-Tweet.]" if has_image else ""
    user_prompt = (
        f"Quoted Tweet:\n\"{clean_tweet}\"{media_note}\n\n"
        "Write a scroll-stopping 1-sentence Quote-Tweet (35-135 chars) written 100% FOR this specific tweet "
        "(escalate the bit, call out the unspoken behavior, or drop a sharp observation — ZERO preachy motivational morals), "
        "or output SKIP if off-topic:"
    )

    # #3: Vision "Easter Egg / Background Detail" Zoom-In when the quoted tweet has a photo
    if has_image and media_urls:
        try:
            vision_resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json={
                    "model": "meta-llama/llama-4-scout-17b-16e-instruct",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": (
                                        f"Quoted Tweet caption: \"{clean_tweet}\"\n"
                                        "Look at the attached photo. Do NOT summarize the caption. Spot ONE tiny specific background detail "
                                        "in the image (e.g., number of open browser tabs, battery %, empty cans/cups, messy handwriting, "
                                        "clock time, or a funny contrast between the photo and caption) and write a deadpan 1-liner "
                                        "(30-120 chars) calling out that visual detail so viewers tap and zoom into the image, "
                                        "or output SKIP if off-topic:"
                                    )
                                },
                                {"type": "image_url", "image_url": {"url": media_urls[0]}}
                            ]
                        }
                    ],
                    "temperature": 0.68
                },
                timeout=15
            )
            if vision_resp.status_code == 200:
                v_text = (vision_resp.json()["choices"][0]["message"].get("content") or "").strip().strip("\"'")
                if v_text.upper().startswith("SKIP"):
                    print("[AI Quote Vision] Vision gate marked image tweet as off-topic (SKIP).")
                    return None
                v_lower = v_text.lower()
                unique_ok, _ = is_reply_unique(v_text, recent_replies or [])
                if (
                    unique_ok
                    and not any(c in v_lower for c in BANNED_REPLY_CLICHES)
                    and 25 <= len(v_text) <= 180
                    and "#" not in v_text
                    and "http" not in v_text
                ):
                    print("  👁 [Vision Quote-Tweet] Generated Easter-Egg zoom-in from live image inspection!")
                    return v_text
        except Exception:
            pass

    primary_model = ai_config.groq_model or "openai/gpt-oss-120b"
    if primary_model == "openai/gpt-oss-20b":
        primary_model = "openai/gpt-oss-120b"
    candidate_models = [primary_model, "openai/gpt-oss-120b", "openai/gpt-oss-20b", "groq/compound-mini"]
    seen_models = set()
    models_to_try = [m for m in candidate_models if not (m in seen_models or seen_models.add(m))]

    for model in models_to_try:
        for _ in range(retries):
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.68
            }
            if model.startswith("openai/gpt-oss"):
                payload["reasoning_effort"] = "low"

            try:
                response = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=15
                )
                if response.status_code == 200:
                    qt_text = (response.json()["choices"][0]["message"].get("content") or "").strip().strip("\"'")
                    if qt_text.upper() == "SKIP" or qt_text.upper().startswith("SKIP"):
                        print("[AI Quote] LLM relevance gate marked tweet as off-topic (SKIP).")
                        return None
                    qt_lower = qt_text.lower()
                    if any(cliche in qt_lower for cliche in BANNED_REPLY_CLICHES):
                        print(f"[AI Quote] Rejected cliché in Quote-Tweet: '{qt_text}'. Retrying...")
                        continue
                    unique_ok, unique_reason = is_reply_unique(qt_text, recent_replies or [])
                    if not unique_ok:
                        print(f"[AI Quote] Rejected non-unique Quote-Tweet ({unique_reason}): '{qt_text}'. Retrying...")
                        continue
                    if 25 <= len(qt_text) <= 220 and "#" not in qt_text and "http" not in qt_text:
                        return qt_text
                    else:
                        print(f"[AI Quote] Quote-Tweet failed length/format check ({len(qt_text)} chars): '{qt_text}'. Retrying...")
                elif response.status_code == 429:
                    print(f"[AI Quote] Model '{model}' hit Groq 429 rate limit; switching to next model pool...")
                    time.sleep(2.0)
                    break
                else:
                    print(f"[AI Quote] Groq error on '{model}' ({response.status_code}): {response.text}")
                    break
            except Exception as e:
                print(f"[AI Quote] Exception calling Groq ({model}): {e}")
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

    for model in ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "groq/compound-mini"]:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.85
        }
        if model.startswith("openai/gpt-oss"):
            payload["reasoning_effort"] = "low"
        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=15
            )
            if response.status_code == 200:
                reply = (response.json()["choices"][0]["message"].get("content") or "").strip().strip("\"'")
                if 20 <= len(reply) <= 180 and "#" not in reply and "http" not in reply:
                    return reply
        except Exception:
            pass
    return None
