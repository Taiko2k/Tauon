# Tauon Music Box - BASS backend Module

# Copyright © 2015-2018, Taiko2k captain(dot)gxj(at)gmail.com

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



from t_modules.t_extra import Timer
import ctypes
from ctypes.util import find_library
from hsaudiotag import auto
import time
import math
import datetime
import os
import copy
import threading
import requests

def player(pctl, gui, prefs, lfm_scrobbler, star_store, tauon):  # BASS

    print("loading bass...")
    player_timer = Timer()
    broadcast_timer = Timer()
    broadcast_update_timer = Timer()
    broadcast_update_timer.set()
    radio_meta_timer = Timer()

    linux_lib_dir = pctl.install_directory + '/lib/'

    if not os.path.isfile(linux_lib_dir + "libbass.so"):
        linux_lib_dir = pctl.user_directory + '/lib/'

    if pctl.macos:
        if not os.path.isfile(linux_lib_dir + "libbass.dylib"):
            linux_lib_dir = pctl.user_directory + '/lib/'

    b_linux_lib_dir = linux_lib_dir.encode()

    if pctl.system == 'windows' or tauon.msys:
        windows_lib_dir = pctl.install_directory + '/lib/'
        bass_module = ctypes.WinDLL(windows_lib_dir + 'bass')
        enc_module = ctypes.WinDLL(windows_lib_dir + 'bassenc')
        mix_module = ctypes.WinDLL(windows_lib_dir + 'bassmix')
        fx_module = ctypes.WinDLL(windows_lib_dir + 'bass_fx')
        # opus_module = ctypes.WinDLL('bassenc_opus')
        ogg_module = ctypes.WinDLL(windows_lib_dir + 'bassenc_ogg')

        function_type = ctypes.WINFUNCTYPE
    elif pctl.system == 'linux' and pctl.macos:
        bass_module = ctypes.CDLL(linux_lib_dir + 'libbass.dylib', mode=ctypes.RTLD_GLOBAL)
        enc_module = ctypes.CDLL(linux_lib_dir + 'libbassenc.dylib', mode=ctypes.RTLD_GLOBAL)
        mix_module = ctypes.CDLL(linux_lib_dir + 'libbassmix.dylib', mode=ctypes.RTLD_GLOBAL)
        ogg_module = ctypes.CDLL(linux_lib_dir + 'libbassenc_ogg.dylib', mode=ctypes.RTLD_GLOBAL)
        #mp3_module = ctypes.CDLL(linux_lib_dir + 'libbassenc_mp3.dylib', mode=ctypes.RTLD_GLOBAL)
        fx_module = ctypes.CDLL(linux_lib_dir + 'libbass_fx.dylib', mode=ctypes.RTLD_GLOBAL)
        function_type = ctypes.CFUNCTYPE
    else:
        bass_module = ctypes.CDLL(linux_lib_dir + 'libbass.so', mode=ctypes.RTLD_GLOBAL)
        enc_module = ctypes.CDLL(linux_lib_dir + 'libbassenc.so', mode=ctypes.RTLD_GLOBAL)
        mix_module = ctypes.CDLL(linux_lib_dir + 'libbassmix.so', mode=ctypes.RTLD_GLOBAL)
        fx_module = ctypes.CDLL(linux_lib_dir + 'libbass_fx.so', mode=ctypes.RTLD_GLOBAL)
        ogg_module = ctypes.CDLL(linux_lib_dir + 'libbassenc_ogg.so', mode=ctypes.RTLD_GLOBAL)
        # mp3_module = ctypes.CDLL(linux_lib_dir + 'libbassenc_mp3.so', mode=ctypes.RTLD_GLOBAL)
        # opus_module = ctypes.CDLL(linux_lib_dir + 'libbassenc_opus.so', mode=ctypes.RTLD_GLOBAL)

        function_type = ctypes.CFUNCTYPE

    QWORD = ctypes.c_int64
    DWORD = ctypes.c_ulong
    HMUSIC = ctypes.c_ulong
    HSAMPLE = ctypes.c_ulong
    HCHANNEL = ctypes.c_ulong
    HSTREAM = ctypes.c_ulong
    HRECORD = ctypes.c_ulong
    HSYNC = ctypes.c_ulong
    HDSP = ctypes.c_ulong
    HFX = ctypes.c_ulong
    HPLUGIN = ctypes.c_ulong

    BASS_Init = function_type(ctypes.c_bool, ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p,
                              ctypes.c_void_p)(('BASS_Init', bass_module))

    BASS_GetVersion = function_type(ctypes.c_ulong)(("BASS_GetVersion", bass_module))

    BASS_FX_GetVersion = function_type(ctypes.c_ulong)(("BASS_FX_GetVersion", fx_module))

    BASS_StreamCreateFile = function_type(ctypes.c_ulong, ctypes.c_bool, ctypes.c_void_p, ctypes.c_int64,
                                          ctypes.c_int64, ctypes.c_ulong)(('BASS_StreamCreateFile', bass_module))
    BASS_Pause = function_type(ctypes.c_bool)(('BASS_Pause', bass_module))
    BASS_Stop = function_type(ctypes.c_bool)(('BASS_Stop', bass_module))
    BASS_Start = function_type(ctypes.c_bool)(('BASS_Start', bass_module))
    BASS_Free = function_type(ctypes.c_int)(('BASS_Free', bass_module))
    BASS_ChannelPause = function_type(ctypes.c_bool, ctypes.c_ulong)(('BASS_ChannelPause', bass_module))
    BASS_ChannelStop = function_type(ctypes.c_bool, ctypes.c_ulong)(('BASS_ChannelStop', bass_module))
    BASS_ChannelPlay = function_type(ctypes.c_bool, ctypes.c_ulong, ctypes.c_bool)(
        ('BASS_ChannelPlay', bass_module))
    BASS_ErrorGetCode = function_type(ctypes.c_int)(('BASS_ErrorGetCode', bass_module))
    BASS_SetConfig = function_type(ctypes.c_bool, ctypes.c_ulong, ctypes.c_ulong)(('BASS_SetConfig', bass_module))
    BASS_SetConfigPtr = function_type(ctypes.c_bool, ctypes.c_ulong, ctypes.c_void_p)(('BASS_SetConfigPtr', bass_module))
    BASS_GetConfig = function_type(ctypes.c_ulong, ctypes.c_ulong)(('BASS_GetConfig', bass_module))
    BASS_ChannelSlideAttribute = function_type(ctypes.c_bool, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_float,
                                               ctypes.c_ulong)(('BASS_ChannelSlideAttribute', bass_module))
    BASS_ChannelSetAttribute = function_type(ctypes.c_bool, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_float)(
        ('BASS_ChannelSetAttribute', bass_module))
    BASS_ChannelGetAttribute = function_type(ctypes.c_int64, ctypes.c_ulong, ctypes.c_ulong)(
        ('BASS_ChannelGetAttribute', bass_module))

    BASS_PluginLoad = function_type(ctypes.c_ulong, ctypes.c_char_p, ctypes.c_ulong)(
        ('BASS_PluginLoad', bass_module))
    BASS_PluginFree = function_type(ctypes.c_bool, ctypes.c_ulong)(('BASS_PluginFree', bass_module))
    BASS_ChannelIsSliding = function_type(ctypes.c_bool, ctypes.c_ulong, ctypes.c_ulong)(
        ('BASS_ChannelIsSliding', bass_module))
    BASS_ChannelSeconds2Bytes = function_type(ctypes.c_int64, ctypes.c_ulong, ctypes.c_double)(
        ('BASS_ChannelSeconds2Bytes', bass_module))
    BASS_ChannelSetPosition = function_type(ctypes.c_bool, ctypes.c_ulong, ctypes.c_int64, ctypes.c_ulong)(
        ('BASS_ChannelSetPosition', bass_module))
    BASS_ChannelGetPosition = function_type(ctypes.c_int64, ctypes.c_ulong, ctypes.c_ulong)(
        ('BASS_ChannelGetPosition', bass_module))

    BASS_StreamFree = function_type(ctypes.c_bool, ctypes.c_ulong)(('BASS_StreamFree', bass_module))
    BASS_ChannelGetLength = function_type(ctypes.c_int64, ctypes.c_ulong, ctypes.c_ulong)(
        ('BASS_ChannelGetLength', bass_module))
    BASS_ChannelBytes2Seconds = function_type(ctypes.c_double, ctypes.c_ulong, ctypes.c_int64)(
        ('BASS_ChannelBytes2Seconds', bass_module))
    BASS_ChannelGetLevel = function_type(ctypes.c_ulong, ctypes.c_ulong)(('BASS_ChannelGetLevel', bass_module))
    BASS_ChannelGetData = function_type(ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p, ctypes.c_ulong)(
        ('BASS_ChannelGetData', bass_module))


    class BASS_BFX_VOLUME(ctypes.Structure):
        _fields_ = [('lChannel', ctypes.c_int),
                    ('fVolume', ctypes.c_float)
                    ]

    class BASS_DX8_PARAMEQ(ctypes.Structure):
        _fields_ = [('fCenter', ctypes.c_float),
                    ('fBandwidth', ctypes.c_float),
                    ('fGain', ctypes.c_float),
                    ]

    para = BASS_DX8_PARAMEQ()


    #
    # fx_bandwidth = 254
    # eqs = [
    #     BASS_DX8_PARAMEQ(510, fx_bandwidth, -15),
    #     BASS_DX8_PARAMEQ(11000, fx_bandwidth, -15),
    #
    # ]



    #BASS_FXSetParameters = function_type(ctypes.c_bool, ctypes.c_ulong, ctypes.POINTER(BASS_BFX_VOLUME))(
    BASS_FXSetParameters = function_type(ctypes.c_bool, ctypes.c_ulong, ctypes.c_void_p)(
        ('BASS_FXSetParameters', bass_module))

    BASS_FXGetParameters = function_type(ctypes.c_bool, ctypes.c_ulong, ctypes.c_void_p)(
        ('BASS_FXGetParameters', bass_module))

    BASS_ChannelSetFX = function_type(ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_int)(
        ('BASS_ChannelSetFX', bass_module))

    SyncProc = function_type(None, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p)
    BASS_ChannelSetSync = function_type(ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_int64, SyncProc,
                                        ctypes.c_void_p)(
        ('BASS_ChannelSetSync', bass_module))

    BASS_ChannelRemoveSync = function_type(ctypes.c_bool, ctypes.c_ulong, ctypes.c_ulong)(
        ('BASS_ChannelRemoveSync', bass_module))


    BASS_ChannelIsActive = function_type(ctypes.c_ulong, ctypes.c_ulong)(
        ('BASS_ChannelIsActive', bass_module))

    BASS_Mixer_StreamCreate = function_type(ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong)(
        ('BASS_Mixer_StreamCreate', mix_module))
    BASS_Mixer_StreamAddChannel = function_type(ctypes.c_bool, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong)(
        ('BASS_Mixer_StreamAddChannel', mix_module))
    BASS_Mixer_ChannelRemove = function_type(ctypes.c_bool, ctypes.c_ulong)(
        ('BASS_Mixer_ChannelRemove', mix_module))
    BASS_Mixer_ChannelSetPosition = function_type(ctypes.c_bool, ctypes.c_ulong, ctypes.c_int64, ctypes.c_ulong)(
        ('BASS_Mixer_ChannelSetPosition', mix_module))
    BASS_Mixer_ChannelFlags = function_type(ctypes.c_int64, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong)(
        ('BASS_Mixer_ChannelFlags', mix_module))


    BASS_Mixer_ChannelGetPositionEx = function_type(QWORD, DWORD, DWORD, DWORD)(
        ('BASS_Mixer_ChannelGetPositionEx', mix_module))

    DownloadProc = function_type(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong, ctypes.c_void_p)

    # BASS_StreamCreateURL = function_type(ctypes.c_ulong, ctypes.c_char_p, ctypes.c_ulong, ctypes.c_ulong,
    #                                      DownloadProc, ctypes.c_void_p)(('BASS_StreamCreateURL', bass_module))
    BASS_StreamCreateURL = function_type(ctypes.c_ulong, ctypes.c_char_p, ctypes.c_ulong, ctypes.c_ulong,
                                         ctypes.c_void_p, ctypes.c_void_p)(('BASS_StreamCreateURL', bass_module))
    BASS_ChannelGetTags = function_type(ctypes.c_char_p, ctypes.c_ulong, ctypes.c_ulong)(
        ('BASS_ChannelGetTags', bass_module))

    BASS_ChannelLock = function_type(ctypes.c_bool, ctypes.c_ulong, ctypes.c_bool)(
        ('BASS_ChannelLock', bass_module))

    BASS_GetCPU = function_type(ctypes.c_float)(('BASS_GetCPU', bass_module))

    def py_down(buffer, length, user):
        # if url_record:
        #
        #     p = create_string_buffer(length)
        #     ctypes.memmove(p, buffer, length)
        #
        #     f = open(record_path + fileline, 'ab')
        #     f.write(p)
        #     f.close
        return 0

    down_func = DownloadProc(py_down)

    EncodeClientProc = function_type(ctypes.c_bool, ctypes.c_ulong, ctypes.c_bool, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_void_p)

    # def py_cmp_func(handle, channel, buffer, length):
    #     return 0
    #
    # cmp_func = EncodeProc(py_cmp_func)
    BASS_Encode_ServerInit = function_type(ctypes.c_ulong, ctypes.c_ulong, ctypes.c_char_p, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, EncodeClientProc,
                           ctypes.c_void_p)(('BASS_Encode_ServerInit', enc_module))


    BASS_Encode_Start = function_type(ctypes.c_ulong, ctypes.c_ulong, ctypes.c_char_p, ctypes.c_ulong,
                                      ctypes.c_bool, ctypes.c_void_p)(('BASS_Encode_Start', enc_module))
    BASS_Encode_CastInit = function_type(ctypes.c_bool, ctypes.c_ulong, ctypes.c_char_p, ctypes.c_char_p,
                                         ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p,
                                         ctypes.c_char_p, ctypes.c_char_p, ctypes.c_ulong, ctypes.c_bool)(
        ('BASS_Encode_CastInit', enc_module))
    BASS_Encode_Stop = function_type(ctypes.c_bool, ctypes.c_ulong)(('BASS_Encode_Stop', enc_module))
    BASS_Encode_SetChannel = function_type(ctypes.c_bool, ctypes.c_ulong, ctypes.c_ulong)(
        ('BASS_Encode_SetChannel', enc_module))
    BASS_Encode_CastSetTitle = function_type(ctypes.c_bool, ctypes.c_ulong, ctypes.c_char_p, ctypes.c_bool)(
        ('BASS_Encode_CastSetTitle', enc_module))
    #
    # BASS_Encode_OPUS_Start = function_type(ctypes.c_ulong, ctypes.c_ulong, ctypes.c_char_p, ctypes.c_ulong, ctypes.c_void_p, ctypes.c_void_p)(
    #     ('BASS_Encode_OPUS_Start', opus_module))

    BASS_Encode_OGG_Start = function_type(ctypes.c_ulong, ctypes.c_ulong, ctypes.c_char_p, ctypes.c_ulong,
                                          ctypes.c_void_p, ctypes.c_void_p)(
        ('BASS_Encode_OGG_Start', ogg_module))

    # BASS_Encode_MP3_Start = function_type(ctypes.c_ulong, ctypes.c_ulong, ctypes.c_char_p, ctypes.c_ulong,
    #                                       ctypes.c_void_p, ctypes.c_void_p)(
    #     ('BASS_Encode_MP3_Start', mp3_module))
    #
    # BASS_Encode_OPUS_Start = function_type(ctypes.c_ulong, ctypes.c_ulong, ctypes.c_char_p, ctypes.c_ulong,
    #                                       ctypes.c_void_p, ctypes.c_void_p)(
    #     ('BASS_Encode_OPUS_Start', opus_module))

    BASS_Encode_OGG_StartFile = function_type(ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p, ctypes.c_ulong,
                                              ctypes.c_void_p)(
        ('BASS_Encode_OGG_StartFile', ogg_module))

    class BASS_DEVICEINFO(ctypes.Structure):
        _fields_ = [('name', ctypes.c_char_p),
                    ('driver', ctypes.c_char_p),
                    ('flags', ctypes.c_ulong)
                    ]

    BASS_GetDeviceInfo = function_type(ctypes.c_bool, ctypes.c_ulong, ctypes.POINTER(BASS_DEVICEINFO))(
        ('BASS_GetDeviceInfo', bass_module))
    BASS_SetDevice = function_type(ctypes.c_bool, ctypes.c_ulong)(('BASS_SetDevice', bass_module))

    BASS_RecordGetDeviceInfo = function_type(ctypes.c_bool, ctypes.c_ulong, ctypes.POINTER(BASS_DEVICEINFO))(
        ('BASS_RecordGetDeviceInfo', bass_module))

    BASS_StreamGetFilePosition = function_type(ctypes.c_int64, ctypes.c_ulong, ctypes.c_ulong)(
        ('BASS_StreamGetFilePosition', bass_module))


    # BASS_StreamGetFilePosition

    BASS_FILEPOS_CURRENT = 0
    BASS_FILEPOS_DOWNLOAD = 1
    BASS_FILEPOS_END = 2
    BASS_FILEPOS_START = 3
    BASS_FILEPOS_CONNECTED = 4
    BASS_FILEPOS_BUFFER = 5
    BASS_FILEPOS_SOCKET = 6
    BASS_FILEPOS_ASYNCBUF = 7
    BASS_FILEPOS_SIZE = 8
    BASS_FILEPOS_BUFFERING = 9


    BASS_FX_DX8_PARAMEQ = 7

    BASS_DEVICE_ENABLED = 1
    BASS_DEVICE_DEFAULT = 2
    BASS_DEVICE_INIT = 4

    BASS_DEVICE_ENABLED = 1
    BASS_DEVICE_DEFAULT = 2
    BASS_DEVICE_INIT = 4

    BASS_POS_BYTE = 0

    BASS_MIXER_END = 0x10000
    BASS_SYNC_END = 2
    BASS_SYNC_STALL = 6
    BASS_SYNC_MIXTIME = 0x40000000
    BASS_UNICODE = 0x80000000
    BASS_STREAM_DECODE = 0x200000
    BASS_ASYNCFILE = 0x40000000
    BASS_SAMPLE_FLOAT = 256
    BASS_DATA_AVAILABLE = 0
    BASS_STREAM_AUTOFREE = 0x40000
    BASS_MIXER_NORAMPIN = 0x800000
    BASS_MIXER_PAUSE = 0x20000

    BASS_DEVICE_DMIX = 0x2000
    BASS_DEVICE_MONO = 2

    BASS_CONFIG_BUFFER = 0
    BASS_CONFIG_ASYNCFILE_BUFFER = 45
    BASS_CONFIG_DEV_BUFFER = 27
    BASS_CONFIG_LIBSSL = 64


    #print(BASS_ErrorGetCode())

    #if system != 'windows':
    # open_flag = 0

    #BASS_SetConfig(BASS_CONFIG_BUFFER, 8000000)
    #BASS_SetConfig(BASS_CONFIG_BUFFER, 30000)

    BASS_SetConfig(BASS_CONFIG_ASYNCFILE_BUFFER, 4000000)
    BASS_SetConfig(BASS_CONFIG_DEV_BUFFER, prefs.device_buffer)
    #if os.path.isfile("/usr/lib/libssl.so.1.0.0"):
    #BASS_SetConfigPtr(BASS_CONFIG_LIBSSL, b"/usr/lib/libssl.so.1.0.0")

    #else:
    #    open_flag = BASS_UNICODE

    # open_flag |= BASS_ASYNCFILE
    # # open_flag |= BASS_STREAM_DECODE
    # open_flag |= BASS_SAMPLE_FLOAT
    # open_flag |= BASS_STREAM_AUTOFREE

    init_flag = BASS_DEVICE_DMIX
    if prefs.mono:
        init_flag |= BASS_DEVICE_MONO


    if pctl.system == 'windows' or tauon.msys:
        #print(BASS_ErrorGetCode())
        windows_lib_dir = pctl.install_directory + '\\lib\\'
        windows_lib_dir = windows_lib_dir.encode()
        BASS_PluginLoad(windows_lib_dir + b'bassopus.dll', 0)
        BASS_PluginLoad(windows_lib_dir + b'bassflac.dll', 0)
        BASS_PluginLoad(windows_lib_dir + b'bass_ape.dll', 0)
        BASS_PluginLoad(windows_lib_dir + b'bass_tta.dll', 0)
        BASS_PluginLoad(windows_lib_dir + b'basswma.dll', 0)
        BASS_PluginLoad(windows_lib_dir + b'basswv.dll', 0)
        BASS_PluginLoad(windows_lib_dir + b'bassalac.dll', 0)

    elif pctl.macos:
        BASS_PluginLoad(b_linux_lib_dir + b'libbassopus.dylib', 0)
        BASS_PluginLoad(b_linux_lib_dir + b'libbassflac.dylib', 0)
        BASS_PluginLoad(b_linux_lib_dir + b'libbass_ape.dylib', 0)
        BASS_PluginLoad(b_linux_lib_dir + b'libbass_aac.dylib', 0)
        BASS_PluginLoad(b_linux_lib_dir + b'libbasswv.dylib', 0)

    else:
        BASS_PluginLoad(b_linux_lib_dir + b'libbassopus.so', 0)
        BASS_PluginLoad(b_linux_lib_dir + b'libbassflac.so', 0)
        BASS_PluginLoad(b_linux_lib_dir + b'libbass_ape.so', 0)
        BASS_PluginLoad(b_linux_lib_dir + b'libbass_aac.so', 0)
        BASS_PluginLoad(b_linux_lib_dir + b'libbass_tta.so', 0)
        BASS_PluginLoad(b_linux_lib_dir + b'libbasswv.so', 0)
        BASS_PluginLoad(b_linux_lib_dir + b'libbassalac.so', 0)
        BASS_PluginLoad(b_linux_lib_dir + b'libbasshls.so', 0)

    BASS_FX_BFX_VOLUME = 65539
    BASS_CONFIG_DEV_DEFAULT = 36

    BASS_SetConfig(BASS_CONFIG_DEV_DEFAULT, True)

    d_info = BASS_DEVICEINFO()

    a = 1
    while True:
        if not BASS_GetDeviceInfo(a, d_info):
            break
        name = d_info.name.decode('utf-8', 'ignore')
        flags = d_info.flags
        enabled = BASS_DEVICE_ENABLED & flags
        default = BASS_DEVICE_DEFAULT & flags
        current = BASS_DEVICE_INIT & flags

        if name != "" and name == prefs.last_device:
            #BassInitSuccess = BASS_Init(a, 48000, init_flag, gui.window_id, 0)
            pctl.set_device = a
        #     #print("Set output device as: " + name)
        #     #bass_ready = True

        # if current > 0:
        #     pctl.set_device = a
        pctl.bass_devices.append((name, enabled, default, current, a))
        a += 1

    # bass_init_success = False
    # if not bass_ready:
    #     bass_init_success = BASS_Init(-1, 48000, init_flag, gui.window_id, 0)
    #     print("Using default sound device")
    # if bass_init_success == True:
    #     print("Bass library initialised")

    if prefs.log_vol:
        BASS_SetConfig(7, True)

    x = (ctypes.c_float * 512)()
    xx = (ctypes.c_float * 1024)()
    ctypes.cast(x, ctypes.POINTER(ctypes.c_float))

    # print(BASS_GetVersion())

    def broadcast_connect(handle, connect, client, headers, user):

        if connect is True:
            pctl.broadcast_clients.append(client.decode())
        else:
            pctl.broadcast_clients.remove(client.decode())
        print((connect, client))

        return True

    client_connect = EncodeClientProc(broadcast_connect)

    BASS_FX_GetVersion()

    centers = [31, 62, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]
    params = [BASS_DX8_PARAMEQ(),
              BASS_DX8_PARAMEQ(),
              BASS_DX8_PARAMEQ(),
              BASS_DX8_PARAMEQ(),
              BASS_DX8_PARAMEQ(),
              BASS_DX8_PARAMEQ(),
              BASS_DX8_PARAMEQ(),
              BASS_DX8_PARAMEQ(),
              BASS_DX8_PARAMEQ(),
              BASS_DX8_PARAMEQ()]

    fxs = [None] * 10

    for i, item in enumerate(params):
        item.fCenter = centers[i]
        item.fBandwidth = 12
        item.fGain = 0

    def replay_gain(stream):
        pctl.active_replaygain = 0
        if prefs.replay_gain > 0 and pctl.target_object.track_gain is not None or pctl.target_object.album_gain is not None:
            gain = None
            if prefs.replay_gain == 1 and pctl.target_object.track_gain is not None:
                gain = pctl.target_object.track_gain
                gui.console.print("Apply track ReplayGain")
            elif prefs.replay_gain == 2 and pctl.target_object.album_gain is not None:
                gain = pctl.target_object.album_gain
                gui.console.print("Apply track ReplayGain")

            if gain is None and prefs.replay_gain == 2:
                gui.console.print("Fallback to track ReplayGain")
                gain = pctl.target_object.track_gain
            if gain is None:
                return

            volfx = BASS_ChannelSetFX(stream, BASS_FX_BFX_VOLUME, 10)
            volparam = BASS_BFX_VOLUME(0, pow(10, gain / 20))
            BASS_FXSetParameters(volfx, ctypes.pointer(volparam))

            gui.console.print(" -- using gain of: " + str(gain))
            pctl.active_replaygain = round(gain, 2)

        if prefs.use_eq:

            bass_player.vol_fx = BASS_ChannelSetFX(stream, BASS_FX_BFX_VOLUME, 9)
            bass_player.vol_param.fVolume = pow(10, (min(prefs.eq)) / 20)
            BASS_FXSetParameters(bass_player.vol_fx, ctypes.pointer(bass_player.vol_param))

            for i in range(len(fxs)):

                fxs[i] = BASS_ChannelSetFX(stream, BASS_FX_DX8_PARAMEQ, 5)

            for i, item in enumerate(params):
                item.fGain = float(prefs.eq[i] * -1)
                BASS_FXSetParameters(fxs[i], ctypes.pointer(params[i]))

    br_timer = Timer()

    class BASSPlayer:

        def __init__(self):

            self.channel = None # Mixer
            self.decode_channel = None
            self.state = 'stopped'
            self.syncing = False
            self.new_handle_for_sync = None

            self.dl_ready = False
            self.loaded_track = None
            self.save_temp = ""
            self.alt = "a"
            self.url = ""
            self.init = False
            self.old_target = ""

            self.vol_fx = None
            self.vol_param = BASS_BFX_VOLUME(0, 0)

            self.end_hit_timer = Timer(10)

            self.open_file_flags = BASS_STREAM_DECODE | BASS_SAMPLE_FLOAT
            if not prefs.short_buffer:
                self.open_file_flags |= BASS_ASYNCFILE
            if pctl.system == "windows" or tauon.msys:
                self.open_file_flags |= BASS_UNICODE

        def try_init(self, re=False):

            if not self.init:
                a = 1
                bass_ready = False
                while True:
                    if not BASS_GetDeviceInfo(a, d_info):
                        break
                    name = d_info.name.decode('utf-8', 'ignore')
                    flags = d_info.flags
                    enabled = BASS_DEVICE_ENABLED & flags
                    default = BASS_DEVICE_DEFAULT & flags
                    current = BASS_DEVICE_INIT & flags

                    if name != "" and name == prefs.last_device:
                        BassInitSuccess = BASS_Init(a, 48000, init_flag, gui.window_id, 0)
                        pctl.set_device = a
                        # print("Set output device as: " + name)
                        bass_ready = True

                    # print((name, enabled, default, current))
                    if current > 0:
                        pctl.set_device = a
                    #pctl.bass_devices.append((name, enabled, default, current, a))
                    a += 1

                bass_init_success = False

                if not bass_ready:
                    bass_init_success = BASS_Init(-1, 48000, init_flag, gui.window_id, 0)
                    print("Using default sound device")
                if bass_init_success == True:
                    print("Bass library initialised")

                else:
                    if not re and prefs.flatpak_mode and prefs.last_device != "PulseAudio Sound Server":
                        prefs.last_device = "PulseAudio Sound Server"
                        self.try_init(re=True)

                self.init = True

        def try_unload(self):
            if self.init and not pctl.broadcast_active:
                BASS_Free()
                self.init = False

        def seek(self):

            if self.state != 'stopped':

                BASS_ChannelStop(self.channel)

                if self.dl_ready:
                    BASS_StreamFree(self.decode_channel)
                    new_handle = BASS_StreamCreateFile(False, self.save_temp.encode(), 0, 0,
                                                       BASS_STREAM_DECODE | BASS_SAMPLE_FLOAT)
                    BASS_Mixer_StreamAddChannel(self.channel, new_handle, BASS_STREAM_AUTOFREE)
                    self.decode_channel = new_handle

                pos = BASS_ChannelSeconds2Bytes(self.decode_channel, pctl.new_time + pctl.start_time)
                BASS_Mixer_ChannelSetPosition(self.decode_channel, pos, 0)
                BASS_ChannelPlay(self.channel, True)

        def update_time(self):

            bpos = BASS_ChannelGetPosition(self.decode_channel, 0)
            tpos = BASS_ChannelBytes2Seconds(self.decode_channel, bpos)
            if tpos >= 0:
                pctl.decode_time = tpos - pctl.start_time


            #BASS_ChannelLock(self.channel, True)

            buffered = BASS_ChannelGetData(self.channel, 0, BASS_DATA_AVAILABLE)
            pos = BASS_Mixer_ChannelGetPositionEx(self.decode_channel, BASS_POS_BYTE, buffered)
            #BASS_ChannelLock(self.channel, False)
            tpos = BASS_ChannelBytes2Seconds(self.decode_channel, pos)

            if tpos >= 0:
                pctl.playing_time = tpos - pctl.start_time

            # print("---")
            # print(BASS_StreamGetFilePosition(self.decode_channel, BASS_FILEPOS_SIZE))
            # print(BASS_StreamGetFilePosition(self.decode_channel, BASS_FILEPOS_ASYNCBUF))

        def stop(self, end=False, now=False):

            if self.state == 'stopped':
                print("Already stopped")
                return

            if now:
                pass
            elif end:
                time.sleep(1.5)
            elif prefs.use_pause_fade:
                BASS_ChannelSlideAttribute(self.channel, 2, 0, prefs.pause_fade_time)
                time.sleep(prefs.pause_fade_time / 1000)

            BASS_ChannelStop(self.channel)
            BASS_StreamFree(self.channel)
            BASS_StreamFree(self.decode_channel)
            self.channel = None
            self.state = 'stopped'
            # BASS_Free()

            if prefs.dc_device:
                self.try_unload()


        def set_volume(self, volume):

            if self.channel is None: return
            BASS_ChannelSlideAttribute(self.channel, 2, volume, prefs.change_volume_fade_time)

        def pause(self, force_suspend=False):

            if self.channel is None:
                return

            if self.state == 'stopped':
                print("Player already stopped")
                return

            if self.state == 'suspend':
                self.start(resume=True)
                return

            if self.state == 'playing':

                if prefs.use_pause_fade:
                    BASS_ChannelSlideAttribute(self.channel, 2, 0, prefs.pause_fade_time)
                    time.sleep(prefs.pause_fade_time / 1000)
                BASS_ChannelPause(self.channel)
                self.state = 'paused'

                if prefs.dc_device or force_suspend:
                    self.try_unload()
                    if not self.init:
                        self.state = 'suspend'

            elif self.state == 'paused':

                BASS_ChannelPlay(self.channel, False)
                if prefs.use_pause_fade:
                    BASS_ChannelSlideAttribute(self.channel, 2, pctl.player_volume / 100, prefs.pause_fade_time)
                self.state = 'playing'

        def download_part(self, url, target, params):

            try:
                self.part = requests.get(url, stream=True, params=params)
            except:
                gui.show_message("Could not connect to server", mode="error")
                self.dl_ready = "Failure"
                return

            #print(self.part.status_code)

            bitrate = 0

            a = 0
            z = 0
            # print(target)
            with open(target, 'wb') as f:
                for chunk in self.part.iter_content(chunk_size=1024):
                    if chunk:  # filter out keep-alive new chunks
                        a += 1
                        if a == 300:  # kilobyes~
                            self.dl_ready = True
                        if url != self.url:
                            self.part.close()
                            break

                        f.write(chunk)

                    z += 1
                    if z == 60:
                        z = 0
                        if bitrate == 0:
                            audio = auto.File(target)
                            bitrate = audio.bitrate
                        if bitrate > 0:
                            gui.update += 1
                            pctl.download_time = a * 1024 / (bitrate / 8) / 1000


            pctl.download_time = -1

            self.dl_ready = True

        def start(self, instant=False, resume=False):

            self.try_init()

            #print("Open file...")

            self.dl_ready = False

            target_object = pctl.target_object
            url = None
            pctl.download_time = 0

            if target_object.is_network:

                # print("START STREAM")

                self.url = ""
                params = None

                try:
                    url, params = pctl.get_url(target_object)
                except:
                    gui.show_message("Failed to query url", "Bad login? Server offline?", mode='info')
                    pctl.stop()
                    return

                if url is None:
                    print(gui.show_message("Failed to query url", "Bad login? Server offline?", mode='info'))
                    pctl.stop()
                    return

                # print(url)
                self.save_temp = prefs.cache_directory + "/" + self.alt + "-temp.mp3"

                if self.alt == 'a':
                    self.alt = 'b'
                else:
                    self.alt = 'a'

                self.url = url

                shoot_dl = threading.Thread(target=self.download_part, args=([url, self.save_temp, params]))
                shoot_dl.daemon = True
                shoot_dl.start()

                while not self.dl_ready:
                    time.sleep(0.02)

                if self.dl_ready == "Failure":
                    self.stop()
                    return

                if url is None:
                    self.stop()
                    return

                target = self.save_temp.encode()

                if pctl.system == "windows" or tauon.msys:
                    target = target.decode().replace("/", "\\")

                new_handle = BASS_StreamCreateFile(False, target, 0, 0, BASS_STREAM_DECODE | BASS_SAMPLE_FLOAT)
                #new_handle = BASS_StreamCreateURL(url, 0, self.open_file_flags, 0, 0)

            else:

                # Get the target filepath and convert to bytes
                #if self.state == "suspend":
                #    target = self.old_target
                #else:
                # print(f"Open file: {pctl.target_open}")
                self.old_target = pctl.target_open.encode('utf-8')
                target = self.old_target

                # Check if the file exists, mark it as missing if not
                if os.path.isfile(pctl.target_object.fullpath):
                    pctl.target_object.found = True
                else:
                    pctl.target_object.found = False
                    gui.pl_update = 1
                    print("Missing File: " + pctl.target_object.fullpath)
                    pctl.playing_state = 0
                    pctl.jump_time = 0
                    pctl.advance(inplace=True, nolock=True)
                    return

                # print(BASS_ErrorGetCode())
                # Load new stream
                if pctl.system == "windows" or tauon.msys:
                    target = target.decode()

                new_handle = BASS_StreamCreateFile(False, target, 0, 0, self.open_file_flags)

                # Verify length if very short
                if pctl.target_object.length < 1:
                    blen = BASS_ChannelGetLength(new_handle, 0)
                    tlen = BASS_ChannelBytes2Seconds(new_handle, blen)
                    pctl.target_object.length = tlen
                    pctl.playing_length = tlen

            # Set the volume to 0 and set replay gain
            # BASS_ChannelSetAttribute(new_handle, 2, 0)

            if self.state == 'paused':
                BASS_ChannelStop(self.channel)
                BASS_StreamFree(self.channel)
                self.state = 'stopped'

            if self.state == 'stopped' or self.state == "suspend":

                # Create Mixer
                mixer = BASS_Mixer_StreamCreate(44100, 2, BASS_MIXER_END)

                # print("Create Mixer")
                # print(BASS_ErrorGetCode())

                BASS_Mixer_StreamAddChannel(mixer, new_handle, BASS_STREAM_AUTOFREE)

                # print("Add channel")
                # print(BASS_ErrorGetCode())

                # Set volume
                if self.state == 'suspend' and prefs.use_pause_fade:
                    BASS_ChannelSetAttribute(mixer, 2, 0)
                else:
                    BASS_ChannelSetAttribute(mixer, 2, pctl.player_volume / 100)

                # Set replay gain
                replay_gain(mixer)

                # print("Play from rest")

                # Add end callback
                BASS_ChannelSetSync(mixer, BASS_SYNC_END | BASS_SYNC_MIXTIME, 0, GapSync2, 0)

                # Set the starting position
                if pctl.start_time_target > 0 or pctl.jump_time > 0 or self.state == 'suspend':
                    target_time = pctl.start_time_target + pctl.jump_time
                    if resume:
                        target_time += pctl.playing_time
                    bytes_position = BASS_ChannelSeconds2Bytes(new_handle, target_time)
                    BASS_ChannelSetPosition(new_handle, bytes_position, 0)


                if self.state == 'suspend' and prefs.use_pause_fade:
                    BASS_ChannelSlideAttribute(mixer, 2, pctl.player_volume / 100, prefs.pause_fade_time)

                # Start playing
                BASS_ChannelPlay(mixer, False)

                # BASS_ChannelSetSync(mixer, BASS_SYNC_STALL, 0, Stall_Sync, new_handle)
                # print(BASS_ErrorGetCode())
                #
                # while True:
                #     time.sleep(1)
                #     print(BASS_StreamGetFilePosition(new_handle, BASS_FILEPOS_ASYNCBUF))

                self.channel = mixer
                self.decode_channel = new_handle
                self.state = 'playing'

            elif self.state == 'playing':

                self.state = 'playing'
                pctl.playing_time = 0

                # A track is already playing, so we need to transition it...

                # Get the length and position of existing track
                BASS_ErrorGetCode()  # Flush any existing error
                blen = BASS_ChannelGetLength(self.decode_channel, 0)
                tlen = BASS_ChannelBytes2Seconds(self.decode_channel, blen)
                bpos = BASS_ChannelGetPosition(self.decode_channel, 0)
                tpos = BASS_ChannelBytes2Seconds(self.decode_channel, bpos)

                # BASS_ChannelLock(self.channel, True)
                # buffered = BASS_ChannelGetData(self.channel, 0, BASS_DATA_AVAILABLE)
                # pos = BASS_Mixer_ChannelGetPositionEx(self.decode_channel, BASS_POS_BYTE, buffered)
                # BASS_ChannelLock(self.channel, False)
                # tpos = BASS_ChannelBytes2Seconds(self.decode_channel, pos)

                if url and pctl.playing_ready():  # not actually currently playing but next / hacky
                    tlen = pctl.playing_object().length

                err = BASS_ErrorGetCode()
                #print(err)

                # print(f"Track transition... Track is {str(tlen - tpos)[:5]} seconds from end")
                #print("TRANSITION")
                # Try to transition without fade and and on time if possible and permitted
                if BASS_ChannelIsActive(self.channel) == 1 and not prefs.use_transition_crossfade and not instant and err == 0 and 0.2 < tlen - tpos < 3:

                    # Start sync on end
                    #print("Activate sync...")
                    # print(BASS_ErrorGetCode())


                    self.new_handle_for_sync = new_handle
                    self.syncing = True
                    br_timer.set()

                    if player_timer.get() > 1:
                        player_timer.set()
                    #print("start sync")
                    while self.syncing:
                        time.sleep(0.005)

                        if (br_timer.get() > 6 and self.syncing):
                            self.syncing = False
                            print("Sync taking too long!")
                            sync_gapless_transition(None, self.channel, 0, new_handle)
                            break

                    add_time = max(min(player_timer.hit(), 3), 0)
                    if self.loaded_track:
                        star_store.add(self.loaded_track.index, add_time)

                    # BASS_ChannelStop(self.channel)
                    BASS_StreamFree(self.decode_channel)

                    # self.channel = mixer
                    self.decode_channel = new_handle

                else:

                    if not instant:
                        # Fade out old track
                        BASS_ChannelSlideAttribute(self.channel, 2, 0, prefs.cross_fade_time)

                    # Create Mixer
                    new_mixer = BASS_Mixer_StreamCreate(44100, 2, BASS_MIXER_END)


                    # print("Create Mixer")
                    # print(BASS_ErrorGetCode())

                    # Set the starting position
                    if pctl.start_time_target > 0 or pctl.jump_time > 0:
                        bytes_position = BASS_ChannelSeconds2Bytes(new_handle, pctl.start_time_target + pctl.jump_time)
                        BASS_ChannelSetPosition(new_handle, bytes_position, 0)
                        pctl.playing_time = pctl.jump_time
                        gui.update = 1
                        pctl.jump_time = 0

                    BASS_Mixer_StreamAddChannel(new_mixer, new_handle, BASS_STREAM_AUTOFREE)

                    # print("Add channel")
                    # print(BASS_ErrorGetCode())

                    # Set volume
                    BASS_ChannelSetAttribute(new_mixer, 2, 0)

                    # Set replay gain
                    replay_gain(new_mixer)

                    # Start playing
                    BASS_ChannelPlay(new_mixer, False)
                    # print("Play from rest")

                    # Add end callback
                    BASS_ChannelSetSync(new_mixer, BASS_SYNC_END | BASS_SYNC_MIXTIME, 0, GapSync2, 0)

                    if instant:
                        gui.console.print("Do transition QUICK")
                        BASS_ChannelSetAttribute(new_mixer, 2, pctl.player_volume / 100)
                    else:
                        gui.console.print("Do transition FADE")

                    if not instant:
                        # Fade in new track
                        BASS_ChannelSlideAttribute(new_mixer, 2, pctl.player_volume / 100, prefs.cross_fade_time)

                    if not instant:
                        time.sleep(prefs.cross_fade_time / 1000)

                    BASS_ChannelStop(self.channel)
                    BASS_StreamFree(self.channel)
                    self.channel = new_mixer
                    self.decode_channel = new_handle

            self.loaded_track = target_object

    bass_player = BASSPlayer()

    def sync_gapless_transition(handle, channel, data, user):

        bass_player.syncing = False
        #BASS_ChannelRemoveSync(channel, handle)
        # print("Sync GO!")
        gui.console.print("Do transition GAPLESS")
        # BASS_ErrorGetCode()
        # BASS_ChannelPlay(user, True)
        BASS_Mixer_StreamAddChannel(channel, user, BASS_STREAM_AUTOFREE | BASS_MIXER_NORAMPIN)
        # print("Add channel")
        # print(BASS_ErrorGetCode())

        if pctl.start_time_target > 0 or pctl.jump_time > 0:
            bytes_position = BASS_ChannelSeconds2Bytes(user, pctl.start_time_target + pctl.jump_time)
            BASS_ChannelSetPosition(user, bytes_position, 0)

        pctl.playing_time = pctl.jump_time
        pctl.jump_time = 0
        BASS_ChannelSetPosition(channel, 0, 0)
        # print("Set position")
        # print(BASS_ErrorGetCode())

    GapSync = SyncProc(sync_gapless_transition)

    def sync_gapless_transition2(handle, channel, data, user):

        bass_player.end_hit_timer.set()
        if bass_player.syncing and bass_player.new_handle_for_sync:

            BASS_Mixer_StreamAddChannel(channel, bass_player.new_handle_for_sync, BASS_STREAM_AUTOFREE | BASS_MIXER_NORAMPIN)
            if pctl.start_time_target > 0 or pctl.jump_time > 0:
                bytes_position = BASS_ChannelSeconds2Bytes(bass_player.new_handle_for_sync, pctl.start_time_target + pctl.jump_time)
                BASS_ChannelSetPosition(bass_player.new_handle_for_sync, bytes_position, 0)

            pctl.playing_time = pctl.jump_time
            pctl.jump_time = 0
            BASS_ChannelSetPosition(channel, 0, 0)

            bass_player.syncing = False
            bass_player.new_handle_for_sync = None

            gui.console.print("Do transition GAPLESS")


        #bass_player.syncing = False
        #BASS_ChannelRemoveSync(channel, handle)
        # print("Sync GO!")

        # BASS_ErrorGetCode()
        # BASS_ChannelPlay(user, True)

        # print("Add channel")
        # print(BASS_ErrorGetCode())

        # print("Set position")
        # print(BASS_ErrorGetCode())

    GapSync2 = SyncProc(sync_gapless_transition2)


    def stall_sync(handle, channel, data, user):

        print("STALL SYNC")
        #print(BASS_StreamGetFilePosition(user, BASS_FILEPOS_ASYNCBUF))

    Stall_Sync = SyncProc(stall_sync)


    while True:

        if gui.turbo is False:
            time.sleep(0.04)
        else:
            gui.turbo_next += 1


            if gui.vis == 4:
                time.sleep(0.015)
            elif gui.vis == 2 or gui.vis == 3:
                time.sleep(0.018)
            else:
                time.sleep(0.02)

            if gui.turbo_next < 6:

                if bass_player.state != 'playing':
                    gui.level = 0
                    if pctl.playerCommandReady is not True:
                        continue

                elif gui.lowered:
                    if pctl.playerCommandReady is not True:
                        continue

                # -----------
                elif gui.vis == 2:

                    BASS_ChannelGetData(bass_player.channel, x, 0x80000002)

                    # BASS_DATA_FFT256 = 0x80000000# -2147483648# 256 sample FFT
                    # BASS_DATA_FFT512 = 0x80000001# -2147483647# 512 FFT
                    # BASS_DATA_FFT1024 = 0x80000002# -2147483646# 1024 FFT
                    # BASS_DATA_FFT2048 = 0x80000003# -2147483645# 2048 FFT
                    # BASS_DATA_FFT4096 = 0x80000004# -2147483644# 4096 FFT
                    # BASS_DATA_FFT8192 = 0x80000005# -2147483643# 8192 FFT
                    # BASS_DATA_FFT16384 = 0x80000006# 16384 FFT

                    p_spec = []
                    BANDS = 24
                    b0 = 0
                    i = 0

                    while i < BANDS:
                        peak = 0
                        b1 = pow(2, i * 10.0 / (BANDS - 1))
                        if b1 > 511:
                            b1 = 511
                        if b1 <= b0:
                            b1 = b0 + 1
                        while b0 < b1 and b0 < 511:
                            if peak < x[1 + b0]:
                                peak = x[1 + b0]
                            b0 += 1

                        outp = math.sqrt(peak)
                        # print(int(outp*20))
                        p_spec.append(int(outp * 45))
                        i += 1
                    gui.spec = p_spec

                    # print(gui.spec)
                    if pctl.playing_time > 0.5 and pctl.playing_state == 1:
                        gui.update_spec = 1
                    # if pctl.playerCommand in ['open', 'stop']:
                    #     gui.update_spec = 0
                    gui.level_update = True

                    if pctl.playerCommandReady is not True:
                        continue

                elif gui.vis == 4:

                    BASS_ChannelGetData(bass_player.channel, xx, 0x80000003)

                    p_spec = []
                    BANDS = 45
                    b0 = 0
                    i = 0

                    while i < BANDS:
                        peak = 0
                        b1 = pow(2, i * 10.0 / (BANDS - 1))
                        if b1 > 511:
                            b1 = 511
                        if b1 <= b0:
                            b1 = b0 + 1
                        while b0 < b1 and b0 < 511:
                            if peak < xx[1 + b0]:
                                peak = xx[1 + b0]
                            b0 += 1

                        outp = math.sqrt(peak)
                        p_spec.append(int(outp * 45))
                        i += 1
                    gui.spec4_array = p_spec

                    # print(gui.spec)
                    if pctl.playing_time > 0.5 and pctl.playing_state == 1:
                        gui.update_spec = 1

                    gui.level_update = True

                    if pctl.playerCommandReady is not True:
                        continue

                # ------------------------------------
                elif gui.vis == 3:

                    if pctl.playing_time > 0.0 and (pctl.playing_state == 1 or pctl.playing_state == 3):

                        BASS_ChannelGetData(bass_player.channel, x, 0x80000002)

                        BANDS = gui.spec2_y + 5
                        b0 = 0
                        i = 0

                        while i < BANDS:
                            peak = 0
                            b1 = pow(2, i * 10.0 / (BANDS - 1))
                            if b1 > 511:
                                b1 = 511
                            if b1 <= b0:
                                b1 = b0 + 1
                            while b0 < b1 and b0 < 511:
                                if peak < x[1 + b0]:
                                    peak = x[1 + b0]
                                b0 += 1

                            outp = math.sqrt(peak)

                            if i < len(gui.spec2):
                                gui.spec2[i] += int(outp * 300)
                            else:
                                break
                            i += 1

                        gui.spec2_phase += 1
                        if gui.spec2_phase == 2:
                            gui.spec2_phase = 0
                            gui.spec2_buffers.append(copy.deepcopy(gui.spec2))
                            if len(gui.spec2_buffers) > 2:
                                del gui.spec2_buffers[0]
                                # print("Buffer Discard")

                            gui.spec2 = [0] * gui.spec2_y

                    if pctl.playerCommandReady is not True:
                        continue

                # -----------------------------------
                elif gui.vis == 1:

                    if bass_player.state == "playing":
                        gui.level = BASS_ChannelGetLevel(bass_player.channel)

                    ppp2 = gui.level & 0x0000FFFF
                    ppp1 = (gui.level & 0xFFFF0000) >> 16

                    # print((ppp1, ppp2, " t: " + str(test_timer.hit())))

                    ppp1 = (ppp1 / 32768) * 11.1
                    ppp2 = (ppp2 / 32768) * 11.1

                    gui.time_passed += gui.level_time.hit()
                    if gui.time_passed > 1:
                        gui.time_passed = 0
                    while gui.time_passed > 0.019:
                        gui.level_peak[1] -= 0.35
                        if gui.level_peak[1] < 0:
                            gui.level_peak[1] = 0
                        gui.level_peak[0] -= 0.35
                        if gui.level_peak[0] < 0:
                            gui.level_peak[0] = 0

                        gui.time_passed -= 0.020

                    if ppp1 > gui.level_peak[0]:
                        gui.level_peak[0] = ppp1
                    if ppp2 > gui.level_peak[1]:
                        gui.level_peak[1] = ppp2

                    gui.level_update = True

                if pctl.playerCommandReady is not True:
                    continue

            else:
                gui.turbo_next = 0
                if pctl.playerCommand == 'open':
                    # gui.update += 1
                    gui.level_peak = [0, 0]

        if pctl.playing_state == 3 and bass_player.state == 'playing':
            if radio_meta_timer.get() > 3:
                radio_meta_timer.set()
                # print(BASS_ChannelGetTags(handle1,4 ))

                meta = BASS_ChannelGetTags(bass_player.channel, 5)

                if meta is not None:
                    meta = meta.decode('utf-8')

                    for tag in meta.split(";"):
                        if '=' in tag:
                            a, b = tag.split('=')
                            if a == 'StreamTitle':
                                pctl.tag_meta = b.rstrip("'").lstrip("'")
                                break

                else:
                    meta = BASS_ChannelGetTags(bass_player.channel, 2)
                    if meta is not None:

                        if type(meta) is not str:
                            meta = meta.decode()
                        if '=' in meta:
                            a, b = meta.split('=')
                            if a == "title":
                                pctl.tag_meta = b.strip()
                            else:
                                pctl.tag_meta = ""
                        else:
                            pctl.tag_meta = ""
                    else:
                        pctl.tag_meta = ""

                # print(pctl.tag_meta)

                if BASS_ChannelIsActive(bass_player.channel) == 0:
                    pctl.playing_state = 0
                    gui.show_message("Stream stopped.", "The stream either ended or the connection was lost.", mode="info")
                    bass_player.stop()
                    pctl.playing_time = 0
                    if pctl.record_stream:
                        pctl.record_stream = False
                        BASS_Encode_Stop(rec_handle)

                if pctl.record_stream and pctl.record_title != pctl.tag_meta:

                    print("Recording track split")
                    BASS_ErrorGetCode()
                    BASS_Encode_Stop(rec_handle)
                    title = '{:%Y-%m-%d %H-%M-%S} - '.format(datetime.datetime.now()) + pctl.tag_meta
                    line = "--quality 3"
                    file = prefs.encoder_output + title + ".ogg"
                    flag = 0
                    if len(pctl.tag_meta) > 6 and ' - ' in pctl.tag_meta:
                        fi = pctl.tag_meta.split(' - ')
                        if len(fi) == 2:
                            line += ' -t "' + fi[0].strip('"') + '"'
                            line += ' -a "' + fi[1].strip('"') + '"'
                    if pctl.system != 'windows' and not tauon.msys:
                        file = file.encode('utf-8')
                        line = line.encode('utf-8')
                        flag = 0
                    else:
                        flag = 0x80000000

                    rec_handle = BASS_Encode_OGG_StartFile(bass_player.channel, line, flag, file)
                    pctl.record_title = pctl.tag_meta

                    print(file)
                    if BASS_ErrorGetCode() != 0:
                        gui.show_message("Recording error.", "An unknown error occurred when splitting the track.",
                                         mode="warning")

        if pctl.broadcast_active and pctl.encoder_pause == 0:
            pctl.broadcast_time += broadcast_timer.hit()
            if broadcast_update_timer.get() > 1:
                broadcast_update_timer.set()
                gui.update += 1

        if bass_player.state == "playing":

            add_time = player_timer.hit()
            if add_time > 2 or add_time < 0:
                add_time = 0

            status = BASS_ChannelIsActive(bass_player.channel)

            if status == 1:
                # Playing
                # print("Channel is playing " + str(pctl.playing_time))
                pass
            elif status == 3 or status == 0:
                # Paused? Stopped? Try unpause
                print("Channel not playing when should be, tring to restart")
                BASS_ChannelPlay(bass_player.channel, False)

            elif status == 2:

                print("Channel has stalled")

                if pctl.target_object and pctl.target_object.is_network and pctl.playing_time < 5:
                    pctl.new_time = 0
                    bass_player.seek()
                    time.sleep(0.1)

                pctl.playing_time += add_time
                pctl.decode_time += add_time

                # if pctl.playing_time > 5 and pctl.playing_state != 3:
                #     pctl.playing_time = 0
                #     print("Advancing")
                #     bass_player.stop(now=True)
                #     pctl.playing_time = 0
                #     pctl.advance(nolock=True)
                #     continue

            if status == 1 and not pctl.playerCommandReady or (pctl.playerCommandReady and pctl.playerCommand == 'volume'):
                if pctl.playing_state == 3:
                    pctl.playing_time += add_time
                    pctl.decode_time += add_time
                else:
                    bass_player.update_time()

            if pctl.playing_state == 1:

                if pctl.playing_time < 3 and pctl.a_time < 3:
                    # This makes sure it syncs up correctly when starting track
                    pctl.a_time = pctl.playing_time
                else:
                    pctl.a_time += add_time
                pctl.total_playtime += add_time

                lfm_scrobbler.update(add_time)

            if pctl.playing_state == 1 and len(pctl.track_queue) > 0 and 2 > add_time > 0:
                star_store.add(pctl.track_queue[pctl.queue_step], add_time)

            if not pctl.playerCommandReady or (pctl.playerCommandReady and pctl.playerCommand == 'volume'):
                # Trigger track advance once end of track is reached
                pctl.test_progress()
                if pctl.playing_state == 3:
                    pctl.radio_progress()

        if pctl.playerCommandReady:
            pctl.playerCommandReady = False
            command = pctl.playerCommand
            pctl.playerCommand = ''

            if pctl.playerSubCommand == 'now':
                transition_instant = True

            else:
                transition_instant = False

            pctl.playerSubCommand = ""

            if command == 'time':

                pctl.target_open = pctl.time_to_get
                if pctl.system != 'windows' and not tauon.msys:
                    pctl.target_open = pctl.target_open.encode('utf-8')
                    flag = 0
                else:
                    flag = 0x80000000

                print(pctl.target_open)
                handle9 = BASS_StreamCreateFile(False, pctl.target_open, 0, 0, flag)
                blen = BASS_ChannelGetLength(handle9, 0)
                tlen = BASS_ChannelBytes2Seconds(handle9, blen)
                pctl.time_to_get = tlen
                BASS_StreamFree(handle9)
                pctl.playerCommand = 'done'

            elif command == 'reload':

                bass_player.pause(force_suspend=True)
                bass_player.try_unload()
                BASS_SetConfig(BASS_CONFIG_DEV_BUFFER, prefs.device_buffer)
                if bass_player.state == 'suspend':
                    bass_player.pause()

            elif command == 'seteq':
                if fxs[0] is not None:

                    bass_player.vol_param.fVolume = pow(10, (min(prefs.eq)) / 20)
                    BASS_FXSetParameters(bass_player.vol_fx, ctypes.pointer(bass_player.vol_param))

                    for i, item in enumerate(params):
                        item.fGain = float(prefs.eq[i] * -1)
                        BASS_FXSetParameters(fxs[i], ctypes.pointer(params[i]))

            elif command == "setdev":

                bass_player.pause(force_suspend=True)
                print("Changing output device")

                print(BASS_Init(pctl.set_device, 48000, init_flag, gui.window_id, 0))
                result = BASS_SetDevice(pctl.set_device)
                print(result)
                if result is False:
                    gui.show_message("Device init failed. Try again maybe?", "", mode='error')
                else:
                    gui.show_message("Device set", prefs.last_device, mode='done')

                bass_player.try_unload()

                if bass_player.state == 'suspend':

                    bass_player.pause()


            if command == "url":
                bass_player.stop()
                bass_player.try_init()

                # fileline = str(datetime.datetime.now()) + ".ogg"
                # print(BASS_ErrorGetCode())
                # print(pctl.url)

                bass_player.channel = BASS_StreamCreateURL(pctl.url.encode('utf-8'), 0, 0, None, 0)
                bass_player.decode_channel = bass_player.channel

                if not bass_player.channel:
                    bass_error = BASS_ErrorGetCode()
                    if bass_error == 40:
                        gui.show_message("Stream error", "Connection timeout", mode="warning")
                    elif bass_error == 32:
                        gui.show_message("Stream error", "No internet connection", mode="warning")
                    elif bass_error == 20:
                        gui.show_message("Stream error", "Bad URL", mode="warning")
                    elif bass_error == 2:
                        gui.show_message("Stream error", "Could not open stream", mode="warning")
                    elif bass_error == 41:
                        gui.show_message("Stream error", "Unknown file format", mode="warning")
                    elif bass_error == 44:
                        gui.show_message("Stream error", "Unknown/unsupported codec", mode="warning")
                    elif bass_error == 10:
                        gui.show_message("Stream error - SSL/HTTPS support not available.", "Try upgrade BASS by going to Audio in Settings and clicking Uninstall then Install.", mode="warning")
                    elif bass_error == -1:
                        gui.show_message("Stream error", "Its a mystery!!", mode="warning")
                    elif bass_error != 0:
                        gui.show_message("Stream error", "Something went wrong... somewhere", mode="warning")
                        print(f"BASS error: {bass_error}")

                    pctl.playing_status = 0
                    bass_player.stop()

                else:
                    BASS_ChannelSetAttribute(bass_player.channel, 2, pctl.player_volume / 100)
                    BASS_ChannelPlay(bass_player.channel, True)

                    bass_player.state = 'playing'

                    pctl.playing_time = 0
                    pctl.last_playing_time = 0
                    player_timer.hit()


            if command == 'record':
                if pctl.playing_state != 3:
                    print("ERROR! Stream not active")
                else:
                    title = '{:%Y-%m-%d %H-%M-%S} - '.format(datetime.datetime.now()) + pctl.tag_meta
                    line = "--quality 3"
                    file = prefs.encoder_output + title + ".ogg"
                    # if system == 'windows':
                    #     file = file.replace("/", '\\')
                    flag = 0
                    if len(pctl.tag_meta) > 6 and ' - ' in pctl.tag_meta:
                        fi = pctl.tag_meta.split(' - ')
                        if len(fi) == 2:
                            line += ' -t "' + fi[0].strip('"') + '"'
                            line += ' -a "' + fi[1].strip('"') + '"'

                    if pctl.system != 'windows' and not tauon.msys:
                        file = file.encode('utf-8')
                        line = line.encode('utf-8')
                        flag = 0
                    else:
                        flag = 0x80000000

                        #print(line)

                    print(file)
                    # print(BASS_ErrorGetCode())

                    rec_handle = BASS_Encode_OGG_StartFile(bass_player.channel, line, flag, file)

                    pctl.record_stream = True
                    pctl.record_title = pctl.tag_meta

                    if rec_handle != 0 and BASS_ErrorGetCode() == 0:
                        gui.show_message("Recording started.",
                                         "Outputting as ogg to encoder directory, press F9 to show.", mode="done")
                    else:
                        gui.show_message("Recording Error.", "An unknown was encountered", mode="warning")
                        pctl.record_stream = False

            if command == 'cast-next':
                #print("Next Enc Rec")

                if pctl.system != 'windows' and not tauon.msys:
                    pctl.target_open = pctl.target_open.encode('utf-8')
                    flag = 0
                else:
                    flag = 0x80000000

                flag |= 0x200000

                BASS_Mixer_ChannelRemove(handle3)
                BASS_StreamFree(handle3)

                handle3 = BASS_StreamCreateFile(False, pctl.target_open, 0, 0, flag)

                if pctl.b_start_time > 0:
                    bytes_position = BASS_ChannelSeconds2Bytes(handle3, pctl.b_start_time)
                    BASS_ChannelSetPosition(handle3, bytes_position, 0)

                BASS_Mixer_StreamAddChannel(mhandle, handle3, 0)
                channel1 = BASS_ChannelPlay(mhandle, True)

                broadcast_timer.hit()

                encerror = BASS_ErrorGetCode()
                #print(encerror)
                #print(pctl.broadcast_line)
                line = pctl.broadcast_line.encode('utf-8')
                BASS_Encode_CastSetTitle(encoder, line, 0)
                #print(BASS_ErrorGetCode())
                if encerror != 0:
                    pctl.broadcast_active = False
                    BASS_Encode_Stop(encoder)
                    BASS_ChannelStop(handle3)
                    BASS_StreamFree(handle3)
                    # BASS_StreamFree(oldhandle)

            if command == 'encseek' and pctl.broadcast_active:

                print("seek")
                bytes_position = BASS_ChannelSeconds2Bytes(handle3, pctl.b_start_time + pctl.broadcast_time)
                BASS_ChannelSetPosition(handle3, bytes_position, 0)

                #BASS_ChannelPlay(handle1, False)

            if command == 'encpause' and pctl.broadcast_active:

                # Pause broadcast
                if pctl.encoder_pause == 0:
                    BASS_ChannelPause(mhandle)
                    pctl.encoder_pause = 1
                else:
                    BASS_ChannelPlay(mhandle, True)
                    pctl.encoder_pause = 0

            if command == "encstop":
                BASS_Encode_Stop(encoder)
                BASS_ChannelStop(handle3)
                BASS_StreamFree(handle3)
                pctl.broadcast_clients.clear()
                pctl.broadcast_active = False

            if command == "encstart":

                bass_player.try_init()

                bitrate = str(prefs.broadcast_bitrate)
                port = str(prefs.broadcast_port)

                pctl.broadcast_active = True
                print("starting encoder")

                if pctl.system != 'windows' and not tauon.msys:
                    pctl.target_open = pctl.target_open.encode('utf-8')
                    flag = 0
                else:
                    flag = 0x80000000

                pctl.broadcast_time = 0

                broadcast_timer.hit()
                flag |= 0x200000
                # print(flag)

                #print(pctl.target_open)

                handle3 = BASS_StreamCreateFile(False, pctl.target_open, 0, 0, flag)
                mhandle = BASS_Mixer_StreamCreate(44100, 2, 0)
                BASS_Mixer_StreamAddChannel(mhandle, handle3, 0)
                channel1 = BASS_ChannelPlay(mhandle, True)
                BASS_ChannelSetAttribute(mhandle, 2, 0)

                #print(BASS_ErrorGetCode())

                line = "--bitrate " + bitrate
                line = line.encode('utf-8')

                #print(BASS_ErrorGetCode())

                encoder = BASS_Encode_OGG_Start(mhandle, line, 0, None, None)
                result = BASS_Encode_ServerInit(encoder, port.encode(), 64000, 64000, 2, client_connect, None)

                if BASS_ErrorGetCode() == -1:
                    gui.show_message("Server initialisation error.", "Sorry, something isn't working right.", mode="warning")
                channel1 = BASS_ChannelPlay(mhandle, True)

                line = pctl.broadcast_line.encode('utf-8')
                BASS_Encode_CastSetTitle(encoder, line, 0)
                
                # Trying to send the stream title here causes the stream to fail for some reason
                # line2 = pctl.broadcast_line.encode('utf-8')
                # BASS_Encode_CastSetTitle(encoder, line2,0)
                # print("after set title")
                e = BASS_ErrorGetCode()
                if result != 0:
                    gui.show_message("Server initiated successfully.", "Listening on port " + port + ".", mode="done")
                else:
                    gui.show_message("Error staring broadcast.", 'Error code ' + str(e) + ".", mode='warning')

                    pctl.playerCommand = "encstop"
                    pctl.playerCommandReady = True

                #print(BASS_ErrorGetCode())

            # OPEN COMMAND

            if command == 'open':

                bass_player.start(transition_instant)

                pctl.last_playing_time = 0
                pctl.jump_time = 0
                player_timer.hit()

            elif command == 'pause':
                bass_player.pause()
                player_timer.hit()

            elif command == 'pauseon':
                if bass_player.state != "paused":
                    bass_player.pause()
                    player_timer.hit()

            elif command == 'pauseoff':
                if bass_player.state == "paused" or bass_player.state == "suspend":
                    bass_player.pause()
                    player_timer.hit()

            elif command == 'volume':

                bass_player.set_volume(pctl.player_volume / 100)

            elif command == 'runstop':

                bass_player.stop(True)

            elif command == 'stop':
                bass_player.stop()
                pctl.playerCommand = 'stopped'

            elif command == 'seek':

                bass_player.seek()

            # UNLOAD PLAYER COMMAND
            if command == 'unload':
                BASS_Free()
                print('BASS Unloaded')
                break

    pctl.playerCommand = 'done'
