# Lions Flute - Audio FX Studio

## Overview

Lions Flute is a web-based audio processing studio that allows users to upload audio files and apply various audio effects. The application is built with Flask as the backend API server and vanilla JavaScript for the frontend interface. It supports multiple audio formats (MP3, WAV, FLAC, AAC, M4A) with a 16MB file size limit and provides functionality for audio splitting and effects processing.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Technology**: Vanilla JavaScript with Bootstrap 5 for UI components
- **Design Pattern**: Class-based component architecture with `LionsFluteApp` as the main controller
- **UI Framework**: Bootstrap 5 with dark theme and Font Awesome icons
- **File Handling**: HTML5 File API for client-side file selection and validation
- **Communication**: Fetch API for REST communication with the backend
- **State Management**: Simple object-based state tracking for current files and processed results

### Backend Architecture
- **Framework**: Flask with CORS enabled for cross-origin requests
- **File Upload**: Werkzeug secure filename handling with configurable upload directory
- **Error Handling**: Centralized logging with DEBUG level configuration
- **Security**: ProxyFix middleware for proper header handling behind proxies
- **Session Management**: Flask sessions with configurable secret key from environment variables

### Data Storage
- **File Storage**: Local filesystem storage in `uploads/` directory
- **File Validation**: Extension-based filtering for allowed audio formats
- **Temporary Processing**: Files stored locally during processing operations

### Audio Processing Pipeline
- **File Upload**: Secure file handling with extension validation
- **Audio Splitting**: Planned functionality for splitting audio files into segments
- **Effects Processing**: Configurable intensity-based audio effects application
- **Output Management**: Processed files tracked and made available for download

## External Dependencies

### Frontend Dependencies
- **Bootstrap 5**: UI framework loaded from Replit CDN with dark theme
- **Font Awesome 6.4.0**: Icon library loaded from cdnjs.cloudflare.com
- **No JavaScript Frameworks**: Pure vanilla JavaScript implementation

### Backend Dependencies
- **Flask**: Core web framework for API endpoints and template rendering
- **Flask-CORS**: Cross-origin resource sharing for frontend integration
- **Werkzeug**: File upload utilities and security helpers
- **Python Standard Library**: os, logging modules for system operations

### Runtime Environment
- **Python**: Backend runtime environment
- **File System**: Local storage for uploaded and processed audio files
- **Environment Variables**: SESSION_SECRET for secure session management

### Audio Processing (Planned)
- The current implementation shows preparation for audio processing capabilities but the actual audio manipulation libraries are not yet integrated
- File structure suggests future integration with audio processing libraries for splitting and effects application