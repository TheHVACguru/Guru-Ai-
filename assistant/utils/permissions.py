"""
Permission checking utilities for Voice Assistant.
"""

import os
import platform
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from assistant.utils.logger import setup_logger

logger = setup_logger(__name__)

def check_permissions() -> bool:
    """Check if the application has necessary permissions."""
    try:
        system = platform.system().lower()
        
        if system == "darwin":
            return check_macos_permissions()
        elif system == "windows":
            return check_windows_permissions()
        elif system == "linux":
            return check_linux_permissions()
        else:
            logger.warning(f"Unknown operating system: {system}")
            return True  # Assume permissions are OK
            
    except Exception as e:
        logger.error(f"Error checking permissions: {e}")
        return False

def check_macos_permissions() -> bool:
    """Check macOS specific permissions."""
    permissions_ok = True
    
    # Check microphone permission
    mic_permission = check_microphone_permission_macos()
    if not mic_permission:
        logger.warning("Microphone permission not granted")
        permissions_ok = False
    
    # Check accessibility permission
    accessibility_permission = check_accessibility_permission_macos()
    if not accessibility_permission:
        logger.warning("Accessibility permission not granted")
        permissions_ok = False
    
    # Check file system permissions
    fs_permission = check_file_system_permissions()
    if not fs_permission:
        logger.warning("File system permissions may be limited")
        permissions_ok = False
    
    if permissions_ok:
        logger.info("All macOS permissions are properly configured")
    else:
        logger.error("Some macOS permissions are missing. Please check System Preferences > Security & Privacy")
        print_macos_permission_instructions()
    
    return permissions_ok

