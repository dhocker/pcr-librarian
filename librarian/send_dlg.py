# coding: utf-8
#
# send_dlg - send control map sysex messages
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


from tkinter import *
import os
from modal_dlg import ModalDlg
from pcr_midi_util import open_midiout, send_sysex_file


class SendDlg(ModalDlg):
    """
    Customized modal dialog box for receiving sysex messages
    """
    PACING_DELAY = 50

    def __init__(self, parent, title=None, port=0, files=[]):
        """
        Create a modal dialog box for receiving sysex messages from PCR
        :param parent: Parent window
        :param title: Title for the dialog
        :param port: midiin port number 0-n
        :param files: List of sysex files to be sent
        """

        self._port = port
        self._files = files
        self._after_id = None

        # Determine length of longest file name
        self._file_name_length = 0
        for f in self._files:
            self._file_name_length = max(self._file_name_length, len(f))

        super(SendDlg, self).__init__(parent, title=title)

        self.begin_modal()

    def body(self, master):
        """
        create dialog body.  return widget that should have
        initial focus.
        :param master:
        :return:
        """

        self._lbl_body = Label(master, text="Send to port {}".format(self._port), width=30)
        self._lbl_body.pack()
        # This label will morph into the status for sending files
        self._lbl_send = Label(master, text="Put PCR into bulk receive mode. Click Send when ready.")
        self._lbl_send.pack()
        self._lbl_sending_file = Label(master=master, text="", width=self._file_name_length)
        self._lbl_sending_file.pack()

    def buttonbox(self):
        """
        Standard OK/Cancel button set. Can be overriden.
        :return: Frame containing buttons.
        """
        box = Frame(self)

        self._btn_send = Button(box, text="Send", width=10, command=self._start_sending, default=ACTIVE)
        self._btn_send.pack(side=LEFT, padx=5, pady=5)
        self._btn_ok = Button(box, text="OK", width=10, command=self.ok, state=DISABLED)
        self._btn_ok.pack(side=LEFT, padx=5, pady=5)
        w = Button(box, text="Cancel", width=10, command=self.cancel)
        w.pack(side=LEFT, padx=5, pady=5)

        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

        box.pack()

        return box

    def _start_sending(self):
        # Update button state
        self._btn_send.config(state=DISABLED)
        self._btn_ok.config(state=NORMAL)
        self._btn_ok.config(default=ACTIVE)

        self._midiout = open_midiout(self._port)
        self._file_index = 0
        self._send_with_pacing()


    def _send_with_pacing(self):
        """
        Poll for updates to number of sysex messages received
        :return:
        """
        # Update status display
        self._lbl_send.config(text="Sending {} of {} control map sysex files".format(self._file_index + 1, len(self._files)))
        self._lbl_send.update()
        self._lbl_sending_file.config(text=self._files[self._file_index], width=100)
        self._lbl_sending_file.update()

        if self._file_index < len(self._files):
            send_sysex_file(self._files[self._file_index], self._midiout)
            self._file_index += 1
            if self._file_index < len(self._files):
                self._after_id = self.after(SendDlg.PACING_DELAY, func=self._send_with_pacing)

    def dlg_destroy(self):
        """
        Take down the dialog and clean up
        :return:
        """
        # Delete midiin instance
        if self._after_id is not None:
            self.after_cancel(self._after_id)
        # self._receiver.close()
        # del self._receiver
        super(SendDlg, self).dlg_destroy()