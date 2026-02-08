# Face Images for Round Display

This directory contains face images for the Pwnagotchi round display. Images are used instead of text-based faces when available.

## Image Specifications

- **Format**: PNG with transparency (RGBA)
- **Size**: 80x80 pixels (will be resized if different)
- **Style**: Cute robot/emoji faces
- **Background**: Transparent or dark (for dark theme)
- **Theme**: Consistent style across all faces

## Naming Convention

Images should be named after the face constant in lowercase:

- `awake.png` - Default awake face
- `happy.png` - Happy expression
- `sad.png` - Sad expression  
- `excited.png` - Excited expression
- `bored.png` - Bored expression
- `angry.png` - Angry expression
- `cool.png` - Cool/confident expression
- `grateful.png` - Grateful expression
- `motivated.png` - Motivated expression
- `demotivated.png` - Demotivated expression
- `intense.png` - Intense/focused expression
- `smart.png` - Smart/thinking expression
- `lonely.png` - Lonely expression
- `sleep.png` - Sleeping face
- `sleep2.png` - Alternative sleeping face
- `friend.png` - Friendly face (when meeting peers)
- `broken.png` - Broken/error state
- `debug.png` - Debug mode
- `look_r.png` - Looking right
- `look_l.png` - Looking left
- `look_r_happy.png` - Looking right happy
- `look_l_happy.png` - Looking left happy
- `upload.png` - Uploading data
- `upload1.png` - Upload state 1
- `upload2.png` - Upload state 2

## Creating Face Images

### Using AI Image Generators

You can use AI tools like:
- DALL-E
- Midjourney
- Stable Diffusion

Example prompt:
```
"Cute minimalist robot face emoji, [emotion], black background, 
simple geometric shapes, glowing blue eyes, transparent background, 
80x80 pixels, flat design, kawaii style"
```

### Using Image Editors

1. Create an 80x80 pixel canvas with transparent background
2. Draw a cute robot face with the desired emotion
3. Keep it simple and clear
4. Use consistent style across all faces
5. Save as PNG with transparency

### Style Guidelines

Based on the example image provided:
- **Eyes**: Circular, glowing effect (cyan/blue)
- **Mouth**: Simple curved line or shapes
- **Background**: Oval/rounded rectangle frame (black)
- **Theme**: Minimal, cute, robotic
- **Expressions**: Clear and distinguishable

## Fallback Behavior

If an image file doesn't exist, the system will automatically fall back to the text-based face representation. This means you can add images gradually without breaking the display.

## Testing

After adding images:
1. Place PNG files in this directory
2. Restart the Pwnagotchi container
3. The display will automatically use images where available
4. Check logs for any loading errors

## Example: Creating a "happy" face

```python
from PIL import Image, ImageDraw

# Create image with transparency
img = Image.new('RGBA', (80, 80), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Draw black oval background
draw.ellipse([5, 5, 75, 75], fill=(0, 0, 0, 255))

# Draw glowing blue eyes
draw.ellipse([20, 25, 30, 35], fill=(0, 200, 255, 255))
draw.ellipse([50, 25, 60, 35], fill=(0, 200, 255, 255))

# Draw smiling mouth
draw.arc([25, 35, 55, 50], 0, 180, fill=(0, 200, 255, 255), width=2)

img.save('happy.png')
```

## Contributing

If you create a nice set of face images, consider sharing them with the community!
