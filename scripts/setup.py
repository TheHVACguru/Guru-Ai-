#!/usr/bin/env python3
"""
Setup wizard for Voice Assistant configuration.
Guides users through initial configuration and testing.
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
import getpass

def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def print_step(step: int, total: int, description: str):
    """Print a step indicator."""
    print(f"\n📋 Step {step}/{total}: {description}")
    print("-" * 40)

def get_user_input(prompt: str, default: str = "", required: bool = False, password: bool = False) -> str:
    """Get user input with optional default and validation."""
    while True:
        if default:
            display_prompt = f"{prompt} [{default}]: "
        else:
            display_prompt = f"{prompt}: "
        
        if password:
            value = getpass.getpass(display_prompt)
        else:
            value = input(display_prompt).strip()
        
        if not value and default:
            return default
        elif not value and required:
            print("❌ This field is required. Please enter a value.")
            continue
        else:
            return value

def yes_no_prompt(prompt: str, default: bool = True) -> bool:
    """Get yes/no input from user."""
    default_str = "Y/n" if default else "y/N"
    response = input(f"{prompt} [{default_str}]: ").strip().lower()
    
    if not response:
        return default
    
    return response in ['y', 'yes', 'true', '1']

def test_api_key(service: str, api_key: str) -> bool:
    """Test an API key by making a simple request."""
    if not api_key:
        return False
    
    try:
        if service == "openai":
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            # Test with a simple completion
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=5
            )
            return True
            
        elif service == "weather":
            import requests
            url = f"http://api.openweathermap.org/data/2.5/weather?q=London&appid={api_key}"
            response = requests.get(url, timeout=10)
            return response.status_code == 200
            
        elif service == "news":
            import requests
            url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={api_key}"
            response = requests.get(url, timeout=10)
            return response.status_code == 200
            
    except Exception as e:
        print(f"   ❌ API test failed: {e}")
        return False
    
    return False

def setup_api_keys() -> Dict[str, str]:
    """Setup API keys for various services."""
    print_step(1, 6, "API Keys Configuration")
    
    print("🔑 Configure API keys for external services.")
    print("   You can skip any service by pressing Enter.")
    print("   API keys will be tested if provided.")
    
    api_keys = {}
    
    # OpenAI API Key
    print("\n🤖 OpenAI API Key (for AI features):")
    print("   Get your key from: https://platform.openai.com/api-keys")
    openai_key = get_user_input("OpenAI API Key", password=True)
    
    if openai_key:
        print("   Testing OpenAI API key...")
        if test_api_key("openai", openai_key):
            print("   ✅ OpenAI API key is valid")
            api_keys["OPENAI_API_KEY"] = openai_key
        else:
            print("   ❌ OpenAI API key test failed")
            if yes_no_prompt("   Use this key anyway?", False):
                api_keys["OPENAI_API_KEY"] = openai_key
    
    # Weather API Key
    print("\n🌤️  Weather API Key (for weather information):")
    print("   Get your key from: https://openweathermap.org/api")
    weather_key = get_user_input("Weather API Key", password=True)
    
    if weather_key:
        print("   Testing Weather API key...")
        if test_api_key("weather", weather_key):
            print("   ✅ Weather API key is valid")
            api_keys["WEATHER_API_KEY"] = weather_key
        else:
            print("   ❌ Weather API key test failed")
            if yes_no_prompt("   Use this key anyway?", False):
                api_keys["WEATHER_API_KEY"] = weather_key
    
    # News API Key
    print("\n📰 News API Key (for news headlines):")
    print("   Get your key from: https://newsapi.org/register")
    news_key = get_user_input("News API Key", password=True)
    
    if news_key:
        print("   Testing News API key...")
        if test_api_key("news", news_key):
            print("   ✅ News API key is valid")
            api_keys["NEWS_API_KEY"] = news_key
        else:
            print("   ❌ News API key test failed")
            if yes_no_prompt("   Use this key anyway?", False):
                api_keys["NEWS_API_KEY"] = news_key
    
    # Telegram Bot Token
    print("\n📱 Telegram Bot Token (for remote control):")
    print("   Create a bot with @BotFather on Telegram")
    telegram_token = get_user_input("Telegram Bot Token", password=True)
    if telegram_token:
        api_keys["TELEGRAM_BOT_TOKEN"] = telegram_token
        
        chat_id = get_user_input("Telegram Chat ID (optional)")
        if chat_id:
            api_keys["TELEGRAM_CHAT_ID"] = chat_id
    
    return api_keys

def setup_voice_settings() -> Dict[str, str]:
    """Setup voice and audio settings."""
    print_step(2, 6, "Voice & Audio Configuration")
    
    settings = {}
    
    print("🎤 Configure voice and audio settings:")
    
    # Wake word
    wake_word = get_user_input("Wake word", "assistant")
    settings["WAKE_WORD"] = wake_word
    
    # Language
    print("\nAvailable languages:")
    languages = {
        "1": ("en-US", "English (US)"),
        "2": ("en-GB", "English (UK)"),
        "3": ("es-ES", "Spanish"),
        "4": ("fr-FR", "French"),
        "5": ("de-DE", "German")
    }
    
    for key, (code, name) in languages.items():
        print(f"   {key}. {name}")
    
    lang_choice = get_user_input("Select language", "1")
    if lang_choice in languages:
        settings["LANGUAGE"] = languages[lang_choice][0]
    else:
        settings["LANGUAGE"] = "en-US"
    
    # Sensitivity
    sensitivity = get_user_input("Wake word sensitivity (0.1-1.0)", "0.5")
    try:
        sens_val = float(sensitivity)
        if 0.1 <= sens_val <= 1.0:
            settings["SENSITIVITY"] = sensitivity
        else:
            settings["SENSITIVITY"] = "0.5"
    except ValueError:
        settings["SENSITIVITY"] = "0.5"
    
    # Voice rate
    voice_rate = get_user_input("Speech rate (words per minute)", "200")
    try:
        rate_val = int(voice_rate)
        if 50 <= rate_val <= 400:
            settings["VOICE_RATE"] = voice_rate
        else:
            settings["VOICE_RATE"] = "200"
    except ValueError:
        settings["VOICE_RATE"] = "200"
    
    return settings

def setup_smart_home() -> Dict[str, str]:
    """Setup smart home configuration."""
    print_step(3, 6, "Smart Home Configuration")
    
    settings = {}
    
    print("🏠 Configure smart home integration:")
    
    enable_smart_home = yes_no_prompt("Enable smart home features?", True)
    settings["ENABLE_SMART_HOME"] = str(enable_smart_home).lower()
    
    if enable_smart_home:
        # MagicHome lights
        print("\n💡 MagicHome Smart Lights:")
        print("   Enter IP addresses of your MagicHome lights (comma-separated)")
        magic_home_ips = get_user_input("MagicHome device IPs")
        if magic_home_ips:
            settings["MAGIC_HOME_DEVICES"] = magic_home_ips
        
        # LG TV
        print("\n📺 LG WebOS TV:")
        lg_tv_ip = get_user_input("LG TV IP address")
        if lg_tv_ip:
            settings["LG_TV_IP"] = lg_tv_ip
        
        # Roku
        print("\n📱 Roku Device:")
        roku_ip = get_user_input("Roku device IP address")
        if roku_ip:
            settings["ROKU_IP"] = roku_ip
    
    return settings

def setup_security() -> Dict[str, str]:
    """Setup security and privacy settings."""
    print_step(4, 6, "Security & Privacy Configuration")
    
    settings = {}
    
    print("🔒 Configure security and privacy settings:")
    
    # Face recognition
    enable_face_recognition = yes_no_prompt("Enable face recognition?", False)
    settings["ENABLE_FACE_RECOGNITION"] = str(enable_face_recognition).lower()
    
    # API token
    print("\n🔑 API Security:")
    print("   Generate a secure token for API access")
    api_token = get_user_input("API Token (leave empty to generate)", "")
    
    if not api_token:
        import secrets
        api_token = secrets.token_urlsafe(32)
        print(f"   Generated token: {api_token}")
    
    settings["API_TOKEN"] = api_token
    
    # JWT secret
    jwt_secret = get_user_input("JWT Secret (leave empty to generate)", "")
    if not jwt_secret:
        import secrets
        jwt_secret = secrets.token_urlsafe(64)
        print(f"   Generated JWT secret: {jwt_secret[:20]}...")
    
    settings["JWT_SECRET"] = jwt_secret
    
    # Debug mode
    debug_mode = yes_no_prompt("Enable debug mode?", False)
    settings["DEBUG_MODE"] = str(debug_mode).lower()
    
    return settings

def test_audio_devices() -> bool:
    """Test audio devices."""
    print_step(5, 6, "Audio Device Testing")
    
    print("🔊 Testing audio devices...")
    
    try:
        # Test microphone
        print("\n🎤 Testing microphone...")
        print("   Please speak for 3 seconds...")
        
        import pyaudio
        import wave
        import tempfile
        
        # Record audio
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100
        RECORD_SECONDS = 3
        
        p = pyaudio.PyAudio()
        
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK
        )
        
        frames = []
        for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK)
            frames.append(data)
        
        stream.stop_stream()
        stream.close()
        
        # Save and play back
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            wf = wave.open(temp_file.name, 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
            wf.close()
            
            print("   ✅ Microphone recording completed")
            
            # Test playback
            if yes_no_prompt("   Play back recording?", True):
                print("   🔊 Playing back recording...")
                
                # Simple playback
                wf = wave.open(temp_file.name, 'rb')
                
                stream = p.open(
                    format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True
                )
                
                data = wf.readframes(CHUNK)
                while data:
                    stream.write(data)
                    data = wf.readframes(CHUNK)
                
                stream.stop_stream()
                stream.close()
                wf.close()
                
                print("   ✅ Speaker playback completed")
            
            # Clean up
            os.unlink(temp_file.name)
        
        p.terminate()
        return True
        
    except Exception as e:
        print(f"   ❌ Audio test failed: {e}")
        print("   The application may still work, but audio features might be limited")
        return False

def create_env_file(settings: Dict[str, str]) -> bool:
    """Create the .env file with all settings."""
    print_step(6, 6, "Creating Configuration File")
    
    print("💾 Creating .env configuration file...")
    
    # Load existing .env.example as template
    env_example_path = Path(".env.example")
    env_path = Path(".env")
    
    try:
        # Start with example file if it exists
        if env_example_path.exists():
            with open(env_example_path, 'r') as f:
                content = f.read()
        else:
            content = ""
        
        # Update with user settings
        for key, value in settings.items():
            # Check if key already exists in content
            import re
            pattern = rf'^{key}=.*$'
            replacement = f'{key}={value}'
            
            if re.search(pattern, content, re.MULTILINE):
                content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
            else:
                content += f'\n{key}={value}'
        
        # Write to .env file
        with open(env_path, 'w') as f:
            f.write(content)
        
        print("   ✅ Configuration file created successfully")
        return True
        
    except Exception as e:
        print(f"   ❌ Failed to create configuration file: {e}")
        return False

def print_setup_complete():
    """Print setup completion message."""
    print("\n" + "="*60)
    print("🎉 SETUP COMPLETE!")
    print("="*60)
    print()
    print("✅ Your Voice Assistant is now configured and ready to use!")
    print()
    print("🚀 Quick Start:")
    print("   python main.py                    # Start full assistant")
    print("   python main.py --api-only         # Start API server only")
    print()
    print("🌐 Access Points:")
    print("   Web UI: http://localhost:5000")
    print("   API:    http://localhost:8000")
    print("   Docs:   http://localhost:8000/docs")
    print()
    print("📚 For more information:")
    print("   - Check README.md for detailed documentation")
    print("   - Edit .env file to modify settings")
    print("   - Run python main.py --help for options")
    print()
    print("🎤 Try saying:")
    print(f"   - '{os.getenv('WAKE_WORD', 'assistant')}, what time is it?'")
    print(f"   - '{os.getenv('WAKE_WORD', 'assistant')}, what's the weather?'")
    print(f"   - '{os.getenv('WAKE_WORD', 'assistant')}, tell me the news'")
    print()
    print("="*60)

def main():
    """Main setup function."""
    clear_screen()
    print_header("🤖 Voice Assistant Setup Wizard")
    
    print("Welcome to the Voice Assistant setup wizard!")
    print("This will guide you through the initial configuration.")
    print()
    
    if not yes_no_prompt("Continue with setup?", True):
        print("Setup cancelled.")
        return
    
    all_settings = {}
    
    try:
        # Step 1: API Keys
        api_settings = setup_api_keys()
        all_settings.update(api_settings)
        
        # Step 2: Voice Settings  
        voice_settings = setup_voice_settings()
        all_settings.update(voice_settings)
        
        # Step 3: Smart Home
        smart_home_settings = setup_smart_home()
        all_settings.update(smart_home_settings)
        
        # Step 4: Security
        security_settings = setup_security()
        all_settings.update(security_settings)
        
        # Step 5: Audio Testing
        audio_working = test_audio_devices()
        
        # Step 6: Create configuration file
        if create_env_file(all_settings):
            print_setup_complete()
        else:
            print("❌ Setup completed with errors")
            print("   Please check the configuration and try again")
            
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
