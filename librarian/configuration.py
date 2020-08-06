# coding: utf-8
#
# PCR-300/500/800 Librarian - configuration
# © 2020 Dave Hocker (email: AtHomeX10@gmail.com)
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
import os
import json


class Configuration():
    active_config = {
        "recent": []
    }

    @classmethod
    def load_configuration(cls):
        # Try to open the conf file. If there isn't one, we give up.
        try:
            cfg_path = cls.get_file_path()
            if not os.path.exists(cfg_path):
                cls.save_configuration()
            cfg = open(cfg_path, 'r')
        except Exception as ex:
            print("Unable to open {0}".format(cfg_path))
            print(str(ex))
            return

        # Read the entire contents of the conf file
        cfg_json = cfg.read()
        cfg.close()
        # print cfg_json

        # Try to parse the conf file into a Python structure
        try:
            cls.active_config = json.loads(cfg_json)
        except Exception as ex:
            print("Unable to parse configuration file as JSON")
            print(str(ex))

    @classmethod
    def save_configuration(cls):
        try:
            cfg_path = cls.get_file_path()

            if not os.path.exists(os.path.dirname(cfg_path)):
                p = os.path.dirname(cfg_path)
                os.makedirs(p)

            cfg = open(cfg_path, 'w')
            cfg_json = json.dumps(cls.active_config, indent=4)
            cfg.write(cfg_json)
            cfg.close()
        except Exception as ex:
            print("Unable to open {0}".format(cfg_path))
            print(str(ex))
            return

    @classmethod
    def get_recent(cls):
        return cls.active_config["recent"]

    @classmethod
    def set_recent(cls, dir):
        try:
            cls.active_config["recent"].remove(dir)
        except ValueError:
            pass
        cls.active_config["recent"].append(dir)
        # TODO Trim list?
        cls.save_configuration()

    @classmethod
    def clear_recent(cls):
        cls.active_config["recent"].clear()
        cls.save_configuration()

    @classmethod
    def get_file_path(cls):
        """
        Returns the full path to the configuration file
        """
        file_name = "pcr_librarian.conf"
        file_path = ""
        if Configuration.IsLinux():
            file_path = os.environ["HOME"]
            return "{}/pcr_librarian/{}".format(file_path, file_name)
        elif Configuration.IsWindows():
            file_path = os.environ["LOCALAPPDATA"]
            return "{}\\pcr_librarian\\{}".format(file_path, file_name)

        return file_name

    @classmethod
    def IsLinux(cls):
        """
        Returns True if the OS is of Linux type (Debian, Ubuntu, etc.)
        """
        return os.name == "posix"

    ######################################################################
    @classmethod
    def IsWindows(cls):
        """
        Returns True if the OS is a Windows type (Windows 7, etc.)
        """
        return os.name == "nt"
