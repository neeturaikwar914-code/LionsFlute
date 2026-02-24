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

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "production-secret")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

CORS(app)

# ================= CONFIG =================

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

# ================= HELPERS =================

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# ================= HOME =================

@app.route("/")
def home():
    return render_template("index.html")

# ================= SPLIT =================

def process_split_task(task_id, filename):
    try:
        processing_tasks[task_id]["status"] = "processing"
        processing_tasks[task_id]["progress"] = 20

        result = audio_processor.split_vocals_instruments(filename)

        processing_tasks[task_id]["progress"] = 70

        vocal_mp3 = audio_processor.convert_to_mp3(result["vocals"])
        instrumental_mp3 = audio_processor.convert_to_mp3(result["instruments"])

        processing_tasks[task_id]["status"] = "completed"
        processing_tasks[task_id]["progress"] = 100
        processing_tasks[task_id]["result"] = {
            "vocal": vocal_mp3,
            "instrumental": instrumental_mp3
        }

    except Exception as e:
        processing_tasks[task_id]["status"] = "failed"
        processing_tasks[task_id]["error"] = str(e)

@app.route("/split", methods=["POST"])
def split_audio():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        if not allowed_file(file.filename):
            return jsonify({"error": "Unsupported format"}), 400

        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        task_id = str(uuid.uuid4())

        processing_tasks[task_id] = {
            "status": "queued",
            "progress": 0,
            "filename": filename,
            "type": "split",
            "created_at": time.time()
        }

        thread = threading.Thread(
            target=process_split_task,
            args=(task_id, filename)
        )
        thread.daemon = True
        thread.start()

        return jsonify({
            "task_id": task_id,
            "status": "processing"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ================= EFFECT =================

def process_effect_task(task_id, filename, effect, intensity):
    try:
        processing_tasks[task_id]["status"] = "processing"
        processing_tasks[task_id]["progress"] = 30

        processed = audio_processor.apply_effect(filename, effect, intensity)

        processing_tasks[task_id]["progress"] = 80

        output_mp3 = audio_processor.convert_to_mp3(processed)

        processing_tasks[task_id]["status"] = "completed"
        processing_tasks[task_id]["progress"] = 100
        processing_tasks[task_id]["result"] = {
            "output": output_mp3
        }

    except Exception as e:
        processing_tasks[task_id]["status"] = "failed"
        processing_tasks[task_id]["error"] = str(e)

@app.route("/apply_fx", methods=["POST"])
def apply_fx():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]
        effect = request.form.get("effect")
        intensity = int(request.form.get("intensity", 50))

        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        if not effect:
            return jsonify({"error": "Effect required"}), 400

        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        task_id = str(uuid.uuid4())

        processing_tasks[task_id] = {
            "status": "queued",
            "progress": 0,
            "filename": filename,
            "type": "effect",
            "created_at": time.time()
        }

        thread = threading.Thread(
            target=process_effect_task,
            args=(task_id, filename, effect, intensity)
        )
        thread.daemon = True
        thread.start()

        return jsonify({
            "task_id": task_id,
            "status": "processing"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ================= TASK STATUS =================

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
        "status": task.get("status"),
        "progress": task.get("progress"),
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
        "version": "3.0.0",
        "supported_formats": list(ALLOWED_EXTENSIONS),
        "max_file_size_mb": 50
    }), 200

# ================= ERROR HANDLERS =================

@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": "File too large (max 50MB)"}), 413

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Internal server error"}), 500

# ================= RUN =================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))