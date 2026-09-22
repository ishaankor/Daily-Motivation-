"""AI Quote & Content Generator using Groq with strict Twitter 280-character validation."""

import json
import os
import random
import time
from typing import Dict, Any, List, Optional
import requests

from bot.config import ai_config, paths

DAY_THEMES = {
    0: ("Motivation Monday", "Relentless Ambition, Grit, and Momentum"),
    1: ("Stoic Tuesday", "Stoic Wisdom, Composure, and Mental Discipline"),
    2: ("Wisdom Wednesday", "Timeless Life Lessons, Humility, and Truth"),
    3: ("Tenacity Thursday", "Perseverance, Overcoming Obstacles, and Resilience"),
    4: ("Focus Friday", "Deep Work, Craftsmanship, and Execution"),
    5: ("Success Saturday", "Leadership, Innovation, and Entrepreneurship"),
    6: ("Sunday Reset", "Reflection, Clarity, and Weekly Mental Renewal")
}

FALLBACK_CATALOG = [
    {
        "id": "stoic_1",
        "quote": "We suffer more often in imagination than in reality.",
        "author": "Seneca",
        "category": "STOIC WISDOM",
        "theme": "Stoic Tuesday",
        "takeaways": [
            "Focus only on what you control.",
            "Never assume malice when exhausted.",
            "Fear is interest on an unpaid debt."
        ],
        "prompt": "Which one do you struggle with most?",
        "axiom": "Control your perceptions, command your peace.",
        "backstory": "Seneca was exiled to Corsica for 8 years. Instead of breaking down, he wrote treatises on emotional composure that leaders still study 2,000 years later.",
        "times_posted": 0,
        "last_posted": None
    },
    {
        "id": "discipline_1",
        "quote": "You have power over your mind—not outside events. Realize this, and you will find strength.",
        "author": "Marcus Aurelius",
        "category": "DISCIPLINE",
        "theme": "Wisdom Wednesday",
        "takeaways": [
            "Acknowledge what is outside your control.",
            "Master your internal dialogue.",
            "Respond with reason, not emotion."
        ],
        "prompt": "What's one thing you need to let go of today?",
        "axiom": "Master your internal response to dominate external reality.",
        "backstory": "Marcus Aurelius journaled his Meditations while leading armies on the northern Roman frontier, writing reminders to remain humble and grounded.",
        "times_posted": 0,
        "last_posted": None
    },
    {
        "id": "execution_1",
        "quote": "Action cures fear. Indecision and delay fertilize it.",
        "author": "David Schwartz",
        "category": "EXECUTION",
        "theme": "Focus Friday",
        "takeaways": [
            "Start before you feel fully ready.",
            "Action produces clarity, not thinking.",
            "Break mountains into 5-minute steps."
        ],
        "prompt": "What have you been postponing that you can start today?",
        "axiom": "Clarity is the byproduct of action, not passive thinking.",
        "backstory": "David Schwartz observed that the single trait separating top achievers from average performers was the speed with which they translated ideas into tangible motion.",
        "times_posted": 0,
        "last_posted": None
    },
    {
        "id": "ambition_1",
        "quote": "The only place where success comes before work is in the dictionary.",
        "author": "Vidal Sassoon",
        "category": "AMBITION",
        "theme": "Motivation Monday",
        "takeaways": [
            "Embrace the unglamorous hours of practice.",
            "Results lag effort by months; keep going.",
            "Compounding happens when nobody is watching."
        ],
        "prompt": "Are you putting in the quiet work today?",
        "axiom": "Results lag effort by months; maintain relentless momentum.",
        "backstory": "Vidal Sassoon grew up in a London orphanage before apprenticing for years without pay, eventually revolutionizing the entire hair styling and salon industry worldwide.",
        "times_posted": 0,
        "last_posted": None
    },
    {
        "id": "sunday_reset_1",
        "quote": "He who has a why to live can bear almost any how.",
        "author": "Friedrich Nietzsche",
        "category": "SUNDAY RESET",
        "theme": "Sunday Reset",
        "takeaways": [
            "Audit where your time leaked last week.",
            "Clarify your singular weekly priority.",
            "Protect your focus before Monday."
        ],
        "prompt": "What is your #1 focus this week?",
        "axiom": "Win the upcoming week before Monday morning arrives.",
        "backstory": "Nietzsche believed true mental resilience stems from an unbreakable purpose that renders any external hardship bearable.",
        "times_posted": 0,
        "last_posted": None
    }
]


def format_tweet_1(entry: Dict[str, Any]) -> str:
    """Format the primary tweet (Quote + 3 Takeaways + Discussion Prompt)."""
    t1 = entry["takeaways"][0]
    t2 = entry["takeaways"][1]
    t3 = entry["takeaways"][2]
    
    # Clean author format
    author_str = entry["author"]
    quote_str = entry["quote"].strip('\"')
    
    is_sunday = "SUNDAY" in entry.get("theme", "").upper()
    shift_header = "Sunday Reset: 3 mental shifts before Monday:" if is_sunday else "3 mental shifts to apply today:"

    tweet = (
        f'"{quote_str}" — {author_str}\n\n'
        f"{shift_header}\n"
        f"1. {t1}\n"
        f"2. {t2}\n"
        f"3. {t3}\n\n"
        f"{entry['prompt']} 🧵👇"
    )
    return tweet


