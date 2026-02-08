"""Face images for round display - cute robot faces for dark theme.

Supports both static PNGs and animated PNGs (APNG).
- Static: single image rendered every frame
- Animated: frames are cycled automatically at the display's fps rate

To add custom face images:
1. Create PNG files with transparent backgrounds (recommended size: 160x160)
2. Name them after the face constants (e.g., happy.png, sad.png, excited.png)
3. Place them in this directory
4. The system will automatically use images if available, falling back to text if not
5. For animated faces, save as APNG with multiple frames
"""

import logging
import os
from PIL import Image

FACES_DIR = os.path.dirname(os.path.abspath(__file__))

# Cache loaded faces to avoid re-reading from disk every time
_face_cache = {}


def _extract_frames(img, size):
    """Extract all frames from an image (animated or static).

    Args:
        img: PIL Image (may be APNG with multiple frames)
        size: Tuple of (width, height) to resize each frame to

    Returns:
        List of PIL Image frames (RGBA mode, resized)
    """
    frames = []
    try:
        n_frames = getattr(img, 'n_frames', 1)
        for i in range(n_frames):
            img.seek(i)
            frame = img.copy()
            if frame.mode != 'RGBA':
                frame = frame.convert('RGBA')
            if frame.size != size:
                frame = frame.resize(size, Image.LANCZOS)
            frames.append(frame)
    except EOFError:
        pass

    if not frames:
        # Fallback: treat as single frame
        frame = img.copy()
        if frame.mode != 'RGBA':
            frame = frame.convert('RGBA')
        if frame.size != size:
            frame = frame.resize(size, Image.LANCZOS)
        frames.append(frame)

    return frames


def get_face_image(face_name, size=(160, 160)):
    """Load a face image by name.

    Returns the first frame for static PNGs. Use get_face_frames()
    to get all frames for animated PNGs.

    Args:
        face_name: Name of the face (e.g., 'happy', 'sad', 'excited')
        size: Tuple of (width, height) to resize to

    Returns:
        PIL Image object or None if image doesn't exist
    """
    frames = get_face_frames(face_name, size)
    return frames[0] if frames else None


def get_face_frames(face_name, size=(160, 160)):
    """Load all frames for a face image (supports APNG animation).

    Args:
        face_name: Name of the face (e.g., 'happy', 'sad', 'excited')
        size: Tuple of (width, height) to resize each frame to

    Returns:
        List of PIL Image frames, or empty list if image doesn't exist
    """
    cache_key = (face_name.lower(), size)
    if cache_key in _face_cache:
        return _face_cache[cache_key]

    face_path = os.path.join(FACES_DIR, f"{face_name.lower()}.png")
    if not os.path.exists(face_path):
        return []

    try:
        img = Image.open(face_path)
        frames = _extract_frames(img, size)
        n = len(frames)
        if n > 1:
            logging.info(f"[FACE] Loaded animated face '{face_name}': {n} frames")
        _face_cache[cache_key] = frames
        return frames
    except Exception as e:
        logging.error(f"Error loading face image {face_name}: {e}")
        return []


def has_face_image(face_name):
    """Check if a face image exists."""
    face_path = os.path.join(FACES_DIR, f"{face_name.lower()}.png")
    return os.path.exists(face_path)


def clear_cache():
    """Clear the face image cache (e.g., after replacing image files)."""
    _face_cache.clear()
