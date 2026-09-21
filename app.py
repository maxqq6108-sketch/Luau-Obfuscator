from flask import Flask, render_template, request, send_file
from io import BytesIO
from pathlib import Path
from obfuscator import obfuscate

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024

@app.get("/")
def index():
    return render_template("index.html")

@app.post("/obfuscate")
def obfuscate_route():
    uploaded = request.files.get("file")
    if not uploaded or not uploaded.filename:
        return "No file selected.", 400
    filename = Path(uploaded.filename).name
    if Path(filename).suffix.lower() not in {".lua", ".luau"}:
        return "Only .lua and .luau files are supported.", 400
    try:
        source = uploaded.read().decode("utf-8")
    except UnicodeDecodeError:
        return "The file must be UTF-8 text.", 400
    if not source.strip():
        return "The file is empty.", 400
    try:
        protected = obfuscate(source)
    except Exception:
        return "Obfuscation failed. Please check the source.", 400
    data = BytesIO(protected.encode("utf-8"))
    data.seek(0)
    return send_file(data, as_attachment=True,
                     download_name=f"{Path(filename).stem}_protected.luau",
                     mimetype="text/plain; charset=utf-8")

@app.errorhandler(413)
def too_large(_):
    return "File is too large. Maximum size is 2 MB.", 413

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
