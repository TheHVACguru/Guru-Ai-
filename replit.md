# Jarvis - Voice-Activated Natural Language UI

## Overview

Jarvis is a comprehensive voice-activated virtual assistant built in Python. It provides natural language processing capabilities to control various smart devices, perform system operations, handle communications, and execute a wide range of automated tasks through voice commands.

## System Architecture

### Core Components
- **Voice Processing Engine**: Uses PvPorcupine for wake word detection and speech recognition for voice input processing
- **Command Processing Pipeline**: Modular executor system that routes voice commands to appropriate handlers
- **FastAPI Web Server**: RESTful API interface for web-based interactions and remote control
- **Database Layer**: PostgreSQL with SQLite fallback for data persistence (command logs, analytics, user preferences)
- **Audio Engine**: Text-to-speech synthesis and audio playback capabilities

### Application Structure
```
jarvis/
├── main.py                    # Core application entry point and wake word detection
├── api/                       # FastAPI web server implementation
├── executors/                 # Command processing modules
├── modules/                   # Core functionality modules
├── _preexec/                  # Pre-execution keyword handlers
├── tests/                     # Test suite
└── docs/                      # Documentation
```

## Key Components

### 1. Voice Recognition System
- **Wake Word Detection**: PvPorcupine-based activation with configurable sensitivity
- **Speech Recognition**: Google Speech Recognition API integration
- **Text-to-Speech**: Multiple synthesis options including speech synthesis API

### 2. Command Processing Framework
- **Condition Matching**: Keyword-based command routing system
- **Function Mapping**: Ordered dictionary mapping commands to executor functions
- **Custom Conditions**: User-defined command extensions via YAML configuration

### 3. Smart Home Integration
- **Lighting Control**: Support for various smart lighting systems
- **Thermostat Management**: Temperature control automation
- **Security System**: Guard mode with face recognition capabilities

### 4. Communication Services
- **Email Integration**: Gmail connectivity for reading and sending emails
- **Notification System**: SMS and email notification capabilities
- **Calendar Integration**: Event management and scheduling

### 5. System Operations
- **Process Control**: System restart, shutdown, and application management
- **Resource Monitoring**: CPU, memory, and disk usage tracking
- **Automation Framework**: Cron-like scheduling for recurring tasks

## Data Flow

1. **Voice Input Processing**:
   - Wake word detection activates the system
   - Audio capture and speech-to-text conversion
   - Command parsing and keyword matching

2. **Command Execution**:
   - Route to appropriate executor module
   - Execute business logic with error handling
   - Generate response text and audio feedback

3. **API Integration**:
   - RESTful endpoints for external integrations
   - CORS-enabled web interface support
   - Authentication and authorization mechanisms

4. **Data Persistence**:
   - SQLite database for structured data
   - YAML files for configuration and user preferences
   - Log files for debugging and monitoring

## External Dependencies

### Core Libraries
- **PvPorcupine**: Wake word detection engine
- **PyAudio**: Audio input/output handling
- **FastAPI**: Web framework for API services
- **SQLite**: Local database storage
- **PyYAML**: Configuration file management

### Optional Integrations
- **Gmail API**: Email communication
- **Smart Device APIs**: Home automation control
- **Weather Services**: Weather information retrieval
- **Calendar Services**: Event management
- **Stock Market APIs**: Financial data access

### Hardware Dependencies
- **Microphone**: Audio input device
- **Speakers**: Audio output device
- **Camera**: Optional for face recognition features

## Deployment Strategy

### Development Environment
- Python 3.10+ required
- Virtual environment recommended
- Local SQLite database
- Configuration via environment variables

### Production Deployment
- Containerization support
- Process management for API server
- Log rotation and monitoring
- Service-based architecture for modular deployment

### Installation Options
- **Package Installation**: Via pip from PyPI
- **Development Setup**: Clone repository and install dependencies
- **Containerized Deployment**: Docker support for isolated environments

## Changelog
- July 01, 2025: Fixed deployment configuration and health endpoints
  - Configured proper run command: `python main.py` for deployment
  - Added HEAD request support to both root (/) and /health endpoints
  - Verified all health checks return HTTP 200 status codes
  - Application runs on correct host (0.0.0.0) and port (5000) for Cloud Run
  - Confirmed FastAPI application responds properly to all health checks
  - Fixed workflow configuration for reliable deployment startup
- July 01, 2025: Fixed OpenAPI specification and deployment configuration
  - Resolved required vs nullable field contradictions in API schemas
  - Added comprehensive JSON schema examples and documentation
  - Created proper deployment configuration with main.py entry point
  - Fixed health endpoints to support HEAD requests for Cloud Run
  - Added Dockerfile and deployment scripts for containerization
- July 01, 2025: Added PostgreSQL database integration with SQLite fallback
  - Implemented command logging and analytics
  - Added database endpoints for history and statistics
  - Created models for CommandLog, UserPreference, SystemMetric, and ApiKey
- July 01, 2025: Initial setup

## User Preferences

Preferred communication style: Simple, everyday language.