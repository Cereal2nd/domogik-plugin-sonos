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

Plugin purpose
==============

Viera Device control

@author: Punie Maikel <maikel.punie@gmail.com>
@copyright: (C) 2007-2016 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.plugin import XplPlugin
from domogik_packages.plugin_viera.lib.viera import Viera
from soco import SoCo
import traceback

class Bluez(XplPlugin):
    '''
    Manage
    '''
    def __init__(self):
        """
        Create the bluez plugin.
        """
        XplPlugin.__init__(self, name = 'sonos')
        if not self.check_configured():
            self.force_leave()
            return
        devices = self.get_device_list(quit_if_no_device = True)
        Listener(self.send_command, self.myxpl,
            {'xpltype': 'xpl-cmnd', 'schema': 'control.basic'})

        # notify ready
        self.ready()

    def send_command(self, msgr):
        device = msgr.data['device']
        typ = msgr.data['type']
        self.log.info("Sending {0} to {1}".format(typ, device))
        dev = SoCo(device)
        if typ == "mute":
            dev.mute()
        elif typ == "play":
            dev.play()
        elif typ == "stop":
            dev.stop()
        elif typ == "volup":
            vol = dev.volume
            vol += 5
            dev.volume = vol
        elif typ == "voldown":
            vol = dev.volume
            vol -= 5
            dev.volume = vol
        # send stats message
        msg = XplMessage()
        msg.set_type("xpl-trig")
        msg.set_schema("sensor.basic")
        msg.add_data({'device' : device})
        msg.add_data({'current' : typ})
        self.myxpl.send(msg)

if __name__ == "__main__":
    Bluez()
