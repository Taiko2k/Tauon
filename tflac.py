# Tauon Music Box - Tag Module

# Copyright © 2015-2016, Taiko2k captain.gxj@gmail.com

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
#     You should have received a copy of the GNU Lesser General Public License
#     along with Tauon Music Box.  If not, see <http://www.gnu.org/licenses/>.
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
import struct


class Flac:

    def __init__(self, file):

        self.filepath = file
        self.has_picture = False
        self.picture = ""

        self.album_artist = ""
        self.artist = ""
        self.genre = ""
        self.date = ""
        self.comment = ""
        self.album = ""
        self.track_number = ""
        self.track_total = ""
        self.title = ""
        self.encoder = ""
        self.disc_number = ""
        self.picture = ""

        self.sample_rate = 48000
        self.bit_rate = 0
        self.length = 0


    def read_vorbis(self, f):

        #print(f.tell())

        #print("LEN: " + str(z[2]))
        block_position = 0

        buffer = f.read(4)
        block_position += 4
        jump = int.from_bytes(buffer, byteorder='little')

        buffer = f.read(jump)
        block_position += jump

        # f.seek(block_position * -1, 1)
        # print(f.tell())

        buffer = f.read(4)
        block_position += 4
        fields = int.from_bytes(buffer, byteorder='little')
        #print(fields)
        for i in range(fields):
            buffer = f.read(4)
            block_position += 4

            jump = int.from_bytes(buffer, byteorder='little')
            buffer = f.read(jump)
            block_position += jump

            #print(buffer.decode('utf-8'))

            point = 0
            position = 0
            while position < 40:
                # print(sss[position:position+1])
                position += 1

                if buffer[position:position + 1] == b'=':
                    # print(sss[0:position])
                    # print(sss[position + 1:])
                    a = buffer[0:position].decode("utf-8").lower()
                    b = buffer[position + 1:]

                    # print(a)
                    # print(b)

                    if a == "genre":
                        self.genre = b.decode("utf-8")
                    elif a == "date":
                        self.date = b.decode("utf-8")
                    elif a == "comment":
                        self.comment = b.decode("utf-8")
                    elif a == "album":
                        self.album = b.decode("utf-8")
                    elif a == "title":
                        self.title = b.decode("utf-8")
                    elif a == "tracknumber":
                        self.track_number = b.decode("utf-8")
                    elif a == "tracktotal" or a == "totaltracks":
                        self.track_total = b.decode("utf-8")
                    elif a == "encoder":
                        self.encoder = b.decode("utf-8")
                    elif a == "albumartist" or a == "album artist":
                        self.album_artist = b.decode("utf-8")
                    elif a == "artist":
                        self.artist = b.decode("utf-8")


        #print("len total: " + str(block_position))
        sss = f.seek(block_position * -1, 1)
        #print(f.tell())


    def read_seek_table(self, f):

        f.read(10)
        buffer = f.read(8)
        a = (int.from_bytes(buffer, byteorder='big'))
        k = bin(a)[2:].zfill(64)

        #print("SEEKTABLE")
        #print(k)

        samplerate = int(k[0:20], 2)
        #print(samplerate)
        self.sample_rate = samplerate

        bps = int(k[23:28], 2)
        #print(bps)
        self.sample_rate = samplerate

        samples = int(k[28:64], 2)
        #print(samples)
        self.length = samples / samplerate

        f.seek(-18, 1)





    def read(self, get_picture=False):

        f = open(self.filepath, "rb")
        s = f.read(4)
        if s != b'fLaC':
            return

        i = 0
        while i < 7:
            i += 1

            z = self.read_block(f)
            # print(z)

            if z[1] == 0:

                self.read_seek_table(f)

            if z[1] == 4:

                self.read_vorbis(f)

            if z[1] == 6 and get_picture:

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

                self.has_picture = True
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


# file = 'b.flac'
#
# item = Flac(file)
# item.read()


