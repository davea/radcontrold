#!/usr/bin/env python
import sys
import logging
from configparser import ConfigParser
from os.path import expanduser
from socket import gethostname

from eq3bt import Thermostat
from bluepy.btle import BTLEException

log = logging.getLogger("health_check")


def check_battery_statuses(config):
    healthy = True
    for room, addresses in config['radiators'].items():
        addresses = addresses.split(",")
        for addr in addresses:
            try:
                thermostat = Thermostat(addr)
                thermostat.update()
            except BTLEException:
                log.error("Couldn't connect to %s %s!", room, addr)
                healthy = False
                continue
            if thermostat.low_battery:
                log.warning("Low battery reported by %s %s", room, addr)
                healthy = False
    return healthy


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

    healthy = check_battery_statuses(config)
    if not healthy:
        sys.exit(1)

if __name__ == '__main__':
    main()
