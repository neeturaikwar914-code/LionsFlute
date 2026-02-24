import os
import logging
import threading
import time
import uuid
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
from audio_processor import AudioProcessor
from demo_generator import generate_demo_track

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "production-secret")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

CORS(app)

UPLOAD_FOLDER = "uploads"
PROCESSED_FOLDER = os.path.join(UPLOAD_FOLDER, "processed")
ALLOWED_EXTENSIONS = {"mp3", "wav", "flac", "aac", "m4a"}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

audio_processor = AudioProcessor(UPLOAD_FOLDER)

processing_tasks = {}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def home():
    return render_template("index.html")

# ================= UPLOAD =================

@app.route("/upload", methods=["POST"])
def upload_file():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        if not allowed_file(file.filename):
            return jsonify({"error": "Unsupported file format"}), 400

        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        return jsonify({
            "message": "Upload successful",
            "filename": filename
        }), 200

    except Exception as e:
        app.logger.error(f"Upload error: {str(e)}")
        return jsonify({"error": "Upload failed"}), 500

# ================= SPLIT PROCESS =================

def process_split_task(task_id, filename):
    try:
        processing_tasks[task_id]["status"] = "processing"
        processing_tasks[task_id]["progress"] = 10

        result = audio_processor.split_vocals_instruments(filename)

        processing_tasks[task_id]["progress"] = 70

        vocals_mp3 = audio_processor.convert_to_mp3(result["vocals"])
        instruments_mp3 = audio_processor.convert_to_mp3(result["instruments"])

        processing_tasks[task_id]["status"] = "completed"
        processing_tasks[task_id]["progress"] = 100
        processing_tasks[task_id]["result"] = {
            "vocals": vocals_mp3,
            "instruments": instruments_mp3
        }

    except Exception as e:
        processing_tasks[task_id]["status"] = "failed"
        processing_tasks[task_id]["error"] = str(e)

@app.route("/split", methods=["POST"])
def split_audio():
    try:
        data = request.get_json()
        filename = data.get("filename")

        if not filename:
            return jsonify({"error": "Filename required"}), 400

        filepath = os.path.join(UPLOAD_FOLDER, filename)
        if not os.path.exists(filepath):
            return jsonify({"error": "File not found"}), 404

        task_id = str(uuid.uuid4())

        processing_tasks[task_id] = {
            "status": "queued",
            "progress": 0,
            "filename": filename,
            "type": "split",
            "created_at": time.time()
        }

        thread = threading.Thread(target=process_split_task, args=(task_id, filename))
        thread.daemon = True
        thread.start()

        return jsonify({
            "task_id": task_id,
            "status": "processing"
        }), 200

    except Exception as e:
        return jsonify({"error": "Split failed"}), 500

# ================= EFFECT PROCESS =================

def process_effect_task(task_id, filename, effect, intensity):
    try:
        processing_tasks[task_id]["status"] = "processing"
        processing_tasks[task_id]["progress"] = 20

        processed = audio_processor.apply_effect(filename, effect, intensity)

        processing_tasks[task_id]["progress"] = 80

        output_mp3 = audio_processor.convert_to_mp3(processed)

        processing_tasks[task_id]["status"] = "completed"
        processing_tasks[task_id]["progress"] = 100
        processing_tasks[task_id]["result"] = {
            "output_file": output_mp3
        }

    except Exception as e:
        processing_tasks[task_id]["status"] = "failed"
        processing_tasks[task_id]["error"] = str(e)

@app.route("/apply_fx", methods=["POST"])
def apply_fx():
    try:
        data = request.get_json()
        filename = data.get("filename")
        effect = data.get("effect")
        intensity = data.get("intensity", 50)

        if not filename or not effect:
            return jsonify({"error": "Missing data"}), 400

        filepath = os.path.join(UPLOAD_FOLDER, filename)
        if not os.path.exists(filepath):
            return jsonify({"error": "File not found"}), 404

        task_id = str(uuid.uuid4())

        processing_tasks[task_id] = {
            "status": "queued",
            "progress": 0,
            "filename": filename,
            "type": "effect",
            "created_at": time.time()
        }

        thread = threading.Thread(target=process_effect_task, args=(task_id, filename, effect, intensity))
        thread.daemon = True
        thread.start()

        return jsonify({
            "task_id": task_id,
            "status": "processing"
        }), 200

    except Exception:
        return jsonify({"error": "Effect failed"}), 500

# ================= TASK STATUS (FIXED FOR SPINNER) =================

@app.route("/task/<task_id>")
def get_task_status(task_id):
    task = processing_tasks.get(task_id)

    if not task:
        return jsonify({
            "status": "failed",
            "error": "Task not found"
        }), 404

    return jsonify({
        "task_id": task_id,
        "status": task.get("status", "processing"),
        "progress": task.get("progress", 0),
        "type": task.get("type"),
        "result": task.get("result", {}),
        "error": task.get("error")
    }), 200

# ================= DOWNLOAD =================

@app.route("/download/<filename>")
def download_file(filename):
    secure_name = secure_filename(filename)
    file_path = os.path.join(PROCESSED_FOLDER, secure_name)

    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404

    return send_from_directory(PROCESSED_FOLDER, secure_name, as_attachment=True)

# ================= STATUS =================

@app.route("/status")
def status():
    return jsonify({
        "status": "active",
        "service": "Lions Flute Audio FX API",
        "version": "2.1.0",
        "supported_formats": list(ALLOWED_EXTENSIONS),
        "max_file_size_mb": 50
    }), 200

# ================= ERROR HANDLERS =================

@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": "File too large. Maximum size is 50MB"}), 413

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)