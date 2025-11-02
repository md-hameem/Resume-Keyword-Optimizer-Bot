
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
    # analyses (create basic first)
    c.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            job_text TEXT,
            resume_text TEXT,
            created_at TEXT
        )
    """)
    # add result_text column if missing
    c.execute("PRAGMA table_info(analyses)")
    cols = [row[1] for row in c.fetchall()]
    if "result_text" not in cols:
        c.execute("ALTER TABLE analyses ADD COLUMN result_text TEXT")

    # chats table (user_id, role, message, ts)
    c.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            role TEXT,
            message TEXT,
            ts TEXT
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
        SELECT id, job_text, resume_text, result_text, created_at
        FROM analyses
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 1
    """, (user_id,))
    row = c.fetchone()
    conn.close()
    return row

# NEW: list past analyses
def list_analyses(user_id: int, limit: int = 20):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT id, created_at
        FROM analyses
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
    """, (user_id, limit))
    rows = c.fetchall()
    conn.close()
    return rows  # list of (id, created_at)

# NEW: get analysis by id
def get_analysis_by_id(analysis_id: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT id, job_text, resume_text, result_text, created_at
        FROM analyses
        WHERE id = ?
    """, (analysis_id,))
    row = c.fetchone()
    conn.close()
    return row

# ===== chat persistence =====
def save_chat(user_id: int, role: str, message: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO chats(user_id, role, message, ts)
        VALUES(?, ?, ?, ?)
    """, (user_id, role, message, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def load_chat(user_id: int, limit: int = 60):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT role, message, ts
        FROM chats
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
    """, (user_id, limit))
    rows = c.fetchall()
    conn.close()
    return rows[::-1]

# ====================== NLP utils (Enhanced) ======================

STOPWORDS = {
    "the","a","an","of","to","in","for","on","and","or","with","at","by",
    "is","it","this","that","from","as","are","be","we","you","your","our",
    "i","me","my","they","their","them","was","were","will","would","can",
    "could","should","has","have","had","do","does","did","not","no","yes",
    "but","so","if","then","than","into","over","under","about","across",
    "per","via","using"
}

# Expanded set of skills/tools (canonical lower-case)
COMMON_SKILLS = [
    # Programming / DS
    "python","java","c++","c","c#","go","rust","scala","javascript","typescript",
    "r","matlab","sql","mysql","postgresql","sqlite","nosql","mongodb","redis",
    "html","css","sass","less",
    # Data / ML
    "machine learning","deep learning","nlp","computer vision","data analysis",
    "data visualization","statistics","probability","feature engineering",
    "time series","recommendation systems","ab testing",
    # Libraries / Frameworks
    "numpy","pandas","scikit-learn","tensorflow","pytorch","keras","xgboost",
    "lightgbm","prophet","opencv","nltk","spacy","hugging face","transformers",
    "matplotlib","plotly","power bi","tableau","seaborn",
    # Backend / APIs
    "rest api","graphql","fastapi","flask","django","spring","node","express",
    "microservices","grpc","rabbitmq","kafka",
    # Cloud / DevOps
    "aws","azure","gcp","docker","kubernetes","terraform","ansible","airflow",
    "spark","hadoop","databricks","snowflake","redshift","bigquery","athena",
    "jenkins","git","github","gitlab","ci cd","ci/cd",
    # Analytics / BI / Tools
    "excel","power query","powerpoint","jira","confluence","visio","miro",
    # Mobile / UI
    "react","nextjs","vue","angular","figma","adobe xd","ux","ui","responsive design",
    # Soft skills
    "communication","teamwork","leadership","problem solving","stakeholder management",
    "mentoring","presentation","collaboration","documentation",
    # Data Eng / MLOps
    "etl","elt","data pipeline","orchestration","model deployment","mlops","feature store",
    # Product / CRM / ERP
    "salesforce","sap","oracle","workday"
]

# Simple synonym map -> canonical skill (all lower-case)
SKILL_SYNONYMS = {
    "tf": "tensorflow",
    "tf2": "tensorflow",
    "torch": "pytorch",
    "sklearn": "scikit-learn",
    "sci-kit learn": "scikit-learn",
    "ms excel": "excel",
    "microsoft excel": "excel",
    "ms powerpoint": "powerpoint",
    "power-bi": "power bi",
    "g suite": "google workspace",
    "gsuite": "google workspace",
    "postgres": "postgresql",
    "sql server": "sql",
    "rest": "rest api",
    "restful": "rest api",
    "react.js": "react",
    "node.js": "node",
    "next.js": "nextjs",
    "ui/ux": "ux",
    "communication skills": "communication",
    "problem-solving": "problem solving",
    "ci cd": "ci/cd",
    "continuous integration": "ci/cd",
    "continuous delivery": "ci/cd",
    "ml": "machine learning",
    "dl": "deep learning",
    "nlp (natural language processing)": "nlp"
}

