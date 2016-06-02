# Tauon Music Box - Tag Module

# Copyright (c) 2015-2016, Taiko2k captain.gxj@gmail.com

#    Permission to use, copy, modify, and/or distribute this software for any
#    purpose with or without fee is hereby granted, provided that the above
#    copyright notice and this permission notice appear in all copies.
#
#    THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
#    WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
#    MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
#    ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
#    WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
#    ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
#    OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE


# The purpose of this module is to read embedded images from FLAC files.


import io
import copy


class Flac:

    def __init__(self, file):

        self.filepath = file
        self.has_pic = False
        self.picture = ""

    def read(self):

        f = open(self.filepath, "rb")
        s = f.read(4)
        if s != b'fLaC':
            return

        i = 0
        while i < 7:
            i += 1

            z = self.read_block(f)

            if z[1] == 6:

                a = f.read(4)
                a = int.from_bytes(a, byteorder='big')
                # print("Picture type: " + str(a))

                a = f.read(4)
                b = int.from_bytes(a, byteorder='big')
                # print("MIME len: " + str(b))

                a = f.read(b)
                # print(a)
                # print("MIME: " + a.decode('ascii'))

                a = f.read(4)
                a = int.from_bytes(a, byteorder='big')
                # print("Description len: " + str(a))

                a = f.read(a)
                # print("Description: " + a.decode('utf-8'))

                a = f.read(4)
                # a = int.from_bytes(a, byteorder='big')
                # print("Width: " + str(a))

                a = f.read(4)
                # a = int.from_bytes(a, byteorder='big')
                # print("Height: " + str(a))

                a = f.read(4)
                # a = int.from_bytes(a, byteorder='big')
                # print("BPP: " + str(a))

                a = f.read(4)
                # a = int.from_bytes(a, byteorder='big')
                # print("Index colour: " + str(a))

                a = f.read(4)
                a = int.from_bytes(a, byteorder='big')
                # print("Bin len: " + str(a))

                self.has_pic = True
                self.picture = f.read(a)
                # print(len(data))

            else:
                data = f.read(z[2])

            if z[0] == 1:
                break

        f.close()

    def read_block(self, f):

        q = f.read(1)
        a = (int.from_bytes(q, byteorder='big'))
        k = bin(a)[2:].zfill(8)
        flag = int(k[:1], 2)
        block_type = int(k[1:], 2)
        s = f.read(3)
        a = (int.from_bytes(s, byteorder='big'))
        length = a

        return flag, block_type, length

    def get(self):
        pass


# file = 'a.flac'
#
# item = Flac(file)
# item.read()
