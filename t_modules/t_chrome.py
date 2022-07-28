
import pychromecast
from t_modules.t_extra import shooter
import time
import socket

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


class Chrome:
    def __init__(self, tauon):
        self.tauon = tauon
        self.services = []
        self.active = False
        self.cast = None
        self.target_playlist = None
        self.target_id = None

    def two(self):
        print("Scanning for chromecasts...")

        if True: #not self.services:
            try:
                self.tauon.gui.show_message(self.tauon.strings.scan_chrome)
                services, browser = pychromecast.discovery.discover_chromecasts()
                pychromecast.discovery.stop_discovery(browser)
                menu = self.tauon.chrome_menu
                menu.items.clear()
                for item in services:
                    self.services.append([str(item.uuid), str(item.friendly_name)])
                    menu.add(self.tauon.strings.cast_to % str(item.friendly_name), self.three, pass_ref=True, set_ref=[str(item.uuid), str(item.friendly_name)])

                if self.services:
                    self.tauon.gui.message_box = False
                    menu.activate(position=(self.tauon.gui.window_size[0] // 2, self.tauon.gui.window_size[1] // 2))
                    self.tauon.gui.update += 1
                else:
                    self.tauon.gui.show_message(self.tauon.strings.no_chromecasts)
                    self.tauon.gui.update += 1

                    return
                print(services)
                print(self.services)

            except:
                raise
                print("Failed to get chromecasts")

    def one(self, playlist_id, track_id):
        self.tauon.pctl.stop()
        self.target_playlist = playlist_id
        self.target_id = track_id
        self.cast = None
        if self.cast is None:
            self.two()
            return

    def three(self, item):
        shooter(self.four, [item])

    def four(self, item):

        #self.tauon.broadcast_select_track(self.target_id)
        time.sleep(2)
        print(item)
        ccs, browser = pychromecast.get_listed_chromecasts(friendly_names=[item[1]], discovery_timeout=3.0)
        print(ccs)
        self.browser = browser
        self.cast = ccs[0]
        self.ip = get_ip()

        mc = self.cast.media_controller
        mc.app_id = "2F76715B"

        self.tauon.chrome_mode = True



    def update(self):
        self.cast.media_controller.update_status()
        return self.cast.media_controller.status.current_time, \
            self.cast.media_controller.status.media_custom_data.get("id"), \
            self.cast.media_controller.status.player_state, \
               self.cast.media_controller.status.duration

    def start(self, track_id):
        self.cast.wait()
        tr = self.tauon.pctl.g(track_id)
        n = 0
        try:
            n = int(tr.track_number)
        except:
            pass
        d = {
            "metadataType": 3,
            "albumName": tr.album,
            "title": tr.title,
            "albumArtist": tr.album_artist,
            "artist": tr.artist,
            "trackNumber": n,
            "images": [{"url": f"http://{self.ip}:7814/api1/pic/medium/{track_id}"}],
            "releaseDate": tr.date
        }
        m = {
            "duration": round(float(tr.length), 1),
            "customData": {"id": str(tr.index)}
            #"contentId": str(tr.index)
        }
        print(m)
        self.cast.media_controller.play_media(f"http://{self.ip}:7814/api1/file/{track_id}", 'audio/mpeg', media_info=m, metadata=d, current_time=0.0)
        self.active = True

    def stop(self):
        if self.active:
            if self.cast:
                mc = self.cast.media_controller
                mc.stop()
            self.active = False
        self.tauon.chrome_mode = False
        pychromecast.discovery.stop_discovery(self.browser)