def format_tweet_2(entry: Dict[str, Any]) -> str:
    """Format the secondary auto-reply tweet (Historical Backstory)."""
    backstory = entry.get("backstory", "").strip()
    is_sunday = "SUNDAY" in entry.get("theme", "").upper()
    header = "💡 Sunday Reflection & Backstory:" if is_sunday else "💡 The Backstory:"
    footer = "Weekly alignment • @MotivationFTD 🎯" if is_sunday else "Daily mindset • @MotivationFTD 🎯"

    tweet = (
        f"{header}\n\n"
        f"{backstory}\n\n"
        f"{footer}"
    )
    return tweet


def validate_character_limits(entry: Dict[str, Any]) -> bool:
    """Ensure both tweets strictly fit within Twitter's 280-character limit."""
    t1 = format_tweet_1(entry)
    t2 = format_tweet_2(entry)
    len_t1 = len(t1)
    len_t2 = len(t2)
    
    valid = (len_t1 <= 280) and (len_t2 <= 280)
    if not valid:
        print(f"[Validation Warning] Tweet 1: {len_t1}/280 chars, Tweet 2: {len_t2}/280 chars")
    return valid


def generate_quote_with_groq(theme_name: str, theme_desc: str, retries: int = 3) -> Optional[Dict[str, Any]]:
    """Call Groq API to generate an authentic mindset quote and actionable structure."""
    if not ai_config.groq_api_key:
        print("[AI Generator] No GROQ_API_KEY set. Falling back to local catalog.")
        return None

    headers = {
        "Authorization": f"Bearer {ai_config.groq_api_key}",
        "Content-Type": "application/json"
    }

    system_prompt = (
        "You are an elite cognitive psychology, philosophy, and mindset curator. "
        "Your task is to provide an authentic, famous quote and translate it into 3 actionable takeaways. "
        "CRITICAL CONSTRAINT: To fit Twitter's 280-character limit, follow these word limits strictly:\n"
        "- \"quote\": Famous inspirational quote (max 12 words, authentic, attributed correctly)\n"
        "- \"author\": Author full name\n"
        "- \"category\": 2-word uppercase theme (e.g. \"STOIC RESILIENCE\", \"DAILY FOCUS\")\n"
        "- \"takeaways\": Exactly 3 strings. Each string MUST be 4 to 6 words ONLY! (Ultra-punchy actionable advice)\n"
        "- \"axiom\": 1 memorable core rule or mental model (max 10 words, e.g. \"Effort is the singular variable 100% in your command.\")\n"
        "- \"prompt\": Engaging question under 35 characters (e.g. \"Which one do you need most?\")\n"
        "- \"backstory\": 2 short sentences explaining the historical context (max 180 characters total)\n\n"
        "Return ONLY a JSON object with these exact keys."
    )

    user_prompt = (
        f"Generate an authentic quote for '{theme_name}' ({theme_desc}). "
        f"Choose from respected historical thinkers, leaders, or philosophers. "
        f"Respond ONLY in valid JSON."
    )

    # Avoid 20b which has a known json_validate_failed issue on Groq
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
                "temperature": 0.7
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
                    
                    parsed["id"] = f"ai_{int(time.time())}_{random.randint(100, 999)}"
                    parsed["theme"] = theme_name
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
    """Manages the local quotes database and persistence."""

    def __init__(self, file_path: str = paths.catalog_path):
        self.file_path = file_path
        self.catalog: List[Dict[str, Any]] = []
        self.load()

    def load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self.catalog = json.load(f)
            except Exception as e:
                print(f"[Catalog] Error loading {self.file_path}: {e}")
                self.catalog = list(FALLBACK_CATALOG)
        else:
            self.catalog = list(FALLBACK_CATALOG)
            self.save()

    def save(self):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.catalog, f, indent=2, ensure_ascii=False)

    def get_entry_for_today(self, weekday_idx: int) -> Dict[str, Any]:
        """Fetch or generate a quote matching today's weekday theme."""
        theme_name, theme_desc = DAY_THEMES.get(weekday_idx, ("Daily Wisdom", "General Inspiration"))

        # 1. Try to generate a fresh one via Groq
        generated = generate_quote_with_groq(theme_name, theme_desc)
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

    def prefill_batch(self, count: int = 7) -> int:
        """Pre-generate N quotes using Groq and store in the catalog."""
        added = 0
        for i in range(count):
            weekday_idx = i % 7
            theme_name, theme_desc = DAY_THEMES[weekday_idx]
            print(f"[Prefill] Generating quote {i+1}/{count} for {theme_name}...")
            entry = generate_quote_with_groq(theme_name, theme_desc)
            if entry:
                self.catalog.append(entry)
                added += 1
            time.sleep(1)
        self.save()
        print(f"[Prefill] Successfully added {added} new quotes to catalog!")
        return added


