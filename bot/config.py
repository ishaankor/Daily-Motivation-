"""Centralized configuration module for the Daily Motivation Twitter Bot."""

import os
import sys
from dataclasses import dataclass
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load .env file from the project root
load_dotenv(os.path.join(BASE_DIR, ".env"))


@dataclass(frozen=True)
class TwitterConfig:
    api_key: str = os.getenv("API_KEY", "")
    api_secret_key: str = os.getenv("API_SECRET_KEY", "")
    bearer_token: str = os.getenv("API_BEARER_TOKEN", "")
    access_token: str = os.getenv("API_ACCESS_TOKEN", "")
    access_token_secret: str = os.getenv("API_SECRET_ACCESS_TOKEN", "")
    client_id: str = os.getenv("CLIENT_ID", "")
    client_secret: str = os.getenv("CLIENT_SECRET", "")
    account_id: str = os.getenv("ACCOUNT_ID", "")
    handle: str = os.getenv("HANDLE", "@MotivationFTD")
    engagement_max_age_hours: float = float(os.getenv("ENGAGEMENT_MAX_AGE_HOURS", "12.0"))


@dataclass(frozen=True)
class DatabaseConfig:
    host: str = os.getenv("DB_HOST", "aws-1-us-west-1.pooler.supabase.com")
    port: int = int(os.getenv("DB_PORT", "6543"))
    name: str = os.getenv("DB_NAME", "postgres")
    user: str = os.getenv("DB_USER", "postgres.xprikamuiprhvovypaoi")
    password: str = os.getenv("DB_PASSWORD", "")
    sqlite_path: str = os.path.join(BASE_DIR, "bot_history.db")


@dataclass(frozen=True)
class AIConfig:
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    fallback_model: str = "qwen/qwen3.8-27b"


@dataclass(frozen=True)
class PathConfig:
    base_dir: str = BASE_DIR
    catalog_path: str = os.path.join(BASE_DIR, "quotes_catalog.json")
    nebula_bg: str = os.path.join(BASE_DIR, "purple-nebula.jpg")
    starry_bg: str = os.path.join(
        BASE_DIR,
        "starry-night-sky-dark-blue-space-black-and-purple-galaxy-with-cosmic-light-of-planets-shiny-astrology-constellations-with-sparkles-winter-fantasy-gradient-bac.jpg"
    )
    output_dir: str = os.path.join(BASE_DIR, "output")


twitter_config = TwitterConfig()
db_config = DatabaseConfig()
ai_config = AIConfig()
paths = PathConfig()

# Ensure output directory exists
os.makedirs(paths.output_dir, exist_ok=True)
