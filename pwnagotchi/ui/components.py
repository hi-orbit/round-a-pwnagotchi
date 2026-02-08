"""
UI components for pwnagotchi display rendering.

Upstream components: Widget, Bitmap, Line, Rect, FilledRect, LabeledValue
Custom additions for round display:
  - Text: Extended with 'image' parameter for PNG face support
  - CurvedText: Draws text along a circular arc (for round LCD layout)
"""
from PIL import Image
from textwrap import TextWrapper
import math

# Default color for all components — white for black-background IPS displays.
# Upstream used 0 (black on white e-paper). Overridden per-component in view.py.
DEFAULT_COLOR = (255, 255, 255)


class Widget(object):
    def __init__(self, xy, color=DEFAULT_COLOR):
        self.xy = xy
        self.color = color

    def draw(self, canvas, drawer):
        raise Exception("not implemented")


class Bitmap(Widget):
    def __init__(self, path, xy, color=DEFAULT_COLOR):
        super().__init__(xy, color)
        self.image = Image.open(path)

    def draw(self, canvas, drawer):
        canvas.paste(self.image, self.xy)


class Line(Widget):
    def __init__(self, xy, color=DEFAULT_COLOR, width=1):
        super().__init__(xy, color)
        self.width = width

    def draw(self, canvas, drawer):
        drawer.line(self.xy, fill=self.color, width=self.width)


class Rect(Widget):
    def draw(self, canvas, drawer):
        drawer.rectangle(self.xy, outline=self.color)


class FilledRect(Widget):
    def draw(self, canvas, drawer):
        drawer.rectangle(self.xy, fill=self.color)


class Text(Widget):
    """Text widget with optional image support.

    Custom addition: 'image' parameter allows rendering a PIL Image
    instead of text, used for face PNG images on the round display.
    """

    def __init__(self, value="", position=(0, 0), font=None, color=DEFAULT_COLOR, wrap=False, max_length=0, image=None):
        super().__init__(position, color)
        self.value = value
        self.font = font
        self.wrap = wrap
        self.max_length = max_length
        self.image = image          # Current frame (PIL Image) for face rendering
        self._frames = []           # All frames for animated faces (APNG)
        self._frame_index = 0       # Current frame index for animation
        self.wrapper = TextWrapper(width=self.max_length, replace_whitespace=False) if wrap else None

    def set_frames(self, frames):
        """Set animation frames for this text widget.

        Args:
            frames: List of PIL Image objects. If len > 1, the face is animated
                    and draw() will cycle through frames automatically.
        """
        self._frames = frames if frames else []
        self._frame_index = 0
        self.image = self._frames[0] if self._frames else None

    def draw(self, canvas, drawer):
        # Animated face: cycle to next frame on each draw
        if self._frames and len(self._frames) > 1:
            self.image = self._frames[self._frame_index]
            self._frame_index = (self._frame_index + 1) % len(self._frames)

        # If an image is set, draw it instead of text
        if self.image is not None:
            try:
                canvas.paste(self.image, self.xy, self.image if self.image.mode == 'RGBA' else None)
                return
            except Exception as e:
                # Fall back to text if image fails
                pass

        if self.value is not None:
            if self.wrap:
                text = '\n'.join(self.wrapper.wrap(self.value))
            else:
                text = self.value
            drawer.text(self.xy, text, font=self.font, fill=self.color)


class LabeledValue(Widget):
    def __init__(self, label, value="", position=(0, 0), label_font=None, text_font=None, color=DEFAULT_COLOR, label_spacing=5):
        super().__init__(position, color)
        self.label = label
        self.value = value
        self.label_font = label_font
        self.text_font = text_font
        self.label_spacing = label_spacing

    def draw(self, canvas, drawer):
        if self.label is None:
            drawer.text(self.xy, self.value, font=self.label_font, fill=self.color)
        else:
            pos = self.xy
            drawer.text(pos, self.label, font=self.label_font, fill=self.color)
            drawer.text((pos[0] + self.label_spacing + 5 * len(self.label), pos[1]), self.value, font=self.text_font, fill=self.color)


class CurvedText(Widget):
    def __init__(self, value="", center=(120, 120), radius=100, start_angle=0, font=None, color=DEFAULT_COLOR, flip=False):
        """
        Draw text along a circular arc with rotated characters.
        center: (x, y) center of the circle
        radius: radius of the circle
        start_angle: starting angle in degrees (0 = right, 90 = bottom, 180 = left, 270 = top)
        flip: if True, characters are flipped upright (tops point inward) and text runs
              counter-clockwise — use for text on the bottom half of the circle so it
              reads left-to-right when viewed from outside.
        """
        super().__init__(center, color)
        self.value = value
        self.center = center
        self.radius = radius
        self.start_angle = start_angle
        self.font = font
        self.flip = flip

    def draw(self, canvas, drawer):
        if not self.value or self.font is None:
            return

        from PIL import ImageDraw

        # Convert value to string and strip any newlines for single-line display
        text = str(self.value).replace('\n', ' ').strip()
        if not text:
            return

        # Calculate total text width to center it on the arc
        try:
            total_width = drawer.textlength(text, font=self.font)
        except:
            total_width = len(text) * 6

        angle_span = (total_width / self.radius) * (180 / math.pi)

        # Direction: clockwise (normal) or counter-clockwise (flipped)
        direction = -1 if self.flip else 1
        current_angle = self.start_angle - direction * (angle_span / 2)

        for char in text:
            # Calculate character width
            try:
                char_width = drawer.textlength(char, font=self.font)
            except:
                char_width = 6

            # Get character dimensions
            try:
                bbox = drawer.textbbox((0, 0), char, font=self.font)
                char_h = bbox[3] - bbox[1]
                char_w = bbox[2] - bbox[0]
            except:
                char_h = 12
                char_w = int(char_width)

            # Calculate position on the circle
            angle_rad = math.radians(current_angle)
            x = self.center[0] + self.radius * math.cos(angle_rad)
            y = self.center[1] + self.radius * math.sin(angle_rad)

            # Create small image for rotated character
            padding = 20
            char_img = Image.new('RGBA', (char_w + padding, char_h + padding), (0, 0, 0, 0))
            char_drawer = ImageDraw.Draw(char_img)

            # Draw character in center of temp image
            char_drawer.text((padding // 2, padding // 2), char, font=self.font, fill=self.color)

            # Normal: bottom of char points toward center (+90°)
            # Flipped: top of char points toward center (-90°), for bottom-half readability
            rotation_angle = current_angle + (90 if not self.flip else -90)
            rotated = char_img.rotate(-rotation_angle, expand=True, resample=Image.BICUBIC)

            # Paste rotated character onto main canvas
            paste_x = int(x - rotated.width / 2)
            paste_y = int(y - rotated.height / 2)

            # Paste if any part of the character is within the canvas
            if (paste_x + rotated.width > 0 and paste_y + rotated.height > 0
                    and paste_x < canvas.width and paste_y < canvas.height):
                canvas.paste(rotated, (paste_x, paste_y), rotated)

            # Move to next character position (counter-clockwise if flipped)
            char_angle_span = (char_width / self.radius) * (180 / math.pi)
            current_angle += direction * char_angle_span
