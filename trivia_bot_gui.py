# trivia_bot_gui.py
# Lizenz: MIT
# Autor: Dein Name
# Beschreibung: Trivia-Quiz-GUI-App mit Benutzerprofilen, Statistik und Fehlerwiederholung

import requests
import html
import random
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import json
import os

# === Globale Zustände ===
score = 0
wrong_questions = []
asked_questions = set()
user_profile = "Gast"
right_count = 0
wrong_count = 0
CONFIG_FILE = "config.json"

# === Trivia API Kategorien ===
CATEGORIES = {
    "9": "General Knowledge",
    "18": "Science: Computers",
    "23": "History",
    "21": "Sports",
    "22": "Geography"
}

DIFFICULTIES = ["easy", "medium", "hard"]

# === GUI Klasse ===
class TriviaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Trivia Bot Advanced GUI")
        self.root.configure(bg="#2D74B2")
        self.root.iconbitmap('resources/fs.ico')
        self.root.minsize(500, 500)
        self.current_question = None

        self.load_config()

        self.user_label = tk.Label(root, text=f"Benutzer: {user_profile}", font=("Arial", 12), bg="#2D74B2", fg="white")
        self.user_label.pack(pady=5)

        self.score_label = tk.Label(root, text="Punkte: 0", font=("Arial", 12), bg="#2D74B2", fg="white")
        self.score_label.pack(pady=5)

        self.config_frame = tk.Frame(root, bg="#2D74B2")
        self.config_frame.pack(pady=5)

        # Kategorie Dropdown (oben)
        tk.Label(self.config_frame, text="Kategorie:", bg="#2D74B2", fg="white").pack(anchor="w")
        self.category_var = tk.StringVar(value=self.category)
        self.category_menu = ttk.Combobox(self.config_frame, textvariable=self.category_var, state="readonly")
        self.category_menu['values'] = [f"{v} ({k})" for k, v in CATEGORIES.items()]
        self.category_menu.pack(fill="x")
        self.category_menu.bind("<<ComboboxSelected>>", self.update_category)

        # Schwierigkeit Dropdown (darunter)
        tk.Label(self.config_frame, text="Schwierigkeit:", bg="#2D74B2", fg="white").pack(anchor="w", pady=(10, 0))
        self.difficulty_var = tk.StringVar(value=self.difficulty)
        self.difficulty_menu = ttk.Combobox(self.config_frame, textvariable=self.difficulty_var, state="readonly")
        self.difficulty_menu['values'] = DIFFICULTIES
        self.difficulty_menu.pack(fill="x")
        self.difficulty_menu.bind("<<ComboboxSelected>>", self.update_difficulty)

        # Scrollbare Frage-Anzeige mit fester Höhe
        self.question_frame = tk.Frame(root)
        self.question_frame.pack(pady=10)
        self.question_scrollbar = tk.Scrollbar(self.question_frame, orient="vertical")
        self.question_text = tk.Text(self.question_frame, height=3, width=40, wrap="word", yscrollcommand=self.question_scrollbar.set)
        self.question_scrollbar.config(command=self.question_text.yview)
        self.question_scrollbar.pack(side="right", fill="y")
        self.question_text.pack(side="left", fill="both", expand=True)
        self.question_text.config(state="disabled")

        # Antwort-Buttons
        self.buttons_frame = tk.Frame(root)
        self.buttons_frame.pack(pady=10)
        self.answer_buttons = []
        for _ in range(4):
            btn = tk.Button(self.buttons_frame, text="", width=40, command=lambda b=_: self.check_answer(b))
            btn.pack(pady=2)
            self.answer_buttons.append(btn)

        # Zentrale Steuerungsbuttons
        self.control_frame = tk.Frame(root, bg="#2D74B2")
        self.control_frame.pack(pady=20)

        self.stats_button = tk.Button(self.control_frame, text="Statistik anzeigen", width=20, command=self.show_stats)
        self.stats_button.grid(row=0, column=0, padx=10)

        self.repeat_button = tk.Button(self.control_frame, text="Falsche Fragen wiederholen", width=20, command=self.repeat_wrong_question)
        self.repeat_button.grid(row=0, column=1, padx=10)

        self.next_button = tk.Button(self.control_frame, text="Neue Frage", width=20, command=self.load_question)
        self.next_button.grid(row=0, column=2, padx=10)

        if user_profile == "Gast":
            self.get_user_profile()

