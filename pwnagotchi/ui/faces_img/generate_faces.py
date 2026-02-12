#!/usr/bin/env python3
"""
Simple face image generator for Pwnagotchi.
Creates basic robot face images with different expressions.
"""

from PIL import Image, ImageDraw
import os

# Face configurations: (eyes, mouth, description)
FACES = {
    'awake': ([(20, 25, 30, 35), (50, 25, 60, 35)], [(25, 40, 55, 55)], "Open eyes, neutral"),
    'happy': ([(20, 25, 30, 35), (50, 25, 60, 35)], [(20, 40, 60, 58)], "Open eyes, big smile"),
    'sad': ([(20, 25, 30, 35), (50, 25, 60, 35)], [(20, 50, 60, 58)], "Open eyes, frown"),
    'excited': ([(18, 23, 32, 37), (48, 23, 62, 37)], [(18, 38, 62, 60)], "Big eyes, big smile"),
    'bored': ([(22, 30, 28, 32), (52, 30, 58, 32)], [(25, 50, 55, 52)], "Half-closed eyes, flat mouth"),
    'angry': ([(20, 28, 28, 32), (52, 28, 60, 32)], [(25, 52, 55, 58)], "Narrow eyes, frown"),
    'cool': ([(20, 28, 35, 30), (50, 28, 65, 30)], [(25, 50, 55, 52)], "Sunglasses, flat mouth"),
    'grateful': ([(18, 25, 32, 35), (48, 25, 62, 35)], [(23, 42, 57, 56)], "^^ eyes, gentle smile"),
    'sleep': ([(22, 30, 28, 32), (52, 30, 58, 32)], [(25, 50, 55, 52)], "Closed eyes, Zzz"),
    'motivated': ([(18, 23, 32, 37), (48, 23, 62, 37)], [(20, 42, 60, 58)], "Wide eyes, determined"),
    'look_r': ([(28, 25, 35, 35), (55, 25, 62, 35)], [(30, 48, 55, 50)], "Eyes looking right"),
    'look_l': ([(18, 25, 25, 35), (45, 25, 52, 35)], [(25, 48, 50, 50)], "Eyes looking left"),
    'look_r_happy': ([(28, 25, 35, 35), (55, 25, 62, 35)], [(25, 42, 55, 56)], "Looking right, smile"),
    'look_l_happy': ([(18, 25, 25, 35), (45, 25, 52, 35)], [(25, 42, 55, 56)], "Looking left, smile"),
    'sleep2': ([(22, 30, 28, 32), (52, 30, 58, 32)], [(30, 48, 50, 50)], "Deep sleep"),
    'intense': ([(18, 24, 32, 36), (48, 24, 62, 36)], [(25, 48, 55, 55)], "Wide intense eyes"),
    'demotivated': ([(22, 28, 28, 33), (52, 28, 58, 33)], [(25, 50, 55, 52)], "Droopy eyes, flat mouth"),
    'smart': ([(18, 24, 32, 36), (48, 24, 62, 36)], [(28, 45, 52, 52)], "Focused eyes, small smile"),
    'lonely': ([(22, 27, 28, 33), (52, 27, 58, 33)], [(28, 52, 52, 58)], "Small eyes, small frown"),
    'friend': ([(18, 23, 32, 37), (48, 23, 62, 37)], [(20, 40, 60, 58)], "Heart eyes, big smile"),
    'broken': ([(20, 25, 30, 35), (50, 25, 60, 35)], [(25, 48, 55, 50)], "X eyes, flat mouth"),
    'debug': ([(20, 25, 30, 35), (50, 25, 60, 35)], [(28, 48, 52, 50)], "Hash eyes, neutral"),
    'upload': ([(20, 25, 30, 35), (50, 25, 60, 35)], [(28, 46, 52, 50)], "Binary eyes 1-0"),
    'upload1': ([(20, 25, 30, 35), (50, 25, 60, 35)], [(28, 46, 52, 50)], "Binary eyes 1-1"),
    'upload2': ([(20, 25, 30, 35), (50, 25, 60, 35)], [(28, 46, 52, 50)], "Binary eyes 0-1"),
}

def create_face(name, eyes, mouth, size=80):
    """Create a simple robot face image."""
    # Create image with transparency
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw black oval background with slight transparency
    margin = size // 16
    draw.ellipse([margin, margin, size-margin, size-margin],
                 fill=(0, 0, 0, 220),
                 outline=(50, 50, 50, 255))

    # Draw eyes (glowing blue/cyan)
    eye_color = (0, 180, 255, 255)
    for eye in eyes:
        draw.ellipse(eye, fill=eye_color)
        # Add white highlight
        highlight_x = eye[0] + (eye[2] - eye[0]) // 3
        highlight_y = eye[1] + (eye[3] - eye[1]) // 3
        draw.ellipse([highlight_x, highlight_y, highlight_x+3, highlight_y+3],
                    fill=(255, 255, 255, 200))

    # Draw mouth
    mouth_color = (0, 180, 255, 255)
    for m in mouth:
        if name in ['happy', 'excited', 'grateful', 'motivated']:
            # Smile - draw arc
            draw.arc(m, 0, 180, fill=mouth_color, width=3)
        elif name in ['sad', 'angry']:
            # Frown - draw inverted arc
            draw.arc(m, 180, 360, fill=mouth_color, width=3)
        else:
            # Neutral - draw line
            draw.line([m[0], m[1], m[2], m[3]], fill=mouth_color, width=2)

    return img

def generate_all_faces(output_dir='.'):
    """Generate all face images."""
    os.makedirs(output_dir, exist_ok=True)

    print(f"Generating face images in {output_dir}/...")

    for name, (eyes, mouth, desc) in FACES.items():
        img = create_face(name, eyes, mouth)
        output_path = os.path.join(output_dir, f'{name}.png')
        img.save(output_path)
        print(f"  ✓ Created {name}.png - {desc}")

    print(f"\nGenerated {len(FACES)} face images!")
    print("\nYou can customize these images with your own designs.")
    print("Images should be 80x80 PNG with transparent backgrounds.")

if __name__ == '__main__':
    import sys
    output_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    generate_all_faces(output_dir)
