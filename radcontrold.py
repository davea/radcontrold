#!/usr/bin/env python
import sys
import logging
from configparser import ConfigParser
from os.path import expanduser
from socket import gethostname

from eq3bt import Thermostat, Mode
from bluepy.btle import BTLEException
from mqttwrapper import run_script

log = logging.getLogger("radcontrold")


def callback(topic, payload, config):
    log.debug("%s %s", topic, payload)
    room = topic.split("/")[2]

    mode = {
        b'0': Mode.Closed,
        b'1': Mode.Open,
    }.get(payload)
    if mode is None:
        log.warning("Ignoring invalid payload on %s", topic)
        return

    addresses = config['radiators'].get(room, "")
    if not addresses:
        # Control message is for a radiator we're not responsible for.
        log.debug("No EQ3 addresses in config for %s", room)
        return

    for address in addresses.split(","):
        log.info("Setting %s in %s to %s", address, room, mode)
        try:
            Thermostat(address).mode = mode
        except BTLEException:
            log.warning("Couldn't set mode %s for %s in %s", mode, address, room)


def main():
    formatter = "[%(asctime)s] %(name)s %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=formatter)
    logging.getLogger('eq3bt').setLevel(logging.ERROR)

    hostname = gethostname().split(".")[0]
    config = ConfigParser()
    config.read(expanduser("~/.config/radcontrold/{}.ini".format(hostname)))
    if not config:
        log.warning("No config for {}, exiting.".format(hostname))
        return

    run_script(callback, broker=config['mqtt']['broker'], topics=['control/radiator/+/active'], config=config)


if __name__ == '__main__':
    main()