#    def get_user_profile(self):
#        global user_profile
#        user_profile = simpledialog.askstring("Benutzername", "Wie heißt du?", parent=self.root) or "Gast"
#        self.user_label.config(text=f"Benutzer: {user_profile}")
#        self.save_config()
    def get_user_profile(self):
        global user_profile

        dialog = tk.Toplevel(self.root)
        dialog.title("Benutzername")
        dialog.geometry("300x130")
        dialog.configure(bg="#2D74B2")
        dialog.iconbitmap("resources/fs.ico")

        dialog.grab_set()

        tk.Label(dialog, text="Wie heißt du?", bg="#2D74B2", fg="white", font=("Arial", 11)).pack(pady=10)
        name_entry = tk.Entry(dialog, width=25)
        name_entry.pack(pady=5)
        name_entry.focus()

        def submit():
            global user_profile
            user_profile = name_entry.get() or "Gast"
            self.user_label.config(text=f"Benutzer: {user_profile}")
            self.save_config()
            dialog.destroy()

        tk.Button(dialog, text="OK", command=submit, bg="#2D74B2", fg="white", width=10).pack(pady=10)

        self.root.wait_window(dialog)


    def update_category(self, event):
        val = self.category_var.get()
        cat_id = val.split("(")[-1].strip(")") if "(" in val else None
        self.category = cat_id
        self.save_config()

    def update_difficulty(self, event):
        self.difficulty = self.difficulty_var.get()
        self.save_config()

    def load_question(self):
        global asked_questions

        self.current_question = fetch_question(self.category, self.difficulty)
        if not self.current_question:
            messagebox.showerror("Fehler", "Keine Frage gefunden.")
            return

        if self.current_question['question'] in asked_questions:
            return self.load_question()

        asked_questions.add(self.current_question['question'])

        self.question_text.config(state="normal")
        self.question_text.delete("1.0", tk.END)
        self.question_text.insert(tk.END, self.current_question['question'])
        self.question_text.config(state="disabled")

        for i, choice in enumerate(self.current_question['choices']):
            self.answer_buttons[i].config(text=choice, state="normal")

    def check_answer(self, idx):
        global score, right_count, wrong_count

        selected = self.answer_buttons[idx]['text']
        correct = self.current_question['correct']

        for btn in self.answer_buttons:
            btn.config(state="disabled")

        if selected == correct:
            messagebox.showinfo("Richtig", "✅ Richtig beantwortet!")
            score += 1
            right_count += 1
        else:
            messagebox.showwarning("Falsch", f"❌ Falsch! Richtig wäre: {correct}")
            wrong_questions.append(self.current_question)
            wrong_count += 1

        self.score_label.config(text=f"Punkte: {score}")

    def show_stats(self):
        messagebox.showinfo("Statistik",
                            f"Benutzer: {user_profile}\nRichtig: {right_count}\nFalsch: {wrong_count}\nPunktestand: {score}")

    def repeat_wrong_question(self):
        if not wrong_questions:
            messagebox.showinfo("Wiederholung", "Keine falschen Fragen gespeichert.")
            return

        self.current_question = wrong_questions.pop(0)
        self.question_text.config(state="normal")
        self.question_text.delete("1.0", tk.END)
        self.question_text.insert(tk.END, "(Wiederholung) " + self.current_question['question'])
        self.question_text.config(state="disabled")

        for i, choice in enumerate(self.current_question['choices']):
            self.answer_buttons[i].config(text=choice, state="normal")

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.category = data.get("category")
                self.difficulty = data.get("difficulty")
        else:
            self.category = None
            self.difficulty = None

    def save_config(self):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "category": self.category,
                "difficulty": self.difficulty
            }, f)

# === Hilfsfunktionen ===
def fetch_question(category=None, difficulty=None):
    url = "https://opentdb.com/api.php?amount=1&type=multiple"
    if category:
        url += f"&category={category}"
    if difficulty:
        url += f"&difficulty={difficulty}"

    resp = requests.get(url)
    data = resp.json()

    if data['response_code'] != 0:
        return None

    q = data['results'][0]
    question = html.unescape(q['question'])
    correct = html.unescape(q['correct_answer'])
    incorrects = [html.unescape(i) for i in q['incorrect_answers']]
    choices = incorrects + [correct]
    random.shuffle(choices)

    return {
        "question": question,
        "correct": correct,
        "choices": choices,
        "category": q['category'],
        "difficulty": q['difficulty']
    }

# === Start ===
if __name__ == "__main__":
    root = tk.Tk()
    app = TriviaApp(root)
    root.mainloop()
