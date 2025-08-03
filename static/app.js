// Lions Flute Audio FX Studio - Frontend JavaScript

class LionsFluteApp {
    constructor() {
        this.currentFile = null;
        this.processedFiles = [];
        this.activeTasks = new Map();
        this.pollInterval = null;
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

        // Drag and drop functionality
        this.setupDragAndDrop();

        // Upload zone click handler
        document.getElementById('upload-zone').addEventListener('click', () => {
            document.getElementById('audio-file').click();
        });

        // Demo track button
        document.getElementById('demo-btn').addEventListener('click', () => {
            this.generateDemo();
        });

        // Audio player controls
        document.getElementById('play-pause-btn').addEventListener('click', () => {
            this.togglePlayPause();
        });

        // File input change handler
        document.getElementById('audio-file').addEventListener('change', (e) => {
            if (e.target.files[0]) {
                this.loadAudioFile(e.target.files[0]);
            }
        });
    }

    setupDragAndDrop() {
        const uploadZone = document.getElementById('upload-zone');
        const fileInput = document.getElementById('audio-file');

        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadZone.addEventListener(eventName, this.preventDefaults, false);
            document.body.addEventListener(eventName, this.preventDefaults, false);
        });

        // Highlight drop area when item is dragged over it
        ['dragenter', 'dragover'].forEach(eventName => {
            uploadZone.addEventListener(eventName, () => {
                uploadZone.classList.add('dragover');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            uploadZone.addEventListener(eventName, () => {
                uploadZone.classList.remove('dragover');
            }, false);
        });

        // Handle dropped files
        uploadZone.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;

            if (files.length > 0) {
                // Create a new file input event
                const dataTransfer = new DataTransfer();
                dataTransfer.items.add(files[0]);
                fileInput.files = dataTransfer.files;
                this.loadAudioFile(files[0]);
            }
        }, false);
    }

    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
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

        // Validate file size (50MB limit)
        if (file.size > 50 * 1024 * 1024) {
            this.showStatus('File too large. Maximum size is 50MB', 'danger');
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
                this.showAudioPlayer(data);
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
                this.showStatus('Audio splitting started...', 'info');
                this.trackTask(data.task_id, 'split');
                this.startPolling();
            } else {
                this.showStatus(data.error || 'Split failed', 'danger');
                this.setLoadingState('split-btn', false);
            }
        } catch (error) {
            console.error('Split error:', error);
            this.showStatus('Split failed. Please try again.', 'danger');
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
                this.showStatus(`${effect} effect processing started...`, 'info');
                this.trackTask(data.task_id, 'effect', { effect, intensity });
                this.startPolling();
            } else {
                this.showStatus(data.error || 'Effect application failed', 'danger');
                this.setLoadingState('apply-fx-btn', false);
            }
        } catch (error) {
            console.error('Effect application error:', error);
            this.showStatus('Effect application failed. Please try again.', 'danger');
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
        this.updateFilesCount();
    }

    updateResultsList() {
        const resultsList = document.getElementById('results-list');
        
        if (this.processedFiles.length === 0) {
            resultsList.innerHTML = '<div class="text-center text-muted"><i class="fas fa-folder-open fs-1 mb-3 opacity-50"></i><p>No processed files yet.</p></div>';
            return;
        }

        const filesHTML = this.processedFiles.map((file, index) => `
            <div class="result-item d-flex justify-content-between align-items-center" style="animation-delay: ${index * 0.1}s">
                <div class="d-flex align-items-center">
                    <div class="file-icon-wrapper me-3">
                        <i class="fas ${file.icon}"></i>
                    </div>
                    <div>
                        <h6 class="mb-1">${file.name}</h6>
                        <span class="badge bg-gradient text-white">${file.type}</span>
                    </div>
                </div>
                <button class="btn btn-sm btn-outline-primary download-btn" onclick="app.downloadFile('${file.name}')">
                    <i class="fas fa-download me-1"></i>Download
                </button>
            </div>
        `).join('');

        resultsList.innerHTML = filesHTML;
    }

    updateFilesCount() {
        const countElement = document.getElementById('files-count');
        const count = this.processedFiles.length;
        countElement.textContent = `${count} file${count !== 1 ? 's' : ''}`;
        
        if (count > 0) {
            countElement.className = 'badge bg-success';
        } else {
            countElement.className = 'badge bg-secondary';
        }
    }

    trackTask(taskId, type, metadata = {}) {
        this.activeTasks.set(taskId, {
            type,
            metadata,
            startTime: Date.now()
        });
    }

    startPolling() {
        if (this.pollInterval) return; // Already polling
        
        this.pollInterval = setInterval(async () => {
            await this.checkTaskStatuses();
        }, 2000); // Poll every 2 seconds
    }

    stopPolling() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
        }
    }

    async checkTaskStatuses() {
        const completedTasks = [];
        
        for (const [taskId, taskInfo] of this.activeTasks) {
            try {
                const response = await fetch(`/task/${taskId}`);
                const data = await response.json();

                if (response.ok) {
                    // Update progress if available
                    if (data.progress !== undefined) {
                        this.updateProgressBar(data.progress);
                    }
                    
                    if (data.status === 'completed') {
                        this.handleTaskCompletion(taskId, data, taskInfo);
                        completedTasks.push(taskId);
                    } else if (data.status === 'failed') {
                        this.handleTaskFailure(taskId, data, taskInfo);
                        completedTasks.push(taskId);
                    } else if (data.status === 'processing') {
                        this.updateTaskProgress(taskId, data, taskInfo);
                    }
                }
            } catch (error) {
                console.error(`Error checking task ${taskId}:`, error);
            }
        }

        // Remove completed tasks
        completedTasks.forEach(taskId => {
            this.activeTasks.delete(taskId);
        });

        // Stop polling if no active tasks
        if (this.activeTasks.size === 0) {
            this.stopPolling();
        }
    }

    handleTaskCompletion(taskId, data, taskInfo) {
        if (data.type === 'split') {
            const files = [];
            if (data.result && data.result.vocals) {
                files.push({ name: data.result.vocals, type: 'Vocals', icon: 'fa-microphone' });
            }
            if (data.result && data.result.instruments) {
                files.push({ name: data.result.instruments, type: 'Instrumentals', icon: 'fa-guitar' });
            }
            this.addProcessedFiles(files);
            this.showStatus('Audio splitting completed successfully!', 'success');
            this.setLoadingState('split-btn', false);
        } else if (data.type === 'effect') {
            const { effect, intensity } = taskInfo.metadata;
            if (data.result && data.result.output_file) {
                this.addProcessedFiles([{
                    name: data.result.output_file,
                    type: `${effect} (${intensity}%)`,
                    icon: 'fa-magic'
                }]);
            }
            this.showStatus(`${effect} effect applied successfully!`, 'success');
            this.setLoadingState('apply-fx-btn', false);
        }
        
        // Update progress to 100%
        this.updateProgressBar(100);
        
        // Hide progress bar after a delay
        setTimeout(() => {
            this.hideProgressBar();
        }, 1500);
        
        this.showResultsSection();
    }

    handleTaskFailure(taskId, data, taskInfo) {
        this.showStatus(`Processing failed: ${data.error}`, 'danger');
        
        if (data.type === 'split') {
            this.setLoadingState('split-btn', false);
        } else if (data.type === 'effect') {
            this.setLoadingState('apply-fx-btn', false);
        }
    }

    updateTaskProgress(taskId, data, taskInfo) {
        if (data.progress !== undefined) {
            this.updateProgressBar(data.progress);
            
            if (data.progress > 0) {
                const processingType = data.type === 'split' ? 'Splitting' : 'Processing';
                this.showStatus(`${processingType} audio... ${data.progress}%`, 'info');
            }
        }
    }

    async downloadFile(filename) {
        try {
            // Create a temporary link and trigger download
            const link = document.createElement('a');
            link.href = `/download/${filename}`;
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            this.showStatus(`Downloading ${filename}...`, 'success');
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

    async generateDemo() {
        try {
            this.showStatus('Generating demo track...', 'info');
            
            const response = await fetch('/generate_demo', {
                method: 'POST'
            });

            const data = await response.json();

            if (response.ok) {
                this.currentFile = data.filename;
                this.showStatus('Demo track generated successfully!', 'success');
                this.showAudioPlayer(data);
                this.showProcessingSection();
            } else {
                this.showStatus(data.error || 'Demo generation failed', 'danger');
            }
        } catch (error) {
            console.error('Demo generation error:', error);
            this.showStatus('Demo generation failed. Please try again.', 'danger');
        }
    }

    showAudioPlayer(fileData) {
        const playerSection = document.getElementById('audio-player-section');
        const fileNameElement = document.getElementById('current-file-name');
        const fileInfoElement = document.getElementById('file-info');
        const audioElement = document.getElementById('audio-element');
        const playPauseBtn = document.getElementById('play-pause-btn');

        // Update file information
        fileNameElement.textContent = fileData.filename;
        fileInfoElement.textContent = `Duration: ${fileData.duration || '--'}s | Format: ${fileData.format || '--'} | Size: ${this.formatFileSize(fileData.size || 0)}`;

        // Set audio source
        audioElement.src = `/audio/${fileData.filename}`;
        
        // Enable play button
        playPauseBtn.disabled = false;

        // Show player
        playerSection.style.display = 'block';

        // Setup audio event listeners
        this.setupAudioEventListeners();

        // Generate waveform
        this.generateWaveform(fileData.filename);
    }

    setupAudioEventListeners() {
        const audioElement = document.getElementById('audio-element');
        if (!audioElement) return;

        // Remove existing listeners to prevent duplicates
        audioElement.removeEventListener('loadedmetadata', this.audioMetadataHandler);
        audioElement.removeEventListener('timeupdate', this.audioTimeUpdateHandler);
        audioElement.removeEventListener('ended', this.audioEndedHandler);

        // Create bound handlers
        this.audioMetadataHandler = () => this.updateTimeDisplay();
        this.audioTimeUpdateHandler = () => {
            this.updateTimeDisplay();
            this.updateProgress();
        };
        this.audioEndedHandler = () => this.resetPlayButton();

        // Add new listeners
        audioElement.addEventListener('loadedmetadata', this.audioMetadataHandler);
        audioElement.addEventListener('timeupdate', this.audioTimeUpdateHandler);
        audioElement.addEventListener('ended', this.audioEndedHandler);
    }

    togglePlayPause() {
        const audioElement = document.getElementById('audio-element');
        const playPauseBtn = document.getElementById('play-pause-btn');
        
        if (!audioElement || !playPauseBtn) return;
        
        const icon = playPauseBtn.querySelector('i');
        if (!icon) return;

        if (audioElement.paused) {
            audioElement.play().catch(error => {
                console.error('Audio play error:', error);
                this.showStatus('Error playing audio', 'danger');
            });
            icon.className = 'fas fa-pause';
        } else {
            audioElement.pause();
            icon.className = 'fas fa-play';
        }
    }

    resetPlayButton() {
        const playPauseBtn = document.getElementById('play-pause-btn');
        const icon = playPauseBtn.querySelector('i');
        icon.className = 'fas fa-play';
    }

    updateTimeDisplay() {
        const audioElement = document.getElementById('audio-element');
        const timeDisplay = document.getElementById('time-display');
        
        if (!audioElement || !timeDisplay) return;
        
        const currentTime = this.formatTime(audioElement.currentTime);
        const duration = this.formatTime(audioElement.duration);
        
        timeDisplay.textContent = `${currentTime} / ${duration}`;
    }

    updateProgress() {
        const audioElement = document.getElementById('audio-element');
        const progressOverlay = document.getElementById('progress-overlay');
        
        if (!audioElement || !progressOverlay) return;
        
        if (audioElement.duration) {
            const progress = (audioElement.currentTime / audioElement.duration) * 100;
            progressOverlay.style.width = `${progress}%`;
        }
    }

    generateWaveform(filename) {
        const canvas = document.getElementById('waveform-canvas');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Draw a placeholder waveform (in real app, you'd analyze the audio)
        this.drawPlaceholderWaveform(ctx, canvas.width, canvas.height);
    }

    drawPlaceholderWaveform(ctx, width, height) {
        const centerY = height / 2;
        const samples = 200;
        const barWidth = width / samples;
        
        ctx.fillStyle = 'rgba(13, 202, 240, 0.6)';
        
        for (let i = 0; i < samples; i++) {
            const x = i * barWidth;
            const amplitude = Math.random() * 0.8 + 0.1;
            const barHeight = amplitude * centerY;
            
            ctx.fillRect(x, centerY - barHeight, barWidth - 1, barHeight * 2);
        }
    }

    formatTime(seconds) {
        if (isNaN(seconds)) return '0:00';
        
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.floor(seconds % 60);
        
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    }

    updateProgressBar(progress) {
        const progressBar = document.getElementById('progress-bar');
        const progressBarContainer = document.getElementById('progress-bar-container');
        
        if (progressBar && progressBarContainer) {
            progressBar.style.width = `${Math.min(progress, 100)}%`;
            progressBar.setAttribute('aria-valuenow', progress);
            progressBarContainer.style.display = 'block';
        }
    }

    hideProgressBar() {
        const progressBarContainer = document.getElementById('progress-bar-container');
        if (progressBarContainer) {
            progressBarContainer.style.display = 'none';
        }
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    async loadAudioFile(file) {
        // Validate file first
        if (file.size > 50 * 1024 * 1024) {
            this.showStatus('File too large. Maximum size is 50MB', 'danger');
            return;
        }

        if (!this.hasValidExtension(file.name)) {
            this.showStatus('Invalid file type. Please upload MP3, WAV, FLAC, AAC, or M4A files', 'danger');
            return;
        }

        // Create a form data object and trigger upload
        const formData = new FormData();
        formData.append('file', file);
        
        // Show processing state
        this.showStatus('Uploading file...', 'info');
        
        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                this.currentFile = data.filename;
                this.showStatus(`File uploaded successfully: ${data.filename}`, 'success');
                this.showAudioPlayer(data);
                this.showProcessingSection();
            } else {
                this.showStatus(data.error || 'Upload failed', 'danger');
            }
        } catch (error) {
            console.error('Upload error:', error);
            this.showStatus('Upload failed. Please try again.', 'danger');
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
