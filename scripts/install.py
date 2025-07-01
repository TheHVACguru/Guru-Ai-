#!/usr/bin/env python3
"""
Installation script for Voice Assistant dependencies.
Installs OS-specific and OS-agnostic dependencies for the voice assistant.
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any

def get_system_info() -> Dict[str, str]:
    """Get system information."""
    return {
        'system': platform.system(),
        'architecture': platform.machine(),
        'python_version': platform.python_version(),
        'platform': platform.platform()
    }

def check_python_version() -> bool:
    """Check if Python version is supported."""
    version = sys.version_info
    if version.major != 3 or version.minor < 10 or version.minor > 11:
        print("❌ Python 3.10 or 3.11 is required")
        print(f"Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is supported")
    return True

def run_command(command: List[str], description: str = "", ignore_errors: bool = False) -> bool:
    """Run a system command and return success status."""
    if description:
        print(f"📦 {description}")
    
    try:
        result = subprocess.run(
            command, 
            check=True, 
            capture_output=True, 
            text=True
        )
        if result.stdout:
            print(f"   {result.stdout.strip()}")
        return True
        
    except subprocess.CalledProcessError as e:
        if not ignore_errors:
            print(f"❌ Command failed: {' '.join(command)}")
            if e.stderr:
                print(f"   Error: {e.stderr.strip()}")
            if e.stdout:
                print(f"   Output: {e.stdout.strip()}")
        return False
    except FileNotFoundError:
        if not ignore_errors:
            print(f"❌ Command not found: {command[0]}")
        return False

def check_command_exists(command: str) -> bool:
    """Check if a command exists in PATH."""
    return shutil.which(command) is not None

def install_python_dependencies() -> bool:
    """Install Python dependencies."""
    print("\n🐍 Installing Python dependencies...")
    
    # Core dependencies
    core_deps = [
        "fastapi>=0.104.0",
        "uvicorn[standard]>=0.24.0",
        "pydantic>=2.5.0",
        "python-dotenv>=1.0.0",
        "aiohttp>=3.9.0",
        "requests>=2.31.0",
        "python-jose[cryptography]>=3.3.0",
        "psutil>=5.9.0",
        "pytz>=2023.3",
        "PyYAML>=6.0"
    ]
    
    # Voice and audio dependencies
    voice_deps = [
        "pvporcupine>=3.0.0",
        "SpeechRecognition>=3.10.0",
        "pyttsx3>=2.90",
        "pyaudio>=0.2.11",
        "sounddevice>=0.4.6",
        "matplotlib>=3.8.0",
        "numpy>=1.24.0"
    ]
    
    # AI and vision dependencies
    ai_deps = [
        "openai>=1.3.0",
        "opencv-python>=4.8.0",
        "face-recognition>=1.3.0"
    ]
    
    # Integration dependencies
    integration_deps = [
        "google-api-python-client>=2.108.0",
        "google-auth-oauthlib>=1.1.0",
        "python-telegram-bot>=20.7",
        "yfinance>=0.2.20",
        "pyowm>=3.3.0"
    ]
    
    # Optional smart home dependencies
    smart_home_deps = [
        "python-magichome>=0.2.5",
        "pywebostv>=0.8.9",
        "roku>=4.1.0"
    ]
    
    all_deps = core_deps + voice_deps + ai_deps + integration_deps + smart_home_deps
    
    # Install dependencies in chunks to handle potential conflicts
    for deps_group, name in [
        (core_deps, "core dependencies"),
        (voice_deps, "voice and audio dependencies"),
        (ai_deps, "AI and vision dependencies"), 
        (integration_deps, "integration dependencies"),
        (smart_home_deps, "smart home dependencies (optional)")
    ]:
        print(f"\n  Installing {name}...")
        for dep in deps_group:
            success = run_command([
                sys.executable, "-m", "pip", "install", dep
            ], ignore_errors=(name == "smart home dependencies (optional)"))
            
            if not success and name != "smart home dependencies (optional)":
                print(f"❌ Failed to install {dep}")
                return False
    
    print("✅ Python dependencies installed successfully")
    return True

def install_system_dependencies_linux() -> bool:
    """Install system dependencies on Linux."""
    print("\n🐧 Installing Linux system dependencies...")
    
    # Check if we can use apt-get
    if not check_command_exists("apt-get"):
        print("⚠️  apt-get not found. Please install dependencies manually:")
        print("   - portaudio19-dev")
        print("   - python3-dev") 
        print("   - build-essential")
        print("   - cmake")
        print("   - libffi-dev")
        print("   - alsa-utils")
        print("   - pulseaudio")
        return True
    
    deps = [
        "portaudio19-dev",
        "python3-dev",
        "build-essential", 
        "cmake",
        "libffi-dev",
        "alsa-utils",
        "pulseaudio",
        "xbacklight"  # For brightness control
    ]
    
    # Update package list
    run_command(["sudo", "apt-get", "update"], "Updating package list")
    
    # Install dependencies
    for dep in deps:
        success = run_command([
            "sudo", "apt-get", "install", "-y", dep
        ], f"Installing {dep}", ignore_errors=True)
    
    print("✅ Linux system dependencies installation attempted")
    return True

def install_system_dependencies_macos() -> bool:
    """Install system dependencies on macOS."""
    print("\n🍎 Installing macOS system dependencies...")
    
    # Check if Homebrew is available
    if not check_command_exists("brew"):
        print("⚠️  Homebrew not found. Please install Homebrew first:")
        print("   /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
        return True
    
    deps = [
        "portaudio",
        "cmake", 
        "pkg-config"
    ]
    
    for dep in deps:
        run_command(["brew", "install", dep], f"Installing {dep}", ignore_errors=True)
    
    print("✅ macOS system dependencies installation attempted")
    return True

def install_system_dependencies_windows() -> bool:
    """Install system dependencies on Windows."""
    print("\n🪟 Windows system dependencies...")
    print("  Please ensure you have:")
    print("  - Microsoft Visual C++ Build Tools")
    print("  - Git for Windows")
    print("  - Windows SDK (if needed)")
    print("  ℹ️  These are typically installed with Visual Studio or Build Tools")
    return True

def create_data_directories() -> bool:
    """Create necessary data directories."""
    print("\n📁 Creating data directories...")
    
    directories = [
        "data",
        "data/logs",
        "data/uploads", 
        "data/photos",
        "data/faces",
        "data/audio",
        "data/cache"
    ]
    
    for directory in directories:
        try:
            Path(directory).mkdir(parents=True, exist_ok=True)
            print(f"   ✅ Created {directory}")
        except Exception as e:
            print(f"   ❌ Failed to create {directory}: {e}")
            return False
    
    return True

def setup_environment_file() -> bool:
    """Set up environment configuration file."""
    print("\n⚙️  Setting up environment configuration...")
    
    env_example = Path(".env.example")
    env_file = Path(".env")
    
    if not env_file.exists() and env_example.exists():
        try:
            shutil.copy(env_example, env_file)
            print("   ✅ Created .env file from .env.example")
            print("   ⚠️  Please edit .env file to configure your API keys and settings")
        except Exception as e:
            print(f"   ❌ Failed to create .env file: {e}")
            return False
    elif env_file.exists():
        print("   ✅ .env file already exists")
    else:
        print("   ⚠️  .env.example not found, please create .env file manually")
    
    return True

def verify_installation() -> bool:
    """Verify that the installation was successful."""
    print("\n🔍 Verifying installation...")
    
    # Test imports
    test_imports = [
        ("fastapi", "FastAPI framework"),
        ("uvicorn", "ASGI server"),
        ("pydantic", "Data validation"),
        ("speech_recognition", "Speech recognition"),
        ("pyttsx3", "Text-to-speech"),
        ("pvporcupine", "Wake word detection"),
        ("openai", "OpenAI API"),
        ("requests", "HTTP requests"),
        ("numpy", "Numerical computing")
    ]
    
    failed_imports = []
    
    for module, description in test_imports:
        try:
            __import__(module)
            print(f"   ✅ {description}")
        except ImportError as e:
            print(f"   ❌ {description}: {e}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"\n❌ Some modules failed to import: {', '.join(failed_imports)}")
        print("   You may need to install them manually or check for compatibility issues")
        return False
    
    print("\n✅ Installation verification completed successfully")
    return True

def print_next_steps():
    """Print next steps after installation."""
    print("\n" + "="*60)
    print("🎉 INSTALLATION COMPLETE!")
    print("="*60)
    print()
    print("📋 Next steps:")
    print("   1. Edit .env file with your API keys:")
    print("      - OPENAI_API_KEY (for AI features)")
    print("      - WEATHER_API_KEY (for weather)")
    print("      - NEWS_API_KEY (for news)")
    print("      - TELEGRAM_BOT_TOKEN (for Telegram bot)")
    print()
    print("   2. Run the setup wizard:")
    print("      python -m scripts.setup")
    print()
    print("   3. Start the Voice Assistant:")
    print("      python main.py")
    print()
    print("   4. Or start API server only:")
    print("      python main.py --api-only")
    print()
    print("🌐 Web UI will be available at: http://localhost:5000")
    print("📚 API documentation at: http://localhost:8000/docs")
    print()
    print("⚠️  Remember to configure permissions:")
    print("   - Microphone access")
    print("   - Camera access (optional)")
    print("   - System control permissions")
    print()
    print("For more information, see README.md")
    print("="*60)

def main():
    """Main installation function."""
    print("🤖 Voice Assistant Installation Script")
    print("=====================================")
    
    # Print system information
    system_info = get_system_info()
    print(f"\n💻 System: {system_info['system']} {system_info['architecture']}")
    print(f"🐍 Python: {system_info['python_version']}")
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install system dependencies based on OS
    system = system_info['system'].lower()
    
    if system == "linux":
        if not install_system_dependencies_linux():
            print("❌ Failed to install system dependencies")
            sys.exit(1)
    elif system == "darwin":
        if not install_system_dependencies_macos():
            print("❌ Failed to install system dependencies")
            sys.exit(1)
    elif system == "windows":
        install_system_dependencies_windows()
    else:
        print(f"⚠️  Unknown system: {system}")
        print("   Please install system dependencies manually")
    
    # Install Python dependencies
    if not install_python_dependencies():
        print("❌ Failed to install Python dependencies")
        sys.exit(1)
    
    # Create data directories
    if not create_data_directories():
        print("❌ Failed to create data directories")
        sys.exit(1)
    
    # Setup environment file
    if not setup_environment_file():
        print("❌ Failed to setup environment file")
        sys.exit(1)
    
    # Verify installation
    if not verify_installation():
        print("⚠️  Installation completed with some issues")
        print("   The application may still work, but some features might be limited")
    
    # Print next steps
    print_next_steps()

if __name__ == "__main__":
    main()
