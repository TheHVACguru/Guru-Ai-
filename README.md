# Voice Assistant

A comprehensive open-source voice assistant with smart home control, AI integration, and extensive automation capabilities across all major platforms.

![Voice Assistant](https://img.shields.io/badge/Voice-Assistant-blue?style=for-the-badge&logo=microphone)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11-blue?style=for-the-badge&logo=python)
![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

## 🌟 Features

### 🎤 Voice Control
- **Wake word detection** with customizable trigger words
- **Speech-to-text** conversion using Google Speech API or offline recognition
- **Natural language processing** for command interpretation
- **Text-to-speech synthesis** with multiple voice options
- **Real-time microphone** amplitude visualization

### 🤖 AI Integration
- **OpenAI GPT integration** for unrecognized commands using latest GPT-4o model
- **Face recognition and detection** with camera integration
- **Natural language understanding** for complex command processing
- **Offline mode** with stored command history

### 🏠 Smart Home Control
- **MagicHome lights** control (on/off, dimming, color changing)
- **LG WebOS TV** control (power, volume, channels, apps)
- **Roku device** control (navigation, apps, playback)
- **Garage door** integration
- **Device discovery** and automatic configuration
- **Scene management** (movie time, bedtime, morning, etc.)

### 📱 Communication & Productivity
- **Email sending** via Gmail API
- **Calendar integration** (Google Calendar, Outlook)
- **Weather information** and alerts with OpenWeatherMap
- **Stock market monitoring** with daily alerts using Yahoo Finance
- **News headlines** retrieval from multiple sources
- **Telegram bot** for remote control
- **Reminders and alarms**

### 🎵 Media & Entertainment
- **Music playbook control** (Spotify, YouTube, local)
- **Video streaming** control (Netflix, YouTube, Prime)
- **Camera integration** for photos and video
- **Screen recording** capabilities

### 🔧 System Automation
- **File operations** and system automation
- **Web browsing** automation
- **System controls** (volume, brightness, power)
- **Application launching**
- **Multi-processing** for resource-intensive tasks
- **Thread pool** for concurrent I/O operations

### 🌐 API & Web Interface
- **RESTful API backend** with FastAPI and automatic documentation
- **Web UI** for control and configuration
- **Health monitoring** with auto-restart capabilities
- **File upload/download** via API and Telegram
- **Secure token-based authentication**
- **Real-time status updates**

## 🚀 Quick Start

### Prerequisites

**Supported Operating Systems:**
- **macOS**: Mojave, Catalina, Big Sur, Monterey, Ventura, Sonoma
- **Windows**: 10, 11
- **Linux**: Ubuntu 20.04+, Debian 11+, Fedora 35+

**Required:**
- Python 3.10 or 3.11
- Microphone access
- Internet connection

**Optional:**
- Camera (for face recognition)
- Smart home devices
- API keys for enhanced features

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-repo/voice-assistant.git
   cd voice-assistant
   ```

2. **Install dependencies:**
   ```bash
   python scripts/install.py
   ```

3. **Run setup wizard:**
   ```bash
   python scripts/setup.py
   