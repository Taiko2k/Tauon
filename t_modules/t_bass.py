from t_modules.t_extra import Timer
import ctypes
import time
import math
import datetime
import os
import copy


def player(pctl, gui, prefs, lfm_scrobbler, star_store):  # BASS

    player_timer = Timer()
    broadcast_timer = Timer()
    broadcast_update_timer = Timer()
    broadcast_update_timer.set()
    radio_meta_timer = Timer()

    if pctl.system == 'windows':
        bass_module = ctypes.WinDLL('bass')
        enc_module = ctypes.WinDLL('bassenc')
        mix_module = ctypes.WinDLL('bassmix')
        fx_module = ctypes.WinDLL('bass_fx')
        # opus_module = ctypes.WinDLL('bassenc_opus')
        ogg_module = ctypes.WinDLL('bassenc_ogg')

        function_type = ctypes.WINFUNCTYPE
    elif pctl.system == 'mac':
        bass_module = ctypes.CDLL(pctl.install_directory + '/lib/libbass.dylib', mode=ctypes.RTLD_GLOBAL)
        enc_module = ctypes.CDLL(pctl.install_directory + '/lib/libbassenc.dylib', mode=ctypes.RTLD_GLOBAL)
        mix_module = ctypes.CDLL(pctl.install_directory + '/lib/libbassmix.dylib', mode=ctypes.RTLD_GLOBAL)
        ogg_module = ctypes.CDLL(pctl.install_directory + '/lib/libbassenc_ogg.dylib', mode=ctypes.RTLD_GLOBAL)
        function_type = ctypes.CFUNCTYPE
    else:
        bass_module = ctypes.CDLL(pctl.install_directory + '/lib/libbass.so', mode=ctypes.RTLD_GLOBAL)
        enc_module = ctypes.CDLL(pctl.install_directory + '/lib/libbassenc.so', mode=ctypes.RTLD_GLOBAL)
        mix_module = ctypes.CDLL(pctl.install_directory + '/lib/libbassmix.so', mode=ctypes.RTLD_GLOBAL)
        fx_module = ctypes.CDLL(pctl.install_directory + '/lib/libbass_fx.so', mode=ctypes.RTLD_GLOBAL)
        ogg_module = ctypes.CDLL(pctl.install_directory + '/lib/libbassenc_ogg.so', mode=ctypes.RTLD_GLOBAL)

        function_type = ctypes.CFUNCTYPE

    BASS_Init = function_type(ctypes.c_bool, ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p,
                              ctypes.c_void_p)(('BASS_Init', bass_module))

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
    BASS_GetConfig = function_type(ctypes.c_ulong, ctypes.c_ulong)(('BASS_GetConfig', bass_module))
    BASS_ChannelSlideAttribute = function_type(ctypes.c_bool, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_float,
                                               ctypes.c_ulong)(('BASS_ChannelSlideAttribute', bass_module))
    BASS_ChannelSetAttribute = function_type(ctypes.c_bool, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_float)(
        ('BASS_ChannelSetAttribute', bass_module))
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

    # class BASS_DX8_PARAMEQ(ctypes.Structure):
    #     _fields_ = [('fCenter', ctypes.c_int),
    #                 ('fBandwidth', ctypes.c_float),
    #                 ('fGain', ctypes.c_float),
    #                 ]
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

    DownloadProc = function_type(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong, ctypes.c_void_p)

    # BASS_StreamCreateURL = function_type(ctypes.c_ulong, ctypes.c_char_p, ctypes.c_ulong,
    #        ctypes.c_ulong, DownloadProc, ctypes.c_void_p)(('BASS_StreamCreateURL', bass_module))
    BASS_StreamCreateURL = function_type(ctypes.c_ulong, ctypes.c_char_p, ctypes.c_ulong, ctypes.c_ulong,
                                         DownloadProc, ctypes.c_void_p)(('BASS_StreamCreateURL', bass_module))
    BASS_ChannelGetTags = function_type(ctypes.c_char_p, ctypes.c_ulong, ctypes.c_ulong)(
        ('BASS_ChannelGetTags', bass_module))


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


    BASS_DEVICE_ENABLED = 1
    BASS_DEVICE_DEFAULT = 2
    BASS_DEVICE_INIT = 4

    BASS_DEVICE_ENABLED = 1
    BASS_DEVICE_DEFAULT = 2
    BASS_DEVICE_INIT = 4

    BASS_MIXER_END = 0x10000
    BASS_SYNC_END = 2
    BASS_SYNC_MIXTIME = 0x40000000
    BASS_UNICODE = 0x80000000
    BASS_STREAM_DECODE = 0x200000
    BASS_ASYNCFILE = 0x40000000
    BASS_SAMPLE_FLOAT = 256
    BASS_STREAM_AUTOFREE = 0x40000
    BASS_MIXER_NORAMPIN = 0x800000
    BASS_MIXER_PAUSE = 0x20000

    BASS_DEVICE_DMIX = 0x2000

    BASS_CONFIG_ASYNCFILE_BUFFER = 45

    #if system != 'windows':
    open_flag = 0
    #BASS_SetConfig(BASS_CONFIG_ASYNCFILE_BUFFER, 128000)
    #else:
    #    open_flag = BASS_UNICODE

    open_flag |= BASS_ASYNCFILE
    # open_flag |= BASS_STREAM_DECODE
    open_flag |= BASS_SAMPLE_FLOAT
    open_flag |= BASS_STREAM_AUTOFREE

    # gap1
    class BassGapless:
        def __init__(self):
            self.mixer = None
            self.source = None
            self.gap_next = None

    bass_gap = BassGapless()

    if pctl.system == 'windows':
        # print(BASS_ErrorGetCode())
        BASS_PluginLoad(b'bassopus.dll', 0)
        BASS_PluginLoad(b'bassflac.dll', 0)
        BASS_PluginLoad(b'bass_ape.dll', 0)
        BASS_PluginLoad(b'bass_tta.dll', 0)
        BASS_PluginLoad(b'basswma.dll', 0)
        BASS_PluginLoad(b'basswv.dll', 0)
        BASS_PluginLoad(b'bassalac.dll', 0)

        # bassenc_opus
    elif pctl.system == 'mac':
        b = pctl.install_directory.encode('utf-8')
        BASS_PluginLoad(b + b'/lib/libbassopus.dylib', 0)
        BASS_PluginLoad(b + b'/lib/libbassflac.dylib', 0)
        BASS_PluginLoad(b + b'/lib/libbass_ape.dylib', 0)
        BASS_PluginLoad(b + b'/lib/libbass_aac.dylib', 0)
        BASS_PluginLoad(b + b'/lib/libbasswv.dylib', 0)
    else:
        b = pctl.install_directory.encode('utf-8')
        BASS_PluginLoad(b + b'/lib/libbassopus.so', 0)
        BASS_PluginLoad(b + b'/lib/libbassflac.so', 0)
        BASS_PluginLoad(b + b'/lib/libbass_ape.so', 0)
        BASS_PluginLoad(b + b'/lib/libbass_aac.so', 0)
        BASS_PluginLoad(b + b'/lib/libbass_tta.so', 0)
        BASS_PluginLoad(b + b'/lib/libbasswv.so', 0)
        BASS_PluginLoad(b + b'/lib/libbassalac.so', 0)

    bass_ready = False

    BASS_CONFIG_DEV_DEFAULT = 36
    BASS_SetConfig(BASS_CONFIG_DEV_DEFAULT, True)

    a = 1
    # if system == "linux":
    #     a = 1
    d_info = BASS_DEVICEINFO()
    while True:
        if not BASS_GetDeviceInfo(a, d_info):
            break
        name = d_info.name.decode('utf-8', 'ignore')
        flags = d_info.flags
        enabled = BASS_DEVICE_ENABLED & flags
        default = BASS_DEVICE_DEFAULT & flags
        current = BASS_DEVICE_INIT & flags

        if name != "" and name == prefs.last_device:
            BassInitSuccess = BASS_Init(a, 48000, BASS_DEVICE_DMIX, gui.window_id, 0)
            pctl.set_device = a
            print("Set output device as: " + name)
            bass_ready = True

        # print((name, enabled, default, current))
        if current > 0:
            pctl.set_device = a
        pctl.bass_devices.append((name, enabled, default, current, a))
        # print(d_info.name.decode('utf-8'))
        a += 1

    bass_init_success = False
    if not bass_ready:
        bass_init_success = BASS_Init(-1, 48000, BASS_DEVICE_DMIX, gui.window_id, 0)
        print("Using default sound device")
    if bass_init_success == True:
        print("Bass library initialised")

    if prefs.log_vol:
        BASS_SetConfig(7, True)

    x = (ctypes.c_float * 512)()
    ctypes.cast(x, ctypes.POINTER(ctypes.c_float))

    def broadcast_connect(handle, connect, client, headers, user):

        if connect is True:
            pctl.broadcast_clients.append(client.decode())
        else:
            pctl.broadcast_clients.remove(client.decode())
        print((connect, client))

        return True

    client_connect = EncodeClientProc(broadcast_connect)

    BASS_FX_GetVersion()

    def replay_gain(stream):
        pctl.active_replaygain = 0
        if prefs.replay_gain > 0 and pctl.target_object.track_gain is not None or pctl.target_object.album_gain is not None:
            gain = None
            if prefs.replay_gain == 1 and pctl.target_object.track_gain is not None:
                gain = pctl.target_object.track_gain
                print("Track ReplayGain")
            elif prefs.replay_gain == 2 and pctl.target_object.album_gain is not None:
                gain = pctl.target_object.album_gain
                print("Album ReplayGain")

            if gain is None and prefs.replay_gain == 2:
                print("Track ReplayGain Fallback")
                gain = pctl.target_object.track_gain
            if gain is None:
                return

            BASS_FX_BFX_VOLUME = 65539

            volfx = BASS_ChannelSetFX(stream, BASS_FX_BFX_VOLUME, 0)
            volparam = BASS_BFX_VOLUME(0, pow(10, gain / 20))

            BASS_FXSetParameters(volfx, ctypes.pointer(volparam))

            print("Using ReplayGain of " + str(gain))
            pctl.active_replaygain = round(gain, 2)

    br_timer = Timer()

    class BASSPlayer:

        def __init__(self):

            self.channel = None # Mixer
            self.decode_channel = None
            self.state = 'stopped'
            self.syncing = False

        def seek(self):

            if self.state is not 'stopped':
                BASS_ChannelStop(self.channel)
                pos = BASS_ChannelSeconds2Bytes(self.decode_channel, pctl.new_time + pctl.start_time)
                BASS_Mixer_ChannelSetPosition(self.decode_channel, pos, 0)
                BASS_ChannelPlay(self.channel, True)

        def update_time(self):

            bpos = BASS_ChannelGetPosition(self.decode_channel, 0)
            tpos = BASS_ChannelBytes2Seconds(self.decode_channel, bpos)
            if tpos >= 0:
                pctl.playing_time = tpos - pctl.start_time

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

        def set_volume(self, volume):

            if self.channel is None: return
            BASS_ChannelSlideAttribute(self.channel, 2, volume, prefs.change_volume_fade_time)

        def pause(self):

            if self.channel is None:
                return

            if self.state == 'stopped':
                print("Player already stopped")
                return

            if self.state == 'playing':

                if prefs.use_pause_fade:
                    BASS_ChannelSlideAttribute(self.channel, 2, 0, prefs.pause_fade_time)
                    time.sleep(prefs.pause_fade_time / 1000)
                BASS_ChannelPause(self.channel)
                self.state = 'paused'

            elif self.state == 'paused':

                BASS_ChannelPlay(self.channel, False)
                if prefs.use_pause_fade:
                    BASS_ChannelSlideAttribute(self.channel, 2, pctl.player_volume / 100, prefs.pause_fade_time)
                self.state = 'playing'

        def start(self, instant=False):

            print("Open file...")

            # Get the target filepath and convert to bytes
            target = pctl.target_open.encode('utf-8')

            # Check if the file exists, mark it as missing if not
            if os.path.isfile(pctl.target_object.fullpath):
                pctl.target_object.found = True
            else:
                pctl.target_object.found = False
                gui.pl_update = 1
                print("Missing File: " + pctl.target_object.fullpath)
                pctl.playing_state = 0
                pctl.advance(inplace=True, nolock=True)
                return

            # print(BASS_ErrorGetCode())
            # Load new stream
            new_handle = BASS_StreamCreateFile(False, target, 0, 0, BASS_STREAM_DECODE|BASS_SAMPLE_FLOAT)

            # print("Creade decode chanel")
            # print(BASS_ErrorGetCode())

            # Verify length if very short
            if pctl.target_object.length < 1:
                blen = BASS_ChannelGetLength(new_handle, 0)
                tlen = BASS_ChannelBytes2Seconds(new_handle, blen)
                pctl.target_object.length = tlen
                pctl.playing_length = tlen

            # Set the volume to 0 and set replay gain
            # BASS_ChannelSetAttribute(new_handle, 2, 0)
            # replay_gain(new_handle)

            if self.state == 'paused':
                BASS_ChannelStop(self.channel)
                BASS_StreamFree(self.channel)
                self.state = 'stopped'

            if self.state == 'stopped':

                # Create Mixer
                mixer = BASS_Mixer_StreamCreate(44100, 2, BASS_MIXER_END)

                # print("Create Mixer")
                # print(BASS_ErrorGetCode())

                BASS_Mixer_StreamAddChannel(mixer, new_handle, BASS_STREAM_AUTOFREE)

                # print("Add channel")
                # print(BASS_ErrorGetCode())

                # Set volume
                BASS_ChannelSetAttribute(mixer, 2, pctl.player_volume / 100)

                # Set replay gain
                replay_gain(mixer)

                # Start playing
                BASS_ChannelPlay(mixer, False)
                # print("Play from rest")

                # Set the starting position
                if pctl.start_time > 0 or pctl.jump_time > 0:
                    bytes_position = BASS_ChannelSeconds2Bytes(new_handle, pctl.start_time + pctl.jump_time)
                    BASS_ChannelSetPosition(new_handle, bytes_position, 0)

                self.channel = mixer
                self.decode_channel = new_handle
                self.state = 'playing'
                return

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
                err = BASS_ErrorGetCode()

                print("Track transition...")
                print("We are " + str(tlen - tpos)[:5] + " seconds from end")

                # Try to transition without fade and and on time if possible and permitted
                if not prefs.use_transition_crossfade and not instant and err == 0 and 0.2 < tlen - tpos < 2.5:

                    # print(BASS_ErrorGetCode())
                    # Start sync on end
                    #print(self.channel)
                    sync = BASS_ChannelSetSync(self.channel, BASS_SYNC_END | BASS_SYNC_MIXTIME, 0, GapSync, new_handle)
                    # print("Set sync...")
                    # print(BASS_ErrorGetCode())
                    self.syncing = True
                    br_timer.set()

                    while self.syncing:
                        time.sleep(0.001)
                        if br_timer.get() > 6 and self.syncing:
                            self.syncing = False
                            print("Sync taking too long!")
                            sync_gapless_transition(sync, self.channel, 0, new_handle)
                            break

                    # BASS_ChannelStop(self.channel)
                    BASS_StreamFree(self.decode_channel)

                    # self.channel = mixer
                    self.decode_channel = new_handle
                    return

                else:

                    if not instant:
                        # Fade out old track
                        BASS_ChannelSlideAttribute(self.channel, 2, 0, prefs.cross_fade_time)

                    # Create Mixer
                    new_mixer = BASS_Mixer_StreamCreate(44100, 2, BASS_MIXER_END)

                    # print("Create Mixer")
                    # print(BASS_ErrorGetCode())

                    BASS_Mixer_StreamAddChannel(new_mixer, new_handle, BASS_STREAM_AUTOFREE)

                    # print("Add channel")
                    # print(BASS_ErrorGetCode())

                    # Set volume
                    BASS_ChannelSetAttribute(new_mixer, 2, 0)

                    # Start playing
                    BASS_ChannelPlay(new_mixer, False)
                    # print("Play from rest")

                    # Set replay gain
                    replay_gain(new_mixer)

                    # Set the starting position
                    if pctl.start_time > 0 or pctl.jump_time > 0:
                        bytes_position = BASS_ChannelSeconds2Bytes(new_handle, pctl.start_time + pctl.jump_time)
                        BASS_ChannelSetPosition(new_handle, bytes_position, 0)

                    if instant:
                        print("Do transition QUICK")
                        BASS_ChannelSetAttribute(new_mixer, 2, pctl.player_volume / 100)
                    else:
                        print("Do transition FADE")

                    if not instant:
                        # Fade in new track
                        BASS_ChannelSlideAttribute(new_mixer, 2, pctl.player_volume / 100, prefs.cross_fade_time)

                    if not instant:
                        time.sleep(prefs.cross_fade_time / 1000)

                    BASS_ChannelStop(self.channel)
                    BASS_StreamFree(self.channel)
                    self.channel = new_mixer
                    self.decode_channel = new_handle

    bass_player = BASSPlayer()

    def sync_gapless_transition(handle, channel, data, user):

        bass_player.syncing = False
        BASS_ChannelRemoveSync(channel, handle)
        # print("Sync GO!")
        print("Do transition GAPLESS")
        BASS_ErrorGetCode()
        # BASS_ChannelPlay(user, True)
        BASS_Mixer_StreamAddChannel(channel, user, BASS_STREAM_AUTOFREE | BASS_MIXER_NORAMPIN)
        # print("Add channel")
        # print(BASS_ErrorGetCode())

        if pctl.start_time > 0 or pctl.jump_time > 0:
            bytes_position = BASS_ChannelSeconds2Bytes(user, pctl.start_time + pctl.jump_time)
            BASS_ChannelSetPosition(user, bytes_position, 0)

        pctl.playing_time = 0
        BASS_ChannelSetPosition(channel, 0, 0)
        # print("Set position")
        # print(BASS_ErrorGetCode())

    GapSync = SyncProc(sync_gapless_transition)

    while True:

        if gui.turbo is False:
            time.sleep(0.04)
        else:
            gui.turbo_next += 1

            if gui.vis == 2 or gui.vis == 3:
                time.sleep(0.018)
            else:
                # time.sleep(0.02)
                time.sleep(0.02)

            if gui.turbo_next < 6 and pctl.playerCommandReady is not True:

                if bass_player.state != 'playing':
                    gui.level = 0
                    continue

                # -----------
                if gui.vis == 2:

                    # # TEMPORARY
                    # continue

                    if gui.lowered:
                        continue

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
                    continue

                # ------------------------------------
                elif gui.vis == 3:

                    if gui.lowered:
                        continue

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

                        continue

                    #gui.spec = p_spec

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
                        #gui.time_passed -= 0.020
                        gui.time_passed -= 0.020

                    if ppp1 > gui.level_peak[0]:
                        gui.level_peak[0] = ppp1
                    if ppp2 > gui.level_peak[1]:
                        gui.level_peak[1] = ppp2

                    # gui.level_peak[1] += random.randint(-100, 100) * 0.01
                    # gui.level_peak[0] += random.randint(-100, 100) * 0.01
                    #
                    # if int(gui.level_peak[0]) != int(last_level[0]) or int(gui.level_peak[1]) != int(last_level[1]):
                    #     #gui.level_update = True
                    #     pass

                    gui.level_update = True

                    # last_level = copy.deepcopy(gui.level_peak)
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
                else:
                    meta = BASS_ChannelGetTags(bass_player.channel, 2)
                    if meta is not None:
                        meta = pctl.tag_meta.decode('utf-8', 'ignore')
                    else:
                        meta = ""

                for tag in meta.split(";"):
                    if '=' in tag:
                        a, b = tag.split('=')
                        if a == 'StreamTitle':
                            pctl.tag_meta = b.rstrip("'").lstrip("'")
                            break
                else:
                    pctl.tag_meta = ""

                # print(pctl.tag_meta)

                if BASS_ChannelIsActive(bass_player.channel) == 0:
                    pctl.playing_state = 0
                    gui.show_message("Stream stopped.", "info", "The stream either ended or the connection was lost.")
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
                    if pctl.system != 'windows':
                        file = file.encode('utf-8')
                        line = line.encode('utf-8')
                        flag = 0
                    else:
                        flag = 0x80000000

                    rec_handle = BASS_Encode_OGG_StartFile(bass_player.channel, line, flag, file)
                    pctl.record_title = pctl.tag_meta

                    print(file)
                    if BASS_ErrorGetCode() != 0:
                        gui.show_message("Recording error.", "warning", "An unknown error occurred when splitting the track.")

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
                pass
            elif status == 3 or status == 0:
                # Paused? Stopped? Try unpause
                print("Channel not playing when should be, tring to restart")
                BASS_ChannelPlay(bass_player.channel, False)

            elif status == 2:
                print("Channel has stalled")
                pctl.playing_time += add_time

                if pctl.playing_time > 10 and pctl.playing_state != 3:
                    pctl.playing_time = 0
                    print("Advancing")
                    bass_player.stop(now=True)
                    pctl.playing_time = 0
                    pctl.advance(nolock=True)
                    continue

            # pctl.playing_time += add_time
            if status == 1 and not pctl.playerCommandReady or (pctl.playerCommandReady and pctl.playerCommand == 'volume'):
                bass_player.update_time()

            if pctl.playing_state == 1:

                pctl.a_time += add_time
                pctl.total_playtime += add_time

                lfm_scrobbler.update(add_time)

            # Trigger track advance once end of track is reached
            pctl.test_progress()

            if pctl.playing_state == 1 and len(pctl.track_queue) > 0 and 2 > add_time > 0:
                star_store.add(pctl.track_queue[pctl.queue_step], add_time)

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
                if pctl.system != 'windows':
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

            elif command == "setdev":

                BASS_Free()
                bass_player.state = 'stopped'
                pctl.playing_state = 0
                pctl.playing_time = 0
                print("Changing output device")
                print(BASS_Init(pctl.set_device, 48000, BASS_DEVICE_DMIX, gui.window_id, 0))
                result = BASS_SetDevice(pctl.set_device)
                print(result)
                if result is False:
                    gui.show_message("Device init failed. Try again maybe?", 'error')
                else:
                    gui.show_message("Set device", 'done', prefs.last_device)

            # if pctl.playerCommand == "monitor":
            #     pass

            if command == "url":
                bass_player.stop()

                # fileline = str(datetime.datetime.now()) + ".ogg"
                # print(BASS_ErrorGetCode())
                # print(pctl.url)
                bass_error = BASS_ErrorGetCode()
                bass_player.channel = BASS_StreamCreateURL(pctl.url, 0, 0, down_func, 0)
                bass_error = BASS_ErrorGetCode()
                if bass_error == 40:
                    gui.show_message("Stream error.", "warning", "Connection timeout")
                elif bass_error == 32:
                    gui.show_message("Stream error.", "warning", "No internet connection")
                elif bass_error == 20:
                    gui.show_message("Stream error.", "warning", "Bad URL")
                elif bass_error == 2:
                    gui.show_message("Stream error.", "warning", "Could not open stream")
                elif bass_error == 41:
                    gui.show_message("Stream error.", "warning", "Unknown file format")
                elif bass_error == 44:
                    gui.show_message("Stream error.", "warning", "Unknown/unsupported codec")
                elif bass_error == -1:
                    gui.show_message("Stream error.", "warning", "Its a mystery!!")
                elif bass_error != 0:
                    gui.show_message("Stream error.", "warning", "Something went wrong... somewhere")
                if bass_error == 0:
                    BASS_ChannelSetAttribute(bass_player.channel, 2, pctl.player_volume / 100)
                    BASS_ChannelPlay(bass_player.channel, True)

                    bass_player.state = 'playing'

                    pctl.playing_time = 0
                    pctl.last_playing_time = 0
                    player_timer.hit()
                else:
                    pctl.playing_status = 0

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

                    if pctl.system != 'windows':
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
                        gui.show_message("Recording started.", "done", "Outputting as ogg to encoder directory, press F9 to show.")
                    else:
                        gui.show_message("Recording Error.", "warning", "An unknown was encountered")
                        pctl.record_stream = False

            if command == 'cast-next':
                print("Next Enc Rec")

                if pctl.system != 'windows':
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
                print(encerror)
                print(pctl.broadcast_line)
                line = pctl.broadcast_line.encode('utf-8')
                BASS_Encode_CastSetTitle(encoder, line, 0)
                print(BASS_ErrorGetCode())
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
                pctl.broadcast_active = False

            if command == "encstart":

                port = "8000"
                bitrate = "128"

                path = pctl.config_directory + "/config.txt"
                with open(path, encoding="utf_8") as f:
                    content = f.read().splitlines()
                    for p in content:
                        if len(p) == 0:
                            continue
                        if p[0] == " " or p[0] == "#":
                            continue
                        if 'broadcast-port=' in p:
                            if len(p) < 40:
                                port = p.split('=')[1]
                        elif 'broadcast-bitrate=' in p:
                            bitrate = p.split('=')[1]

                pctl.broadcast_active = True
                print("starting encoder")

                if pctl.system != 'windows':
                    pctl.target_open = pctl.target_open.encode('utf-8')
                    flag = 0
                else:
                    flag = 0x80000000

                pctl.broadcast_time = 0

                broadcast_timer.hit()
                flag |= 0x200000
                # print(flag)

                print(pctl.target_open)

                handle3 = BASS_StreamCreateFile(False, pctl.target_open, 0, 0, flag)

                mhandle = BASS_Mixer_StreamCreate(44100, 2, 0)

                BASS_Mixer_StreamAddChannel(mhandle, handle3, 0)

                channel1 = BASS_ChannelPlay(mhandle, True)

                BASS_ChannelSetAttribute(mhandle, 2, 0)

                print(BASS_ErrorGetCode())

                line = "--bitrate " + bitrate
                line = line.encode('utf-8')

                print(BASS_ErrorGetCode())

                encoder = BASS_Encode_OGG_Start(mhandle, line, 0, None, None)

                result = BASS_Encode_ServerInit(encoder, port.encode(), 32000, 32000, 2, client_connect, None)

                if BASS_ErrorGetCode() == -1:
                    gui.show_message("Server initialisation error.", "warning", "Sorry, something isn't working right.")
                channel1 = BASS_ChannelPlay(mhandle, True)

                line = pctl.broadcast_line.encode('utf-8')
                BASS_Encode_CastSetTitle(encoder, line, 0)
                
                # Trying to send the stream title here causes the stream to fail for some reason
                # line2 = pctl.broadcast_line.encode('utf-8')
                # BASS_Encode_CastSetTitle(encoder, line2,0)
                print("after set title")
                e = BASS_ErrorGetCode()
                if result != 0:
                    gui.show_message("Server initiated successfully.", "done", "Listening on port " + port + ".")
                else:
                    gui.show_message("Error staring broadcast.", 'warning', 'Error code ' + str(e) + ".")

                    pctl.playerCommand = "encstop"
                    pctl.playerCommandReady = True

                print(BASS_ErrorGetCode())

            # OPEN COMMAND

            if command == 'open' and pctl.target_open != '':

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
                if bass_player.state == "paused":
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
