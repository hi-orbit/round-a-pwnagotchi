import logging
import os
import sys
from pathlib import Path

from PIL import Image

import pwnagotchi.ui.fonts as fonts
from pwnagotchi.ui.hw.base import DisplayImpl

# Possible locations for the Waveshare LCD_Module_RPI_code library.
# The driver searches these paths in order to find LCD_1inch28.py.
# Add your custom path here if the library is installed elsewhere.
LCD_LIB_SEARCH_PATHS = [
    '/home/noppitgotchi/app/LCD_Module_RPI_code/RaspberryPi/python/lib',
    '/home/pi/pwnagotchi/LCD_Module_RPI_code/RaspberryPi/python/lib',
]


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

    def _find_lcd_library(self):
        """Search for the Waveshare LCD library in known paths.

        Returns:
            str: Path to the 'lib' directory containing LCD_1inch28.py

        Raises:
            ImportError: If the library is not found in any search path
        """
        # Build search paths: configured paths + dynamic home-based paths
        search_paths = list(LCD_LIB_SEARCH_PATHS)
        for subdir in ('pwnagotchi', 'app'):
            candidate = str(Path.home() / subdir / 'LCD_Module_RPI_code' / 'RaspberryPi' / 'python' / 'lib')
            if candidate not in search_paths:
                search_paths.append(candidate)

        for path in search_paths:
            if os.path.isfile(os.path.join(path, 'LCD_1inch28.py')):
                logging.info(f"Found LCD library at: {path}")
                return path

        raise ImportError(
            f"LCD_1inch28.py not found. Searched: {search_paths}. "
            f"Clone Waveshare LCD_Module_RPI_code into ~/app/ or ~/pwnagotchi/."
        )

    def initialize(self):
        """Initialize the physical SPI display hardware."""
        try:
            lib_path = self._find_lcd_library()

            # The Waveshare library uses relative imports (from . import lcdconfig)
            # so the 'lib' dir must be a Python package with __init__.py
            init_file = os.path.join(lib_path, '__init__.py')
            if not os.path.exists(init_file):
                with open(init_file, 'w') as f:
                    f.write('# Auto-generated for Waveshare LCD package imports\n')
                logging.info(f"Created {init_file}")

            # Add parent of 'lib' to sys.path so Python treats 'lib' as a package
            parent_path = os.path.dirname(lib_path)
            if parent_path not in sys.path:
                sys.path.insert(0, parent_path)

            from lib.LCD_1inch28 import LCD_1inch28  # noqa: E402

            self._display = LCD_1inch28()
            self._display.Init()
            self._display.clear()
            self._display.bl_DutyCycle(100)

            logging.info("Waveshare 1.28\" Round LCD initialized successfully")

        except ImportError as e:
            logging.error(f"Could not import Waveshare LCD library: {e}")
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
