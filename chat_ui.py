import streamlit.components.v1 as components

def _escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br>")
    )

def render_chat_iframe(chat_rows, height: int = 520):
    rows_html = []
    for role, message, ts in chat_rows:
        who = "You" if role == "user" else "Bot"
        cls = "you" if role == "user" else "bot"
        rows_html.append(f"""
        <div class="msg {cls}">
            <div class="bubble"><strong>{who}:</strong> {_escape_html(message)}</div>
        </div>
        """)
    html = f"""
    <html>
    <head>
        <meta charset="utf-8" />
        <style>
            body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Inter, Arial, sans-serif; }}
            .chat-window {{
                height: {height - 40}px;
                overflow-y: auto;
                padding: 10px 12px;
                border: 1px solid #eee;
                border-radius: 8px;
                background: #fafafa;
                box-sizing: border-box;
            }}
            .msg {{ margin: 8px 0; line-height: 1.35; }}
            .bubble {{ display: inline-block; padding: 8px 12px; border-radius: 12px; background: #f2f2f2; }}
            .msg.you .bubble {{ background: #e6f2ff; }}
            .msg.bot .bubble {{ background: #f5f5f5; }}
        </style>
    </head>
    <body>
        <div id="chat-window" class="chat-window">
            {''.join(rows_html)}
        </div>
        <script>
            const el = document.getElementById('chat-window');
            if (el) {{ el.scrollTop = el.scrollHeight; }}
        </script>
    </body>
    </html>
    """
    components.html(html, height=height, scrolling=True)
