import logging, sys
import time
import yaml
import paho.mqtt.client as mqtt
import schedule
import argparse
import os

from .aqualin import *

class Worker:

    config_defaults = {
        'aqualin': { 
            'ble'      : None 
        },
        'mqtt': {
            'broker'   : 'localhost',
            'client'   : None,
            'topic'    : 'aqualin/device',
            'port'     : 1883,
            'keepalive': 60,
            'qos'      : False,
            'user'     : None,
            'passwd'   : None,
        },
        'general': {
            'interval' : 1,
            'verbose'  : 0
        }
    }
    
    def __init__(self, yaml_cfg, cmdline_config):
        logging.basicConfig(stream = sys.stdout, level = logging.DEBUG)
        self.L = logging.getLogger(self.__class__.__name__)
        self.config = self.config_defaults
        read_config = None
        for path in ['~/.aqualin', '~/etc', '/usr/local/etc', '/usr/etc', '/etc', '.' ]:
            full_path = os.path.expanduser(os.path.join(path, yaml_cfg))
            try:
                with open(full_path, 'r') as cfg:
                    read_config = yaml.load(cfg, Loader = yaml.FullLoader)
                    break
            except FileNotFoundError:
                self.L.warning(f"{full_path} not found, continuing")
            except Exception:
                self.L.exception(e)
        self.config = update_dict(self.config, read_config or {})
        self.config = update_dict(self.config, cmdline_config or {})
        self.L.setLevel(max(50 - self.config['general']['verbose'] * 10, 0))
        self.L.debug(self.config)
        self.client = mqtt.Client(self.config['mqtt']['client'])
        self.update_time = None
        self.publish = 0
        self.command = None
        self.aqualin = Aqualin(self.config['aqualin']['ble'])

    def message(self, client, userdata, message):
        self.L.debug("Received %s" % str(message.payload.decode('utf-8')))
        command = str(message.payload.decode('utf-8'))
        if command.upper() == 'ON':
            self.aqualin.on()
        elif command.upper() == 'OFF':
            self.aqualin.off()
        else:
            self.L.warning(f"Unrecognized command {command}")
            return
        self.L.debug("Publishing state now....")
        self.publish_state()

    def connect(self, client, userdata, flags, rc):
        self.L.info(f"Connected to {self.config['mqtt']['broker']}")
        self.client.subscribe(self.config['mqtt']['topic'] + "/set", self.config['mqtt']['qos'])
        self.L.info(f"subscribed to {self.config['mqtt']['topic'] + '/set'}")
        self.publish_state()
        self.publish_battery()

    def mqtt_connect(self):
        self.L.info(f"Connecting to {self.config['mqtt']['broker']}:{self.config['mqtt']['port']}")
        self.client.on_message = lambda client, userdata, message: self.message(client, userdata, message)
        self.client.on_connect = lambda client, userdata, flags, rc: self.connect(client, userdata, flags, rc)
        self.client.on_log = lambda client, userdata, level, buf: self.L.log(level, buf)
        connected = False
        delay = 10
        while not connected:
            try:
                self.client.connect(self.config['mqtt']['broker'],
                            self.config['mqtt']['port'],
                            self.config['mqtt']['keepalive'])
                connected = True
            except:
                self.L.warning(f"Cannot connect to broker {self.config['mqtt']['broker']}, retrying in {delay}s")
                time.sleep(delay)
        return self

    def __publish_state(self, **kwargs):
        kwmap = { 'state' : { 0 : 'OFF', 1 : 'ON' } }
        self.L.debug(f"Requesting state from the device {kwargs}")
        state = self.aqualin.state(**kwargs)
        self.L.debug(f"Publishing {state}")
        for (k,v) in state.items():
            if v is None:
                continue
            if k in kwmap and v in kwmap[k]:
                self.L.debug(f"replaced value of {k}: {v} => {kwmap[k][v]}")
                v = kwmap[k][v]
            self.client.publish(self.config['mqtt']['topic'] + '/' + k, str(v), self.config['mqtt']['qos'], True)

    def publish_state(self):
        self.__publish_state(read_status = True, read_battery = False)

    def publish_battery(self):
        self.__publish_state(read_status = False, read_battery = True)

    def timers(self):
        schedule.every(300).seconds.do(self.publish_state)
        schedule.every(1).hour.do(self.publish_battery)
        return self

    def run(self):
        self.L.info("Entered run loop")
        while True:
            try:
                schedule.run_pending()
                self.client.loop(self.config['general']['interval'])
            except Exception as e:
                self.L.exception(e)
        self.L.info("Exiting")

def update_dict(d1, d2):
    for k in d1.keys():
        if k in d2.keys():
             d1[k].update(d2[k])
    return d1
 
def parse_arguments():
    p = argparse.ArgumentParser("aqualin-mqtt")
    p.add_argument("-v", dest="general.verbose", action = "count", default = 0, help = "verbosity level")
    a = p.parse_args()
    result = {}
    for (k, v) in vars(a).items():
        (k1, k2) = k.split('.')
        if k1 not in result.keys():
            result[k1] = {}
        result[k1][k2] = v
    return result