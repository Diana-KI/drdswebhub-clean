# transcription_utils.py

import os
import uuid
import docx
import PyPDF2
import openai
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import re

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

MAX_TTS_CHARS = 4096

def extract_text_from_file(file):
    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1].lower()
    if ext == ".txt" or ext == ".doc":
        try:
            return file.read().decode("utf-8")
        except UnicodeDecodeError:
            file.seek(0)
            return file.read().decode("latin-1", errors="ignore")
    elif ext == ".docx":
        doc = docx.Document(file)
        return "\n".join([p.text for p in doc.paragraphs])
    elif ext == ".pdf":
        reader = PyPDF2.PdfReader(file)
        return "\n".join([page.extract_text() or "" for page in reader.pages])
    return ""

def split_text(text, max_len=MAX_TTS_CHARS):
    cleaned_text = re.sub(r'[\x00-\x1f\x7f]+', '', text)
    paragraphs = [p.strip() for p in cleaned_text.split('\n\n') if p.strip()]
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        if len(para) > max_len:
            for i in range(0, len(para), max_len):
                part = para[i:i+max_len].strip()
                if part:
                    chunks.append(part)
        else:
            if len(current_chunk) + len(para) <= max_len:
                current_chunk += para + "\n\n"
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = para + "\n\n"

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks

def convert_text_to_speech(text, voice="nova"):
    response = openai.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text
    )
    return response.content

def convert_chunks_to_audio(chunks, voice="nova"):
    full_audio = b""
    for idx, chunk in enumerate(chunks):
        print(f"🔊 Teil {idx + 1}/{len(chunks)} wird verarbeitet …")
        full_audio += convert_text_to_speech(chunk, voice)
    return full_audio

def save_uploaded_audio(file):
    """Speichert hochgeladene Audiodatei temporär im Ordner /static/transcriptions und gibt Pfad zurück."""
    upload_dir = os.path.join("static", "transcriptions")
    os.makedirs(upload_dir, exist_ok=True)

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".mp3", ".wav"]:
        raise ValueError("Ungültiges Audioformat.")

    filename = f"{uuid.uuid4().hex}{ext}"
    abs_path = os.path.join(upload_dir, filename)

    with open(abs_path, "wb") as f:
        f.write(file.read())

    print(f"✅ Audio gespeichert unter: {abs_path}")
    return filename, abs_path
