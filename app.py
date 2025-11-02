import streamlit as st
import sqlite3
import hashlib
from datetime import datetime
import re
import math
import string

DB_NAME = "data.db"

# ====================== DB utils ======================

def get_conn():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    return conn

def create_tables():
    conn = get_conn()
    c = conn.cursor()
    # users table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    # analyses table
    c.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            job_text TEXT,
            resume_text TEXT,
            result_text TEXT,
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

def save_analysis(user_id: int, job_text: str, resume_text: str, result_text: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO analyses(user_id, job_text, resume_text, result_text, created_at)
        VALUES(?, ?, ?, ?, ?)
    """, (user_id, job_text, resume_text, result_text, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def get_latest_analysis(user_id: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT job_text, resume_text, result_text, created_at
        FROM analyses
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 1
    """, (user_id,))
    row = c.fetchone()
    conn.close()
    return row  # (job_text, resume_text, result_text, created_at) or None

# ====================== NLP utils ======================

STOPWORDS = {
    "the","a","an","of","to","in","for","on","and","or","with","at","by",
    "is","it","this","that","from","as","are","be","we","you","your","our"
}

COMMON_SKILLS = [
    "python", "java", "c++", "javascript", "react", "node", "django", "flask",
    "sql", "mysql", "postgresql", "excel", "power bi", "tableau",
    "machine learning", "deep learning", "data analysis", "data visualization",
    "communication", "teamwork", "problem solving", "git", "github",
    "html", "css", "docker", "kubernetes", "rest api"
]

def preprocess_text(txt: str):
    txt = txt.lower()
    txt = txt.translate(str.maketrans('', '', string.punctuation))
    txt = re.sub(r"\s+", " ", txt)
    return txt.strip()

def tokenize(txt: str):
    txt = preprocess_text(txt)
    tokens = [t for t in txt.split() if t not in STOPWORDS]
    return tokens

def split_docs(text: str):
    parts = re.split(r"[.\n]", text)
    docs = [p.strip() for p in parts if p.strip()]
    if not docs:
        docs = [text.strip()]
    return docs

def term_freq(doc_tokens):
    tf = {}
    for t in doc_tokens:
        tf[t] = tf.get(t, 0) + 1
    total = len(doc_tokens)
    if total == 0:
        return {}
    for t in tf:
        tf[t] /= total
    return tf

def inverse_doc_freq(all_docs_tokens):
    N = len(all_docs_tokens)
    df = {}
    for doc in all_docs_tokens:
        for t in set(doc):
            df[t] = df.get(t, 0) + 1
    idf = {}
    for t, d in df.items():
        idf[t] = math.log((N + 1) / (d + 1)) + 1  # smoothed
    return idf

def tfidf_keywords_manual(text: str, top_k=10):
    docs = split_docs(text)
    docs_tokens = [tokenize(d) for d in docs]
    idf = inverse_doc_freq(docs_tokens)

    scores = {}
    for doc_tokens in docs_tokens:
        tf = term_freq(doc_tokens)
        for term, tf_val in tf.items():
            scores[term] = scores.get(term, 0.0) + tf_val * idf.get(term, 0.0)

    sorted_terms = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [t for t, _ in sorted_terms[:top_k]]

def extract_skills_from_text(text: str):
    text_p = preprocess_text(text)
    found = []
    for skill in COMMON_SKILLS:
        if skill in text_p:
            found.append(skill)
    return sorted(list(set(found)))

def compare_job_and_resume(job_text, resume_text):
    job_skills = set(extract_skills_from_text(job_text))
    resume_skills = set(extract_skills_from_text(resume_text))

    jd_keywords = set(tfidf_keywords_manual(job_text, top_k=12))

    job_all = job_skills.union(jd_keywords)

    missing = job_all - resume_skills
    present = job_all & resume_skills
    extra = resume_skills - job_all

    return {
        "job_skills": sorted(list(job_all)),
        "resume_skills": sorted(list(resume_skills)),
        "missing_skills": sorted(list(missing)),
        "present_skills": sorted(list(present)),
        "extra_skills": sorted(list(extra))
    }

def suggestion_rules(missing_skills):
    suggestions = []
    for skill in missing_skills:
        if skill in ["python", "java", "sql", "excel", "power bi", "tableau"]:
            suggestions.append(f"Add **{skill}** under a 'Technical Skills' section or inside a relevant experience bullet.")
        elif "communication" in skill:
            suggestions.append("Add a soft-skills bullet: “Strong written and verbal communication”.")
        else:
            suggestions.append(f"Mention **{skill}** in a project / coursework / experience bullet if you used it.")
    if not suggestions:
        suggestions.append("Your resume already covers the main keywords. You can still mirror the exact wording from the job post.")
    return suggestions

# ====================== Streamlit app ======================

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

    if st.button("Analyze"):
        if job_desc.strip() and resume_txt.strip():
            analysis = compare_job_and_resume(job_desc, resume_txt)
            # make a readable text to save
            result_text = (
                f"Job skills: {', '.join(analysis['job_skills'])}\n"
                f"Resume skills: {', '.join(analysis['resume_skills'])}\n"
                f"Missing skills: {', '.join(analysis['missing_skills'])}\n"
            )
            save_analysis(st.session_state.user["id"], job_desc, resume_txt, result_text)

            st.success("Analysis complete ✅")

            st.subheader("Detected job keywords")
            st.write(", ".join(analysis["job_skills"]) or "—")

            st.subheader("Your resume keywords")
            st.write(", ".join(analysis["resume_skills"]) or "—")

            st.subheader("Missing (add these!)")
            if analysis["missing_skills"]:
                st.write(", ".join(analysis["missing_skills"]))
            else:
                st.write("None 🎉")

            st.subheader("Extra in your resume")
            st.write(", ".join(analysis["extra_skills"]) or "—")

            st.subheader("Suggestions")
            for s in suggestion_rules(analysis["missing_skills"]):
                st.write("- " + s)

            # store latest analysis in session for chatbot (next step)
            st.session_state["last_analysis"] = analysis

        else:
            st.warning("Please paste both job description and resume.")

    st.divider()
    st.subheader("Your latest saved analysis")
    latest = get_latest_analysis(st.session_state.user["id"])
    if latest:
        jd, res, res_txt, created_at = latest
        st.write(f"**Last saved at:** {created_at}")
        with st.expander("Job description"):
            st.write(jd)
        with st.expander("Resume"):
            st.write(res)
        with st.expander("Raw analysis"):
            st.code(res_txt)
    else:
        st.write("No analysis saved yet.")

if __name__ == "__main__":
    main()
