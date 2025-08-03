# Lions Flute - Audio FX Studio

## Overview

Lions Flute is a comprehensive web-based audio processing studio featuring real-time audio processing capabilities. The application provides professional-grade vocal/instrumental separation, multiple audio effects, and a modern glassmorphism interface. Built with Flask backend and vanilla JavaScript frontend, it supports multiple audio formats with real-time progress tracking and background processing.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Technology**: Vanilla JavaScript with Bootstrap 5 dark theme glassmorphism design
- **Design Pattern**: Class-based component architecture with `LionsFluteApp` as the main controller
- **UI Framework**: Bootstrap 5 with custom dark theme and Font Awesome icons
- **File Handling**: HTML5 File API with drag & drop functionality and real-time validation
- **Communication**: Fetch API for REST communication with task polling for background processes
- **State Management**: Task tracking with Map-based active task monitoring and real-time progress updates
- **Audio Player**: Built-in audio player with waveform visualization and playback controls

### Backend Architecture
- **Framework**: Flask with CORS enabled and ProxyFix middleware
- **Audio Processing**: Real librosa-based vocal separation and scipy-based effects processing
- **Task Management**: UUID-based background task tracking with threading for non-blocking processing
- **File Upload**: Werkzeug secure filename handling with 50MB limit support
- **Error Handling**: Comprehensive logging with task status tracking and error reporting
- **Audio Pipeline**: Multi-stage processing with progress reporting and MP3 conversion

### Data Storage
- **File Storage**: Local filesystem with `uploads/` and `uploads/processed/` directories
- **Task Storage**: In-memory task tracking with automatic cleanup after 1 hour
- **Audio Formats**: Support for MP3, WAV, FLAC, AAC, M4A with automatic format detection
- **Output Management**: Automatic MP3 conversion for processed files with direct download capability

### Audio Processing Pipeline
- **Real-Time Processing**: Background threading with progress tracking and status updates
- **Vocal Separation**: Advanced harmonic-percussive separation using librosa with spectral subtraction
- **Effects Engine**: 7 professional effects (reverb, echo, chorus, distortion, compressor, equalizer, delay)
- **Quality Control**: Intensity-based effect application with normalization and clipping prevention
- **Demo Generation**: Built-in demo track generator with multiple music styles

## External Dependencies

### Frontend Dependencies
- **Bootstrap 5**: UI framework loaded from Replit CDN with dark theme
- **Font Awesome 6.4.0**: Icon library loaded from cdnjs.cloudflare.com
- **No JavaScript Frameworks**: Pure vanilla JavaScript implementation

### Backend Dependencies
- **Flask**: Core web framework with RESTful API endpoints
- **Flask-CORS**: Cross-origin resource sharing for frontend integration
- **librosa**: Advanced audio analysis and processing library for vocal separation
- **pydub**: Audio file manipulation and format conversion with FFmpeg integration
- **soundfile**: High-quality audio I/O operations
- **numpy & scipy**: Scientific computing for signal processing and effects
- **threading & uuid**: Background task management and unique identifier generation

### Runtime Environment
- **Python 3.11**: Backend runtime with comprehensive audio processing capabilities
- **FFmpeg**: Audio codec support for multiple format handling and conversion
- **File System**: Dual-directory storage with automatic cleanup and organization
- **Environment Variables**: SESSION_SECRET for secure session management

### Current Features (Implemented)
- **Real Audio Processing**: Complete vocal/instrumental separation using advanced algorithms
- **7 Professional Effects**: Reverb, echo, chorus, distortion, compressor, equalizer, and delay
- **Background Processing**: Non-blocking task execution with real-time progress tracking
- **Audio Player**: Built-in playback with waveform visualization and progress tracking
- **Demo Generation**: Multiple demo tracks with different musical styles for testing
- **Modern UI**: Glassmorphism design with smooth animations and responsive layout
- **File Management**: Secure upload, processing, and download with automatic format conversion