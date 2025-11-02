from db import get_user_name
from nlp_engine import preprocess_text, suggestion_rules

WELCOME_MSG = "Hi! 👋 I'm your Resume Optimizer Bot. Paste a Job Description and your Resume below and click **Analyze**. Then ask me things like **what am I missing?**, **recommend improvements**, or **how do I add X?**"

def chatbot_reply(user_msg: str, last_analysis: dict | None, user_id: int):
    # Fetch the user's name from the database
    user_name = get_user_name(user_id)

    msg_p = preprocess_text(user_msg)

    # Personalized Greeting
    if any(g in msg_p for g in ["hi", "hello", "hey"]):
        return f"Hello, {user_name}! 👋 I'm here to help you with your resume. Ask me anything, like **what am I missing?** or **recommend improvements**."

    # Missing skills
    if "what am i missing" in msg_p or "missing" in msg_p or "keywords" in msg_p:
        if last_analysis and last_analysis.get("missing_ranked"):
            top = last_analysis["missing_ranked"][:10]
            return f"{user_name}, here are the top missing skills in your resume: {', '.join(top)}"
        elif last_analysis and last_analysis.get("missing_skills"):
            return f"{user_name}, you're missing: {', '.join(last_analysis['missing_skills'])}"
        else:
            return f"{user_name}, I don't have an analysis yet. Paste a job description and resume, then click **Analyze**."

    # Recommendations
    if "recommend" in msg_p or "improve" in msg_p or "how to add" in msg_p or "how do i add" in msg_p:
        if last_analysis:
            sug = suggestion_rules(last_analysis.get("missing_ranked", last_analysis.get("missing_skills", [])))
            return f"Here are some personalized suggestions for you, {user_name}:\n- " + "\n- ".join(sug)
        else:
            return f"First give me a job description + resume so I know what's missing, {user_name}."

    # Help message
    if "what can you do" in msg_p or "help" in msg_p:
        return f"{user_name}, I compare the job description to your resume using an expanded keyword catalog, synonym normalization, and context-weighted n-gram TF-IDF (no LLM), then tell you what to add."

    # Default message
    return f"Try asking me, {user_name}: **what am I missing?** or **recommend improvements**. If you haven't yet, paste JD + Resume and click **Analyze**."