class Opus:

    def __init__(self, file):

        self.filepath = file
        self.has_picture = False

        self.album_artist = ""
        self.artist = ""
        self.genre = ""
        self.date = ""
        self.comment = ""
        self.album = ""
        self.track_number = ""
        self.track_total = ""
        self.title = ""
        self.encoder = ""
        self.disc_number = ""
        self.picture = ""

        self.sample_rate = 48000
        self.bit_rate = 0
        self.length = 0

    def read(self):

        f = open(self.filepath, "rb")

        header = struct.unpack('<4sBBqIIiB', f.read(27))
        #print(header)

        #s = f.read(header[7])
        #print(s)
        segs = struct.unpack('B'*header[7], f.read(header[7]))
        #print(segs)


        s = f.read(7)
        #print(s)

        if s == b'OpusHea':
            f.seek(-7, 1)
        elif s == b'\x01vorbis':

            s = f.read(4)
            #print(s)

            # a = struct.unpack("<BBHIHB", f.read(11))
            a = struct.unpack("<B4i", f.read(17)) # 44100
            self.sample_rate = a[1]
            self.bit_rate = int(a[3] / 1000)
            #print(a)

            f.seek(-28, 1)
        else:
            return

        for p in segs:
            f.read(p)


        header = struct.unpack('<4sBBqIIiB', f.read(27))
        #print(header)

        s = f.read(header[7])
        #print(s)

        #s = f.read(20)
        #print(s)
        s = f.read(7)
        #print(s)
        if s == b"OpusTag":
            f.read(1)
        elif s == b"\x03vorbis":
            pass
        else:
            return
        # print(s)

        #s = f.read(4)

        s = f.read(4)
        a = int.from_bytes(s, byteorder='little')
        #print(a)


        s = f.read(a)
        #print(s)

        s = f.read(4)
        number = int.from_bytes(s, byteorder='little')
        #print(number)
        for i in range(number):
            s = f.read(4)
            length = int.from_bytes(s, byteorder='little')
            s = f.read(length)

            #print(s.decode('utf-8'))

            point = 0
            position = 0
            while position < 40:
                #print(s[position:position+1])
                position += 1

                if s[position:position+1] == b'=':

                    # print(s[0:position])
                    # print(s[position + 1:])
                    a = s[0:position].decode("utf-8").lower()
                    b = s[position + 1:]

                    # print(a)
                    # print(b)

                    if a == "genre":
                        self.genre = b.decode("utf-8")
                    elif a == "date":
                        self.date = b.decode("utf-8")
                    elif a == "comment":
                        self.comment = b.decode("utf-8")
                    elif a == "album":
                        self.album = b.decode("utf-8")
                    elif a == "title":
                        self.title = b.decode("utf-8")
                    elif a == "tracknumber":
                        self.track_number = b.decode("utf-8")
                    elif a == "tracktotal" or a == "totaltracks":
                        self.track_total = b.decode("utf-8")
                    elif a == "encoder":
                        self.encoder = b.decode("utf-8")
                    elif a == "albumartist" or a == "album artist":
                        self.album_artist = b.decode("utf-8")
                    elif a == "artist":
                        self.artist = b.decode("utf-8")
                    elif a == "metadata_block_picture" and False:
                        self.has_picture = True
                        #self.picture = b

                        print(b)
                        import base64
                        import io
                        # ss = io.BytesIO()
                        # bb = io.BytesIO(b)
                        # base64.decode(bb, ss)
                        # ss.seek(0)


                        ee = base64.b64decode(b)
                        ss = io.BytesIO(ee)
                        ss.seek(0)

                        z = ss.read(4)
                        print(int.from_bytes(z, byteorder='big'))

                        ss.seek(0)

                        qqq = ss.read(4)
                        qqq = int.from_bytes(qqq, byteorder='big')
                        print("Picture type: " + str(qqq))
                        qqq = ss.read(4)
                        b = int.from_bytes(qqq, byteorder='big')
                        print("MIME len: " + str(b))

                        qqq = ss.read(b)
                        # print(qqq)
                        print("MIME: " + qqq.decode('ascii'))

                        qqq = ss.read(4)
                        qqq = int.from_bytes(qqq, byteorder='big')
                        print("Description len: " + str(qqq))

                        qqq = ss.read(qqq)
                        print("Description: " + qqq.decode('utf-8'))

                        qqq = ss.read(4)
                        qqq = int.from_bytes(qqq, byteorder='big')
                        print("Width: " + str(qqq))

                        qqq = ss.read(4)
                        qqq = int.from_bytes(qqq, byteorder='big')
                        print("Height: " + str(qqq))

                        qqq = ss.read(4)
                        qqq = int.from_bytes(qqq, byteorder='big')
                        print("BPP: " + str(qqq))

                        qqq = ss.read(4)
                        qqq = int.from_bytes(qqq, byteorder='big')
                        print("Index colour: " + str(qqq))

                        qqq = ss.read(4)
                        qqq = int.from_bytes(qqq, byteorder='big')
                        print("Bin len: " + str(qqq))

                        self.has_picture = True
                        self.picture = ss.read(qqq)
                        print(self.picture)

                        print("HAS PICTURE")
                        #print(self.picture)
                        # print(len(data))


                        # print(ss.read(50))
                        # ss.seek(0)
                        # print(struct.unpack('>i4s8s', ss.read(16)))
                        # 
                        # print(ss)

                    elif a == "discnumber":
                        self.disc_number = b.decode("utf-8")

                    break

        f.seek(-1, 2)
        # s = f.read(50)
        # print(s)
        g = 100000
        while g > 0:
            if f.tell() < 10:
                break
            g -= 1
            f.seek(-5, 1)
            s = f.read(4)
            #print(s)
            if s == b"OggS":
                # print('found')
                f.seek(-4, 1)
                header = struct.unpack('<4sBBqIIiB', f.read(27))
                # print(header)
                # print(header[3] / 48000)
                self.length = header[3] / 48000
                # print(self.length)
                break



# file = 'd.ogg'
#
# item = Opus(file)
# item.read()