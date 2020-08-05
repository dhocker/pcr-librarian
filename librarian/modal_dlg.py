# coding: utf-8
#
# modal_dlg - base modal dialog box
# Copyright © 2020 Dave Hocker (email: AtHomeX10@gmail.com)
# Based on concepts and code from https://effbot.org/tkinterbook/tkinter-dialog-windows.htm
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the LICENSE.md file for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program (the LICENSE.md file).  If not, see <http://www.gnu.org/licenses/>.
#


from tkinter import *
import os


class ModalDlg(Toplevel):
    """
    Base class for a stock modal dialog box
    """
    def __init__(self, parent, title = None):
        """
        Construct an instance of a modal dialog box. Designed to be
        a base class for a customized dialog. The derived class whould
        call the begin_modal() method to make the dialog modal.
        :param parent: Parent widget/frame
        :param title: Title of the dialog
        """

        super(ModalDlg, self).__init__(parent)
        self.transient(parent)

        if title:
            self.title(title)

        self.parent = parent

        self.result = None

        # Body of dialog
        body = Frame(self)
        self.initial_focus = self.body(body)
        body.pack(padx=5, pady=5)

        # Buttons at bottom of dialog
        self.buttonbox()

        self.grab_set()

        if not self.initial_focus:
            self.initial_focus = self

        self.protocol("WM_DELETE_WINDOW", self.cancel)

        self.dlg_center()

        self.initial_focus.focus_set()

    def begin_modal(self):
        """
        This makes the dialog modal.
        :return:
        """
        self.wait_window(window=self)

    def body(self, master):
        """
        Main content of dialog. Designed to be overriden in a
        derived class
        :param master:
        :return: Widget that should receive initial focus
        """
        pass

    def buttonbox(self):
        """
        Standard OK/Cancel button set. Can be overriden.
        :return: Frame containing buttons.
        """
        box = Frame(self)

        self.btn_ok = Button(box, text="OK", width=10, command=self.ok, default=ACTIVE)
        self.btn_ok.pack(side=LEFT, padx=5, pady=5)
        self.btn_cancel = Button(box, text="Cancel", width=10, command=self.cancel)
        self.btn_cancel.pack(side=LEFT, padx=5, pady=5)

        self.bind("<Return>", self.ok)
        self.bind("<KP_Enter>", self.ok)
        self.bind("<Escape>", self.cancel)

        box.pack()

        return box

    def ok(self, event=None):
        """
        The OK button was clicked
        :param event:
        :return:
        """
        if not self.validate():
            self.initial_focus.focus_set() # put focus back
            return

        self.withdraw()
        self.update_idletasks()

        self.apply()
        self.result = True

        self.dlg_destroy()

    def cancel(self, event=None):
        """
        The Cancel button was clicked.
        :param event:
        :return:
        """
        self.result = False
        self.dlg_destroy()

    def validate(self):
        return 1 # override

    def apply(self):
        pass # override

    def dlg_destroy(self):
        """
        Take down the dialog
        :return:
        """
        # put focus back to the parent window
        self.parent.focus_set()
        self.destroy()

    def dlg_center(self):
        """
        Center the dialog in the current screen
        :return:
        """
        # Screen metrics
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()

        # Size the dialog window according to its contents
        self.update()
        w = self.winfo_width()
        h = self.winfo_height()
        # Centered
        x = int((sw - w) / 2)
        y = int((sh - h) / 2)
        # width x height + x + y
        geo = "{0}x{1}+{2}+{3}".format(w, h, x, y)
        # geo = "+{}+{}".format(x, y)
        self.geometry(geo)
        # self.resizable(width=True, height=True)
        self.resizable(width=True, height=False)
