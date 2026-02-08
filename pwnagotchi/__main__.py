#!/usr/bin/env python3
"""
Pwnagotchi entry point for module execution (python -m pwnagotchi).
This allows running Pwnagotchi in development mode from Docker.
"""
import logging
import argparse
import time
import signal
import sys
import os
import toml

import pwnagotchi
from pwnagotchi import utils
from pwnagotchi.plugins import cmd as plugins_cmd
from pwnagotchi import log
from pwnagotchi import restart
from pwnagotchi import fs
from pwnagotchi.utils import DottedTomlEncoder
from pwnagotchi.ui import faces


def do_clear(display):
    logging.info("clearing the display ...")
    display.clear()
    sys.exit(0)


def do_manual_mode(agent):
    logging.info("entering manual mode ...")

    agent.mode = 'manual'
    agent.last_session.parse(agent.view(), args.skip_session)
    if not args.skip_session:
        logging.info(
            "the last session lasted %s (%d completed epochs, trained for %d), average reward:%s (min:%s max:%s)" % (
                agent.last_session.duration_human,
                agent.last_session.epochs,
                agent.last_session.train_epochs,
                agent.last_session.avg_reward,
                agent.last_session.min_reward,
                agent.last_session.max_reward))

    while True:
        display.on_manual_mode(agent.last_session)
        time.sleep(5)
        if grid.is_connected():
            plugins.on('internet_available', agent)


def do_auto_mode(agent):
    import os
    logging.info("entering auto mode ...")

    agent.mode = 'auto'
    agent.start()

    # In DEV_MODE, just keep the UI updating without actual WiFi operations
    if os.getenv("DEV_MODE") == "1":
        logging.warning("DEV_MODE: Running in display-only mode (no WiFi operations)")
        # Give the UI a moment to initialize
        time.sleep(2)

        while True:
            try:
                logging.info("DEV: Setting bored state with face...")
                agent.set_bored()
                agent.view().set('status', 'Bored in dev mode...')
                agent.view().set('name', 'pwnagotchi-dev')
                agent.view().set('face', faces.BORED)
                agent.view().update(force=True)
                time.sleep(5)

                logging.info("DEV: Setting excited state with face...")
                agent.set_excited()
                agent.view().set('status', 'Excited!')
                agent.view().set('face', faces.EXCITED)
                agent.view().update(force=True)
                time.sleep(5)

                logging.info("DEV: Setting sad state with face...")
                agent.set_sad()
                agent.view().set('status', 'Sad...')
                agent.view().set('face', faces.SAD)
                agent.view().update(force=True)
                time.sleep(5)
            except Exception as e:
                logging.exception("error in dev mode loop")
                time.sleep(30)
        return

    while True:
        try:
            # recon on all channels
            agent.recon()
            # get nearby access points grouped by channel
            channels = agent.get_access_points_by_channel()
            # for each channel
            for ch, aps in channels:
                agent.set_channel(ch)

                if not agent.is_stale() and agent.any_activity():
                    logging.info("%d access points on channel %d" % (len(aps), ch))

                # for each ap on this channel
                for ap in aps:
                    # send an association frame in order to get for a PMKID
                    agent.associate(ap)
                    # deauth all client stations in order to get a full handshake
                    for sta in ap['clients']:
                        agent.deauth(ap, sta)

            # An interesting effect of this:
            #
            # From Pwnagotchi's perspective, the more new access points
            # and / or client stations nearby, the longer one epoch of
            # its relative time will take ... basically, in Pwnagotchi's universe,
            # WiFi electromagnetic fields affect time like gravitational fields
            # affect ours ... neat ^_^
            agent.next_epoch()

            if grid.is_connected():
                plugins.on('internet_available', agent)

        except Exception as e:
            if str(e).find("wifi.interface not set") > 0:
                logging.exception("main loop exception due to unavailable wifi device, likely programmatically disabled (%s)", e)
                logging.info("sleeping 60 seconds then advancing to next epoch to allow for cleanup code to trigger")
                time.sleep(60)
                agent.next_epoch()
            else:
                logging.exception("main loop exception (%s)", e)


def main():
    parser = argparse.ArgumentParser()
    parser = plugins_cmd.add_parsers(parser)

    # Development mode: Use local config if available, otherwise defaults
    default_config = os.getenv('PWN_CONFIG', '/etc/pwnagotchi/default.toml')
    default_user_config = os.getenv('PWN_USER_CONFIG', '/etc/pwnagotchi/config.toml')

    parser.add_argument('-C', '--config', action='store', dest='config', default=default_config,
                        help='Main configuration file.')
    parser.add_argument('-U', '--user-config', action='store', dest='user_config', default=default_user_config,
                        help='If this file exists, configuration will be merged and this will override default values.')

    parser.add_argument('--manual', dest="do_manual", action="store_true", default=False, help="Manual mode.")
    parser.add_argument('--skip-session', dest="skip_session", action="store_true", default=False,
                        help="Skip last session parsing in manual mode.")

    parser.add_argument('--clear', dest="do_clear", action="store_true", default=False,
                        help="Clear the display and exit.")

    parser.add_argument('--debug', dest="debug", action="store_true", default=False,
                        help="Enable debug logs.")

    parser.add_argument('--version', dest="version", action="store_true", default=False,
                        help="Print the version.")

    parser.add_argument('--print-config', dest="print_config", action="store_true", default=False,
                        help="Print the configuration.")

    global args
    args = parser.parse_args()

    if plugins_cmd.used_plugin_cmd(args):
        config = utils.load_config(args)
        log.setup_logging(args, config)
        rc = plugins_cmd.handle_cmd(args, config)
        sys.exit(rc)

    if args.version:
        print(pwnagotchi.__version__)
        sys.exit(0)

    config = utils.load_config(args)

    if args.print_config:
        print(toml.dumps(config, encoder=DottedTomlEncoder()))
        sys.exit(0)

    from pwnagotchi.identity import KeyPair
    from pwnagotchi.agent import Agent
    from pwnagotchi.ui import fonts
    from pwnagotchi.ui.display import Display
    from pwnagotchi import grid
    from pwnagotchi import plugins

    pwnagotchi.config = config

    # Setup filesystem - skip if in dev mode
    if os.getenv('DEV_MODE') != '1':
        fs.setup_mounts(config)
    else:
        logging.info("DEV_MODE: Skipping filesystem setup")

    log.setup_logging(args, config)
    fonts.init(config)

    # Skip hostname setting in dev mode
    if os.getenv('DEV_MODE') != '1':
        pwnagotchi.set_name(config['main']['name'])
    else:
        logging.info("DEV_MODE: Skipping hostname setup")

    plugins.load(config)

    display = Display(config=config, state={'name': '%s>' % pwnagotchi.name()})

    if args.do_clear:
        do_clear(display)
        sys.exit(0)

    agent = Agent(view=display, config=config, keypair=KeyPair(view=display))

    def usr1_handler(*unused):
        logging.info('Received USR1 signal. Restart process ...')
        restart("MANU" if args.do_manual else "AUTO")

    signal.signal(signal.SIGUSR1, usr1_handler)

    if args.do_manual:
        do_manual_mode(agent)
    else:
        do_auto_mode(agent)


if __name__ == '__main__':
    main()
