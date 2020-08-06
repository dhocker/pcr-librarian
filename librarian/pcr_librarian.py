# coding: utf-8
#
# PCR-300/500/800 Librarian
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
# along with this program (the LICENSE.md file).  If not, see <http://www.gnu.org/licenses/>.
#
# How to make an app
# https://py2app.readthedocs.io/en/latest/index.html
# https://www.metachris.com/2015/11/create-standalone-mac-os-x-applications-with-python-and-py2app/
#
# Icons
# https://stackoverflow.com/questions/12306223/how-to-manually-create-icns-files-using-iconutil
#

# Python 3
import os.path
import time
import inspect
# from collections import OrderedDict
from tkinter import filedialog, messagebox
from tkinter import Tk, Frame, Button, Label, LabelFrame, Entry, StringVar, Menu, Listbox, Scrollbar
from tkinter import ttk
from tkinter.ttk import Combobox
import tkinter
from text_message_box import TextMessageBox
from pcr_midi_util import get_midiout_ports, get_midiin_ports
from receive_dlg import ReceiveDlg
from send_dlg import SendDlg
from version import app_version
from configuration import Configuration


class PCRLibrarianApp(Tk):
    """
    Main window for thePCR Librarian app
    """
    def __init__(self):
        super(PCRLibrarianApp, self).__init__()

        # Screen metrics
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()

        # TODO Position and size main window
        self.title("PCR Librarian")

        # ttk theme
        # s = ttk.Style()
        # s.theme_use('classic')
        self.background_color = "#ffffff"
        self.highlight_color = "#e0e0e0"

        # Create window widgets
        self._create_widgets(sw, sh)

        # Size the main window according to its contents
        self.update()
        w = self.winfo_width()
        h = self.winfo_height()
        # Centered
        x = int((sw - w) / 2)
        y = int((sh - h) / 2)
        # width x height + x + y
        geo = "{0}x{1}+{2}+{3}".format(w, h, x, y)
        self.geometry(geo)
        # self.resizable(width=True, height=True)
        self.resizable(width=True, height=False)

        # Handle app exit
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_widgets(self, sw, sh):
        """
        Create the UI widgets
        :param sw: Screen width
        :param sh: Screen height
        :return:
        """
        MIN_WIDTH = 100

        # Create a menu bar for the current OS
        self._create_menu()

        # Control/widget experimentation
        self.config(padx=10)
        self.config(pady=10)

        # Around control map directory widgets
        self._ctrl_frame = LabelFrame(master=self, padx=10, pady=10, text="Control Map Directory")
        self._ctrl_frame.grid(row=0, column=0, sticky="ew")

        # Container for action buttons
        self._button_frame = Frame(master=self, bd=5, padx=5, pady=5)
        self._button_frame.grid(row=2, column=0, pady=5)

        self.columnconfigure(0, weight=1, minsize=MIN_WIDTH)
        self._ctrl_frame.columnconfigure(0, weight=1)

        # Control frame row tracker
        r = 0

        # Directory entry
        self._ent_directory = Entry(master=self._ctrl_frame, width=MIN_WIDTH)
        self._ent_directory.grid(row=r, column=0, sticky="ew")
        r += 1

        # Frame for directory widgets
        self._fr_dir = Frame(master=self._ctrl_frame)

        # Select a directory
        self._btn_dir_button = Button(master=self._fr_dir, text="Select Control Map Directory", command=self._on_select_directory)
        self._btn_dir_button.grid(row=0, column=0, padx=5, pady=5)

        # Recently used directories
        self._cb_recent_dirs = Combobox(master=self._fr_dir, width=50,
                                        values=Configuration.get_recent())
        self._cb_recent_dirs.grid(row=0, column=1, padx=5, pady=5)
        self._cb_recent_dirs.bind("<<ComboboxSelected>>", self._on_recent_directory)

        self._fr_dir.grid(row=r, column=0, padx=10)
        r += 1

        # Control map file listbox with scrollbar
        self._lb_frame = LabelFrame(self._ctrl_frame, text="Control Map Files", pady=5, padx=5)
        self._lb_scrollbar = Scrollbar(self._lb_frame, orient=tkinter.VERTICAL)
        self._lb_filelist = Listbox(master=self._lb_frame, width=100)
        self._lb_scrollbar.config(command=self._lb_filelist.yview)
        self._lb_scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        self._lb_filelist.pack()
        self._lb_frame.grid(row=r, column=0, pady=5)
        r += 1

        # Action buttons are inside the button frame on one row

        self._btn_receive_current_button = Button(master=self._button_frame, text="Receive Current Map", state=tkinter.DISABLED, command=self._on_receive_current_map)
        self._btn_receive_current_button.grid(row=0, column=0, padx=5)

        self._btn_receive_all_button = Button(master=self._button_frame, text="Receive All Maps", state=tkinter.DISABLED, command=self._on_receive_all_maps)
        self._btn_receive_all_button.grid(row=0, column=1, padx=5)

        self._btn_send_button = Button(master=self._button_frame, text="Send Control Map Files", state=tkinter.DISABLED, command=self._on_send)
        self._btn_send_button.grid(row=0, column=2, padx=5)

        self._btn_quit_button = Button(master=self._button_frame, text="Quit", command=self._on_close)
        self._btn_quit_button.grid(row=0, column=3, padx=5)

        # MIDI in/out ports listboxes
        self._lb_midiports_frame = LabelFrame(self, text="MIDI Ports", pady=5, padx=5)

        self._lbl_inports = Label(master=self._lb_midiports_frame, text="In")
        self._lb_midiin_ports = Listbox(master=self._lb_midiports_frame, width=30, height=5,
                                        selectmode=tkinter.SINGLE, exportselection=0)
        self._lbl_inports.grid(row=0, column=0)
        self._lb_midiin_ports.grid(row=1, column=0, padx=5, pady=5)

        self._lbl_outports = Label(master=self._lb_midiports_frame, text="Out")
        self._lb_midiout_ports = Listbox(master=self._lb_midiports_frame, width=30, height=5,
                                         selectmode=tkinter.SINGLE, exportselection=0)
        self._lbl_outports.grid(row=0, column=1)
        self._lb_midiout_ports.grid(row=1, column=1, padx=5, pady=5)

        self._lb_midiports_frame.grid(row=1, column=0, pady=5)

        # Populate midin ports listbox
        self._in_ports = get_midiin_ports()
        for p in self._in_ports:
            self._lb_midiin_ports.insert(tkinter.END, p)

        # Populate midout ports listbox
        self._out_ports = get_midiout_ports()
        for p in self._out_ports:
            self._lb_midiout_ports.insert(tkinter.END, p)

        # Minimize the height of the ports listboxes
        max_height = max(len(self._in_ports), len(self._out_ports))
        self._lb_midiin_ports.config(height=max_height)
        self._lb_midiout_ports.config(height=max_height)

        # Default midi port selections
        self._lb_midiin_ports.select_set(0)
        self._lb_midiout_ports.select_set(0)

        # Status bar
        self._v_statusbar = StringVar(value="Select control map directory")
        self._lbl_statusbar = Label(master=self, textvariable=self._v_statusbar, bd=5, relief=tkinter.RIDGE, anchor=tkinter.W)
        self._lbl_statusbar.grid(row=3, column=0, pady=5, padx=5, sticky="ew")

        # Put the focus in the directory text box
        self._ent_directory.focus_set()

    def _create_menu(self):
        # will return x11 (Linux), win32 or aqua (macOS)
        gfx_platform = self.tk.call('tk', 'windowingsystem')

        # App menu bar
        self._menu_bar = Menu(self)

        if gfx_platform == "aqua":
            # macOS app menu covering things specific to macOS X
            self._appmenu = Menu(self._menu_bar, name='apple')
            self._appmenu.add_command(label='About PCR Librarian', command=self._show_about)
            self._appmenu.add_separator()
            self._menu_bar.add_cascade(menu=self._appmenu, label='PCRLibrarian')

            self.createcommand('tk::mac::ShowPreferences', self._show_preferences)

            filemenu = Menu(self._menu_bar, tearoff=0)
            filemenu.add_command(label="Clear recent directories list", command=self._on_clear_recent)
            self._menu_bar.add_cascade(label="File", menu=filemenu)
        elif gfx_platform in ["win32", "x11"]:
            # Build a menu for Windows or Linux
            filemenu = Menu(self._menu_bar, tearoff=0)
            filemenu.add_command(label="Clear recent directories list", command=self._on_clear_recent)
            filemenu.add_separator()
            filemenu.add_command(label="Exit", command=self._on_close)
            self._menu_bar.add_cascade(label="File", menu=filemenu)

            helpmenu = Menu(self._menu_bar, tearoff=0)
            helpmenu.add_command(label="About", command=self._show_about)
            self._menu_bar.add_cascade(label="Help", menu=helpmenu)

        self.config(menu=self._menu_bar)

    def _set_statusbar(self, text):
        """
        Update the status bar
        :param text:
        :return:
        """
        self._v_statusbar.set(text)
        # Force the widget to update now
        self._lbl_statusbar.update()

    def _on_recent_directory(self, event=None):
        directory = self._cb_recent_dirs.get()
        self._set_directory(directory)

        self._set_statusbar("Ready")

    def _on_select_directory(self):
        """
        Select a directory as the source or target of control map(s)
        :return:
        """
        directory = filedialog.askdirectory(initialdir=os.getcwd(), title="Select source/target directory")
        self._set_directory(directory)

        self._set_statusbar("Ready")

    def _on_clear_recent(self):
        Configuration.clear_recent()
        self._cb_recent_dirs.config(values=Configuration.get_recent())

    def _set_directory(self, directory):
        if directory:
            Configuration.set_recent(directory)

            self._ent_directory.delete(0, tkinter.END)
            self._ent_directory.insert(0, directory)

            self._load_files()

            self._btn_receive_current_button["state"] = tkinter.NORMAL
            self._btn_receive_all_button["state"] = tkinter.NORMAL

            self._fill_files_listbox()
            self._cb_recent_dirs.config(values=Configuration.get_recent())

    def _on_send(self):
        """
        Send control map(s). Sends all .syx files from selected directory.
        :return:
        """
        selected_port = self._lb_midiout_ports.curselection()
        dlg = SendDlg(self, title="Send Control Map Sysex Files",
                      port=selected_port[0], files=self._files)

    def _on_receive_current_map(self):
        self._set_statusbar("Ready to receive current control map")
        self._on_receive_control_maps(ReceiveDlg.SINGLE)

    def _on_receive_all_maps(self):
        self._set_statusbar("Ready to receive all 15 control maps")
        self._on_receive_control_maps(ReceiveDlg.ALL)

    def _on_receive_control_maps(self, count):
        # Delete existing .syx files
        self._delete_existing_files()

        selected_port = self._lb_midiin_ports.curselection()
        # Modal dialog box for receiving sysex messages from PCR
        dlg = ReceiveDlg(self, title="Receive Current Control Map",
                         port=selected_port[0], dir=self._ent_directory.get(), control_map=count)

        dlg.begin_modal()

        if dlg.result:
            self._set_statusbar("Current control map(s) received")
        else:
            self._set_statusbar("Canceled")
        self._load_files()
        self._fill_files_listbox()

        del dlg

    def _delete_existing_files(self):
        """
        Delete existing .syx files
        :return:
        """
        for file in self._files:
            os.remove(file)
        self._files.clear()
        self._fill_files_listbox()

    def _load_files(self):
        """
        Load all of the .syx files in the selected directory
        :return:
        """
        self._files = []
        directory = self._ent_directory.get()
        self._files.extend(sorted([os.path.join(directory, fn) for fn in os.listdir(directory)
                                   if fn.lower().endswith('.syx')]))
        if len(self._files) >= 50:
            self._btn_send_button["state"] = tkinter.NORMAL
        else:
            self._btn_send_button["state"] = tkinter.DISABLED

    def _fill_files_listbox(self):
        """
        Load the files listbox with all of the .syx files in the selected diretory
        :return:
        """
        self._lb_filelist.delete(0, tkinter.END)
        for f in self._files:
            self._lb_filelist.insert(tkinter.END, f)

    def _on_close(self):
        """
        App is closing. Warn user if unsaved changes.
        :return:
        """
        print(self._ent_directory.get())
        # TODO Save the directory setting?
        # if self._are_unsaved_changes():
        #     return False
        self.destroy()
        return True

    def _show_about(self):
        about_text = \
            "© 2020 by Dave Hocker\n" + \
            "\n" + \
            "Source: https://github.com/dhocker/pcr_librarian\n" + \
            "License: GNU General Public License v3\n" + \
            "as published by the Free Software Foundation, Inc. "

        # Locate logo image file
        cwd = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0]))
        if os.path.exists(cwd + "/pcr_librarian.gif"):
            image_path = cwd + "/pcr_librarian.gif"
        elif os.path.exists(cwd + "/resources/pcr_librarian.gif"):
            image_path = cwd + "/resources/pcr_librarian.gif"
        else:
            image_path = "pcr_librarian.gif"

        # This is a modal message box
        mb = TextMessageBox(self, title="About PCR Librarian", text=about_text,
                            heading="PCR Librarian {}".format(app_version()),
                            image=image_path,
                            width=150, height=110,
                            orient=tkinter.HORIZONTAL)
        mb.show()
        self.wait_window(window=mb)

    def _show_preferences(self):
        tkinter.messagebox.showinfo("Preferences for PCR Librarian", "None currently defined")


if __name__ == '__main__':
    Configuration.load_configuration()

    main_frame = PCRLibrarianApp()
    main_frame.mainloop()
    print("Ended")
