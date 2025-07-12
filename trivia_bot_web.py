# trivia_bot_web.py
import streamlit as st
import requests
import html
import random
import json
import os
import base64

# === Konfiguration ===
CONFIG_FILE = "config.json"
ICON_PATH = "resources/fs.ico"
BG_COLOR = "#2D74B2"
WHITE = "#FFFFFF"

# === Kategorien und Schwierigkeitsgrade ===
CATEGORIES = {
    "9": "General Knowledge",
    "18": "Science: Computers",
    "23": "History",
    "21": "Sports",
    "22": "Geography"
}
DIFFICULTIES = ["easy", "medium", "hard"]

# === Styling ===
# 👉 Sidebar-Farbe setzen und Fragebox-Hintergrund entfernen
CUSTOM_CSS = f"""
    <style>
    .stApp {{
        background-color: {WHITE};
    }}
    section[data-testid="stSidebar"] > div {{
        background-color: {BG_COLOR};
        color: white;
    }}
    .title-strip {{
        background-color: {BG_COLOR};
        color: white;
        padding: 0.7rem 1rem;
        font-size: 1.6rem;
        font-weight: bold;
        display: flex;
        align-items: center;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }}
    .question-box {{
        background-color: #2D74B2;
        color: white;
        padding: 0.7rem 1rem;
        border-radius: 0.5rem;
        font-size: 1.1rem;
        margin-bottom: 1rem;
    }}
    .stButton > button {{
        width: 100%;
        margin: 0.25rem 0;
    }}
    .stRadio > div {{
        background-color: #f5f5f5;
        padding: 0.2rem;
        border-radius: 0.3rem;
        margin-top: -10px; /* optional zusätzlicher Abstand nach oben */
    }}
    .stRadio label:hover {{
        background-color: #dbe9f6;
    }}
    </style>
"""
st.set_page_config(page_title="Trivia Bot Web", page_icon=ICON_PATH)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# === Icon einlesen und Base64 enkodieren ===
def get_icon_base64(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        return None

icon_base64 = get_icon_base64(ICON_PATH)

# === Persistenzfunktionen ===
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f)

# === Initialisierung ===
if "user" not in st.session_state:
    config = load_config()
    st.session_state.user = config.get("user", "Gast")
    st.session_state.category = config.get("category", "9")
    st.session_state.difficulty = config.get("difficulty", "easy")
    st.session_state.score = 0
    st.session_state.right = 0
    st.session_state.wrong = 0
    st.session_state.wrong_questions = []
    st.session_state.current = None
    st.session_state.mode = "normal"

# === Sidebar ===
st.sidebar.markdown(f"## 👤 Benutzerprofil")
user = st.sidebar.text_input("Wie heißt du?", st.session_state.user)
st.session_state.user = user

st.sidebar.markdown("## ⚙️ Einstellungen")
cat_key = st.sidebar.selectbox("Kategorie", list(CATEGORIES.keys()), format_func=lambda k: CATEGORIES[k])
diff = st.sidebar.selectbox("Schwierigkeit", DIFFICULTIES)

st.session_state.category = cat_key
st.session_state.difficulty = diff

save_config({
    "user": user,
    "category": cat_key,
    "difficulty": diff
})

# === Frage laden ===
def fetch_question():
    url = f"https://opentdb.com/api.php?amount=1&type=multiple&category={st.session_state.category}&difficulty={st.session_state.difficulty}"
    resp = requests.get(url)
    data = resp.json()
    if data["response_code"] != 0:
        return None
    q = data["results"][0]
    question = html.unescape(q["question"])
    correct = html.unescape(q["correct_answer"])
    incorrects = [html.unescape(i) for i in q["incorrect_answers"]]
    choices = incorrects + [correct]
    random.shuffle(choices)
    return {"question": question, "correct": correct, "choices": choices}

# === Titelzeile mit Bild oder Fallback ===
if icon_base64:
    st.markdown(f"""<div class='title-strip'>
        <img src="data:image/x-icon;base64,{icon_base64}" width="24" height="24" style="margin-right: 10px;" />
        Trivia Bot Web-Version
    </div>""", unsafe_allow_html=True)
else:
    st.markdown(f"""<div class='title-strip'>
        🎯 Trivia Bot Web-Version
    </div>""", unsafe_allow_html=True)

# === Neue Frage Button ===
if st.button("➡️ Neue Frage"):
    st.session_state.current = fetch_question()
    st.session_state.answer_checked = False
    st.session_state.feedback = ""
    st.rerun()

# === Frage anzeigen ===
if st.session_state.mode == "repeat" and st.session_state.wrong_questions:
    current = st.session_state.wrong_questions.pop(0)
    st.session_state.current = current
    st.markdown("*Wiederholungsfrage:*")

if st.session_state.current is None:
    st.session_state.current = fetch_question()

if st.session_state.current:
    st.markdown("**Frage:**")
    st.markdown(f"<div class='question-box'>{st.session_state.current['question']}</div>", unsafe_allow_html=True)

    st.markdown("**Wähle deine Antwort:**")
    selected = st.radio("", st.session_state.current["choices"], index=None, key="answer")

if "answer_checked" not in st.session_state:
    st.session_state.answer_checked = False

# Button: Antwort prüfen
if st.button("Antwort prüfen") and selected:
    st.session_state.answer_checked = True
    if selected == st.session_state.current['correct']:
        st.session_state.feedback = "✅ Richtig beantwortet!"
        st.session_state.score += 1
        st.session_state.right += 1
    else:
        st.session_state.feedback = f"❌ Falsch! Richtige Antwort: {st.session_state.current['correct']}"
        st.session_state.wrong += 1
        st.session_state.wrong_questions.append(st.session_state.current)

# Feedback anzeigen
if st.session_state.get("answer_checked"):
    st.info(st.session_state.get("feedback", ""))

# === Trennlinie ===
st.markdown("---")

# === Steuerungs-Buttons ===
col1, col2 = st.columns(2)
with col1:
    if st.button("🔁 Falsche Fragen wiederholen"):
        if st.session_state.wrong_questions:
            st.session_state.mode = "repeat"
            st.rerun()
        else:
            st.warning("Keine falschen Fragen gespeichert.")
with col2:
    if st.button("📊 Statistik anzeigen"):
        st.info(
            f"👤 Benutzer: {st.session_state.user}\n"
            f"✅ Richtig: {st.session_state.right}\n"
            f"❌ Falsch: {st.session_state.wrong}\n"
            f"🏆 Punkte: {st.session_state.score}"
        )
