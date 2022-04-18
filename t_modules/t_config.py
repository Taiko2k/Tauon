# Tauon Music Box - Configuration file module

# Copyright © 2015-2019, Taiko2k captain(dot)gxj(at)gmail.com

#     This file is part of Tauon Music Box.
#
#     Tauon Music Box is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     Tauon Music Box is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU Lesser General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with Tauon Music Box.  If not, see <http://www.gnu.org/licenses/>.



# The purpose of this module is to update, parse and write to a configuration file

import os


class Config:

    def __init__(self):

        self.live = []
        self.old = []

    def reset(self):
        self.live.clear()
        self.old.clear()

    def add_text(self, text):

        self.live.append(['comment', text])

    def add_comment(self, text):

        self.live.append(['comment', "# " + text])

    def br(self):

        self.live.append(['comment', ""])

    def update_value(self, key, value):

        for item in self.live:
            if item[0] != "comment":
                if item[1] == key:
                    item[2] = value
                    break

    def load(self, path):

        if os.path.isfile(path):
            with open(path, encoding="utf_8") as f:
                self.old = f.readlines()

    def dump(self, path):

        # if os.path.exists(path) and not os.access("test.conf", os.W_OK):
        #     print("ERROR! Config file cannot be written")
        #     return

        with open(path, 'w', encoding="utf_8") as f:

            for item in self.live:

                if item[0] == 'comment':
                    f.write(item[1])
                    f.write(os.linesep)
                    continue

                c = 0
                f.write(item[1])
                c += len(item[1])

                f.write(" = ")
                c += 3

                if item[0] == 'bool':
                    if item[2] is True:
                        f.write("true")
                        c += 4
                    else:
                        f.write("false")
                        c += 5

                if item[0] == 'string':
                    f.write('"')
                    f.write(item[2])
                    f.write('"')
                    c += len(item[2]) + 2

                if item[0] == 'int':
                    f.write(str(item[2]))
                    c += len(str(item[2]))

                if item[0] == 'float':
                    f.write(str(item[2]))
                    c += len(str(item[2]))

                if item[3]:
                    d = 30 - c
                    if d > 0:
                        f.write(" " * d)
                    f.write("  # ")
                    f.write(item[3])

                f.write(os.linesep)

            f.write(os.linesep)

    def sync_add(self, type, key, default_value, comment=""):

        got_old = False
        old_value = None

        for row in self.old:
            row = row.split(" #", 1)[0]
            if "=" in row:
                if row.split("=", 1)[0].strip() == key:
                    old_value = row.split("=", 1)[1].strip()
                    if old_value:
                        got_old = True
                        break

        if type == 'bool':
            if got_old:
                if old_value == 'true':
                    self.live.append(['bool', key, True, comment])
                    return True
                if old_value == 'false':
                    self.live.append(['bool', key, False, comment])
                    return False
            self.live.append(['bool', key, default_value, comment])
            return default_value

        if type == 'string':

            if old_value is None:
                self.live.append(['string', key, default_value, comment])
                return default_value

            #old_value = old_value.strip('"')
            if old_value and old_value[0] == old_value[-1] == "\"":
                old_value = old_value[1:-1]

            if not got_old:
                self.live.append(['string', key, default_value, comment])
                return default_value

            self.live.append(['string', key, old_value, comment])
            return old_value

            # if got_old:
            #     old_value = old_value.strip('"')
            #     if old_value:
            #         self.live.append(['string', key, old_value, comment])
            #         return old_value
            #
            # self.live.append(['string', key, default_value, comment])
            # return default_value

        if type == 'int':
            if got_old and old_value.isdigit():
                old_value = int(old_value)
                self.live.append(['int', key, old_value, comment])
                return old_value

            self.live.append(['int', key, default_value, comment])
            return default_value

        if type == 'float':
            if got_old:
                try:
                    old_value = float(old_value)
                    self.live.append(['float', key, old_value, comment])
                    return old_value
                except:
                    print("Warning: Config file contains invalid float")
                    pass
            self.live.append(['float', key, default_value, comment])
            return default_value


