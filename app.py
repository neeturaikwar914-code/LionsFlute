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

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Enable CORS for frontend integration
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = os.path.join(UPLOAD_FOLDER, 'processed')
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'flac', 'aac', 'm4a'}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

# Initialize audio processor
audio_processor = AudioProcessor(UPLOAD_FOLDER)

# Store for tracking processing tasks
processing_tasks = {}

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    """Home route - serves the web interface."""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle audio file uploads."""
    try:
        # Check if the post request has the file part
        if 'file' not in request.files:
            return jsonify({'error': 'No file part in request'}), 400
        
        file = request.files['file']
        
        # Check if user selected a file
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Check if file is allowed
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed. Supported formats: MP3, WAV, FLAC, AAC, M4A'}), 400
        
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Get audio information
            try:
                audio_info = audio_processor.get_audio_info(filename)
                app.logger.info(f"File uploaded successfully: {filename}")
                
                return jsonify({
                    'message': 'File uploaded successfully',
                    'filename': filename,
                    'size': audio_info['file_size'],
                    'duration': audio_info['duration'],
                    'sample_rate': audio_info['sample_rate'],
                    'channels': audio_info['channels'],
                    'format': audio_info['format']
                }), 200
            except Exception as info_error:
                app.logger.warning(f"Could not get audio info: {str(info_error)}")
                return jsonify({
                    'message': 'File uploaded successfully',
                    'filename': filename,
                    'size': os.path.getsize(filepath)
                }), 200
            
    except Exception as e:
        app.logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': 'Upload failed'}), 500

def process_split_task(task_id: str, filename: str):
    """Background task for audio splitting."""
    try:
        processing_tasks[task_id]['status'] = 'processing'
        processing_tasks[task_id]['progress'] = 10
        
        # Perform actual audio splitting
        result = audio_processor.split_vocals_instruments(filename)
        
        processing_tasks[task_id]['progress'] = 80
        
        # Convert to MP3 for smaller file sizes
        vocals_mp3 = audio_processor.convert_to_mp3(result['vocals'])
        instruments_mp3 = audio_processor.convert_to_mp3(result['instruments'])
        
        processing_tasks[task_id]['progress'] = 100
        processing_tasks[task_id]['status'] = 'completed'
        processing_tasks[task_id]['result'] = {
            'vocals': vocals_mp3,
            'instruments': instruments_mp3,
            'original': filename
        }
        
        app.logger.info(f"Audio splitting completed for task {task_id}")
        
    except Exception as e:
        processing_tasks[task_id]['status'] = 'failed'
        processing_tasks[task_id]['error'] = str(e)
        app.logger.error(f"Split task {task_id} failed: {str(e)}")

@app.route('/split', methods=['POST'])
def split_audio():
    """Start audio splitting process."""
    try:
        data = request.get_json()
        
        if not data or 'filename' not in data:
            return jsonify({'error': 'Filename required in request body'}), 400
        
        filename = data['filename']
        
        # Check if file exists
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        # Create task ID
        task_id = str(uuid.uuid4())
        
        # Initialize task tracking
        processing_tasks[task_id] = {
            'status': 'queued',
            'progress': 0,
            'filename': filename,
            'type': 'split',
            'created_at': time.time()
        }
        
        # Start background processing
        thread = threading.Thread(target=process_split_task, args=(task_id, filename))
        thread.daemon = True
        thread.start()
        
        app.logger.info(f"Started audio splitting task {task_id} for: {filename}")
        
        return jsonify({
            'message': 'Audio splitting started',
            'task_id': task_id,
            'status': 'processing'
        }), 200
        
    except Exception as e:
        app.logger.error(f"Split error: {str(e)}")
        return jsonify({'error': 'Audio splitting failed'}), 500

def process_effect_task(task_id: str, filename: str, effect_name: str, intensity: int):
    """Background task for applying audio effects."""
    try:
        processing_tasks[task_id]['status'] = 'processing'
        processing_tasks[task_id]['progress'] = 20
        
        # Apply the effect
        processed_filename = audio_processor.apply_effect(filename, effect_name, intensity)
        
        processing_tasks[task_id]['progress'] = 80
        
        # Convert to MP3
        mp3_filename = audio_processor.convert_to_mp3(processed_filename)
        
        processing_tasks[task_id]['progress'] = 100
        processing_tasks[task_id]['status'] = 'completed'
        processing_tasks[task_id]['result'] = {
            'output_file': mp3_filename,
            'effect': effect_name,
            'intensity': intensity,
            'original_file': filename
        }
        
        app.logger.info(f"Effect processing completed for task {task_id}")
        
    except Exception as e:
        processing_tasks[task_id]['status'] = 'failed'
        processing_tasks[task_id]['error'] = str(e)
        app.logger.error(f"Effect task {task_id} failed: {str(e)}")

@app.route('/apply_fx', methods=['POST'])
def apply_effects():
    """Start audio effect processing."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'JSON data required'}), 400
        
        if 'effect' not in data:
            return jsonify({'error': 'Effect name required'}), 400
        
        if 'filename' not in data:
            return jsonify({'error': 'Filename required'}), 400
        
        effect_name = data['effect']
        filename = data['filename']
        intensity = data.get('intensity', 50)  # Default intensity
        
        # List of supported effects
        supported_effects = ['reverb', 'echo', 'distortion', 'chorus', 'delay', 'compressor', 'equalizer']
        
        if effect_name.lower() not in supported_effects:
            return jsonify({
                'error': f'Effect not supported. Available effects: {", ".join(supported_effects)}'
            }), 400
        
        # Check if file exists
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        # Create task ID
        task_id = str(uuid.uuid4())
        
        # Initialize task tracking
        processing_tasks[task_id] = {
            'status': 'queued',
            'progress': 0,
            'filename': filename,
            'effect': effect_name,
            'intensity': intensity,
            'type': 'effect',
            'created_at': time.time()
        }
        
        # Start background processing
        thread = threading.Thread(target=process_effect_task, args=(task_id, filename, effect_name, intensity))
        thread.daemon = True
        thread.start()
        
        app.logger.info(f"Started effect processing task {task_id}: {effect_name} on {filename}")
        
        return jsonify({
            'message': f'{effect_name} processing started',
            'task_id': task_id,
            'status': 'processing',
            'effect': effect_name,
            'intensity': intensity
        }), 200
        
    except Exception as e:
        app.logger.error(f"Effect application error: {str(e)}")
        return jsonify({'error': 'Effect application failed'}), 500