BANNED_REPLY_STARTERS = (
    "honestly,", "honestly ", "totally,", "totally ", "so true,", "so true ",
    "i agree,", "i completely agree,", "it sounds like", "as someone who",
    "remember,", "remember that", "that is the most", "it's the most",
    "take a deep breath", "as they say"
)

BANNED_REPLY_CLICHES = [
    "future self", "listen to your body", "give yourself permission",
    "heavy mental load", "take a deep breath", "it's okay to not be okay",
    "mental static", "prescription for", "nourish the soul", "doormat",
    "crush it"
]


def generate_human_reply(tweet_text: str, author_name: str = "", retries: int = 2) -> Optional[str]:
    """
    Generate a gentle, casual, and warmly motivational peer reply.
    Observational and reassuring without giving bossy commands or aggressive advice.
    """
    if not ai_config.groq_api_key:
        print("[AI Reply] No GROQ_API_KEY set.")
        return None

    headers = {
        "Authorization": f"Bearer {ai_config.groq_api_key}",
        "Content-Type": "application/json"
    }

    system_prompt = (
        "You are the voice of Daily Motivation (@MotivationFTD) on X (Twitter).\n"
        "Your tone is CASUAL, GENTLE, GROUNDED, and WARM. NEVER ASSERTIVE, BOSSY, OR AGGRESSIVE.\n\n"
        "MISSION: Offer quiet encouragement, reassurance, or a gentle reframe like a thoughtful friend nodding along on the timeline.\n\n"
        "CRITICAL RULES — AVOID BEING TOO ASSERTIVE:\n"
        "- NO DIRECT COMMANDS: Never tell them what to do (avoid: 'do it', 'go do X', 'stop doing Y', 'skip the grind', 'wake up ready to crush it', 'be a doormat').\n"
        "- NO AGGRESSIVE HYPE: Don't push people to 'grind' or 'crush it' when they are exhausted. Avoid exclamation marks (!).\n"
        "- GENTLE OBSERVATIONS: Instead of giving orders, share a warm, grounded perspective or quiet validation.\n"
        "- NO THERAPIST SPEAK: Never say 'give yourself permission', 'your future self will thank you', 'heavy mental load', 'listen to your body'.\n"
        "- NO ESSAY METAPHORS: Never say 'mental static', 'prescription for exhaustion', 'nourish the soul'.\n"
        "- NO CORNY OPENERS: Never start with 'Honestly,', 'Totally,', 'So true,', 'I agree,'.\n\n"
        "AUTHENTIC GENTLE EXAMPLES:\n"
        "- Tweet: 'I have coffee and a good breakfast but I am still dragging ass today. mentally exhausted. need a nature reset.'\n"
        "  Reply: 'sometimes the body just needs to slow way down before it can go again. hope you get that peaceful reset you need'\n"
        "- Tweet: 'all I want is comfort food and sleep today'\n"
        "  Reply: 'there is no guilt in trading productivity for a warm meal and good sleep. recharge days are just as important as the work'\n"
        "- Tweet: 'struggling to stay consistent with my morning routine lately. feel like I fell off.'\n"
        "  Reply: 'the days you miss don\\'t erase all the days you showed up. it\\'s always just one morning at a time'\n"
        "- Tweet: 'hard to stay focused today'\n"
        "  Reply: 'some days the focus just isn\\'t there and that\\'s okay. even moving the needle an inch still counts'\n"
        "- Tweet: 'building in public is tough'\n"
        "  Reply: 'the building phase is always quiet and slow. proud of you for showing up even when it\\'s tough'\n"
        "- Tweet: 'drained from work'\n"
        "  Reply: 'hope you get to unplug tonight and get some quiet time. you need that energy for the things that matter to you'\n\n"
        "FORMAT & STYLE:\n"
        "- Casual, conversational lowercase or relaxed casing.\n"
        "- 1 to 2 short sentences (50 to 125 characters).\n"
        "- Output ONLY the reply text itself. No quotes, no hashtags, no links."
    )

    clean_tweet = tweet_text.strip()
    user_prompt = f"Tweet from {author_name or 'someone'}:\n\"{clean_tweet}\"\n\nWrite a gentle, casual, non-assertive motivational reply:"

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
                "max_tokens": 150
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
                    # Strip wrapping quotes if LLM added them
                    if (reply.startswith('"') and reply.endswith('"')) or (reply.startswith("'") and reply.endswith("'")):
                        reply = reply[1:-1].strip()

                    reply_lower = reply.lower().strip()

                    # Enforce anti-bot filters
                    if any(reply_lower.startswith(starter) for starter in BANNED_REPLY_STARTERS):
                        print(f"[AI Reply] Rejected banned starter in reply: '{reply}'. Retrying...")
                        continue

                    if any(cliche in reply_lower for cliche in BANNED_REPLY_CLICHES):
                        print(f"[AI Reply] Rejected cliché in reply: '{reply}'. Retrying...")
                        continue

                    if 15 <= len(reply) <= 220 and "#" not in reply and "http" not in reply:
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

