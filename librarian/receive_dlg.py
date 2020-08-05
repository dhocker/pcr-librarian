# coding: utf-8
#
# receive_dlg - receive control map sysex messages
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
from modal_dlg import ModalDlg
from sysex_receiver import SysexReceiverPolled


class ReceiveDlg(ModalDlg):
    """
    Customized modal dialog box for receiving sysex messages
    """
    POLLING_INTERVAL = 100
    # There are 50 sysex messages for each control map and there are 15 control maps.
    SINGLE = 50
    ALL = 750

    def __init__(self, parent, title=None, port=0, dir=None, control_map=SINGLE):
        """
        Create a modal dialog box for receiving sysex messages from PCR
        :param parent: Parent window
        :param title: Title for the dialog
        :param port: midiin port number 0-n
        :param dir: directory where sysex messages are to be stored
        :param control_map: number of expected messages: SINGLE or ALL
        """

        self._port = port
        self._dir = dir
        self._control_map = control_map

        super(ReceiveDlg, self).__init__(parent, title=title)

        # Hook up SysexReceiver
        self._receiver = SysexReceiverPolled(self._port, self._dir)

        # Poll for number of sysex messages received
        self._after_id = self.after(self.POLLING_INTERVAL, func=self.midiin_poll)

    def body(self, master):
        """
        create dialog body.  return widget that should have
        initial focus.
        :param master:
        :return:
        """

        self._lbl_body = Label(master, text="Receive from port {}".format(self._port), width=30)
        self._lbl_body.pack()
        if self._control_map == self.SINGLE:
            text = "Start current control map bulk transfer at PCR"
        else:
            text = "Start all control maps bulk transfer at PCR"
        self._lbl_receive = Label(master, text=text, width=50)
        self._lbl_receive.pack()

    def buttonbox(self):
        """
        Standard OK/Cancel button set. Can be overriden.
        :return: Frame containing buttons.
        """
        super(ReceiveDlg, self).buttonbox()
        # The OK button is disable until reception is complete
        self.btn_ok.config(state=DISABLED)
        # And, Cancel is the default
        self.btn_cancel.config(default=ACTIVE)

    def midiin_poll(self):
        """
        Poll for updates to number of sysex messages received
        :return:
        """

        received = self._receiver.poll()
        if received == self._control_map:
            self._lbl_receive.config(text="Receive complete")
            self.btn_ok.config(state=NORMAL)
            self.btn_ok.config(default=ACTIVE)
            self.btn_cancel.config(default=DISABLED)
            self._after_id = None
        else:
            if received > 0:
                self._lbl_receive.config(text="{} of {} sysex messages".format(received, self._control_map))
            # Only schedule polling if there is something left to receive
            self._after_id = self.after(ReceiveDlg.POLLING_INTERVAL, func=self.midiin_poll)

    def dlg_destroy(self):
        """
        Take down the dialog and clean up
        :return:
        """
        # Delete midiin instance
        if self._after_id is not None:
            self.after_cancel(self._after_id)
        self._receiver.close()
        del self._receiver
        super(ReceiveDlg, self).dlg_destroy()