def check_microphone_permission_macos() -> bool:
    """Check microphone permission on macOS."""
    try:
        # Try to access microphone using system command
        result = subprocess.run(
            ["system_profiler", "SPAudioDataType"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # If command succeeds, microphone access is likely available
        return result.returncode == 0
        
    except Exception as e:
        logger.debug(f"Error checking microphone permission: {e}")
        return False

def check_accessibility_permission_macos() -> bool:
    """Check accessibility permission on macOS."""
    try:
        # Try to use AppleScript to check accessibility
        script = '''
        tell application "System Events"
            return name of first process
        end tell
        '''
        
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        return result.returncode == 0
        
    except Exception as e:
        logger.debug(f"Error checking accessibility permission: {e}")
        return False

def check_windows_permissions() -> bool:
    """Check Windows specific permissions."""
    permissions_ok = True
    
    # Check microphone permission (basic test)
    mic_permission = check_microphone_permission_windows()
    if not mic_permission:
        logger.warning("Microphone access may be restricted")
        permissions_ok = False
    
    # Check file system permissions
    fs_permission = check_file_system_permissions()
    if not fs_permission:
        logger.warning("File system permissions may be limited")
        permissions_ok = False
    
    # Check if running as administrator (optional)
    admin_check = check_admin_windows()
    if not admin_check:
        logger.info("Not running as administrator (this is usually fine)")
    
    if permissions_ok:
        logger.info("Windows permissions appear to be properly configured")
    else:
        logger.error("Some Windows permissions may be missing")
        print_windows_permission_instructions()
    
    return permissions_ok

def check_microphone_permission_windows() -> bool:
    """Check microphone permission on Windows."""
    try:
        # Try to access microphone using basic test
        import pyaudio
        
        pa = pyaudio.PyAudio()
        
        # Get default input device
        try:
            device_info = pa.get_default_input_device_info()
            pa.terminate()
            return device_info is not None
        except Exception:
            pa.terminate()
            return False
            
    except ImportError:
        logger.debug("PyAudio not available for microphone test")
        return True  # Assume it's OK if we can't test
    except Exception as e:
        logger.debug(f"Error checking microphone permission: {e}")
        return False

def check_admin_windows() -> bool:
    """Check if running as administrator on Windows."""
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

def check_linux_permissions() -> bool:
    """Check Linux specific permissions."""
    permissions_ok = True
    
    # Check audio group membership
    audio_permission = check_audio_group_linux()
    if not audio_permission:
        logger.warning("User not in audio group")
        permissions_ok = False
    
    # Check file system permissions
    fs_permission = check_file_system_permissions()
    if not fs_permission:
        logger.warning("File system permissions may be limited")
        permissions_ok = False
    
    # Check for required tools
    tools_available = check_required_tools_linux()
    if not tools_available:
        logger.warning("Some required tools are missing")
        permissions_ok = False
    
    if permissions_ok:
        logger.info("Linux permissions and requirements are properly configured")
    else:
        logger.error("Some Linux permissions or tools are missing")
        print_linux_permission_instructions()
    
    return permissions_ok

def check_audio_group_linux() -> bool:
    """Check if user is in audio group on Linux."""
    try:
        import grp
        import os
        
        # Get current user ID
        uid = os.getuid()
        
        # Get user's groups
        user_groups = [g.gr_gid for g in grp.getgrall() if uid in g.gr_mem]
        
        # Check if audio group is in user's groups
        try:
            audio_group = grp.getgrnam('audio')
            return audio_group.gr_gid in user_groups
        except KeyError:
            # Audio group doesn't exist, which is fine on some systems
            return True
            
    except Exception as e:
        logger.debug(f"Error checking audio group: {e}")
        return True  # Assume it's OK if we can't check

def check_required_tools_linux() -> bool:
    """Check if required tools are available on Linux."""
    required_tools = ['amixer', 'aplay', 'arecord']
    missing_tools = []
    
    for tool in required_tools:
        if not check_command_available(tool):
            missing_tools.append(tool)
    
    if missing_tools:
        logger.warning(f"Missing tools: {', '.join(missing_tools)}")
        return False
    
    return True

def check_file_system_permissions() -> bool:
    """Check basic file system permissions."""
    try:
        # Test write permission in current directory
        test_file = Path.cwd() / "permission_test.tmp"
        
        try:
            with open(test_file, 'w') as f:
                f.write("test")
            
            # Test read permission
            with open(test_file, 'r') as f:
                content = f.read()
            
            # Clean up
            test_file.unlink()
            
            return content == "test"
            
        except Exception:
            # Try in temp directory
            with tempfile.NamedTemporaryFile(mode='w', delete=True) as f:
                f.write("test")
                f.flush()
                
                with open(f.name, 'r') as rf:
                    content = rf.read()
                
                return content == "test"
                
    except Exception as e:
        logger.debug(f"Error checking file system permissions: {e}")
        return False

def check_command_available(command: str) -> bool:
    """Check if a command is available in PATH."""
    try:
        result = subprocess.run(
            ["which", command] if platform.system() != "Windows" else ["where", command],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except Exception:
        return False

def check_network_permissions() -> bool:
    """Check network access permissions."""
    try:
        import socket
        
        # Test basic network connectivity
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        try:
            result = sock.connect_ex(("8.8.8.8", 53))  # Google DNS
            sock.close()
            return result == 0
        except Exception:
            sock.close()
            return False
            
    except Exception as e:
        logger.debug(f"Error checking network permissions: {e}")
        return False

def print_macos_permission_instructions():
    """Print instructions for setting up macOS permissions."""
    print("\n" + "="*60)
    print("macOS PERMISSION SETUP REQUIRED")
    print("="*60)
    print("To use Voice Assistant properly, please grant the following permissions:")
    print()
    print("1. MICROPHONE ACCESS:")
    print("   • Go to System Preferences > Security & Privacy > Privacy")
    print("   • Select 'Microphone' from the left sidebar")
    print("   • Check the box next to your terminal/IDE application")
    print()
    print("2. ACCESSIBILITY ACCESS (for system controls):")
    print("   • Go to System Preferences > Security & Privacy > Privacy")
    print("   • Select 'Accessibility' from the left sidebar")
    print("   • Click the lock icon and enter your password")
    print("   • Check the box next to your terminal/IDE application")
    print()
    print("3. FILES AND FOLDERS ACCESS:")
    print("   • Go to System Preferences > Security & Privacy > Privacy")
    print("   • Select 'Files and Folders' from the left sidebar")
    print("   • Grant access to folders as needed")
    print()
    print("4. CAMERA ACCESS (optional, for face recognition):")
    print("   • Go to System Preferences > Security & Privacy > Privacy")
    print("   • Select 'Camera' from the left sidebar")
    print("   • Check the box next to your terminal/IDE application")
    print()
    print("After granting permissions, restart the application.")
    print("="*60)

def print_windows_permission_instructions():
    """Print instructions for setting up Windows permissions."""
    print("\n" + "="*60)
    print("WINDOWS PERMISSION SETUP")
    print("="*60)
    print("To use Voice Assistant properly, please check the following:")
    print()
    print("1. MICROPHONE ACCESS:")
    print("   • Go to Settings > Privacy > Microphone")
    print("   • Make sure 'Allow apps to access your microphone' is ON")
    print("   • Allow your terminal/IDE application to access microphone")
    print()
    print("2. CAMERA ACCESS (optional, for face recognition):")
    print("   • Go to Settings > Privacy > Camera")
    print("   • Make sure 'Allow apps to access your camera' is ON")
    print("   • Allow your terminal/IDE application to access camera")
    print()
    print("3. FIREWALL SETTINGS:")
    print("   • If you encounter network issues, check Windows Firewall")
    print("   • Allow Python through Windows Defender Firewall")
    print()
    print("4. ANTIVIRUS SOFTWARE:")
    print("   • Some antivirus software may block voice recognition")
    print("   • Add exceptions for Python and your application directory")
    print()
    print("="*60)

def print_linux_permission_instructions():
    """Print instructions for setting up Linux permissions."""
    print("\n" + "="*60)
    print("LINUX PERMISSION SETUP")
    print("="*60)
    print("To use Voice Assistant properly, please check the following:")
    print()
    print("1. AUDIO GROUP MEMBERSHIP:")
    print("   • Add your user to the audio group:")
    print("   • sudo usermod -a -G audio $USER")
    print("   • Log out and log back in for changes to take effect")
    print()
    print("2. REQUIRED PACKAGES:")
    print("   • Install ALSA utilities: sudo apt-get install alsa-utils")
    print("   • Install PortAudio: sudo apt-get install portaudio19-dev")
    print("   • Install PulseAudio: sudo apt-get install pulseaudio")
    print()
    print("3. AUDIO DEVICE PERMISSIONS:")
    print("   • Check audio devices: aplay -l")
    print("   • Test microphone: arecord -d 5 test.wav && aplay test.wav")
    print()
    print("4. DESKTOP ENVIRONMENT:")
    print("   • Some desktop environments require additional permissions")
    print("   • Check your desktop's privacy settings")
    print()
    print("="*60)

def get_permission_status() -> Dict[str, bool]:
    """Get detailed permission status."""
    system = platform.system().lower()
    status = {
        "microphone": False,
        "file_system": False,
        "network": False,
        "system_control": False
    }
    
    try:
        # File system permissions
        status["file_system"] = check_file_system_permissions()
        
        # Network permissions
        status["network"] = check_network_permissions()
        
        if system == "darwin":
            status["microphone"] = check_microphone_permission_macos()
            status["system_control"] = check_accessibility_permission_macos()
        elif system == "windows":
            status["microphone"] = check_microphone_permission_windows()
            status["system_control"] = True  # Assume basic system control is available
        elif system == "linux":
            status["microphone"] = check_audio_group_linux()
            status["system_control"] = check_required_tools_linux()
        
    except Exception as e:
        logger.error(f"Error getting permission status: {e}")
    
    return status

def diagnose_permissions() -> List[str]:
    """Diagnose permission issues and return recommendations."""
    recommendations = []
    status = get_permission_status()
    system = platform.system().lower()
    
    if not status["microphone"]:
        if system == "darwin":
            recommendations.append("Grant microphone access in System Preferences > Security & Privacy > Privacy > Microphone")
        elif system == "windows":
            recommendations.append("Grant microphone access in Settings > Privacy > Microphone")
        elif system == "linux":
            recommendations.append("Add user to audio group: sudo usermod -a -G audio $USER")
    
    if not status["file_system"]:
        recommendations.append("Check file system permissions and ensure write access to application directory")
    
    if not status["network"]:
        recommendations.append("Check network connectivity and firewall settings")
    
    if not status["system_control"]:
        if system == "darwin":
            recommendations.append("Grant accessibility access in System Preferences > Security & Privacy > Privacy > Accessibility")
        elif system == "linux":
            recommendations.append("Install required audio tools: sudo apt-get install alsa-utils portaudio19-dev")
    
    return recommendations

def request_permissions_interactively() -> bool:
    """Request permissions interactively where possible."""
    system = platform.system().lower()
    
    if system == "darwin":
        return request_macos_permissions()
    elif system == "windows":
        return request_windows_permissions()
    elif system == "linux":
        return request_linux_permissions()
    
    return True

def request_macos_permissions() -> bool:
    """Request macOS permissions interactively."""
    try:
        # Request microphone access by attempting to use it
        try:
            import pyaudio
            pa = pyaudio.PyAudio()
            
            # This will trigger permission request if needed
            stream = pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=44100,
                input=True,
                frames_per_buffer=1024
            )
            stream.close()
            pa.terminate()
            
        except Exception as e:
            logger.debug(f"Microphone access test failed: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error requesting macOS permissions: {e}")
        return False

def request_windows_permissions() -> bool:
    """Request Windows permissions interactively."""
    # Windows permissions are usually handled by the system
    return True

def request_linux_permissions() -> bool:
    """Request Linux permissions interactively."""
    # Linux permissions are usually handled by package managers and user groups
    return True
