"""
Pygame-based display emulator for round display development.
This allows local development without physical hardware.
"""
import pygame
import logging
from PIL import Image
import pwnagotchi.ui.fonts as fonts
from pwnagotchi.ui.hw.base import DisplayImpl


class PygameDisplay(DisplayImpl):
    """
    Pygame display emulator for testing round display rendering
    without physical hardware.
    """

    def __init__(self, config):
        super(PygameDisplay, self).__init__(config, 'pygame')
        self.width = 240
        self.height = 240
        self.screen = None

        logging.info(f"Initializing Pygame display emulator ({self.width}x{self.height})")

    def layout(self):
        """Set up the layout for the round display - optimized for 240x240 circular screen."""
        fonts.setup(10, 9, 10, 25, 25, 9)
        self._layout['width'] = self.width
        self._layout['height'] = self.height

        # For round display, position face in center
        # Face is 160x160 pixels, so center it: (240-160)/2 = 40
        self._layout['face'] = (40, 40)

        # Circular layout - position text around the face
        # Top-left arc: Name
        self._layout['name'] = (10, 15)

        # Top center arc: APS count
        self._layout['aps'] = (95, 8)

        # Top-right arc: Uptime
        self._layout['uptime'] = (165, 15)

        # Left side: Channel
        self._layout['channel'] = (5, 110)

        # Status text below the face
        self._layout['status'] = {
            'pos': (70, 205),
            'font': fonts.status_font(fonts.Medium),
            'max': 20
        }

        # Bottom-left: Shakes
        self._layout['shakes'] = (10, 220)

        # Bottom-right: Mode
        self._layout['mode'] = (165, 220)

        # Friend info (for when interacting with peers)
        self._layout['friend_face'] = (10, 185)
        self._layout['friend_name'] = (50, 190)

        logging.info(f"Pygame layout configured: face={self._layout['face']}, status={self._layout['status']['pos']}")
        return self._layout

    def initialize(self):
        """Initialize the pygame display window."""
        import os
        # Use X11 video driver for VNC display
        os.environ['SDL_VIDEODRIVER'] = 'x11'
        # Disable OpenGL completely
        os.environ['SDL_VIDEO_X11_NODIRECTCOLOR'] = '1'

        pygame.init()
        pygame.display.init()
        # Force software surface without any hardware acceleration
        self.screen = pygame.display.set_mode((self.width, self.height), 0)
        pygame.display.set_caption("Pwnagotchi Round Display Emulator")
        # Fill with black background for IPS display
        self.screen.fill((0, 0, 0))
        try:
            pygame.display.flip()
        except:
            pass  # Ignore GL errors during initialization
        logging.info("Pygame display initialized")

    def render(self, canvas):
        """
        Render a PIL Image to the pygame window.

        Args:
            canvas: PIL Image object to render
        """
        if canvas is None:
            logging.warning("render() called with None canvas")
            return

        logging.info(f"render() called with canvas: mode={canvas.mode}, size={canvas.size}")

        try:
            # Save canvas for debugging
            try:
                canvas.save('/tmp/pwnagotchi_canvas.png')
            except:
                pass

            # Ensure RGB mode
            if canvas.mode != 'RGB':
                canvas = canvas.convert('RGB')

            # Resize if needed to fit the display
            if canvas.size != (self.width, self.height):
                canvas = canvas.resize((self.width, self.height), Image.LANCZOS)

            # Convert PIL image to pygame surface
            mode = canvas.mode
            size = canvas.size
            data = canvas.tobytes()

            py_image = pygame.image.fromstring(data, size, mode)
            self.screen.blit(py_image, (0, 0))
            try:
                pygame.display.flip()
            except Exception as flip_error:
                # GL context errors can be ignored - the blit still works
                if "GL context" not in str(flip_error):
                    raise

            # Handle pygame events to keep window responsive
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()

        except Exception as e:
            logging.error(f"Error rendering to pygame display: {e}")

    def clear(self):
        """Clear the display to black."""
        if self.screen:
            self.screen.fill((0, 0, 0))  # Black background
            pygame.display.flip()

    def image(self):
        """Get the current display as PIL Image."""
        if not self.screen:
            return None

        # Convert pygame surface to PIL Image
        img_str = pygame.image.tostring(self.screen, 'RGB')
        return Image.frombytes('RGB', (self.width, self.height), img_str)
