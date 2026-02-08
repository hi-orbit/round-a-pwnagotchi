"""
Face images for round display - cute robot faces for dark theme.
Each face should be a PNG file with transparent background, approximately 80x80 pixels.
Files should be named after the face constant in lowercase (e.g., happy.png, sad.png).

To add custom face images:
1. Create PNG files with transparent backgrounds (recommended size: 80x80 or 100x100)
2. Name them after the face constants (e.g., happy.png, sad.png, excited.png)
3. Place them in this directory
4. The system will automatically use images if available, falling back to text if not

Recommended style:
- Cute robot/emoji style (like the example provided)
- Dark background or transparent (for dark theme)
- Simple, clear expressions
- Consistent size and style across all faces
"""

import os
from PIL import Image

FACES_DIR = os.path.dirname(os.path.abspath(__file__))

def get_face_image(face_name, size=(80, 80)):
    """
    Load a face image by name.
    
    Args:
        face_name: Name of the face (e.g., 'happy', 'sad', 'excited')
        size: Tuple of (width, height) to resize to
        
    Returns:
        PIL Image object or None if image doesn't exist
    """
    face_path = os.path.join(FACES_DIR, f"{face_name.lower()}.png")
    
    if os.path.exists(face_path):
        try:
            img = Image.open(face_path)
            if img.size != size:
                img = img.resize(size, Image.LANCZOS)
            return img
        except Exception as e:
            print(f"Error loading face image {face_name}: {e}")
            return None
    return None

def has_face_image(face_name):
    """Check if a face image exists."""
    face_path = os.path.join(FACES_DIR, f"{face_name.lower()}.png")
    return os.path.exists(face_path)

# List of all face names from faces.py
FACE_NAMES = [
    'look_r', 'look_l', 'look_r_happy', 'look_l_happy',
    'sleep', 'sleep2', 'awake', 'bored', 'intense', 'cool',
    'happy', 'grateful', 'excited', 'motivated', 'demotivated',
    'smart', 'lonely', 'sad', 'angry', 'friend', 'broken',
    'debug', 'upload', 'upload1', 'upload2'
]
