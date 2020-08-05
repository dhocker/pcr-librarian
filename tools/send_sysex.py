#
# -*- coding: utf-8 -*-
#
# send_sysex.py - send control map sysex files to Editol PCR-800
#
# Based on code from the https://github.com/SpotlightKid/python-rtmidi repo.
# See https://github.com/SpotlightKid/python-rtmidi/sendsysex.py
#
# Original GitHub code © 2012, 2020 Christopher Arndt
# License: https://github.com/SpotlightKid/python-rtmidi/LICENSE.txt
#
# Changes and re-purposing © 2020 Dave Hocker (AtHomeX10@gmail.com)
#
# Syntax
#   Show help
#       python3 send_sysex.py -h
#   List available output ports
#       python3 send_sysex.py {-l | --list-ports}
#   Send control map sysex files
#       python3 send_sysex.py {-p | --port} port {-i | --input} directory [{-d | --delay} delayms] [{-v | --verbose}]
#


# This is the __doc__ string
"""
Send all MIDI System Exclusive files (*.syx) given on the command line.

The path given on the command line (-i path) is a directory and all files
with a *.syx extension in it will be sent (in alphabetical order).

All consecutive sysex messages in each file will be sent to the chosen MIDI
output.

"""

import argparse
import logging
import os
import sys
import time

from os.path import basename, exists, isdir, join

import rtmidi
from rtmidi.midiutil import list_output_ports, open_midioutput
from rtmidi.midiconstants import END_OF_EXCLUSIVE, SYSTEM_EXCLUSIVE


log = logging.getLogger("sendsysex")


def send_sysex_file(filename, midiout, portname, delay=50):
    """Send contents of sysex file to given MIDI output.

    Reads file given by filename and sends all consecutive sysex messages found
    in it to given midiout after prompt.

    """
    bn = basename(filename)

    with open(filename, 'rb') as sysex_file:
        data = sysex_file.read()

        if data[0] == SYSTEM_EXCLUSIVE:
            sox = 0
            i = 0

            while sox >= 0:
                sox = data.find(SYSTEM_EXCLUSIVE, sox)

                if sox >= 0:
                    eox = data.find(END_OF_EXCLUSIVE, sox)

                    if eox >= 0:
                        sysex_msg = data[sox:eox + 1]
                        # Python 2: convert data into list of integers
                        if isinstance(sysex_msg, str):
                            sysex_msg = [ord(c) for c in sysex_msg]

                        log.info("Sending '%s' message #%03i...", bn, i)
                        midiout.send_message(sysex_msg)
                        # This is pacing the send rate
                        time.sleep(0.001 * delay)

                        i += 1
                    else:
                        break

                    sox = eox + 1
        else:
            log.warning("File '%s' does not start with a sysex message.", bn)


def main(args=None):
    """Main program function.

    Parses command line (parsed via ``args`` or from ``sys.argv``), detects
    and optionally lists MIDI output ports, opens given MIDI output port,
    assembles list of SysEx files and calls ``send_sysex_file`` on each of
    them.

    """
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('-i', '--input', dest="input_dir",
         help='directory containing .syx files to be sent')
    ap.add_argument('-l', '--list-ports', action="store_true",
         help='list available MIDI output ports')
    ap.add_argument('-p', '--port', dest='port',
         help='MIDI output port number (default: open virtual port)')
    ap.add_argument('-d', '--delay', default="50", metavar="MS", type=int,
         help='delay between sending each Sysex message in milliseconds. Use for pacing. '
         'Default: %(default)s ms')
    ap.add_argument('-v', '--verbose', action="store_true", help='verbose logging output (debug)')

    args = ap.parse_args(args)
    logging.basicConfig(format="%(name)s: %(levelname)s - %(message)s",
                        level=logging.DEBUG if args.verbose else logging.INFO)

    if args.list_ports:
        try:
            list_output_ports()
        except rtmidi.RtMidiError as exc:
            log.error(exc)
            return 1

        return 0

    files = []
    files.extend(sorted([join(args.input_dir, fn) for fn in os.listdir(args.input_dir)
                         if fn.lower().endswith('.syx')]))

    if not files:
        log.error("No SysEx (.syx) files found in given directory.")
        return 1

    if args.verbose:
        log.debug("List of .syx files to be sent")
        for filename in files:
            log.debug(filename)

    try:
        midiout, portname = open_midioutput(args.port, interactive=False, use_virtual=True)
    except rtmidi.InvalidPortError:
        log.error("Invalid MIDI port number or name.")
        log.error("Use '-l' option to list MIDI ports.")
        return 2
    except rtmidi.RtMidiError as exc:
        log.error(exc)
        return 1
    except (EOFError, KeyboardInterrupt):
        return 0

    # Ask user to start bulk receive at PCR-800
    print("Put the PCR-800 into bulk receive mode for one or all control maps")
    try:
        yn = input("Press ENTER to begin sending, CTRL-C to cancel and exit...\n")
    except KeyboardInterrupt:
        log.info("Canceled")
        return 0

    try:
        for filename in files:
            try:
                send_sysex_file(filename, midiout, portname, args.delay)
            except StopIteration:
                break
            except Exception as exc:
                log.error("Error while sending file '%s': %s", (filename, exc))
    finally:
        midiout.close_port()
        del midiout

    return 0


if __name__ == '__main__':
    sys.exit(main() or 0)
