# Resume Keyword Optimizer (No LLM)

Modularized Streamlit app for comparing a job description and resume using a large keyword catalog + synonym normalization + context-weighted n-gram TF-IDF.

## Files
- `app.py` — Streamlit entry point
- `db.py` — SQLite helpers (users, analyses, chat)
- `nlp_engine.py` — All keyword/NLP logic (no LLM)
- `chat_ui.py` — Scrollable chat iframe renderer
- `chatbot.py` — Simple rule-based chatbot

## Run
```bash
pip install streamlit
streamlit run app.py
```

> Tip: Run from inside this directory so local imports work.
