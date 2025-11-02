import streamlit as st
import sqlite3
import hashlib
from datetime import datetime

DB_NAME = "data.db"

# ============ DB utils ============

def get_conn():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    return conn

def create_tables():
    conn = get_conn()
    c = conn.cursor()
    # users
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    # analyses (to store JD + resume per user)
    c.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            job_text TEXT,
            resume_text TEXT,
            created_at TEXT
        )
    """)
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

# NEW: save analysis
def save_analysis(user_id: int, job_text: str, resume_text: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO analyses(user_id, job_text, resume_text, created_at)
        VALUES(?, ?, ?, ?)
    """, (user_id, job_text, resume_text, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

# NEW: get latest analysis for a user
def get_latest_analysis(user_id: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT job_text, resume_text, created_at
        FROM analyses
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 1
    """, (user_id,))
    row = c.fetchone()
    conn.close()
    return row  # (job_text, resume_text, created_at) or None

# ============ Streamlit app ============

def main():
    st.set_page_config(page_title="Resume Keyword Optimizer", page_icon="🤖")

    create_tables()

    if "auth" not in st.session_state:
        st.session_state.auth = False
        st.session_state.user = None

    # ---- SIDEBAR AUTH ----
    st.sidebar.title("🔐 Account")
    auth_choice = st.sidebar.radio("Login / Sign Up", ["Login", "Sign Up"])

    if auth_choice == "Sign Up":
        new_user = st.sidebar.text_input("New username")
        new_pass = st.sidebar.text_input("New password", type="password")
        if st.sidebar.button("Create account"):
            if new_user and new_pass:
                try:
                    add_user(new_user, new_pass)
                    st.sidebar.success("Account created. You can login now.")
                except Exception:
                    st.sidebar.error("Username already exists.")
            else:
                st.sidebar.warning("Please fill both fields.")
    else:
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Login"):
            user = login_user(username, password)
            if user:
                st.session_state.auth = True
                st.session_state.user = user
                st.sidebar.success(f"Logged in as {user['username']}")
            else:
                st.sidebar.error("Invalid credentials")

    if st.session_state.auth:
        if st.sidebar.button("Logout"):
            st.session_state.auth = False
            st.session_state.user = None
            st.rerun()

    # ---- MAIN ----
    st.title("🤖 Resume Keyword Optimizer (MVP)")

    if not st.session_state.auth:
        st.info("Please login (or sign up) from the sidebar to use the tool.")
        return

    st.success(f"Welcome, {st.session_state.user['username']}! ✅")

    st.subheader("1. Job Description")
    job_desc = st.text_area("Job Description", height=160, placeholder="Paste the job post here...")

    st.subheader("2. Your Resume (text)")
    resume_txt = st.text_area("Resume", height=160, placeholder="Paste your resume text here...")

    if st.button("Save / Analyze"):
        if job_desc.strip() and resume_txt.strip():
            save_analysis(st.session_state.user["id"], job_desc, resume_txt)
            st.success("Saved! ✅ In the next step we'll actually analyze the text.")
        else:
            st.warning("Please paste both job description and resume.")

    st.divider()

    st.subheader("Your latest submission")
    latest = get_latest_analysis(st.session_state.user["id"])
    if latest:
        jd, res, created_at = latest
        st.write(f"**Last saved at:** {created_at}")
        with st.expander("View last job description"):
            st.write(jd)
        with st.expander("View last resume"):
            st.write(res)
    else:
        st.write("No analysis saved yet.")

if __name__ == "__main__":
    main()