@app.route('/task/<task_id>')
def get_task_status(task_id):
    """Get processing task status."""
    try:
        if task_id not in processing_tasks:
            return jsonify({'error': 'Task not found'}), 404
        
        task = processing_tasks[task_id]
        
        response_data = {
            'task_id': task_id,
            'status': task['status'],
            'progress': task['progress'],
            'type': task['type'],
            'filename': task['filename']
        }
        
        if task['status'] == 'completed':
            response_data['result'] = task['result']
        elif task['status'] == 'failed':
            response_data['error'] = task.get('error', 'Unknown error')
        
        return jsonify(response_data), 200
        
    except Exception as e:
        app.logger.error(f"Task status error: {str(e)}")
        return jsonify({'error': 'Failed to get task status'}), 500

@app.route('/download/<filename>')
def download_file(filename):
    """Download processed audio files."""
    try:
        # Validate filename
        secure_name = secure_filename(filename)
        if not secure_name:
            return jsonify({'error': 'Invalid filename'}), 400
        
        # Check if file exists in processed folder
        file_path = os.path.join(PROCESSED_FOLDER, secure_name)
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        app.logger.info(f"Downloading file: {secure_name}")
        
        # Serve the actual file
        return send_from_directory(PROCESSED_FOLDER, secure_name, as_attachment=True)
        
    except Exception as e:
        app.logger.error(f"Download error: {str(e)}")
        return jsonify({'error': 'Download failed'}), 500

