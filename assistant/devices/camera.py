"""
Camera device integration for face recognition and detection.
"""

import numpy as np
from typing import Optional, List, Dict, Any, Generator
import threading
import time
from pathlib import Path
from assistant.utils.logger import setup_logger

# Try to import camera dependencies
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False

logger = setup_logger(__name__)

class CameraDevice:
    """Camera device for face recognition and detection."""
    
    def __init__(self, config):
        """Initialize camera device."""
        self.config = config
        self.camera_index = config.camera_index
        self.face_recognition_tolerance = config.face_recognition_tolerance
        self.known_faces = {}
        self.camera = None
        self.is_active = False
        self.face_detection_enabled = config.enable_face_recognition
        
        # Create faces directory if it doesn't exist
        self.faces_dir = Path("data/faces")
        self.faces_dir.mkdir(parents=True, exist_ok=True)
        
        if self.face_detection_enabled:
            self._load_known_faces()
        else:
            logger.info("Face recognition disabled in configuration")
    
    def _load_known_faces(self):
        """Load known faces from the faces directory."""
        try:
            for face_file in self.faces_dir.glob("*.jpg"):
                name = face_file.stem
                image = face_recognition.load_image_file(str(face_file))
                
                # Get face encodings
                face_encodings = face_recognition.face_encodings(image)
                if face_encodings:
                    self.known_faces[name] = face_encodings[0]
                    logger.info(f"Loaded face for: {name}")
                else:
                    logger.warning(f"No face found in image: {face_file}")
            
            logger.info(f"Loaded {len(self.known_faces)} known faces")
            
        except Exception as e:
            logger.error(f"Error loading known faces: {e}")
    
    def get_available_cameras(self) -> List[Dict[str, Any]]:
        """Get list of available cameras."""
        cameras = []
        
        # Test camera indices 0-5
        for index in range(6):
            try:
                cap = cv2.VideoCapture(index)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret:
                        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        fps = cap.get(cv2.CAP_PROP_FPS)
                        
                        camera_info = {
                            'index': index,
                            'name': f"Camera {index}",
                            'width': width,
                            'height': height,
                            'fps': fps,
                            'available': True
                        }
                        cameras.append(camera_info)
                
                cap.release()
                
            except Exception as e:
                logger.debug(f"Camera {index} not available: {e}")
        
        logger.info(f"Found {len(cameras)} available cameras")
        return cameras
    
    def start_camera(self) -> bool:
        """Start camera capture."""
        try:
            if self.camera is not None:
                logger.warning("Camera already active")
                return True
            
            self.camera = cv2.VideoCapture(self.camera_index)
            
            if not self.camera.isOpened():
                logger.error(f"Could not open camera {self.camera_index}")
                return False
            
            # Set camera properties
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            
            self.is_active = True
            logger.info(f"Camera {self.camera_index} started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error starting camera: {e}")
            return False
    
    def stop_camera(self):
        """Stop camera capture."""
        try:
            self.is_active = False
            
            if self.camera is not None:
                self.camera.release()
                self.camera = None
            
            cv2.destroyAllWindows()
            logger.info("Camera stopped")
            
        except Exception as e:
            logger.error(f"Error stopping camera: {e}")
    
    def capture_frame(self) -> Optional[np.ndarray]:
        """Capture a single frame from camera."""
        if not self.camera or not self.is_active:
            logger.error("Camera not active")
            return None
        
        try:
            ret, frame = self.camera.read()
            if ret:
                return frame
            else:
                logger.error("Failed to capture frame")
                return None
                
        except Exception as e:
            logger.error(f"Error capturing frame: {e}")
            return None
    
    def detect_faces(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Detect faces in a frame."""
        if not self.face_detection_enabled:
            return []
        
        try:
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Find face locations and encodings
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            
            detected_faces = []
            
            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                # Check if this face matches any known face
                matches = face_recognition.compare_faces(
                    list(self.known_faces.values()), 
                    face_encoding,
                    tolerance=self.face_recognition_tolerance
                )
                
                name = "Unknown"
                confidence = 0.0
                
                if True in matches:
                    # Find the best match
                    face_distances = face_recognition.face_distance(
                        list(self.known_faces.values()), 
                        face_encoding
                    )
                    best_match_index = np.argmin(face_distances)
                    
                    if matches[best_match_index]:
                        name = list(self.known_faces.keys())[best_match_index]
                        confidence = 1.0 - face_distances[best_match_index]
                
                face_info = {
                    'name': name,
                    'confidence': confidence,
                    'location': {
                        'top': top,
                        'right': right,
                        'bottom': bottom,
                        'left': left
                    },
                    'known': name != "Unknown"
                }
                
                detected_faces.append(face_info)
            
            return detected_faces
            
        except Exception as e:
            logger.error(f"Error detecting faces: {e}")
            return []
    
    def add_known_face(self, name: str, image_path: Optional[str] = None) -> bool:
        """Add a new known face from image or camera capture."""
        try:
            if image_path:
                # Load from file
                if not Path(image_path).exists():
                    logger.error(f"Image file not found: {image_path}")
                    return False
                
                image = cv2.imread(image_path)
            else:
                # Capture from camera
                if not self.start_camera():
                    return False
                
                image = self.capture_frame()
                if image is None:
                    return False
            
            # Convert to RGB for face_recognition
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Get face encodings
            face_encodings = face_recognition.face_encodings(rgb_image)
            
            if not face_encodings:
                logger.error("No face found in the image")
                return False
            
            if len(face_encodings) > 1:
                logger.warning("Multiple faces found, using the first one")
            
            # Save the face encoding
            self.known_faces[name] = face_encodings[0]
            
            # Save the image file
            face_image_path = self.faces_dir / f"{name}.jpg"
            cv2.imwrite(str(face_image_path), image)
            
            logger.info(f"Added new known face: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding known face: {e}")
            return False
    
    def remove_known_face(self, name: str) -> bool:
        """Remove a known face."""
        try:
            if name in self.known_faces:
                del self.known_faces[name]
                
                # Remove image file
                face_image_path = self.faces_dir / f"{name}.jpg"
                if face_image_path.exists():
                    face_image_path.unlink()
                
                logger.info(f"Removed known face: {name}")
                return True
            else:
                logger.warning(f"Face not found: {name}")
                return False
                
        except Exception as e:
            logger.error(f"Error removing known face: {e}")
            return False
    
    def take_photo(self, filename: Optional[str] = None) -> Optional[str]:
        """Take a photo and save it."""
        try:
            if not self.start_camera():
                return None
            
            frame = self.capture_frame()
            if frame is None:
                return None
            
            # Generate filename if not provided
            if not filename:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"photo_{timestamp}.jpg"
            
            # Ensure photos directory exists
            photos_dir = Path("data/photos")
            photos_dir.mkdir(parents=True, exist_ok=True)
            
            photo_path = photos_dir / filename
            cv2.imwrite(str(photo_path), frame)
            
            logger.info(f"Photo saved: {photo_path}")
            return str(photo_path)
            
        except Exception as e:
            logger.error(f"Error taking photo: {e}")
            return None
    
    def stream_camera(self) -> Generator[bytes, None, None]:
        """Stream camera frames as JPEG bytes."""
        if not self.start_camera():
            return
        
        try:
            while self.is_active:
                frame = self.capture_frame()
                if frame is None:
                    break
                
                # Encode frame as JPEG
                ret, buffer = cv2.imencode('.jpg', frame)
                if ret:
                    yield buffer.tobytes()
                
                time.sleep(0.033)  # ~30 FPS
                
        except Exception as e:
            logger.error(f"Error streaming camera: {e}")
        finally:
            self.stop_camera()
    
    def get_camera_info(self) -> Dict[str, Any]:
        """Get camera information."""
        info = {
            'camera_index': self.camera_index,
            'face_recognition_enabled': self.face_detection_enabled,
            'known_faces_count': len(self.known_faces),
            'is_active': self.is_active,
            'available_cameras': len(self.get_available_cameras())
        }
        
        if self.camera and self.is_active:
            info.update({
                'width': int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                'fps': self.camera.get(cv2.CAP_PROP_FPS)
            })
        
        return info
    
    def cleanup(self):
        """Clean up camera resources."""
        self.stop_camera()
    
    def is_available(self) -> bool:
        """Check if camera is available."""
        available_cameras = self.get_available_cameras()
        return len(available_cameras) > 0
