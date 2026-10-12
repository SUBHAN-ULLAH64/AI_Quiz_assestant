"""SQLite storage for users, quizzes, attempts, and per-topic adaptive stats."""
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path(__file__).resolve().parent / "data" / "quiz_master.sqlite3"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

DIFFICULTIES = ["easy", "medium", "hard"]

def connect():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with connect() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            topic TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            question_type TEXT NOT NULL,
            questions_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            quiz_id INTEGER NOT NULL,
            topic TEXT NOT NULL,
            question TEXT NOT NULL,
            question_type TEXT NOT NULL,
            student_answer TEXT NOT NULL,
            correct_answer TEXT NOT NULL,
            is_correct INTEGER NOT NULL,
            explanation TEXT NOT NULL,
            source_file TEXT NOT NULL,
            source_location TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(quiz_id) REFERENCES quizzes(id)
        );
        CREATE TABLE IF NOT EXISTS user_topic_stats (
            user_id INTEGER NOT NULL,
            topic TEXT NOT NULL,
            total_attempts INTEGER NOT NULL DEFAULT 0,
            correct_attempts INTEGER NOT NULL DEFAULT 0,
            correct_streak INTEGER NOT NULL DEFAULT 0,
            wrong_streak INTEGER NOT NULL DEFAULT 0,
            difficulty TEXT NOT NULL DEFAULT 'medium',
            PRIMARY KEY(user_id, topic),
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        """)

def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def get_or_create_user(username):
    username = username.strip()
    if not username:
        raise ValueError("Username cannot be empty.")
    if len(username) > 60:
        raise ValueError("Username must be 60 characters or fewer.")
    with connect() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO users(username, created_at) VALUES (?, ?)",
            (username, now_iso()),
        )
        row = conn.execute("SELECT id, username FROM users WHERE username = ?", (username,)).fetchone()
        return dict(row)

def get_usernames():
    with connect() as conn:
        return [r["username"] for r in conn.execute("SELECT username FROM users ORDER BY username")]

def get_topic_stats(user_id, topic):
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM user_topic_stats WHERE user_id=? AND topic=?",
            (user_id, topic),
        ).fetchone()
    if row:
        return dict(row)
    return {"user_id": user_id, "topic": topic, "total_attempts": 0,
            "correct_attempts": 0, "correct_streak": 0, "wrong_streak": 0,
            "difficulty": "medium"}

def save_quiz(user_id, topic, difficulty, question_type, questions):
    with connect() as conn:
        cursor = conn.execute(
            """INSERT INTO quizzes(user_id, topic, difficulty, question_type, questions_json, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, topic, difficulty, question_type,
             json.dumps(questions, ensure_ascii=False), now_iso()),
        )
        return cursor.lastrowid

def _next_difficulty(current, correct_streak, wrong_streak):
    idx = DIFFICULTIES.index(current if current in DIFFICULTIES else "medium")
    if correct_streak >= 3:
        idx = min(2, idx + 1)
        correct_streak = 0
    if wrong_streak >= 2:
        idx = max(0, idx - 1)
        wrong_streak = 0
    return DIFFICULTIES[idx], correct_streak, wrong_streak

def save_attempt(user_id, quiz_id, topic, question, question_type, student_answer,
                 correct_answer, is_correct, explanation, source_file, source_location):
    with connect() as conn:
        conn.execute(
            """INSERT INTO attempts
            (user_id, quiz_id, topic, question, question_type, student_answer,
             correct_answer, is_correct, explanation, source_file, source_location, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, quiz_id, topic, question, question_type, student_answer,
             correct_answer, int(is_correct), explanation, source_file, source_location, now_iso()),
        )
        row = conn.execute(
            "SELECT * FROM user_topic_stats WHERE user_id=? AND topic=?",
            (user_id, topic),
        ).fetchone()
        if row:
            total = row["total_attempts"] + 1
            correct_total = row["correct_attempts"] + int(is_correct)
            correct_streak = row["correct_streak"] + 1 if is_correct else 0
            wrong_streak = row["wrong_streak"] + 1 if not is_correct else 0
            difficulty = row["difficulty"]
        else:
            total = 1
            correct_total = int(is_correct)
            correct_streak = 1 if is_correct else 0
            wrong_streak = 0 if is_correct else 1
            difficulty = "medium"

        difficulty, correct_streak, wrong_streak = _next_difficulty(
            difficulty, correct_streak, wrong_streak
        )
        conn.execute(
            """INSERT INTO user_topic_stats
            (user_id, topic, total_attempts, correct_attempts, correct_streak, wrong_streak, difficulty)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, topic) DO UPDATE SET
            total_attempts=excluded.total_attempts,
            correct_attempts=excluded.correct_attempts,
            correct_streak=excluded.correct_streak,
            wrong_streak=excluded.wrong_streak,
            difficulty=excluded.difficulty""",
            (user_id, topic, total, correct_total, correct_streak, wrong_streak, difficulty),
        )

def get_dashboard_data(user_id):
    with connect() as conn:
        attempts = [dict(r) for r in conn.execute(
            "SELECT * FROM attempts WHERE user_id=? ORDER BY created_at, id", (user_id,)
        )]
        topics = [dict(r) for r in conn.execute(
            """SELECT topic, total_attempts, correct_attempts, difficulty
               FROM user_topic_stats WHERE user_id=? ORDER BY topic""", (user_id,)
        )]
        quizzes = [dict(r) for r in conn.execute(
            "SELECT id, topic, difficulty, question_type, created_at FROM quizzes WHERE user_id=? ORDER BY id DESC",
            (user_id,),
        )]
    return attempts, topics, quizzes
