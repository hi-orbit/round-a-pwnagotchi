# memtemp shows memory infos and cpu temperature
#
# mem usage, cpu load, cpu temp, cpu frequency
#
###############################################################
#
# Updated 18-10-2019 by spees <speeskonijn@gmail.com>
# - Changed the place where the data was displayed on screen
# - Made the data a bit more compact and easier to read
# - removed the label so we wont waste screen space
# - Updated version to 1.0.1
#
# 20-10-2019 by spees <speeskonijn@gmail.com>
# - Refactored to use the already existing functions
# - Now only shows memory usage in percentage
# - Added CPU load
# - Added horizontal and vertical orientation
#
# 19-09-2020 by crahan <crahan@n00.be>
# - Added CPU frequency
# - Made field types and order configurable (max 3 fields)
# - Made line spacing and position configurable
# - Updated code to dynamically generate UI elements
# - Changed horizontal UI elements to Text
# - Updated to version 1.0.2
###############################################################
from pwnagotchi.ui.components import LabeledValue, Text, CurvedText
from pwnagotchi.ui.view import WHITE, CYAN
import pwnagotchi.ui.fonts as fonts
import pwnagotchi.plugins as plugins
import pwnagotchi
import logging


class MemTemp(plugins.Plugin):
    __author__ = 'https://github.com/xenDE'
    __version__ = '1.0.2'
    __license__ = 'GPL3'
    __description__ = 'A plugin that will display memory/cpu usage and temperature'

    ALLOWED_FIELDS = {
        'mem': 'mem_usage',
        'cpu': 'cpu_load',
        'temp': 'cpu_temp',
        'freq': 'cpu_freq'
    }
    DEFAULT_FIELDS = ['mem', 'cpu', 'temp']
    LINE_SPACING = 10
    LABEL_SPACING = 0
    FIELD_WIDTH = 4

    def on_loaded(self):
        logging.info("memtemp plugin loaded.")

    def mem_usage(self):
        return f"{int(pwnagotchi.mem_usage() * 100)}%"

    def cpu_load(self):
        return f"{int(pwnagotchi.cpu_load() * 100)}%"

    def cpu_temp(self):
        if self.options['scale'] == "fahrenheit":
            temp = (pwnagotchi.temperature() * 9 / 5) + 32
            symbol = "f"
        elif self.options['scale'] == "kelvin":
            temp = pwnagotchi.temperature() + 273.15
            symbol = "k"
        else:
            # default to celsius
            temp = pwnagotchi.temperature()
            symbol = "c"
        return f"{temp}{symbol}"

    def cpu_freq(self):
        with open('/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq', 'rt') as fp:
            return f"{round(float(fp.readline())/1000000, 1)}G"

    def pad_text(self, data):
        return " " * (self.FIELD_WIDTH - len(data)) + data

    def on_ui_setup(self, ui):
        try:
            # Configure field list
            self.fields = self.options['fields'].split(',')
            self.fields = [x.strip() for x in self.fields if x.strip() in self.ALLOWED_FIELDS.keys()]
            self.fields = self.fields[:3]  # limit to the first 3 fields
        except Exception:
            # Set default value
            self.fields = self.DEFAULT_FIELDS

        # Single CurvedText on the right side, just inside uptime
        ui.add_element(
            'memtemp',
            CurvedText(
                value=" ".join([f"{x}:-" for x in self.fields]),
                center=(120, 120),
                radius=98,
                start_angle=0,
                font=fonts.Medium,
                color=CYAN,
            )
        )

    def on_unload(self, ui):
        with ui._lock:
            ui.remove_element('memtemp')

    def on_ui_update(self, ui):
        data = " ".join([f"{x}:{getattr(self, self.ALLOWED_FIELDS[x])()}" for x in self.fields])
        ui.set('memtemp', data)
