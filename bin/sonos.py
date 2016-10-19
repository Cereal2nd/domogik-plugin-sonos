#!/usr/bin/python
# -*- coding: utf-8 -*-

""" This file is part of B{Domogik} project (U{http://www.domogik.org}).

License
=======

B{Domogik} is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

B{Domogik} is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Domogik. If not, see U{http://www.gnu.org/licenses}.

@author: Punie Maikel <maikel.punie@gmail.com>
@copyright: (C) 2007-2016 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.common.plugin import Plugin
from soco import SoCo, discover
import traceback

class Sonos(Plugin):
    '''
    Manage
    '''
    def __init__(self):
        Plugin.__init__(self, name='sonos')
        if not self.check_configured():
            self.force_leave()
            return
        self.devices = self.get_device_list(quit_if_no_device = True)
        self._soco_to_dev = {}
        self._map_device_to_soco()
    
        # notify ready
        self.ready()

    def _map_device_to_soco(self):
        found = discover()
        for dev in self.devices:
            for fnd in found.copy():
                if 'device' in dev['parameters'] and \
                    fnd.player_name == dev['parameters']['device']['value']:
                    self._soco_to_dev[dev['id']] = fnd
                    found.remove(fnd)
                else:
                    print "Device does not have an soco device"
        if len(found) != 0:
            print "Not all sonos devices mapped"
            print "Trigger a device_detected message"

    def on_mdp_request(self, msg):
        Plugin.on_mdp_request(self, msg)
        if msg.get_action() == "client.cmd":
            data = msg.get_data()
	    if 'cmd' in data and 'dev' in data:
		typ = data['cmd']
		dev = self._soco_to_dev[data['dev']]
		if typ == "mute":
		    dev.mute()
		elif typ == "play":
		    dev.play()
		elif typ == "pause":
		    dev.pause)
		elif typ == "stop":
		    dev.stop()
		elif typ == "next":
		    dev.next()
		elif typ == "previous":
		    dev.previous()
		elif typ == "volup":
		    vol = dev.volume
		    vol += 5
		    dev.volume = vol
		elif typ == "voldown":
		    vol = dev.volume
		    vol -= 5
		    dev.volume = vol
            reply_msg = MQMessage()
            reply_msg.set_action('client.cmd.result')
            reply_msg.add_data('status', True)
            reply_msg.add_data('reason', None)
            self.reply(reply_msg.get())

if __name__ == "__main__":
    Sonos()
