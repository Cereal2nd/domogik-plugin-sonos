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
from soco.events import event_listener
from soco.exceptions import DIDLMetadataError
from soco.data_structures import DidlItem, DidlMusicTrack 
from threading import Thread
from pprint import pprint
try:
    from queue import Empty
except:  # Py2.7
    from Queue import Empty


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
        self._sub_to_dev = {}
        self._dev_to_sensor = {}
        self._map_device_to_soco()

        self.add_stop_cb(self._unregister_all)
        # start a subscriber thread
        self.subThread = Thread(name="Event", target=self._subEvents)
        self.subThread.start()
        self.register_thread(self.subThread)

        # notify ready
        self.ready()

    def _subEvents(self):
        while not self.should_stop():
            for did, subs in self._sub_to_dev.items():
                for sub in subs:
                    try:
                        event = sub.events.get(timeout=0.5)
                    except Empty:
                        pass
                    else:
                        self._parse_renderControl(did, event)

    def _parse_renderControl(self, did, event):
        print "+++++++++++++++"
        sens = self._dev_to_sensor[did]
        #print sens
        data = {}
        #pprint(event.variables)
        if 'bass' in event.variables and 'Bass' in sens:
            data[sens['Bass']] = event.variables['bass']
        if 'treble' in event.variables and 'Treble' in sens:
            data[sens['Treble']] = event.variables['treble']
        if 'loudness' in event.variables and 'Master' in event.variables['loudness'] and 'Loudness' in sens:
            data[sens['Loudness']] = event.variables['loudness']['Master']
        if 'volume' in event.variables and 'Master' in event.variables['volume'] and 'Volume' in sens:
            data[sens['Volume']] = event.variables['volume']['Master']
        if 'transport_state' in event.variables:
            if 'State' in sens:
                data[sens['State']] = event.variables['transport_state']
            if event.variables['transport_state'] == 'PLAYING':
                # These are only usefull if we are playing
                if 'current_track_duration' in event.variables and 'Current Duration' in sens:
                    data[sens['Current Duration']] = event.variables['current_track_duration']
                if 'current_track_meta_data' in event.variables and type(event.current_track_meta_data) is not str:
                    cur = event.current_track_meta_data
                    # title, album, creator, radio_show, stream_content
                    if 'Current Title' in sens:
                        data[sens['Current Title']] = cur.title
                    if type(cur) is DidlItem:
                        if 'Current Stream' in sens:
                            data[sens['Current Stream']] = cur.stream_content
                        if 'Current Radio Show' in sens:
                            data[sens['Current Radio Show']] = cur.radio_show
                        if 'Current Albun' in sens:
                            data[sens['Current Album']] = ''
                        if 'Current Creator' in sens:
                            data[sens['Current Creator']] = ''
                    elif type(cur) is DidlMusicTrack:
                        if 'Current Stream' in sens:
                            data[sens['Current Stream']] = ''
                        if 'Current Radio Show' in sens:
                            data[sens['Current Radio Show']] = ''
                        if 'Current Albun' in sens:
                            data[sens['Current Album']] = cur.album
                        if 'Current Creator' in sens:
                            data[sens['Current Creator']] = cur.creator
                if 'play_mode' in event.variables and 'Play Mode' in sens:
                    data[sens['Play Mode']] = event.variables['play_mode']
        print data
        self._pub.send_event('client.sensor', data)
        print "+++++++++++++++"

    def _map_device_to_soco(self):
        found = discover()
        if found is None:
            print "No sonos devices found"
            self.force_leave()
        for dev in self.devices:
            for fnd in found.copy():
                if 'device' in dev['parameters'] and \
                    fnd.player_name == dev['parameters']['device']['value']:
                    # create a list
                    self._soco_to_dev[dev['id']] = fnd
                    # build a sensorlist
                    self._dev_to_sensor[dev['id']] = {}
                    for (senid, sen)  in dev['sensors'].items():
                        self._dev_to_sensor[dev['id']][sen['name']] = sen['id']
                    # subscribe to events
                    self._sub_to_dev[dev['id']] = []
                    self._sub_to_dev[dev['id']].append(fnd.renderingControl.subscribe())
                    self._sub_to_dev[dev['id']].append(fnd.avTransport.subscribe())
                    found.remove(fnd)
                else:
                    print "Device does not have an soco device"
        if len(found) != 0:
            print "Not all sonos devices mapped"
            print "Trigger a device_detected message"

    def _unregister_all(self):
        for (id, subs) in self._sub_to_dev.items():
            for sub in subs:
                sub.unsubscribe()
        event_listener.stop()

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
		    dev.pause()
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
