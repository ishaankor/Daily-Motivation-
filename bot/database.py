"""Database layer supporting Supabase PostgreSQL with seamless local SQLite fallback."""

import os
import sqlite3
import time
from typing import Dict, Any, List, Optional
try:
    import psycopg2
except ImportError:
    psycopg2 = None

from bot.config import db_config


class DatabaseManager:
    """Manages database connections, table creation, and post history logging."""

    def __init__(self):
        self.use_sqlite = False
        self.init_database()

    def get_postgres_connection(self):
        """Attempt connection to Supabase PostgreSQL pooler."""
        if not psycopg2:
            return None
        try:
            conn = psycopg2.connect(
                host=db_config.host,
                port=db_config.port,
                user=db_config.user,
                password=db_config.password,
                database=db_config.name,
                connect_timeout=6
            )
            conn.autocommit = True
            return conn
        except Exception as e:
            print(f"[Database] PostgreSQL connection failed ({e}). Falling back to local SQLite.")
            return None

    def get_sqlite_connection(self):
        """Open or create local SQLite database."""
        conn = sqlite3.connect(db_config.sqlite_path)
        return conn

    def init_database(self):
        """Create tables in PostgreSQL or SQLite."""
        pg_conn = self.get_postgres_connection()
        if pg_conn:
            try:
                with pg_conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS tweet_history (
                            id SERIAL PRIMARY KEY,
                            tweet_id TEXT UNIQUE,
                            reply_tweet_id TEXT,
                            quote TEXT NOT NULL,
                            author TEXT NOT NULL,
                            category TEXT,
                            theme TEXT,
                            style_used TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                        CREATE TABLE IF NOT EXISTS bot_replies (
                            id SERIAL PRIMARY KEY,
                            target_tweet_id TEXT UNIQUE,
                            target_user_id TEXT,
                            target_screen_name TEXT,
                            original_tweet_text TEXT,
                            reply_tweet_id TEXT,
                            reply_text TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """)
                pg_conn.close()
                print("[Database] Connected & initialized Supabase PostgreSQL tables.")
                return
            except Exception as e:
                print(f"[Database] Failed initializing PostgreSQL schema: {e}")

        # Fallback to SQLite
        self.use_sqlite = True
        sq_conn = self.get_sqlite_connection()
        with sq_conn:
            sq_conn.execute("""
                CREATE TABLE IF NOT EXISTS tweet_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tweet_id TEXT UNIQUE,
                    reply_tweet_id TEXT,
                    quote TEXT NOT NULL,
                    author TEXT NOT NULL,
                    category TEXT,
                    theme TEXT,
                    style_used TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            sq_conn.execute("""
                CREATE TABLE IF NOT EXISTS bot_replies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target_tweet_id TEXT UNIQUE,
                    target_user_id TEXT,
                    target_screen_name TEXT,
                    original_tweet_text TEXT,
                    reply_tweet_id TEXT,
                    reply_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
        sq_conn.close()
        print(f"[Database] Initialized local SQLite database at: {db_config.sqlite_path}")

    def log_post(
        self,
        tweet_id: str,
        reply_tweet_id: Optional[str],
        entry: Dict[str, Any],
        style_used: str
    ) -> bool:
        """Record a successful post in the database."""
        quote = entry.get("quote", "")
        author = entry.get("author", "")
        category = entry.get("category", "")
        theme = entry.get("theme", "")

        # Try PostgreSQL first if not forced SQLite
        if not self.use_sqlite:
            pg_conn = self.get_postgres_connection()
            if pg_conn:
                try:
                    with pg_conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO tweet_history 
                            (tweet_id, reply_tweet_id, quote, author, category, theme, style_used)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (tweet_id) DO NOTHING;
                        """, (tweet_id, reply_tweet_id, quote, author, category, theme, style_used))
                    pg_conn.close()
                    print(f"[Database] Logged tweet {tweet_id} to Supabase PostgreSQL.")
                    return True
                except Exception as e:
                    print(f"[Database] Failed logging to PostgreSQL: {e}. Falling back to SQLite.")

        # Fallback logging to SQLite
        try:
            sq_conn = self.get_sqlite_connection()
            with sq_conn:
                sq_conn.execute("""
                    INSERT OR IGNORE INTO tweet_history 
                    (tweet_id, reply_tweet_id, quote, author, category, theme, style_used)
                    VALUES (?, ?, ?, ?, ?, ?, ?);
                """, (tweet_id, reply_tweet_id, quote, author, category, theme, style_used))
            sq_conn.close()
            print(f"[Database] Logged tweet {tweet_id} to local SQLite.")
            return True
        except Exception as e:
            print(f"[Database] Error logging to SQLite: {e}")
            return False

    def get_recent_history(self, limit: int = 7) -> List[Dict[str, Any]]:
        """Retrieve the most recent N posts for weekly review or analytics."""
        results = []
        if not self.use_sqlite:
            pg_conn = self.get_postgres_connection()
            if pg_conn:
                try:
                    with pg_conn.cursor() as cur:
                        cur.execute("""
                            SELECT tweet_id, quote, author, category, theme, style_used, created_at
                            FROM tweet_history
                            ORDER BY created_at DESC
                            LIMIT %s;
                        """, (limit,))
                        rows = cur.fetchall()
                        for r in rows:
                            results.append({
                                "tweet_id": r[0],
                                "quote": r[1],
                                "author": r[2],
                                "category": r[3],
                                "theme": r[4],
                                "style": r[5],
                                "created_at": str(r[6])
                            })
                    pg_conn.close()
                    return results
                except Exception as e:
                    print(f"[Database] Error reading PostgreSQL history: {e}")

        # Fallback to SQLite
        try:
            sq_conn = self.get_sqlite_connection()
            cur = sq_conn.cursor()
            cur.execute("""
                SELECT tweet_id, quote, author, category, theme, style_used, created_at
                FROM tweet_history
                ORDER BY created_at DESC
                LIMIT ?;
            """, (limit,))
            rows = cur.fetchall()
            for r in rows:
                results.append({
                    "tweet_id": r[0],
                    "quote": r[1],
                    "author": r[2],
                    "category": r[3],
                    "theme": r[4],
                    "style": r[5],
                    "created_at": str(r[6])
                })
            sq_conn.close()
        except Exception as e:
            print(f"[Database] Error reading SQLite history: {e}")

        return results

    def has_replied_to_tweet(self, tweet_id: str) -> bool:
        """Check if we have already replied to this specific tweet."""
        if not tweet_id:
            return False

        if not self.use_sqlite:
            pg_conn = self.get_postgres_connection()
            if pg_conn:
                try:
                    with pg_conn.cursor() as cur:
                        cur.execute("SELECT 1 FROM bot_replies WHERE target_tweet_id = %s LIMIT 1;", (str(tweet_id),))
                        found = cur.fetchone() is not None
                    pg_conn.close()
                    return found
                except Exception as e:
                    print(f"[Database] Error checking tweet in PostgreSQL: {e}")

        try:
            sq_conn = self.get_sqlite_connection()
            cur = sq_conn.cursor()
            cur.execute("SELECT 1 FROM bot_replies WHERE target_tweet_id = ? LIMIT 1;", (str(tweet_id),))
            found = cur.fetchone() is not None
            sq_conn.close()
            return found
        except Exception as e:
            print(f"[Database] Error checking tweet in SQLite: {e}")
            return False

    def has_replied_to_user(self, screen_name: str, days: int = 30) -> bool:
        """Check if we have replied to this user within the last N days (cooldown)."""
        if not screen_name:
            return False
        clean_handle = screen_name.lstrip("@").lower()

        if not self.use_sqlite:
            pg_conn = self.get_postgres_connection()
            if pg_conn:
                try:
                    with pg_conn.cursor() as cur:
                        cur.execute("""
                            SELECT 1 FROM bot_replies 
                            WHERE LOWER(target_screen_name) = %s 
                              AND created_at >= NOW() - INTERVAL '%s days'
                            LIMIT 1;
                        """, (clean_handle, days))
                        found = cur.fetchone() is not None
                    pg_conn.close()
                    return found
                except Exception as e:
                    print(f"[Database] Error checking user in PostgreSQL: {e}")

        try:
            sq_conn = self.get_sqlite_connection()
            cur = sq_conn.cursor()
            cur.execute("""
                SELECT 1 FROM bot_replies 
                WHERE LOWER(target_screen_name) = ? 
                  AND created_at >= datetime('now', '-' || ? || ' days')
                LIMIT 1;
            """, (clean_handle, days))
            found = cur.fetchone() is not None
            sq_conn.close()
            return found
        except Exception as e:
            print(f"[Database] Error checking user in SQLite: {e}")
            return False

    def log_reply(
        self,
        target_tweet_id: str,
        target_user_id: str,
        target_screen_name: str,
        original_tweet_text: str,
        reply_tweet_id: Optional[str],
        reply_text: str
    ) -> bool:
        """Record an engagement reply in the database."""
        clean_handle = (target_screen_name or "").lstrip("@")

        if not self.use_sqlite:
            pg_conn = self.get_postgres_connection()
            if pg_conn:
                try:
                    with pg_conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO bot_replies 
                            (target_tweet_id, target_user_id, target_screen_name, original_tweet_text, reply_tweet_id, reply_text)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (target_tweet_id) DO NOTHING;
                        """, (
                            str(target_tweet_id),
                            str(target_user_id or ""),
                            clean_handle,
                            original_tweet_text[:1000] if original_tweet_text else "",
                            str(reply_tweet_id or ""),
                            reply_text
                        ))
                    pg_conn.close()
                    print(f"[Database] Logged reply to @{clean_handle} in Supabase PostgreSQL.")
                    return True
                except Exception as e:
                    print(f"[Database] Failed logging reply to PostgreSQL: {e}. Falling back to SQLite.")

        try:
            sq_conn = self.get_sqlite_connection()
            with sq_conn:
                sq_conn.execute("""
                    INSERT OR IGNORE INTO bot_replies 
                    (target_tweet_id, target_user_id, target_screen_name, original_tweet_text, reply_tweet_id, reply_text)
                    VALUES (?, ?, ?, ?, ?, ?);
                """, (
                    str(target_tweet_id),
                    str(target_user_id or ""),
                    clean_handle,
                    original_tweet_text[:1000] if original_tweet_text else "",
                    str(reply_tweet_id or ""),
                    reply_text
                ))
            sq_conn.close()
            print(f"[Database] Logged reply to @{clean_handle} in local SQLite.")
            return True
        except Exception as e:
            print(f"[Database] Error logging reply to SQLite: {e}")
            return False

    def get_recent_replies(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve recent engagement replies."""
        results = []
        if not self.use_sqlite:
            pg_conn = self.get_postgres_connection()
            if pg_conn:
                try:
                    with pg_conn.cursor() as cur:
                        cur.execute("""
                            SELECT target_tweet_id, target_screen_name, original_tweet_text, reply_tweet_id, reply_text, created_at
                            FROM bot_replies
                            ORDER BY created_at DESC
                            LIMIT %s;
                        """, (limit,))
                        rows = cur.fetchall()
                        for r in rows:
                            results.append({
                                "target_tweet_id": r[0],
                                "target_screen_name": r[1],
                                "original_tweet_text": r[2],
                                "reply_tweet_id": r[3],
                                "reply_text": r[4],
                                "created_at": str(r[5])
                            })
                    pg_conn.close()
                    return results
                except Exception as e:
                    print(f"[Database] Error reading PostgreSQL replies: {e}")

        try:
            sq_conn = self.get_sqlite_connection()
            cur = sq_conn.cursor()
            cur.execute("""
                SELECT target_tweet_id, target_screen_name, original_tweet_text, reply_tweet_id, reply_text, created_at
                FROM bot_replies
                ORDER BY created_at DESC
                LIMIT ?;
            """, (limit,))
            rows = cur.fetchall()
            for r in rows:
                results.append({
                    "target_tweet_id": r[0],
                    "target_screen_name": r[1],
                    "original_tweet_text": r[2],
                    "reply_tweet_id": r[3],
                    "reply_text": r[4],
                    "created_at": str(r[5])
                })
            sq_conn.close()
        except Exception as e:
            print(f"[Database] Error reading SQLite replies: {e}")

        return results


db_manager = DatabaseManager()
