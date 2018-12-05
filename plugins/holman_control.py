#!/usr/bin/env python
from __future__ import print_function

from blinker import signal
import subprocess
import web, json, time
from threading import Thread
import socket
import gv  # Get access to SIP's settings, gv = global variables
from urls import urls  # Get access to SIP's URLs
from sip import template_render
from webpages import ProtectedPage


gv.use_gpio_pins = False  # Signal SIP to not use GPIO pins

json_data = './data/holman_control.json'

holman_socket = '/run/holman.sock'

# Add a new url to open the data entry page.
urls.extend(['/holman', 'plugins.holman_control.settings',
	'/holmanj', 'plugins.holman_control.settings_json',
	'/holmanu', 'plugins.holman_control.update']) 

# Add this plugin to the plugins menu
gv.plugin_menu.append(['Holman Timer Control', '/holman'])

class HolmanController(Thread):

    def __init__(self, gv):
        Thread.__init__(self)
        self.gv = gv
        self.daemon = True
        self.config = {}
        self.prior = [0] * len(gv.srvals)
        self.load_params()

        zones = signal('zone_change')
        zones.connect(self.on_zone_change)

        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)

        # Establish initial state
        for station, value in enumerate(self.gv.srvals):
            if self.config['mac'][station]:
                self.control_timer(station, self.config['runtime'] if value else 0)

        self.start()

    def load_params(self):
        # Read in the parameters for this plugin from its JSON file
        try:
            with open(json_data, 'r') as f:  # Read the settings from file
                self.config = json.load(f)
        except IOError: #  If file does not exist create file with defaults.
            self.config = {
                "runtime": 40,
                "mac": [
        	       "f7:52:49:38:b8:e0",
                	"",
                	"",
                	"",
                	"",
                	"",
                	"",
                	"" 
                ],
            } 

            with open(json_data, 'w') as f:
                json.dump(self.config, f, indent=4)

    def control_timer(self, station, runtime):
        message = json.dumps({
            "mac": self.config['mac'][station],
            "runtime": runtime,
        })

        try:
            self.sock.sendto(message, holman_socket)
        except socket.error:
            print('failed to communicate with holman socket')

    def on_zone_change(self, name, **kw):
        """ Switch relays when core program signals a change in station state."""
        if self.gv.srvals != self.prior: # check for a change   
            for i in range(len(self.gv.srvals)):
                if self.gv.srvals[i] != self.prior[i]: #  this station has changed
                    if self.gv.srvals[i]: # station is on
                        print('switching on station %d mac %s' % (i, self.config['mac'][i]))
                        self.control_timer(i, self.config['runtime'])
                    else:
                        print('switching off station %d mac %s' % (i, self.config['mac'][i]))
                        self.control_timer(i, 0)

            self.prior = self.gv.srvals[:]

    def run(self):
        while True:
            time.sleep(1)
            # check if timer needs to be renewed


controller = HolmanController(gv)


################################################################################
# Web pages:                                                                   #
################################################################################

class settings(ProtectedPage):
    """Load an html page for entering cli_control commands"""

    def GET(self):
        with open(json_data, 'r') as f:  # Read the settings from file
            config = json.load(f)
        return template_render.holman_control(config)


class settings_json(ProtectedPage):
    """Returns plugin settings in JSON format"""

    def GET(self):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Content-Type', 'application/json')
        return json.dumps(controller.config)


class update(ProtectedPage):
    """Save user input to holman_control.json file"""

    def GET(self):
        qdict = web.input()
        config = { 'mac': [] }

        for i in range(gv.sd['nst']):
            config['mac'].append(qdict['mac'+str(i)])
        config['runtime'] = int(qdict['runtime'])

        with open(json_data, 'w') as f:  # write the settings to file
          	json.dump(config, f, indent=4)
        raise web.seeother('/')
