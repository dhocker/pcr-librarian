#
# -*- coding: utf-8 -*-
#
# receive_sysex - from Edirol PCR-800 MIDI Keyboard
# Based on code from the https://github.com/SpotlightKid/python-rtmidi repo.
# See https://github.com/SpotlightKid/python-rtmidi/examples/sysexsaver
#
# Original GitHub code © 2012, 2020 Christopher Arndt
# License: https://github.com/SpotlightKid/python-rtmidi/LICENSE.txt
#
# Changes © 2020 Dave Hocker (AtHomeX10@gmail.com)
#
# References
#   (1) https://www.2writers.com/eddie/TutSysEx.htm
#       Format of a Roland sysex
#
"""
Save control map sysex messages uploaded from an Edirol PCR-800 MIDI keyboard.
There will be 50 individual sysex messages for each control map.
An upload of all control maps will consist of 750 sysex messages.
"""

import argparse
import logging
import os
import re
import sys
import time

from datetime import datetime
from os.path import exists, join

from rtmidi.midiconstants import END_OF_EXCLUSIVE, SYSTEM_EXCLUSIVE
from rtmidi.midiutil import open_midiinput

from manufacturers import manufacturers
from models import models


log = logging.getLogger('upload_sysex')


def _sanitize_name(s, replace='/?*&\\'):
    s = s.strip()
    s = re.sub(r'\s+', '_', s)
    for c in replace:
        s = s.replace(c, '_')
    return s.lower()


class SysexMessage(object):
    """
    Encapsulates a control map sysex message sent by the PCR-800

    sx[0:141]
    F0411000 001A1200 00000000 07000000
    04000100 0F030800 00070F00 00000000
    00000000 00000000 00000000 00000000
    00000000 00000000 00000000 00000000
    00000000 00000000 00000000 00000000
    00000000 00000000 00000000 00000000
    00000000 00000000 00000000 00000000
    00000000 00000000 00000000 00000000
    00000000 00000000 00000044 F7

    sx[0] = F0 = sysex start
    sx[1] = 41 = manufacturer ID = Roland
    sx[2] = 10 = device ID = default
    sx[3] = 00 = model ID = unknown/undefined
    sx[4] = 00 = ?
    sx[5] = 1A = ?
    sx[6] = 12 = ?
    sz[7:139] = control map data
    sz[139] = 44 = Roland checksum over sx[7:139]
    sz[140] = F7 = end of sysex

    """
    _CONTROL_MAP_LEN = 141

    @classmethod
    def fromdata(cls, data):
        self = cls()
        if data[0] != SYSTEM_EXCLUSIVE:
            raise ValueError("Message does not start with 0xF0", data)
        if data[-1] != END_OF_EXCLUSIVE:
            raise ValueError("Message does not end with 0xF7", data)
        if len(data) != cls._CONTROL_MAP_LEN:
            raise ValueError("Message wrong length: exp {0} act {1}".format(cls._CONTROL_MAP_LEN, len(data)), data)

        self._data = data

        if data[1] == 0:
            self.manufacturer_id = (data[1], data[2], data[3])
            self.model_id = data[5]
            self.device_id = data[6]
        else:
            self.manufacturer_id = data[1]
            self.model_id = data[2]
            self.device_id = data[3]

        return self

    def __getitem__(self, i):
        return self._data[i]

    def __getslice(self, i, j):
        return self._data[i:j]

    def calc_check_sum(self):
        """
        Compute checksum over bytes 7-138 of the sysex.
        See https://www.2writers.com/eddie/TutSysEx.htm for an
        explanation of the algorithm.
        The sum of all data bytes 2-138 AND the checksum
        byte 139 should be 0.
        :return:
        """
        s = 0
        for i in range(7, 139):
            s += self._data[i]
            s = s & 0x7F
        if s > 0:
            return 128 - s
        return 0

    def validate_check_sum(self):
        """
        The sum of all data bytes AND the checksum
        byte should be 0.
        :return: True if checksum is valid
        """
        s = 0
        for i in range(7, 140):
            s += self._data[i]
            s = s & 0x7F
        return s == 0

    @property
    def check_sum(self):
        return self._data[139]

    @property
    def manufacturer(self):
        mname = manufacturers.get(self.manufacturer_id)
        if mname:
            return mname[0]

    @property
    def manufacturer_tag(self):
        mname = manufacturers.get(self.manufacturer_id, [])
        if len(mname) >= 2:
            return mname[1]
        elif mname:
            return mname[0]

    @property
    def model(self):
        model_name = models.get(self.manufacturer_id, {}).get(self.model_id)
        return model_name[0] if model_name else "0x%02X" % self.model_id

    @property
    def model_tag(self):
        model_name = models.get(self.manufacturer_id, {}).get(self.model_id, [])
        if len(model_name) >= 2:
            return model_name[1]
        elif model_name:
            return model_name[1]
        else:
            "0x%02X" % self.model_id

    def __repr__(self):
        return "".join(["%02X " % b for b in self._data])

    def as_bytes(self):
        if bytes == str:
            return "".join([chr(b) for b in self._data])
        else:
            return bytes(self._data)


