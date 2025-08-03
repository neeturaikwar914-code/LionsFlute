import os
import logging
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix

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
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'flac', 'aac', 'm4a'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    """Home route - can serve the web interface or return API status."""
    if request.headers.get('Accept') == 'application/json':
        return jsonify({'message': 'Lions Flute Server Running'})
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
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            app.logger.info(f"File uploaded successfully: {filename}")
            return jsonify({
                'message': 'File uploaded successfully',
                'filename': filename,
                'size': os.path.getsize(filepath)
            }), 200
            
    except Exception as e:
        app.logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': 'Upload failed'}), 500

@app.route('/split', methods=['POST'])
def split_audio():
    """Simulate splitting audio into vocals and instrumentals."""
    try:
        data = request.get_json()
        
        if not data or 'filename' not in data:
            return jsonify({'error': 'Filename required in request body'}), 400
        
        filename = data['filename']
        base_name = os.path.splitext(filename)[0]
        
        app.logger.info(f"Splitting audio: {filename}")
        
        # Simulate processing time and return mock results
        return jsonify({
            'message': 'Audio split successfully',
            'vocals': f'{base_name}_vocals.mp3',
            'music': f'{base_name}_music.mp3',
            'original': filename
        }), 200
        
    except Exception as e:
        app.logger.error(f"Split error: {str(e)}")
        return jsonify({'error': 'Audio splitting failed'}), 500

@app.route('/apply_fx', methods=['POST'])
def apply_effects():
    """Apply audio effects to uploaded files."""
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
        
        base_name = os.path.splitext(filename)[0]
        output_filename = f'{base_name}_{effect_name}_processed.mp3'
        
        app.logger.info(f"Applying {effect_name} effect to {filename} with intensity {intensity}")
        
        return jsonify({
            'message': f'{effect_name} applied successfully',
            'output_file': output_filename,
            'effect': effect_name,
            'intensity': intensity,
            'original_file': filename
        }), 200
        
    except Exception as e:
        app.logger.error(f"Effect application error: {str(e)}")
        return jsonify({'error': 'Effect application failed'}), 500

@app.route('/download/<filename>')
def download_file(filename):
    """Provide download URLs for processed files."""
    try:
        # Validate filename
        secure_name = secure_filename(filename)
        if not secure_name or not allowed_file(secure_name):
            return jsonify({'error': 'Invalid filename'}), 400
        
        # In a real implementation, you would check if the file exists
        # For now, return a mock download URL
        download_url = f'https://example.com/static/{secure_name}'
        
        app.logger.info(f"Download requested for: {secure_name}")
        
        return jsonify({
            'download_url': download_url,
            'filename': secure_name,
            'message': 'Download link generated successfully'
        }), 200
        
    except Exception as e:
        app.logger.error(f"Download error: {str(e)}")
        return jsonify({'error': 'Download link generation failed'}), 500

@app.route('/status')
def status():
    """API status endpoint."""
    return jsonify({
        'status': 'active',
        'service': 'Lions Flute Audio FX API',
        'version': '1.0.0',
        'supported_formats': list(ALLOWED_EXTENSIONS),
        'max_file_size_mb': MAX_CONTENT_LENGTH / (1024 * 1024)
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
