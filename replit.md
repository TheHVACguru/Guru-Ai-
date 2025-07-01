# Voice Assistant Replit Guide

## Overview

This is a comprehensive open-source voice assistant application that provides smart home control, AI integration, and extensive automation capabilities. The system is built using Python 3.10+ and offers both voice-activated commands and a web-based control interface. The application uses a modular architecture with clear separation of concerns between core voice processing, command handling, device integrations, and API services.

## System Architecture

The application follows a layered architecture pattern:

- **Core Layer**: Handles voice processing (wake word detection, speech recognition, text-to-speech)
- **Command Layer**: Processes and routes voice commands to appropriate handlers
- **Integration Layer**: Manages external service integrations (OpenAI, weather, stock, news, etc.)
- **Device Layer**: Controls smart home devices and system hardware
- **API Layer**: Provides REST API and web UI for remote control
- **Utility Layer**: Shared utilities for logging, permissions, and helpers

The main application entry point is `main.py` which orchestrates all components through a central `VoiceAssistant` class.

## Key Components

### Core Voice Processing
- **Wake Word Detection**: Uses Porcupine for customizable wake word detection
- **Speech Recognition**: Google Speech API with offline fallback using speech_recognition library
- **Text-to-Speech**: Cross-platform TTS using pyttsx3
- **Audio Management**: PyAudio for microphone and speaker control

### Command Processing
- **Command Router**: Central processor that routes commands to specialized handlers
- **System Commands**: Time, date, system information, file operations
- **Media Commands**: Music control, camera operations, screen recording
- **Information Commands**: Weather, stocks, news, AI-powered responses
- **Communication Commands**: Email, calendar, reminders, Telegram integration
- **Automation Commands**: Smart home device control and scene management

### External Integrations
- **OpenAI**: GPT-4 integration for natural language processing of unrecognized commands
- **Google Services**: Gmail API for email, Google Calendar for scheduling
- **Weather**: OpenWeatherMap API for weather information
- **Stock Market**: Yahoo Finance for stock prices and market data
- **News**: NewsAPI for current headlines
- **Telegram**: Bot integration for remote control

### Smart Home Control
- **MagicHome Lights**: RGB light control with color and brightness adjustment
- **LG WebOS TV**: Television control for power, volume, channels, and apps
- **Roku Devices**: Media streaming device navigation and control
- **Camera Integration**: Face recognition and detection capabilities

### Web Interface
- **FastAPI Backend**: RESTful API with authentication
- **HTML/CSS/JS Frontend**: Real-time control panel with voice visualization
- **WebSocket Support**: Live status updates and streaming capabilities

## Data Flow

1. **Voice Input**: Wake word detector activates → Speech recognition captures command → Text processed by command router
2. **Command Processing**: Router identifies command type → Appropriate handler processes request → Response generated
3. **Response Output**: Text-to-speech synthesis → Audio output through speakers
4. **API Requests**: Web UI sends HTTP requests → FastAPI processes → Commands routed to processors → JSON responses returned
5. **Smart Home Control**: Commands trigger device-specific APIs → Status updates propagated back to UI

## External Dependencies

### Core Dependencies
- **speech_recognition**: Google Speech API and offline recognition
- **pyttsx3**: Cross-platform text-to-speech synthesis
- **pyaudio**: Audio input/output handling
- **pvporcupine**: Wake word detection engine
- **opencv-python**: Computer vision and face recognition
- **face_recognition**: Facial detection and identification

### API and Integration Dependencies
- **fastapi**: Web API framework with async support
- **uvicorn**: ASGI server for FastAPI
- **openai**: GPT integration for AI responses
- **google-auth**, **google-auth-oauthlib**, **google-api-python-client**: Google services integration
- **aiohttp**: Async HTTP client for external APIs
- **python-telegram-bot**: Telegram bot integration

### Smart Home Dependencies
- **magichome**: RGB light control (optional)
- **pywebostv**: LG TV control (optional)
- **roku**: Roku device control (optional)

### Data and Utility Dependencies
- **yfinance**: Stock market data
- **python-dotenv**: Environment variable management
- **python-jose**: JWT token handling

## Deployment Strategy

The application is designed for local deployment on personal devices with the following considerations:

1. **Installation Process**: 
   - `scripts/install.py` handles OS-specific dependency installation
   - `scripts/setup.py` provides guided configuration wizard
   - Environment variables configured through `.env` file

2. **Platform Support**: Cross-platform compatibility for Linux, macOS, and Windows

3. **Permission Requirements**: Microphone access, camera access (optional), accessibility permissions on macOS

4. **Configuration Management**: Environment-based configuration with sensible defaults

5. **API Security**: Token-based authentication for web interface and remote access

6. **Storage**: Local file storage for face recognition data, configuration, and logs

The system is primarily intended for single-user local deployment rather than multi-tenant cloud deployment, focusing on privacy and personal automation.

## Changelog

- July 01, 2025. Initial setup

## User Preferences

Preferred communication style: Simple, everyday language.