class SysexSaver(object):
    """MIDI input callback handler object."""

    fn_tmpl = "pcr-{:04}.syx"
    fn_index = 1

    def __init__(self, portname, directory, debug=False):
        self.portname = portname
        self.directory = directory
        self.debug = debug

    def __call__(self, event, data=None):
        try:
            message, deltatime = event
            if message[:1] != [SYSTEM_EXCLUSIVE]:
                return

            dt = datetime.now()
            log.debug("[%s: %s] Received sysex msg of %i bytes." % (
                self.portname, dt.strftime('%x %X'), len(message)))
            sysex = SysexMessage.fromdata(message)

            # XXX: This should be implemented in a subclass
            #      loaded via a plugin infrastructure
            data = dict(timestamp=dt.strftime('%Y%m%dT%H%M%S.%f'))
            data['manufacturer'] = _sanitize_name(
                sysex.manufacturer_tag or 'unknown')
            data['device'] = _sanitize_name(sysex.model_tag or 'unknown')

            if sysex.manufacturer_id == 62 and sysex.model_id == 0x0E:
                if sysex[4] == 0x10:
                    # sound dump
                    name = "".join(chr(c) for c in sysex[247:263]).rstrip('_')
                elif sysex[4] == 0x11:
                    # multi dump
                    name = "".join(chr(c) for c in sysex[23:38]).rstrip('_')
                elif sysex[4] == 0x12:
                    # wave dump
                    if sysex[5] > 1:
                        name = "userwave_%04i"
                    else:
                        name = "romwave_%03i"
                    name = name % ((sysex[5] << 7) | sysex[6])
                elif sysex[4] == 0x13:
                    # wave table dump
                    if sysex[6] >= 96:
                        name = "userwavetable_%03i" % (sysex[6] + 1)
                    else:
                        name = "romwavetable_%03i" % (sysex[6] + 1)
                else:
                    name = "%02X" % sysex[4]

                data['name'] = _sanitize_name(name)

            outfn = join(self.directory, SysexSaver.fn_tmpl.format(SysexSaver.fn_index))
            SysexSaver.next_filename_index()

            if exists(outfn):
                log.error("Output file already exists, will not overwrite.")
            else:
                data = sysex.as_bytes()
                with open(outfn, 'wb') as outfile:
                    outfile.write(data)
                    log.info("Sysex message of %i bytes written to '%s'.",
                             len(data), outfn)

                    # This is here because the first sysex for control map 1
                    # has a checksum error. The sysex appears to be empty.
                    if not sysex.validate_check_sum():
                        log.error("Checksum error: exp %d act %d", sysex.check_sum, sysex.calc_check_sum())
                    if sysex.calc_check_sum() != sysex.check_sum:
                        log.error("Checksum calc error: exp %d act %d", sysex.check_sum, sysex.calc_check_sum())
        except Exception as exc:
            msg = "Error handling MIDI message: %s" % exc.args[0]
            if self.debug:
                log.debug(msg)
                if len(exc.args) >= 2:
                    log.debug("Message data: %r", exc.args[1])
            else:
                log.error(msg)

    @classmethod
    def next_filename_index(cls):
        """
        Generate the next sequential sysex filename index
        :return: Nothing.
        """
        cls.fn_index += 1
        if cls.fn_index % 100 > 50:
            cls.fn_index = ((cls.fn_index // 100) * 100) + 101

def main(args=None):
    """Save revceived sysex message to directory given on command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    padd = parser.add_argument
    padd('-o', '--outdir', default=os.getcwd(),
         help="Output directory (default: current working directory).")
    padd('-p', '--port',
         help='MIDI output port number (default: ask)')
    padd('-v', '--verbose', action="store_true",
         help='verbose output')

    args = parser.parse_args(args)

    logging.basicConfig(format="%(name)s: %(levelname)s - %(message)s",
                        level=logging.DEBUG if args.verbose else logging.INFO)

    try:
        midiin, port = open_midiinput(args.port)
    except IOError as exc:
        log.error(exc)
        return 1
    except (EOFError, KeyboardInterrupt):
        return 0

    ss = SysexSaver(port, args.outdir, args.verbose)

    log.debug("Attaching MIDI input callback handler.")
    midiin.set_callback(ss)
    log.debug("Enabling reception of sysex messages.")
    midiin.ignore_types(sysex=False)

    log.info("Uploading to: %s", args.outdir)
    log.info("Waiting for sysex reception. Press Control-C to exit.")
    try:
        # just wait for keyboard interrupt in main thread
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print('')
    finally:
        log.debug("Exit.")
        midiin.close_port()
        del midiin


if __name__ == '__main__':
    sys.exit(main() or 0)
