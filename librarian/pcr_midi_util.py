# coding: utf-8
#
# pcr_midi_util
# Copyright © 2020 Dave Hocker (email: AtHomeX10@gmail.com)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the LICENSE file for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program (the LICENSE file).  If not, see <http://www.gnu.org/licenses/>.
#


from os.path import basename, exists, isdir, join
import os
import time
import rtmidi
from rtmidi.midiutil import open_midioutput, open_midiinput, get_api_from_environment
from rtmidi.midiconstants import END_OF_EXCLUSIVE, SYSTEM_EXCLUSIVE


def get_midiout_ports():
    """
    Return a list of MIDI out ports (names)
    :return:
    """
    ports = []
    midiout = rtmidi.MidiOut(get_api_from_environment())
    port_list = midiout.get_ports()
    for portno, name in enumerate(port_list):
        ports.append(name)
    return ports


def open_midiout(port):
    """
    Return a MIDI out port instance for the given port.
    :param port: Port to be opened, 0-n.
    :return:
    """
    midiout, name = open_midioutput(port=port)
    return midiout


def get_midiin_ports():
    """
    Return a list of MIDI in ports (names)
    :return:
    """
    ports = []
    midiin = rtmidi.MidiIn(get_api_from_environment())
    port_list = midiin.get_ports()
    for portno, name in enumerate(port_list):
        ports.append(name)
    return ports


def open_midiin(port):
    """
    Return a MIDI in port instance for the given port.
    :param port: Port to be opened, 0-n.
    :return:
    """
    midiin, name = open_midiinput(port=port)
    return midiin


def send_sysex_file(filename, midiout, delay=50):
    """
    Send the contents of a .syx file
    :param filename: The .syx file to be sent. Technically, it can contain
    multiple sysex messages.
    :param midiout: The MIDI out port to be used.
    :param delay: Pacing delay in milliseconds.
    :return:
    """
    success = True
    bn = basename(filename)

    with open(filename, 'rb') as sysex_file:
        data = sysex_file.read()

        if data[0] == SYSTEM_EXCLUSIVE:
            sox = 0

            while sox >= 0:
                sox = data.find(SYSTEM_EXCLUSIVE, sox)

                if sox >= 0:
                    eox = data.find(END_OF_EXCLUSIVE, sox)

                    if eox >= 0:
                        sysex_msg = data[sox:eox + 1]
                        # Convert string data into list of integers
                        if isinstance(sysex_msg, str):
                            sysex_msg = [ord(c) for c in sysex_msg]

                        midiout.send_message(sysex_msg)

                        # This is pacing the send rate
                        if float(delay) > 0.0:
                            time.sleep(0.001 * float(delay))
                    else:
                        break

                    sox = eox + 1
        else:
            # log.warning("File '%s' does not start with a sysex message.", bn)
            success = False

    return success


def receive_current_control_map(port, control_map_dir):
    receiver = SysexReceiver(port, control_map_dir)
    return receiver

def receive_all_control_maps(port, control_map_dir):
    pass


class SysexReceiver(object):
    """MIDI input callback handler object."""

    fn_tmpl = "pcr-{:04}.syx"

    def __init__(self, port, directory, debug=False, overwrite=True):
        self._directory = directory
        self._debug = debug
        self._overwrite = overwrite
        self._fn_index = 1
        self.sysex_count = 0

        self._midiin, name = open_midiinput(port)
        self._midiin.set_callback(self, data=None)
        self._midiin.ignore_types(sysex=False)
        # At this point, sysex messages will be received asynchronously

    @property
    def received_files(self):
        return self.sysex_count

    def __call__(self, event, data=None):
        """
        Callback for handling incoming sysex messages
        :param event: sysex data and timestamp
        :param data: Reference data provided by receiver creator
        :return:
        """
        try:
            sysex, deltatime = event
            if sysex[:1] != [SYSTEM_EXCLUSIVE]:
                return

            outfn = join(self._directory, SysexReceiver.fn_tmpl.format(self._fn_index))
            self.next_filename_index()

            if self._overwrite and exists(outfn):
                os.remove(outfn)

            sx_data = bytes(sysex)
            with open(outfn, 'wb') as outfile:
                outfile.write(sx_data)
            self.sysex_count += 1
        except Exception as ex:
            print(ex)
            # pass

    def next_filename_index(self):
        """
        Generate the next sequential sysex filename index
        :return: Nothing.
        """
        self._fn_index += 1
        if self._fn_index % 100 > 50:
            self._fn_index = ((self._fn_index // 100) * 100) + 101

    def as_bytes(self):
        if bytes == str:
            return "".join([chr(b) for b in self._data])
        else:
            return bytes(self._data)

    def close(self):
        self._midiin.close_port()


class SysexReceiverPolled():
    """Polled Sysex handler"""

    FN_TMPL = "pcr-{:04}.syx"

    def __init__(self, port, directory, debug=False, overwrite=True):
        self._directory = directory
        self._debug = debug
        self._overwrite = overwrite
        self._fn_index = 1
        self.sysex_count = 0

        self._midiin, name = open_midiinput(port)
        self._midiin.ignore_types(sysex=False)

    @property
    def received_files(self):
        return self.sysex_count

    def poll(self):
        event = self._midiin.get_message()
        while event is not None:
            self._handle_event(event)
            event = self._midiin.get_message()
        return self.sysex_count

    def _handle_event(self, event):
        """
        Callback for handling incoming sysex messages
        :param event: A tuple containing a midi message and timestamp
        :return:
        """
        try:
            sysex, deltatime = event
            if sysex[:1] != [SYSTEM_EXCLUSIVE]:
                return

            outfn = join(self._directory, SysexReceiverPolled.FN_TMPL.format(self._fn_index))
            self._next_filename_index()

            if self._overwrite and exists(outfn):
                os.remove(outfn)

            sx_data = bytes(sysex)
            with open(outfn, 'wb') as outfile:
                outfile.write(sx_data)
            self.sysex_count += 1
        except Exception as ex:
            print(ex)
            # pass

    def _next_filename_index(self):
        """
        Generate the next sequential sysex filename index
        :return: Nothing.
        """
        self._fn_index += 1
        if self._fn_index % 100 > 50:
            self._fn_index = ((self._fn_index // 100) * 100) + 101

    def as_bytes(self):
        if bytes == str:
            return "".join([chr(b) for b in self._data])
        else:
            return bytes(self._data)

    def close(self):
        self._midiin.close_port()