@app.route('/files')
def list_processed_files():
    """List all processed files."""
    try:
        files = []
        if os.path.exists(PROCESSED_FOLDER):
            for filename in os.listdir(PROCESSED_FOLDER):
                if filename.lower().endswith(('.mp3', '.wav')):
                    file_path = os.path.join(PROCESSED_FOLDER, filename)
                    file_info = {
                        'filename': filename,
                        'size': os.path.getsize(file_path),
                        'created': os.path.getctime(file_path)
                    }
                    files.append(file_info)
        
        return jsonify({'files': files}), 200
        
    except Exception as e:
        app.logger.error(f"List files error: {str(e)}")
        return jsonify({'error': 'Failed to list files'}), 500

@app.route('/generate_demo', methods=['POST'])
def generate_demo():
    """Generate a demo audio file."""
    try:
        # Generate demo track
        demo_filename = "demo_track.wav"
        filepath = generate_demo_track(demo_filename, duration=20)
        
        # Get audio info
        audio_info = audio_processor.get_audio_info(demo_filename)
        
        return jsonify({
            'message': 'Demo track generated successfully',
            'filename': demo_filename,
            'size': audio_info['file_size'],
            'duration': audio_info['duration'],
            'sample_rate': audio_info['sample_rate'],
            'channels': audio_info['channels']
        }), 200
        
    except Exception as e:
        app.logger.error(f"Demo generation error: {str(e)}")
        return jsonify({'error': 'Failed to generate demo'}), 500

@app.route('/audio/<filename>')
def serve_audio(filename):
    """Serve audio files for playback."""
    try:
        secure_name = secure_filename(filename)
        if not secure_name:
            return jsonify({'error': 'Invalid filename'}), 400
        
        # Check both upload and processed folders
        upload_path = os.path.join(UPLOAD_FOLDER, secure_name)
        processed_path = os.path.join(PROCESSED_FOLDER, secure_name)
        
        if os.path.exists(upload_path):
            return send_from_directory(UPLOAD_FOLDER, secure_name)
        elif os.path.exists(processed_path):
            return send_from_directory(PROCESSED_FOLDER, secure_name)
        else:
            return jsonify({'error': 'Audio file not found'}), 404
            
    except Exception as e:
        app.logger.error(f"Audio serve error: {str(e)}")
        return jsonify({'error': 'Failed to serve audio'}), 500

@app.route('/status')
def status():
    """API status endpoint."""
    # Clean up old tasks (older than 1 hour)
    current_time = time.time()
    tasks_to_remove = []
    for task_id, task in processing_tasks.items():
        if current_time - task['created_at'] > 3600:  # 1 hour
            tasks_to_remove.append(task_id)
    
    for task_id in tasks_to_remove:
        del processing_tasks[task_id]
    
    active_tasks = len([t for t in processing_tasks.values() if t['status'] in ['queued', 'processing']])
    
    return jsonify({
        'status': 'active',
        'service': 'Lions Flute Audio FX API',
        'version': '2.0.0',
        'supported_formats': list(ALLOWED_EXTENSIONS),
        'max_file_size_mb': MAX_CONTENT_LENGTH / (1024 * 1024),
        'active_tasks': active_tasks,
        'total_tasks': len(processing_tasks),
        'features': [
            'Real-time audio processing',
            'Vocal/instrumental separation',
            'Multiple audio effects',
            'High-quality export',
            'Background processing'
        ]
    }), 200

@app.errorhandler(413)
def too_large(e):
    """Handle file too large errors."""
    return jsonify({'error': 'File too large. Maximum size is 16MB'}), 413

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    """Handle internal server errors."""
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
