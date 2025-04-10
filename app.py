from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import json
import uuid

from tts_utils import (
    extract_text_from_file,
    split_text,
    convert_text_to_speech,
    convert_chunks_to_audio
)
from transcription_utils import (
    save_uploaded_audio,
    transcribe_audio,
    gpt_improve_text,
    delete_audio_file
)

app = Flask(__name__)
app.secret_key = "DEIN_GEHEIMWERT"

BLOG_FILE = "blogposts.json"

# ---------- TRANSKRIPTION ----------
@app.route("/transcription", methods=["GET", "POST"])
def transcription():
    if request.method == "POST":
        if "audiofile" in request.files:
            file = request.files["audiofile"]
            filename, filepath = save_uploaded_audio(file)

            print(f"📁 Datei empfangen und gespeichert unter: {filepath}")  # 🪵 Debug-Ausgabe
            
            text = transcribe_audio(filepath)
            return render_template("transcription.html", audio_file=filename, transcript=text)
    return render_template("transcription.html", audio_file=None, transcript=None)

@app.route("/improve_text", methods=["POST"])
def improve_text():
    data = request.get_json()
    text = data.get("text")
    mode = data.get("mode", "korrektur")
    if not text:
        return jsonify({"error": "Kein Text vorhanden."}), 400
    improved = gpt_improve_text(text, mode)
    return jsonify({"improved_text": improved})

@app.route("/delete_audio", methods=["POST"])
def delete_audio():
    data = request.get_json()
    filename = data.get("filename")
    filepath = os.path.join("static", filename)
    return delete_audio_file(filepath)

# ---------- BLOG ----------
def load_posts():
    if os.path.exists(BLOG_FILE):
        with open(BLOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_post(post):
    posts = load_posts()
    posts.insert(0, post)
    with open(BLOG_FILE, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/blog")
def blog():
    posts = load_posts()
    return render_template("blog.html", posts=posts)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        image_url = request.form["image_url"]
        post = {"title": title, "content": content, "image_url": image_url}
        save_post(post)
        return redirect(url_for("blog"))
    return render_template("admin.html")

@app.route("/login_writer")
def login_writer():
    session["role"] = "writer"
    return redirect(url_for("blog"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("blog"))

# ---------- TEXT-TO-SPEECH ----------
@app.route("/tts", methods=["GET", "POST"])
def tts():
    if request.method == "POST":
        voice = request.form.get("voice", "nova")
        filename = f"output_{uuid.uuid4().hex}.mp3"
        speech_file_path = os.path.join("static", filename)

        if "text" in request.form and request.form["text"].strip():
            text = request.form["text"]
            audio = convert_text_to_speech(text, voice)
            with open(speech_file_path, "wb") as f:
                f.write(audio)
            return render_template("tts.html", audio_file=filename)

        elif "textfile" in request.files:
            file = request.files["textfile"]
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in [".txt", ".docx", ".doc", ".pdf"]:
                return render_template("tts.html", audio_file=None, error="Ungültiges Dateiformat.")
            text = extract_text_from_file(file)
            if not text.strip():
                return render_template("tts.html", audio_file=None, error="Die Datei enthält keinen lesbaren Text.")
            chunks = split_text(text)
            full_audio = convert_chunks_to_audio(chunks, voice)
            with open(speech_file_path, "wb") as f:
                f.write(full_audio)
            return render_template("tts.html", audio_file=filename)

    return render_template("tts.html", audio_file=None)

# ---------- BLOG VORLESEN ----------
@app.route("/read_post/<int:post_id>")
def read_post(post_id):
    posts = load_posts()
    if post_id < 0 or post_id >= len(posts):
        return "Post nicht gefunden", 404
    post = posts[post_id]
    text = f"{post['title']}. {post['content']}"
    filename = f"blogpost_{uuid.uuid4().hex}.mp3"
    speech_file_path = os.path.join("static", filename)
    audio = convert_text_to_speech(text, "nova")
    with open(speech_file_path, "wb") as f:
        f.write(audio)
    return render_template("read_post.html", post=post, audio_file=filename)

@app.route("/generate_audio/<int:post_id>")
def generate_audio(post_id):
    posts = load_posts()
    if post_id < 0 or post_id >= len(posts):
        return jsonify({"error": "Post nicht gefunden"}), 404
    post = posts[post_id]
    text = f"{post['title']}. {post['content']}"
    filename = f"blogpost_{uuid.uuid4().hex}.mp3"
    speech_file_path = os.path.join("static", filename)
    audio = convert_text_to_speech(text, "nova")
    with open(speech_file_path, "wb") as f:
        f.write(audio)
    return jsonify({"audio_url": f"/static/{filename}"})


if __name__ == "__main__":
    app.run(debug=True)

