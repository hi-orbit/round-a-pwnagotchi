"""
SPI-based round display driver for GC9A01 (240x240 round LCD).
This will be used on the actual Raspberry Pi hardware.
"""
import logging
from PIL import Image
import pwnagotchi.ui.fonts as fonts
from pwnagotchi.ui.hw.base import DisplayImpl


class SPIDisplay(DisplayImpl):
    """
    SPI display driver for GC9A01 round LCD display.
    This interfaces with the physical hardware on the Raspberry Pi.
    """

    def __init__(self, config):
        super(SPIDisplay, self).__init__(config, 'spi_round')
        self.width = 240
        self.height = 240
        self.spi_speed_hz = 60000000
        self.device = None

        logging.info(f"Initializing SPI round display ({self.width}x{self.height})")

    def layout(self):
        """Set up the layout for the round display."""
        fonts.setup(10, 9, 10, 25, 25, 9)
        self._layout['width'] = self.width
        self._layout['height'] = self.height
        self._layout['face'] = (120, 80)
        self._layout['name'] = (5, 20)
        self._layout['channel'] = (0, 0)
        self._layout['aps'] = (40, 0)
        self._layout['uptime'] = (150, 0)
        self._layout['line1'] = [0, 35, self.width, 35]
        self._layout['line2'] = [0, 200, self.width, 200]
        self._layout['friend_face'] = (0, 150)
        self._layout['friend_name'] = (40, 155)
        self._layout['shakes'] = (0, 210)
        self._layout['mode'] = (180, 210)
        self._layout['status'] = {
            'pos': (120, 40),
            'font': fonts.status_font(fonts.Medium),
            'max': 20
        }
        return self._layout

    def initialize(self):
        """
        Initialize the SPI display hardware.
        This will import and configure the GC9A01 driver when running on Pi.
        """
        try:
            # Import the round display library
            # TODO: Add actual GC9A01 driver initialization
            # from round_display import GC9A01
            # self.device = GC9A01(spi_speed_hz=self.spi_speed_hz)

            logging.info("SPI round display initialized")
            logging.warning("GC9A01 driver not yet implemented - placeholder active")

        except ImportError as e:
            logging.error(f"Could not import SPI display driver: {e}")
            logging.error("Make sure you're running on a Raspberry Pi with the display library installed")
        except Exception as e:
            logging.error(f"Error initializing SPI display: {e}")

    def render(self, canvas):
        """
        Render a PIL Image to the physical display.

        Args:
            canvas: PIL Image object to render
        """
        if canvas is None:
            return

        try:
            # Convert to RGB if needed
            if canvas.mode != 'RGB':
                canvas = canvas.convert('RGB')

            # Resize if needed
            if canvas.size != (self.width, self.height):
                canvas = canvas.resize((self.width, self.height), Image.LANCZOS)

            # TODO: Send to actual hardware
            # if self.device:
            #     self.device.display(canvas)

            logging.debug("Rendered frame to SPI display")

        except Exception as e:
            logging.error(f"Error rendering to SPI display: {e}")

    def clear(self):
        """Clear the display."""
        try:
            # Create a white image and display it
            blank = Image.new('RGB', (self.width, self.height), 'white')
            self.render(blank)
        except Exception as e:
            logging.error(f"Error clearing SPI display: {e}")

    def image(self):
        """
        Get the current display content.
        Note: Most SPI displays don't support reading back, so this returns None.
        """
        return None
