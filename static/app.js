// Lions Flute Audio FX Studio - Frontend JavaScript

class LionsFluteApp {
    constructor() {
        this.currentFile = null;
        this.processedFiles = [];
        this.init();
    }

    init() {
        this.bindEvents();
        this.checkServerStatus();
        this.updateIntensityDisplay();
    }

    bindEvents() {
        // File upload form
        document.getElementById('upload-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleFileUpload();
        });

        // Split audio button
        document.getElementById('split-btn').addEventListener('click', () => {
            this.splitAudio();
        });

        // Apply effects button
        document.getElementById('apply-fx-btn').addEventListener('click', () => {
            this.applyEffect();
        });

        // Intensity range slider
        document.getElementById('intensity-range').addEventListener('input', (e) => {
            this.updateIntensityDisplay(e.target.value);
        });
    }

    updateIntensityDisplay(value = 50) {
        document.getElementById('intensity-value').textContent = value;
    }

    async checkServerStatus() {
        try {
            const response = await fetch('/status');
            const data = await response.json();
            
            if (response.ok) {
                this.updateServerStatus('online', 'Server Online');
            } else {
                this.updateServerStatus('offline', 'Server Error');
            }
        } catch (error) {
            console.error('Server status check failed:', error);
            this.updateServerStatus('offline', 'Server Offline');
        }
    }

    updateServerStatus(status, message) {
        const statusElement = document.getElementById('server-status');
        statusElement.textContent = message;
        statusElement.className = `badge bg-${status === 'online' ? 'success' : 'danger'}`;
    }

    showStatus(message, type = 'info') {
        const alertElement = document.getElementById('status-alert');
        const messageElement = document.getElementById('status-message');
        
        alertElement.className = `alert alert-${type}`;
        messageElement.textContent = message;
        alertElement.classList.remove('d-none');

        // Auto-hide after 5 seconds
        setTimeout(() => {
            alertElement.classList.add('d-none');
        }, 5000);
    }

    async handleFileUpload() {
        const fileInput = document.getElementById('audio-file');
        const file = fileInput.files[0];

        if (!file) {
            this.showStatus('Please select a file', 'warning');
            return;
        }

        // Validate file size (16MB limit)
        if (file.size > 16 * 1024 * 1024) {
            this.showStatus('File too large. Maximum size is 16MB', 'danger');
            return;
        }

        // Validate file type
        const allowedTypes = ['audio/mpeg', 'audio/wav', 'audio/flac', 'audio/aac', 'audio/mp4'];
        if (!allowedTypes.includes(file.type) && !this.hasValidExtension(file.name)) {
            this.showStatus('Invalid file type. Please upload MP3, WAV, FLAC, AAC, or M4A files', 'danger');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        this.setLoadingState('upload-form', true);

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                this.currentFile = data.filename;
                this.showStatus(`File uploaded successfully: ${data.filename}`, 'success');
                this.showProcessingSection();
            } else {
                this.showStatus(data.error || 'Upload failed', 'danger');
            }
        } catch (error) {
            console.error('Upload error:', error);
            this.showStatus('Upload failed. Please try again.', 'danger');
        } finally {
            this.setLoadingState('upload-form', false);
        }
    }

    hasValidExtension(filename) {
        const validExtensions = ['.mp3', '.wav', '.flac', '.aac', '.m4a'];
        const extension = filename.toLowerCase().substring(filename.lastIndexOf('.'));
        return validExtensions.includes(extension);
    }

    async splitAudio() {
        if (!this.currentFile) {
            this.showStatus('Please upload a file first', 'warning');
            return;
        }

        this.setLoadingState('split-btn', true);

        try {
            const response = await fetch('/split', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    filename: this.currentFile
                })
            });

            const data = await response.json();

            if (response.ok) {
                this.showStatus('Audio split successfully', 'success');
                this.addProcessedFiles([
                    { name: data.vocals, type: 'Vocals', icon: 'fa-microphone' },
                    { name: data.music, type: 'Instrumentals', icon: 'fa-guitar' }
                ]);
                this.showResultsSection();
            } else {
                this.showStatus(data.error || 'Split failed', 'danger');
            }
        } catch (error) {
            console.error('Split error:', error);
            this.showStatus('Split failed. Please try again.', 'danger');
        } finally {
            this.setLoadingState('split-btn', false);
        }
    }

    async applyEffect() {
        if (!this.currentFile) {
            this.showStatus('Please upload a file first', 'warning');
            return;
        }

        const effect = document.getElementById('effect-select').value;
        if (!effect) {
            this.showStatus('Please select an effect', 'warning');
            return;
        }

        const intensity = document.getElementById('intensity-range').value;

        this.setLoadingState('apply-fx-btn', true);

        try {
            const response = await fetch('/apply_fx', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    filename: this.currentFile,
                    effect: effect,
                    intensity: parseInt(intensity)
                })
            });

            const data = await response.json();

            if (response.ok) {
                this.showStatus(`${effect} effect applied successfully`, 'success');
                this.addProcessedFiles([{
                    name: data.output_file,
                    type: `${effect} (${intensity}%)`,
                    icon: 'fa-magic'
                }]);
                this.showResultsSection();
            } else {
                this.showStatus(data.error || 'Effect application failed', 'danger');
            }
        } catch (error) {
            console.error('Effect application error:', error);
            this.showStatus('Effect application failed. Please try again.', 'danger');
        } finally {
            this.setLoadingState('apply-fx-btn', false);
        }
    }

    addProcessedFiles(files) {
        files.forEach(file => {
            if (!this.processedFiles.find(f => f.name === file.name)) {
                this.processedFiles.push(file);
            }
        });
        this.updateResultsList();
    }

    updateResultsList() {
        const resultsList = document.getElementById('results-list');
        
        if (this.processedFiles.length === 0) {
            resultsList.innerHTML = '<p class="text-muted">No processed files yet.</p>';
            return;
        }

        const filesHTML = this.processedFiles.map(file => `
            <div class="result-item d-flex justify-content-between align-items-center">
                <div>
                    <i class="fas ${file.icon} me-2 text-primary"></i>
                    <strong>${file.name}</strong>
                    <span class="badge bg-secondary ms-2">${file.type}</span>
                </div>
                <button class="btn btn-sm btn-outline-primary" onclick="app.downloadFile('${file.name}')">
                    <i class="fas fa-download me-1"></i>Download
                </button>
            </div>
        `).join('');

        resultsList.innerHTML = filesHTML;
    }

    async downloadFile(filename) {
        try {
            const response = await fetch(`/download/${filename}`);
            const data = await response.json();

            if (response.ok) {
                this.showStatus(`Download link generated for ${filename}`, 'info');
                // In a real implementation, you would redirect to the download URL
                console.log('Download URL:', data.download_url);
            } else {
                this.showStatus(data.error || 'Download failed', 'danger');
            }
        } catch (error) {
            console.error('Download error:', error);
            this.showStatus('Download failed. Please try again.', 'danger');
        }
    }

    showProcessingSection() {
        document.getElementById('processing-section').style.display = 'block';
    }

    showResultsSection() {
        document.getElementById('results-section').style.display = 'block';
    }

    setLoadingState(elementId, loading) {
        const element = document.getElementById(elementId);
        const isForm = element.tagName === 'FORM';
        const button = isForm ? element.querySelector('button[type="submit"]') : element;

        if (loading) {
            button.disabled = true;
            const originalText = button.innerHTML;
            button.dataset.originalText = originalText;
            button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';
        } else {
            button.disabled = false;
            button.innerHTML = button.dataset.originalText || button.innerHTML;
        }
    }
}

// Initialize the app when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new LionsFluteApp();
});

// Utility functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatDuration(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}