def preprocess_text(txt: str):
    txt = txt.lower()
    txt = txt.translate(str.maketrans('', '', string.punctuation))
    txt = re.sub(r"\s+", " ", txt)
    return txt.strip()

def tokenize(txt: str):
    txt = preprocess_text(txt)
    tokens = [t for t in txt.split() if t not in STOPWORDS]
    return tokens

def simple_stem(token: str):
    # ultra-light stemming for fuzzy matching
    for suf in ["ing","ed","ly","ies","s"]:
        if token.endswith(suf) and len(token) > len(suf) + 2:
            return token[:-len(suf)]
    return token

def ngrams(tokens, n=2):
    return [" ".join(tokens[i:i+n]) for i in range(len(tokens)-n+1)]

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
        idf[t] = math.log((N + 1) / (d + 1)) + 1
    return idf

def build_token_space(text: str, use_ngrams=True):
    # create 1-3 gram token space for better keyword extraction
    docs = split_docs(text)
    all_docs_tokens = []
    for d in docs:
        toks = tokenize(d)
        if use_ngrams:
            grams = toks + ngrams(toks,2) + ngrams(toks,3)
            all_docs_tokens.append(grams)
        else:
            all_docs_tokens.append(toks)
    return all_docs_tokens

def tfidf_keywords_manual(text: str, top_k=20):
    docs_tokens = build_token_space(text, use_ngrams=True)
    idf = inverse_doc_freq(docs_tokens)

    scores = {}
    for doc_tokens in docs_tokens:
        tf = term_freq(doc_tokens)
        for term, tf_val in tf.items():
            scores[term] = scores.get(term, 0.0) + tf_val * idf.get(term, 0.0)

    # penalize very short generic terms
    for term in list(scores.keys()):
        if len(term) <= 2:
            scores[term] *= 0.5

    sorted_terms = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    # filter out stopwords again + too generic
    filtered = [t for t,_ in sorted_terms if t not in STOPWORDS][:top_k]
    return filtered

def normalize_skill(term: str):
    t = preprocess_text(term)
    if t in SKILL_SYNONYMS:
        t = SKILL_SYNONYMS[t]
    return t

def skill_in_text(text_p: str, skill: str):
    # check presence by direct phrase, synonyms, and light stemming
    skill = normalize_skill(skill)
    if skill in text_p:
        return True
    # check stemmed token overlap for multi-word skills
    skill_tokens = [simple_stem(t) for t in skill.split()]
    text_tokens = [simple_stem(t) for t in text_p.split()]
    if all(s in text_tokens for s in skill_tokens):
        return True
    return False

def extract_skills_from_text(text: str):
    text_p = preprocess_text(text)
    found = set()
    # direct and synonym lookup
    for skill in COMMON_SKILLS:
        if skill_in_text(text_p, skill):
            found.add(normalize_skill(skill))
    # also scan synonyms keys explicitly
    for syn, canon in SKILL_SYNONYMS.items():
        if skill_in_text(text_p, syn):
            found.add(canon)
    return sorted(list(found))

def compare_job_and_resume(job_text, resume_text):
    job_skills = set(extract_skills_from_text(job_text))
    resume_skills = set(extract_skills_from_text(resume_text))

    jd_keywords = set(tfidf_keywords_manual(job_text, top_k=24))

    # Only keep JD keywords that look like skill-ish ngrams (heuristic)
    jd_skillish = {kw for kw in jd_keywords if any(
        k in kw for k in [
            "python","sql","api","ml","data","learning","cloud","docker","kuber",
            "pipeline","model","pandas","spark","aws","azure","gcp","react","java",
            "ci","cd","testing","deployment","analytics","analysis","visualization",
            "communication","leadership","etl","airflow","kafka","git"
        ]
    ) or kw in COMMON_SKILLS}

    job_all = job_skills.union(jd_skillish)

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
        if skill in ["python", "java", "sql", "excel", "power bi", "tableau", "pandas", "numpy"]:
            suggestions.append(f"Add **{skill}** under a 'Technical Skills' section or inside a relevant experience bullet.")
        elif skill in ["tensorflow","pytorch","scikit-learn","mlops","airflow","docker","kubernetes"]:
            suggestions.append(f"Include **{skill}** in a 'Tools' line for your ML project, and show a concrete outcome (e.g., accuracy, latency).")
        elif "communication" in skill or "presentation" in skill or "leadership" in skill:
            suggestions.append("Add a soft-skills bullet: “Strong written and verbal communication; led cross-functional demos and stakeholder updates.”")
        else:
            suggestions.append(f"Mention **{skill}** in a project / coursework / experience bullet if you used it.")
    if not suggestions:
        suggestions.append("Your resume already covers the main keywords. You can still mirror the exact wording from the job post.")
    return suggestions

