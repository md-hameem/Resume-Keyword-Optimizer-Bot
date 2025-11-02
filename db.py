import sqlite3
import hashlib
from datetime import datetime

DB_NAME = "data.db"

def get_conn():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def create_tables():
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            job_text TEXT,
            resume_text TEXT,
            created_at TEXT
        )"""
    )
    c.execute("PRAGMA table_info(analyses)")
    cols = [row[1] for row in c.fetchall()]
    if "result_text" not in cols:
        c.execute("ALTER TABLE analyses ADD COLUMN result_text TEXT")

    c.execute(
        """CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            role TEXT,
            message TEXT,
            ts TEXT
        )"""
    )
    conn.commit()
    conn.close()

def make_hash(password: str):
    return hashlib.sha256(password.encode()).hexdigest()

def add_user(username: str, password: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO users(username, password) VALUES(?, ?)", (username, make_hash(password)))
    conn.commit()
    conn.close()

def login_user(username: str, password: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, username, password FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    if row:
        user_id, uname, hashed = row
        if hashed == make_hash(password):
            return {"id": user_id, "username": uname}
    return None

def save_analysis(user_id: int, job_text: str, resume_text: str, result_text: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        """INSERT INTO analyses(user_id, job_text, resume_text, result_text, created_at)
               VALUES(?, ?, ?, ?, ?)""",
        (user_id, job_text, resume_text, result_text, datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()

def get_latest_analysis(user_id: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        """SELECT id, job_text, resume_text, result_text, created_at
               FROM analyses WHERE user_id = ?
               ORDER BY id DESC LIMIT 1""",
        (user_id,)
    )
    row = c.fetchone()
    conn.close()
    return row

def list_analyses(user_id: int, limit: int = 20):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        """SELECT id, created_at FROM analyses
               WHERE user_id = ? ORDER BY id DESC LIMIT ?""",
        (user_id, limit)
    )
    rows = c.fetchall()
    conn.close()
    return rows

def get_analysis_by_id(analysis_id: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        """SELECT id, job_text, resume_text, result_text, created_at
               FROM analyses WHERE id = ?""",
        (analysis_id,)
    )
    row = c.fetchone()
    conn.close()
    return row

def save_chat(user_id: int, role: str, message: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        """INSERT INTO chats(user_id, role, message, ts)
               VALUES(?, ?, ?, ?)""",
        (user_id, role, message, datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()

def load_chat(user_id: int, limit: int = 100):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        """SELECT role, message, ts FROM chats
               WHERE user_id = ? ORDER BY id DESC LIMIT ?""" ,
        (user_id, limit)
    )
    rows = c.fetchall()
    conn.close()
    return rows[::-1]
