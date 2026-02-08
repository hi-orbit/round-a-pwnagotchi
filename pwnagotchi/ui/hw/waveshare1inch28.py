import logging
import time
from PIL import Image
import pwnagotchi.ui.fonts as fonts
from pwnagotchi.ui.hw.base import DisplayImpl


class Waveshare1inch28(DisplayImpl):
    """
    Waveshare 1.28" Round LCD Display Driver
    - Resolution: 240x240
    - Driver: GC9A01
    - Interface: SPI
    """

    def __init__(self, config):
        super(Waveshare1inch28, self).__init__(config, 'waveshare1inch28')
        self._display = None
        self.width = 240
        self.height = 240

    def layout(self):
        """Set up the layout for the round display - matching pygame_display.py"""
        fonts.setup(10, 9, 10, 25, 25, 9)
        self._layout['width'] = self.width
        self._layout['height'] = self.height

        # Face centered
        self._layout['face'] = (40, 40)

        # Curved text positions (will be handled by CurvedText components)
        self._layout['name'] = (10, 15)
        self._layout['channel'] = (5, 110)
        self._layout['aps'] = (95, 8)
        self._layout['uptime'] = (165, 15)

        # Status text
        self._layout['status'] = {
            'pos': (70, 205),
            'font': fonts.status_font(fonts.Medium),
            'max': 20
        }

        # Bottom info
        self._layout['shakes'] = (10, 220)
        self._layout['mode'] = (165, 220)

        # Friend info
        self._layout['friend_face'] = (10, 185)
        self._layout['friend_name'] = (50, 190)

        logging.info(f"Waveshare 1.28\" layout configured: face={self._layout['face']}")
        return self._layout

    def initialize(self):
        """Initialize the physical display hardware."""
        try:
            # Import the Waveshare library
            import sys
            import os

            # Add the library path
            lib_path = '/home/pi/pwnagotchi/LCD_Module_RPI_code/RaspberryPi/python/lib'
            if os.path.exists(lib_path):
                sys.path.insert(0, lib_path)

            from LCD_1inch28 import LCD_1inch28

            # Initialize the display
            self._display = LCD_1inch28()
            self._display.Init()
            self._display.clear()

            # Set backlight to 100% (0-100)
            self._display.bl_DutyCycle(100)

            logging.info("Waveshare 1.28\" Round LCD initialized successfully")
            logging.info(f"Display size: {self.width}x{self.height}")

        except ImportError as e:
            logging.error(f"Could not import Waveshare LCD library: {e}")
            logging.error("Make sure the LCD_Module_RPI_code is installed at /home/pi/pwnagotchi/")
            raise
        except Exception as e:
            logging.error(f"Error initializing Waveshare display: {e}")
            raise

    def render(self, canvas):
        """
        Render a PIL Image to the physical display.

        Args:
            canvas: PIL Image object (240x240) to display
        """
        if self._display is None:
            logging.warning("Display not initialized, skipping render")
            return

        try:
            # Ensure canvas is RGB mode
            if canvas.mode != 'RGB':
                canvas = canvas.convert('RGB')

            # Ensure correct size
            if canvas.size != (self.width, self.height):
                canvas = canvas.resize((self.width, self.height), Image.LANCZOS)

            # Rotate 180 degrees (display is typically upside down)
            canvas = canvas.rotate(180)

            # Send to display
            self._display.ShowImage(canvas)

        except Exception as e:
            logging.error(f"Error rendering to Waveshare display: {e}")

    def clear(self):
        """Clear the display to black."""
        if self._display:
            try:
                self._display.clear()
            except Exception as e:
                logging.error(f"Error clearing display: {e}")