# ====================== Chatbot logic ======================

WELCOME_MSG = "Hi! 👋 I'm your Resume Optimizer Bot. Paste a Job Description and your Resume below and click **Analyze**. Then ask me things like **what am I missing?**, **recommend improvements**, or **how do I add X?**"

def chatbot_reply(user_msg: str, last_analysis: dict | None):
    msg_p = preprocess_text(user_msg)

    if any(g in msg_p for g in ["hi", "hello", "hey"]):
        return WELCOME_MSG

    if "what am i missing" in msg_p or "missing" in msg_p or "keywords" in msg_p:
        if last_analysis and last_analysis.get("missing_skills"):
            return "You're missing: " + ", ".join(last_analysis["missing_skills"])
        else:
            return "I don't have an analysis yet. Paste a job description and resume, then click **Analyze**."

    if "recommend" in msg_p or "improve" in msg_p or "how to add" in msg_p or "how do i add" in msg_p:
        if last_analysis:
            sug = suggestion_rules(last_analysis.get("missing_skills", []))
            return "Here are some suggestions:\n- " + "\n- ".join(sug)
        else:
            return "First give me a job description + resume so I know what's missing."

    if "what can you do" in msg_p or "help" in msg_p:
        return "I compare the job description to your resume using expanded keyword matching + n-gram TF-IDF, then tell you what to add."

    return "Try: **what am I missing?** or **recommend improvements**. If you haven't yet, paste JD + Resume and click **Analyze**."

# ====================== Streamlit app ======================

