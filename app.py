import streamlit as st
import sqlite3
import hashlib

# ============ DB utils ============

DB_NAME = "data.db"

def get_conn():
    # check_same_thread=False so Streamlit can reuse the connection
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    return conn

def create_tables():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
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

# ============ Streamlit app ============

def main():
    st.set_page_config(page_title="Resume Keyword Optimizer", page_icon="🤖")

    # create tables at start
    create_tables()

    # session init
    if "auth" not in st.session_state:
        st.session_state.auth = False
        st.session_state.user = None

    # sidebar auth
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
                except Exception as e:
                    st.sidebar.error("Username already exists.")
            else:
                st.sidebar.warning("Please fill both fields.")
    else:  # Login
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

    # logout button (only show if logged in)
    if st.session_state.auth:
        if st.sidebar.button("Logout"):
            st.session_state.auth = False
            st.session_state.user = None
            st.rerun()

    # ============ MAIN PAGE ============
    st.title("🤖 Resume Keyword Optimizer (MVP)")

    if not st.session_state.auth:
        st.info("Please login (or sign up) from the sidebar to use the tool.")
        return

    # if logged in, show the real app
    st.success(f"Welcome, {st.session_state.user['username']}! ✅")

    st.subheader("1. Job Description")
    job_desc = st.text_area("Job Description", height=180, placeholder="Paste the job post here...")

    st.subheader("2. Your Resume (text)")
    resume_txt = st.text_area("Resume", height=180, placeholder="Paste your resume text here...")

    if st.button("Analyze (will work in Step 4)"):
        st.info("Logged in ✅. In the next step we’ll add NLP to compare them.")

if __name__ == "__main__":
    main()
