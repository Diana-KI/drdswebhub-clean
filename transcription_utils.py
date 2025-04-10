# transcription_utils.py
# ------------------------------------------------
# Hier sind alle Hilfsfunktionen zur Transkription:
# - Datei speichern
# - Transkribieren mit OpenAI Whisper-API
# - Text stilistisch verbessern
# - Datei löschen
# - Transkriptionskosten abschätzen
# ------------------------------------------------

import os
import uuid
import openai
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

# 🧪 API-Key laden
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# 📁 Wo gespeicherte Audiodateien hin sollen
UPLOAD_FOLDER = "static/transcriptions"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ------------------------------------------
# 💾 Audiodatei speichern – egal ob Upload oder Aufnahme
def save_uploaded_audio(file):
    # Datei-Endung erkennen
    ext = os.path.splitext(file.filename)[1].lower()
    # Zufälliger Dateiname
    filename = f"{uuid.uuid4().hex}{ext}"
    # Pfad im Upload-Ordner
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    # Datei speichern
    file.save(filepath)
    return filename, filepath

# ------------------------------------------
# 🎙 Transkribieren mit OpenAI Whisper API (keine lokale Installation nötig!)
from openai import OpenAI
client = OpenAI()

def transcribe_audio(filepath):
    with open(filepath, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
    return transcript.text

# ------------------------------------------
# ✍️ Text verbessern – wähle zwischen: korrektur, höflich, freundlich, humorvoll
def gpt_improve_text(text, mode="korrektur"):
    mode_map = {
        "korrektur": "Korrigiere Rechtschreibung und Ausdruck:",
        "hoeflich": "Formuliere höflich wie für ein E-Mail:",
        "freundlich": "Formuliere freundlich wie an eine:n Freund:in:",
        "humorvoll": "Formuliere humorvoll wie für einen Blogpost:"
    }

    prompt = f"{mode_map.get(mode, mode_map['korrektur'])}\n\n{text}"

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )

    return response.choices[0].message.content.strip()

# ------------------------------------------
# 🧹 Datei nach Transkription löschen (optional)
def delete_audio_file(filepath):
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"🧹 Audio-Datei gelöscht: {filepath}")
            return "", 204
        else:
            print("⚠️ Datei nicht gefunden.")
            return "", 404
    except Exception as e:
        print(f"⚠️ Fehler beim Löschen: {e}")
        return "", 500

# ------------------------------------------
# 💸 Kostenabschätzung für Whisper-Transkription (ca. $0.006 pro Minute)
def estimate_cost_of_transcription(filepath):
    try:
        import wave

        with wave.open(filepath, "rb") as f:
            frames = f.getnframes()
            rate = f.getframerate()
            duration_seconds = frames / float(rate)
            minutes = duration_seconds / 60

        # Whisper API ca. $0.006 pro Minute
        return round(minutes * 0.006, 4)

    except Exception as e:
        print(f"⚠️ Fehler bei Kostenschätzung: {e}")
        return 0.0