def main():
    st.set_page_config(page_title="Resume Keyword Optimizer", page_icon="🤖", layout="wide")
    create_tables()

    if "auth" not in st.session_state:
        st.session_state.auth = False
        st.session_state.user = None

    if "last_analysis" not in st.session_state:
        st.session_state["last_analysis"] = None

    if "jd_text" not in st.session_state:
        st.session_state["jd_text"] = ""

    if "resume_text" not in st.session_state:
        st.session_state["resume_text"] = ""

    if "chat_input" not in st.session_state:
        st.session_state["chat_input"] = ""

    # ---- SIDEBAR ----
    st.sidebar.title("🔐 Account")

    if not st.session_state.auth:
        auth_choice = st.sidebar.radio("Login / Sign Up", ["Login", "Sign Up"], horizontal=True)

        if auth_choice == "Sign Up":
            new_user = st.sidebar.text_input("New username")
            new_pass = st.sidebar.text_input("New password", type="password")
            if st.sidebar.button("Create account", use_container_width=True):
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
            if st.sidebar.button("Login", use_container_width=True):
                user = login_user(username, password)
                if user:
                    st.session_state.auth = True
                    st.session_state.user = user
                    st.sidebar.success(f"Logged in as {user['username']}")
                    st.rerun()
                else:
                    st.sidebar.error("Invalid credentials")

    else:
        # Logged-in view: greet + logout + quick keywords
        st.sidebar.success(f"👋 Hello, {st.session_state.user['username']}")
        if st.sidebar.button("Logout", type="primary", use_container_width=True):
            st.session_state.auth = False
            st.session_state.user = None
            st.session_state["last_analysis"] = None
            st.session_state["jd_text"] = ""
            st.session_state["resume_text"] = ""
            st.session_state["chat_input"] = ""
            st.rerun()

        st.sidebar.markdown("---")
        st.sidebar.subheader("💡 Chat keywords")
        kw_cols = st.sidebar.columns(2)
        kws = [
            "what am i missing?",
            "recommend improvements",
            "how do i add python?",
            "help",
            "show suggestions",
            "missing keywords"
        ]
        for i, kw in enumerate(kws):
            if (kw_cols[i % 2]).button(kw.title() if i < 2 else kw, key=f"kw_{i}"):
                st.session_state["chat_input"] = kw
                st.experimental_rerun()

    # ---- MAIN ----
    st.title("🤖 Resume Keyword Optimizer")

    if not st.session_state.auth:
        st.info("Please login (or sign up) from the sidebar to use the tool.")
        return

    user_id = st.session_state.user["id"]

    # Layout: Left = Chat + Analyze form, Right = History + Latest Saved
    col_left, col_right = st.columns([2, 1], gap="large")

    with col_left:
        st.subheader("💬 Chat with the Optimizer")
        st.caption("The bot will use your latest analysis. Provide a Job Description and your Resume below, then click **Analyze**.")

        with st.expander("📝 Provide Job Description & Resume", expanded=True):
            st.session_state["jd_text"] = st.text_area("Job Description", value=st.session_state.get("jd_text",""), height=160, placeholder="Paste the job post here...")
            st.session_state["resume_text"] = st.text_area("Your Resume (text)", value=st.session_state.get("resume_text",""), height=160, placeholder="Paste your resume text here...")

            analyze_clicked = st.button("Analyze", type="primary")
            if analyze_clicked:
                jd = st.session_state["jd_text"].strip()
                rs = st.session_state["resume_text"].strip()
                if jd and rs:
                    analysis = compare_job_and_resume(jd, rs)
                    result_text = (
                        f"Job skills: {', '.join(analysis['job_skills'])}\n"
                        f"Resume skills: {', '.join(analysis['resume_skills'])}\n"
                        f"Missing skills: {', '.join(analysis['missing_skills'])}\n"
                    )
                    save_analysis(user_id, jd, rs, result_text)
                    st.session_state["last_analysis"] = analysis

                    # Drop a bot message into chat summarizing
                    summary = []
                    summary.append(f"**Analysis complete ✅**")
                    summary.append(f"**Missing:** {len(analysis['missing_skills'])} → " + (", ".join(analysis['missing_skills']) if analysis['missing_skills'] else "None 🎉"))
                    summary.append(f"**Present:** {len(analysis['present_skills'])}")
                    summary.append(f"**Extra:** {len(analysis['extra_skills'])}")
                    sug = suggestion_rules(analysis['missing_skills'])
                    summary.append("\n**Suggestions:**\n- " + "\n- ".join(sug))

                    save_chat(user_id, "bot", "\n".join(summary))
                    st.success("Analysis complete and saved ✅")
                    st.rerun()
                else:
                    st.warning("Please paste both job description and resume.")

        # Chat history
        chat_rows = load_chat(user_id, limit=60)
        for role, message, ts in chat_rows:
            if role == "user":
                st.markdown(f"**You:** {message}")
            else:
                st.markdown(f"**Bot:** {message}")

        # Chat input
        user_msg = st.text_input("Your message", key="chat_input")
        if st.button("Send"):
            if user_msg.strip():
                save_chat(user_id, "user", user_msg)
                last_analysis = st.session_state.get("last_analysis")
                bot_msg = chatbot_reply(user_msg, last_analysis)
                save_chat(user_id, "bot", bot_msg)
                st.rerun()

    with col_right:
        st.subheader("🗂️ History")
        analyses_list = list_analyses(user_id, limit=30)
        if analyses_list:
            labels = [f"{aid} — {created_at.split('T')[0]}" for (aid, created_at) in analyses_list]
            selected_label = st.selectbox("Past analyses", labels)
            selected_id = int(selected_label.split(" — ")[0])
            if st.button("Load selected"):
                row = get_analysis_by_id(selected_id)
                if row:
                    _id, jd, res, res_txt, created_at = row
                    analysis = compare_job_and_resume(jd, res)
                    st.session_state["last_analysis"] = analysis
                    st.success(f"Loaded analysis from {created_at}")
                    st.write("**Job description (preview):**")
                    st.write(jd[:300] + "..." if len(jd) > 300 else jd)
                    st.write("**Resume (preview):**")
                    st.write(res[:300] + "..." if len(res) > 300 else res)
        else:
            st.write("No history yet.")

        st.divider()
        st.subheader("📌 Your latest saved analysis")
        latest = get_latest_analysis(user_id)
        if latest:
            _id, jd, res, res_txt, created_at = latest
            st.write(f"**Last saved at:** {created_at}")
            # quick metrics based on recompute (keeps schema simple)
            a = compare_job_and_resume(jd, res)
            m1, m2, m3 = st.columns(3)
            m1.metric("Missing", len(a["missing_skills"]))
            m2.metric("Present", len(a["present_skills"]))
            m3.metric("Extra", len(a["extra_skills"]))

            with st.expander("Missing (add these!)", expanded=False):
                st.write(", ".join(a["missing_skills"]) or "None 🎉")
            with st.expander("Detected JD keywords"):
                st.write(", ".join(a["job_skills"]) or "—")
            with st.expander("Your resume keywords"):
                st.write(", ".join(a["resume_skills"]) or "—")
            with st.expander("Extra in your resume"):
                st.write(", ".join(a["extra_skills"]) or "—")
        else:
            st.write("No analysis saved yet.")

    # Footer
    st.caption("Tip: After analyzing, ask the bot to recommend improvements or how to add a specific skill.")

if __name__ == "__main__":
    main()
