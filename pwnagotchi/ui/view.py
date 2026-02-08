import _thread
import logging
import random
import time
from threading import Lock

from PIL import ImageDraw

import pwnagotchi
import pwnagotchi.plugins as plugins
import pwnagotchi.ui.faces as faces
import pwnagotchi.ui.faces_img as faces_img
import pwnagotchi.ui.fonts as fonts
import pwnagotchi.ui.web as web
import pwnagotchi.utils as utils
from pwnagotchi.ui.components import *
from pwnagotchi.ui.state import State
from pwnagotchi.voice import Voice

# RGB Color mode for high-resolution IPS display
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 100)
CYAN = (0, 200, 255)
RED = (255, 50, 50)
YELLOW = (255, 255, 0)

# Legacy support for monochrome
WHITE_MONO = 0xff
BLACK_MONO = 0x00
ROOT = None


class View(object):
    def __init__(self, config, impl, state=None):
        global ROOT

        # setup faces from the configuration in case the user customized them
        faces.load_from_config(config['ui']['faces'])

        self._agent = None
        self._render_cbs = []
        self._config = config
        self._canvas = None
        self._frozen = False
        self._lock = Lock()
        self._voice = Voice(lang=config['main']['lang'])
        self._implementation = impl
        self._layout = impl.layout()
        self._width = self._layout['width']
        self._height = self._layout['height']
        self._state = State(state={
            'channel': CurvedText(value='CH 00', center=(120, 120), radius=110, start_angle=180,
                                 font=fonts.Medium, color=CYAN),

            'aps': CurvedText(value='APS 0 (00)', center=(120, 120), radius=112, start_angle=270,
                             font=fonts.Medium, color=CYAN),

            'uptime': CurvedText(value='UP 00:00:00', center=(120, 120), radius=110, start_angle=0,
                                font=fonts.Medium, color=CYAN),

            'face': Text(value=faces.SLEEP, position=self._layout['face'], color=WHITE, font=fonts.Huge),

            'friend_face': Text(value=None, position=self._layout['friend_face'], font=fonts.Bold, color=GREEN),
            'friend_name': Text(value=None, position=self._layout['friend_name'], font=fonts.BoldSmall,
                                color=GREEN),

            'name': CurvedText(value='pwnagotchi>', center=(120, 120), radius=107, start_angle=225,
                              font=fonts.Bold, color=GREEN),

            'status': CurvedText(value=self._voice.default(), center=(120, 120), radius=107, start_angle=90,
                                font=fonts.Medium, color=WHITE),

            'shakes': CurvedText(value='PWND 0 (00)', center=(120, 120), radius=107, start_angle=135,
                                font=fonts.Medium, color=CYAN),

            'mode': CurvedText(value='AUTO', center=(120, 120), radius=107, start_angle=45,
                              font=fonts.Bold, color=CYAN),
        })

        if state:
            for key, value in state.items():
                self._state.set(key, value)

        plugins.on('ui_setup', self)

        if config['ui']['fps'] > 0.0:
            _thread.start_new_thread(self._refresh_handler, ())
            self._ignore_changes = ()
        else:
            logging.warning("ui.fps is 0, the display will only update for major changes")
            self._ignore_changes = ('uptime', 'name')

        ROOT = self

    def set_agent(self, agent):
        self._agent = agent

    def has_element(self, key):
        self._state.has_element(key)

    def add_element(self, key, elem):
        self._state.add_element(key, elem)

    def remove_element(self, key):
        self._state.remove_element(key)

    def width(self):
        return self._width

    def height(self):
        return self._height

    def on_state_change(self, key, cb):
        self._state.add_listener(key, cb)

    def on_render(self, cb):
        if cb not in self._render_cbs:
            self._render_cbs.append(cb)

    def _refresh_handler(self):
        delay = 1.0 / self._config['ui']['fps']
        while True:
            try:
                name = self._state.get('name')
                self.set('name', name.rstrip('█').strip() if '█' in name else (name + ' █'))
                self.update()
            except Exception as e:
                logging.warning("non fatal error while updating view: %s" % e)

            time.sleep(delay)

    def set(self, key, value):
        # Format values for CurvedText components that need labels
        if key == 'channel':
            value = f'CH {value}'
        elif key == 'aps':
            value = f'APS {value}'
        elif key == 'uptime':
            value = f'UP {value}'
        elif key == 'shakes':
            value = f'PWND {value}'
        elif key == 'name':
            value = f'{value}>'

        # Special handling for face to support both text and images
        if key == 'face' and isinstance(value, str):
            # Try to load corresponding face image
            # Extract face name from the face value (e.g., "(◕‿‿◕)" -> "awake")
            face_name = self._get_face_name_from_value(value)
            if face_name:
                face_image = faces_img.get_face_image(face_name, size=(160, 160))
                if face_image is not None:
                    # Access the face component directly from _state, not through .get()
                    if 'face' in self._state._state:
                        face_component = self._state._state['face']
                        if hasattr(face_component, 'image'):
                            face_component.image = face_image
                            logging.info(f"[FACE] ✓ Using image for face: {face_name}")
                        else:
                            logging.error(f"[FACE] Component doesn't have image attr: {type(face_component)}")
                    else:
                        logging.error("[FACE] Face component not found in state")

        self._state.set(key, value)

    def _get_face_name_from_value(self, face_value):
        """Map a face text value to its name for image lookup."""
        face_map = {
            faces.LOOK_R: 'look_r',
            faces.LOOK_L: 'look_l',
            faces.LOOK_R_HAPPY: 'look_r_happy',
            faces.LOOK_L_HAPPY: 'look_l_happy',
            faces.SLEEP: 'sleep',
            faces.SLEEP2: 'sleep2',
            faces.AWAKE: 'awake',
            faces.BORED: 'bored',
            faces.INTENSE: 'intense',
            faces.COOL: 'cool',
            faces.HAPPY: 'happy',
            faces.GRATEFUL: 'grateful',
            faces.EXCITED: 'excited',
            faces.MOTIVATED: 'motivated',
            faces.DEMOTIVATED: 'demotivated',
            faces.SMART: 'smart',
            faces.LONELY: 'lonely',
            faces.SAD: 'sad',
            faces.ANGRY: 'angry',
            faces.FRIEND: 'friend',
            faces.BROKEN: 'broken',
            faces.DEBUG: 'debug',
            faces.UPLOAD: 'upload',
            faces.UPLOAD1: 'upload1',
            faces.UPLOAD2: 'upload2',
        }
        return face_map.get(face_value)

    def get(self, key):
        return self._state.get(key)

    def on_starting(self):
        self.set('status', self._voice.on_starting() + ("\n(v%s)" % pwnagotchi.__version__))
        self.set('face', faces.AWAKE)
        self.update()

    def on_ai_ready(self):
        self.set('mode', '  AI')
        self.set('face', faces.HAPPY)
        self.set('status', self._voice.on_ai_ready())
        self.update()

    def on_manual_mode(self, last_session):
        self.set('mode', 'MANU')
        self.set('face', faces.SAD if (last_session.epochs > 3 and last_session.handshakes == 0) else faces.HAPPY)
        self.set('status', self._voice.on_last_session_data(last_session))
        self.set('epoch', "%04d" % last_session.epochs)
        self.set('uptime', last_session.duration)
        self.set('channel', '-')
        self.set('aps', "%d" % last_session.associated)
        self.set('shakes', '%d (%s)' % (last_session.handshakes, \
                                        utils.total_unique_handshakes(self._config['bettercap']['handshakes'])))
        self.set_closest_peer(last_session.last_peer, last_session.peers)
        self.update()

    def is_normal(self):
        return self._state.get('face') not in (
            faces.INTENSE,
            faces.COOL,
            faces.BORED,
            faces.HAPPY,
            faces.EXCITED,
            faces.MOTIVATED,
            faces.DEMOTIVATED,
            faces.SMART,
            faces.SAD,
            faces.LONELY)

    def on_keys_generation(self):
        self.set('face', faces.AWAKE)
        self.set('status', self._voice.on_keys_generation())
        self.update()

    def on_normal(self):
        self.set('face', faces.AWAKE)
        self.set('status', self._voice.on_normal())
        self.update()

    def set_closest_peer(self, peer, num_total):
        if peer is None:
            self.set('friend_face', None)
            self.set('friend_name', None)
        else:
            # ref. https://www.metageek.com/training/resources/understanding-rssi-2.html
            if peer.rssi >= -67:
                num_bars = 4
            elif peer.rssi >= -70:
                num_bars = 3
            elif peer.rssi >= -80:
                num_bars = 2
            else:
                num_bars = 1

            name = '▌' * num_bars
            name += '│' * (4 - num_bars)
            name += ' %s %d (%d)' % (peer.name(), peer.pwnd_run(), peer.pwnd_total())

            if num_total > 1:
                if num_total > 9000:
                    name += ' of over 9000'
                else:
                    name += ' of %d' % num_total

            self.set('friend_face', peer.face())
            self.set('friend_name', name)
        self.update()

    def on_new_peer(self, peer):
        face = ''
        # first time they met, neutral mood
        if peer.first_encounter():
            face = random.choice((faces.AWAKE, faces.COOL))
        # a good friend, positive expression
        elif peer.is_good_friend(self._config):
            face = random.choice((faces.MOTIVATED, faces.FRIEND, faces.HAPPY))
        # normal friend, neutral-positive
        else:
            face = random.choice((faces.EXCITED, faces.HAPPY, faces.SMART))

        self.set('face', face)
        self.set('status', self._voice.on_new_peer(peer))
        self.update()
        time.sleep(3)

    def on_lost_peer(self, peer):
        self.set('face', faces.LONELY)
        self.set('status', self._voice.on_lost_peer(peer))
        self.update()

    def on_free_channel(self, channel):
        self.set('face', faces.SMART)
        self.set('status', self._voice.on_free_channel(channel))
        self.update()

    def on_reading_logs(self, lines_so_far=0):
        self.set('face', faces.SMART)
        self.set('status', self._voice.on_reading_logs(lines_so_far))
        self.update()

    def wait(self, secs, sleeping=True):
        was_normal = self.is_normal()
        part = secs / 10.0

        for step in range(0, 10):
            # if we weren't in a normal state before going
            # to sleep, keep that face and status on for
            # a while, otherwise the sleep animation will
            # always override any minor state change before it
            if was_normal or step > 5:
                if sleeping:
                    if secs > 1:
                        self.set('face', faces.SLEEP)
                        self.set('status', self._voice.on_napping(int(secs)))
                    else:
                        self.set('face', faces.SLEEP2)
                        self.set('status', self._voice.on_awakening())
                else:
                    self.set('status', self._voice.on_waiting(int(secs)))
                    good_mood = self._agent.in_good_mood()
                    if step % 2 == 0:
                        self.set('face', faces.LOOK_R_HAPPY if good_mood else faces.LOOK_R)
                    else:
                        self.set('face', faces.LOOK_L_HAPPY if good_mood else faces.LOOK_L)

            time.sleep(part)
            secs -= part

        self.on_normal()

    def on_shutdown(self):
        self.set('face', faces.SLEEP)
        self.set('status', self._voice.on_shutdown())
        self.update(force=True)
        self._frozen = True

    def on_bored(self):
        self.set('face', faces.BORED)
        self.set('status', self._voice.on_bored())
        self.update()

    def on_sad(self):
        self.set('face', faces.SAD)
        self.set('status', self._voice.on_sad())
        self.update()

    def on_angry(self):
        self.set('face', faces.ANGRY)
        self.set('status', self._voice.on_angry())
        self.update()

    def on_motivated(self, reward):
        self.set('face', faces.MOTIVATED)
        self.set('status', self._voice.on_motivated(reward))
        self.update()

    def on_demotivated(self, reward):
        self.set('face', faces.DEMOTIVATED)
        self.set('status', self._voice.on_demotivated(reward))
        self.update()

    def on_excited(self):
        self.set('face', faces.EXCITED)
        self.set('status', self._voice.on_excited())
        self.update()

    def on_assoc(self, ap):
        self.set('face', faces.INTENSE)
        self.set('status', self._voice.on_assoc(ap))
        self.update()

    def on_deauth(self, sta):
        self.set('face', faces.COOL)
        self.set('status', self._voice.on_deauth(sta))
        self.update()

    def on_miss(self, who):
        self.set('face', faces.SAD)
        self.set('status', self._voice.on_miss(who))
        self.update()

    def on_grateful(self):
        self.set('face', faces.GRATEFUL)
        self.set('status', self._voice.on_grateful())
        self.update()

    def on_lonely(self):
        self.set('face', faces.LONELY)
        self.set('status', self._voice.on_lonely())
        self.update()

    def on_handshakes(self, new_shakes):
        self.set('face', faces.HAPPY)
        self.set('status', self._voice.on_handshakes(new_shakes))
        self.update()

    def on_unread_messages(self, count, total):
        self.set('face', faces.EXCITED)
        self.set('status', self._voice.on_unread_messages(count, total))
        self.update()
        time.sleep(5.0)

    def on_uploading(self, to):
        self.set('face', random.choice((faces.UPLOAD, faces.UPLOAD1, faces.UPLOAD2)))
        self.set('status', self._voice.on_uploading(to))
        self.update(force=True)

    def on_rebooting(self):
        self.set('face', faces.BROKEN)
        self.set('status', self._voice.on_rebooting())
        self.update()

    def on_custom(self, text):
        self.set('face', faces.DEBUG)
        self.set('status', self._voice.custom(text))
        self.update()

    def update(self, force=False, new_data={}):
        for key, val in new_data.items():
            self.set(key, val)

        with self._lock:
            if self._frozen:
                return

            state = self._state
            changes = state.changes(ignore=self._ignore_changes)
            if force or len(changes):
                # Create RGB canvas with black background for IPS display
                self._canvas = Image.new('RGB', (self._width, self._height), BLACK)
                drawer = ImageDraw.Draw(self._canvas)

                plugins.on('ui_update', self)

                for key, lv in state.items():
                    lv.draw(self._canvas, drawer)

                web.update_frame(self._canvas)

                for cb in self._render_cbs:
                    cb(self._canvas)

                self._state.reset()
