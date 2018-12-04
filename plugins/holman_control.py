#!/usr/bin/env python

from blinker import signal

# import urllib
# import urllib2

import subprocess
import web, json, time
import gv  # Get access to SIP's settings, gv = global variables
from urls import urls  # Get access to SIP's URLs
from sip import template_render
from webpages import ProtectedPage

gv.use_gpio_pins = False  # Signal SIP to not use GPIO pins


# Add a new url to open the data entry page.
urls.extend(['/holman', 'plugins.holman_control.settings',
	'/holmanj', 'plugins.holman_control.settings_json',
	'/holmanu', 'plugins.holman_control.update']) 

# Add this plugin to the plugins menu
gv.plugin_menu.append(['Holman Timer Control', '/holman'])

config = {}
prior = [0] * len(gv.srvals)

# Read in the parameters for this plugin from its JSON file
def load_params():
    global config
    try:
        with open('./data/holman_control.json', 'r') as f:  # Read the settings from file
            config = json.load(f)
    except IOError: #  If file does not exist create file with defaults.
        config = {
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

        with open('./data/holman_control.json', 'w') as f:
            json.dump(config, f, indent=4)
    return

load_params()

#### output command when signal received ####
def on_zone_change(name, **kw):
    """ Switch relays when core program signals a change in station state."""
    global prior
#     print 'change signaled'
#     print prior
#     print gv.srvals
    if gv.srvals != prior: # check for a change   
        for i in range(len(gv.srvals)):
            if gv.srvals[i] != prior[i]: #  this station has changed
                if gv.srvals[i]: # station is on
# 					command = "wget http://xxx.xxx.xxx.xxx/relay1on"
                    command = commands['on'][i]
                    if command:
                    	subprocess.call(command.split())
                else:              	
	                command = commands['off'][i]
	                if command:	                	
						subprocess.call(command.split())                 
        prior = gv.srvals[:]
    return


zones = signal('zone_change')
zones.connect(on_zone_change)

################################################################################
# Web pages:                                                                   #
################################################################################

class settings(ProtectedPage):
    """Load an html page for entering cli_control commands"""

    def GET(self):
        with open('./data/holman_control.json', 'r') as f:  # Read the settings from file
            config = json.load(f)
        return template_render.holman_control(config)


class settings_json(ProtectedPage):
    """Returns plugin settings in JSON format"""

    def GET(self):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Content-Type', 'application/json')
        return json.dumps(config)


class update(ProtectedPage):
    """Save user input to holman_control.json file"""

    def GET(self):
        qdict = web.input()
        config = { 'mac': [] }

        for i in range(gv.sd['nst']):
            config['mac'].append(qdict['mac'+str(i)])
        	
#         print 'new commands: ', commands
        with open('./data/holman_control.json', 'w') as f:  # write the settings to file
          	json.dump(config, f, indent=4)
        raise web.seeother('/')
