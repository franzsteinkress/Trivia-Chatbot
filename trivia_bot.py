import requests
import html

def fetch_question():
    url = "https://opentdb.com/api.php?amount=1&type=multiple"
    response = requests.get(url)
    data = response.json()

    if data["response_code"] != 0:
        print("Fehler beim Abrufen der Frage.")
        return None

    question_data = data["results"][0]
    question = html.unescape(question_data["question"])
    correct_answer = html.unescape(question_data["correct_answer"])
    all_answers = [html.unescape(ans) for ans in question_data["incorrect_answers"]]
    all_answers.append(correct_answer)
    all_answers.sort()  # Sortierung für gleiche Reihenfolge

    return {
        "question": question,
        "correct": correct_answer,
        "choices": all_answers
    }

def ask_user_question():
    q = fetch_question()
    if not q:
        return

    print("\nFrage:")
    print(q["question"])
    print("Antwortmöglichkeiten:")
    for idx, choice in enumerate(q["choices"], 1):
        print(f"  {idx}. {choice}")

    try:
        user_input = input("Deine Antwort (Nummer eingeben oder 'exit'): ").strip()
        if user_input.lower() == "exit":
            return False

        selected_idx = int(user_input) - 1
        if q["choices"][selected_idx] == q["correct"]:
            print("✅ Richtig!")
        else:
            print(f"❌ Falsch! Richtige Antwort: {q['correct']}")
    except (ValueError, IndexError):
        print("⚠️ Ungültige Eingabe. Bitte gib eine gültige Zahl ein.")

    return True

def run_chatbot():
    print("📚 Willkommen beim Trivia-Chatbot!")
    print("Gib 'exit' ein, um zu beenden.\n")

    while True:
        cont = ask_user_question()
        if cont is False:
            print("👋 Auf Wiedersehen!")
            break

if __name__ == "__main__":
    run_chatbot()
