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


from os.path import exists, isdir, join
import os
from rtmidi.midiutil import open_midiinput
from rtmidi.midiconstants import SYSTEM_EXCLUSIVE


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
