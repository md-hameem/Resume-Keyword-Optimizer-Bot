from nlp_engine import preprocess_text, suggestion_rules

WELCOME_MSG = "Hi! 👋 I'm your Resume Optimizer Bot. Paste a Job Description and your Resume below and click **Analyze**. Then ask me things like **what am I missing?**, **recommend improvements**, or **how do I add X?**"

def chatbot_reply(user_msg: str, last_analysis: dict | None):
    msg_p = preprocess_text(user_msg)

    if any(g in msg_p for g in ["hi", "hello", "hey"]):
        return WELCOME_MSG

    if "what am i missing" in msg_p or "missing" in msg_p or "keywords" in msg_p:
        if last_analysis and last_analysis.get("missing_ranked"):
            top = last_analysis["missing_ranked"][:10]
            return "Top missing (priority): " + ", ".join(top)
        elif last_analysis and last_analysis.get("missing_skills"):
            return "You're missing: " + ", ".join(last_analysis["missing_skills"])
        else:
            return "I don't have an analysis yet. Paste a job description and resume, then click **Analyze**."

    if "recommend" in msg_p or "improve" in msg_p or "how to add" in msg_p or "how do i add" in msg_p:
        if last_analysis:
            basis = last_analysis.get("missing_ranked", last_analysis.get("missing_skills", []))
            sug = suggestion_rules(basis)
            return "Here are some suggestions:\n- " + "\n- ".join(sug)
        else:
            return "First give me a job description + resume so I know what's missing."

    if "what can you do" in msg_p or "help" in msg_p:
        return "I compare the job description to your resume using an expanded keyword catalog, synonym normalization, and context-weighted n-gram TF-IDF (no LLM), then tell you what to add."

    return "Try: **what am I missing?** or **recommend improvements**. If you haven't yet, paste JD + Resume and click **Analyze**."
