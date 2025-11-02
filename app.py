import streamlit as st
from datetime import datetime

from db import (
    create_tables, add_user, login_user,
    save_analysis, get_latest_analysis, list_analyses,
    get_analysis_by_id, save_chat, load_chat
)

from nlp_engine import compare_job_and_resume, suggestion_rules
from chat_ui import render_chat_iframe
from chatbot import chatbot_reply

def main():
    st.set_page_config(page_title="Resume Keyword Optimizer", page_icon="🤖", layout="wide")
    create_tables()

    # ---- Session ----
    for k, v in [
        ("auth", False),
        ("user", None),
        ("last_analysis", None),
        ("jd_text", ""),
        ("resume_text", ""),
        ("chat_input", ""),
    ]:
        if k not in st.session_state:
            st.session_state[k] = v

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
        st.sidebar.success(f"👋 Hello, {st.session_state.user['username']}")
        if st.sidebar.button("Logout", type="primary", use_container_width=True):
            for k in ["auth","user","last_analysis","jd_text","resume_text","chat_input"]:
                st.session_state[k] = None if k in ["user","last_analysis"] else ""
            st.session_state.auth = False
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
                jd = (st.session_state["jd_text"] or "").strip()
                rs = (st.session_state["resume_text"] or "").strip()
                if jd and rs:
                    analysis = compare_job_and_resume(jd, rs)
                    result_text = (
                        f"Job skills: {', '.join(analysis['job_skills'])}\n"
                        f"Resume skills: {', '.join(analysis['resume_skills'])}\n"
                        f"Missing skills: {', '.join(analysis['missing_skills'])}\n"
                    )
                    save_analysis(user_id, jd, rs, result_text)
                    st.session_state["last_analysis"] = analysis

                    top_missing = analysis.get("missing_ranked", analysis["missing_skills"])[:10]
                    summary = []
                    summary.append(f"**Analysis complete ✅**")
                    summary.append(f"**Top missing (priority):** " + (", ".join(top_missing) if top_missing else "None 🎉"))
                    summary.append(f"**Present:** {len(analysis['present_skills'])}")
                    summary.append(f"**Extra:** {len(analysis['extra_skills'])}")
                    sug = suggestion_rules(top_missing if top_missing else [])
                    if sug:
                        summary.append("\n**Suggestions:**\n- " + "\n- ".join(sug))

                    save_chat(user_id, "bot", "\n".join(summary))
                    st.success("Analysis complete and saved ✅")
                    st.rerun()
                else:
                    st.warning("Please paste both job description and resume.")

        # Scrollable chat window
        chat_rows = load_chat(user_id, limit=150)
        render_chat_iframe(chat_rows, height=520)

        # Chat input
        user_msg = st.text_input("Your message", key="chat_input")
        if st.button("Send"):
            if (user_msg or "").strip():
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
            a = compare_job_and_resume(jd, res)
            m1, m2, m3 = st.columns(3)
            m1.metric("Missing", len(a["missing_skills"]))
            m2.metric("Present", len(a["present_skills"]))
            m3.metric("Extra", len(a["extra_skills"]))

            with st.expander("Top priority to add", expanded=True):
                top = a.get("missing_ranked", a["missing_skills"])[:12]
                st.write(", ".join(top) or "None 🎉")

            with st.expander("Missing (full list)", expanded=False):
                st.write(", ".join(a["missing_skills"]) or "None 🎉")

            with st.expander("Detected JD keywords"):
                st.write(", ".join(a["job_skills"]) or "—")
            with st.expander("Your resume keywords"):
                st.write(", ".join(a["resume_skills"]) or "—")
            with st.expander("Extra in your resume"):
                st.write(", ".join(a["extra_skills"]) or "—")
        else:
            st.write("No analysis saved yet.")

    st.caption("No LLM used. Keywords powered by catalog + synonym normalization + context-weighted n-gram TF-IDF.")

if __name__ == "__main__":
    main()
