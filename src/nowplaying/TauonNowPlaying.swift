import Foundation
import AppKit
import MediaPlayer

final class JsonLineIO {
    private let stdoutHandle = FileHandle.standardOutput
    private let stdinHandle = FileHandle.standardInput
    private let stdinQueue = DispatchQueue(label: "tauon.nowplaying.stdin")

    var onMessage: (([String: Any]) -> Void)?

    func startReading() {
        stdinQueue.async { [weak self] in
            guard let self else { return }
            while true {
                autoreleasepool {
                    guard let lineData = self.readLineData() else {
                        exit(0)
                    }
                    guard let object = try? JSONSerialization.jsonObject(with: lineData, options: []),
                          let dict = object as? [String: Any] else {
                        self.send(["type": "log", "level": "warn", "message": "Invalid JSON received"])
                        return
                    }
                    self.onMessage?(dict)
                }
            }
        }
    }

    private func readLineData() -> Data? {
        var buffer = Data()
        while true {
            let chunk = stdinHandle.readData(ofLength: 1)
            if chunk.isEmpty {
                return buffer.isEmpty ? nil : buffer
            }
            if chunk[0] == 0x0A { // \n
                return buffer
            }
            buffer.append(chunk)
        }
    }

    func send(_ dict: [String: Any]) {
        guard let data = try? JSONSerialization.data(withJSONObject: dict, options: []),
              var line = String(data: data, encoding: .utf8) else {
            return
        }
        line.append("\n")
        if let out = line.data(using: .utf8) {
            stdoutHandle.write(out)
        }
    }
}

final class NowPlayingController {
    private let io: JsonLineIO

    private func loadArtwork(from path: String) -> MPMediaItemArtwork? {
        if path.isEmpty { return nil }
        guard let image = NSImage(contentsOfFile: path) else { return nil }
        let size = image.size
        if #available(macOS 10.13, *) {
            return MPMediaItemArtwork(boundsSize: size) { _ in image }
        }
        return nil
    }

    init(io: JsonLineIO) {
        self.io = io
    }

    func installRemoteCommands() {
        let center = MPRemoteCommandCenter.shared()

        center.togglePlayPauseCommand.isEnabled = true
        center.playCommand.isEnabled = true
        center.pauseCommand.isEnabled = true
        center.stopCommand.isEnabled = true
        center.nextTrackCommand.isEnabled = true
        center.previousTrackCommand.isEnabled = true

        center.changePlaybackPositionCommand.isEnabled = true

        center.togglePlayPauseCommand.addTarget { [weak self] _ in
            self?.io.send(["type": "media_key", "name": "PlayPause"])
            return .success
        }
        center.playCommand.addTarget { [weak self] _ in
            self?.io.send(["type": "media_key", "name": "Play"])
            return .success
        }
        center.pauseCommand.addTarget { [weak self] _ in
            self?.io.send(["type": "media_key", "name": "Pause"])
            return .success
        }
        center.stopCommand.addTarget { [weak self] _ in
            self?.io.send(["type": "media_key", "name": "Stop"])
            return .success
        }
        center.nextTrackCommand.addTarget { [weak self] _ in
            self?.io.send(["type": "media_key", "name": "Next"])
            return .success
        }
        center.previousTrackCommand.addTarget { [weak self] _ in
            self?.io.send(["type": "media_key", "name": "Previous"])
            return .success
        }

        center.changePlaybackPositionCommand.addTarget { [weak self] event in
            guard let self else { return .commandFailed }
            guard let ev = event as? MPChangePlaybackPositionCommandEvent else { return .commandFailed }
            self.io.send(["type": "seek", "position": ev.positionTime])
            return .success
        }

        io.send(["type": "log", "level": "info", "message": "Remote commands installed"])
    }

    func updateNowPlaying(from msg: [String: Any]) {
        var info: [String: Any] = [:]

        if let title = msg["title"] as? String { info[MPMediaItemPropertyTitle] = title }
        if let artist = msg["artist"] as? String { info[MPMediaItemPropertyArtist] = artist }
        if let album = msg["album"] as? String { info[MPMediaItemPropertyAlbumTitle] = album }

        if let artPath = msg["art_path"] as? String, let artwork = loadArtwork(from: artPath) {
            info[MPMediaItemPropertyArtwork] = artwork
        }

        if let duration = msg["duration"] as? Double {
            info[MPMediaItemPropertyPlaybackDuration] = duration
        } else if let durationInt = msg["duration"] as? Int {
            info[MPMediaItemPropertyPlaybackDuration] = Double(durationInt)
        }

        if let elapsed = msg["elapsed"] as? Double {
            info[MPNowPlayingInfoPropertyElapsedPlaybackTime] = elapsed
        } else if let elapsedInt = msg["elapsed"] as? Int {
            info[MPNowPlayingInfoPropertyElapsedPlaybackTime] = Double(elapsedInt)
        }

        let state = msg["state"] as? Int ?? -1
        if let playing = msg["playing"] as? Bool {
            info[MPNowPlayingInfoPropertyPlaybackRate] = playing ? 1.0 : 0.0
        } else if state == 1 {
            info[MPNowPlayingInfoPropertyPlaybackRate] = 1.0
        } else {
            info[MPNowPlayingInfoPropertyPlaybackRate] = 0.0
        }

        MPNowPlayingInfoCenter.default().nowPlayingInfo = info
    }

    func clearNowPlaying() {
        MPNowPlayingInfoCenter.default().nowPlayingInfo = nil
    }
}

final class AppDelegate: NSObject, NSApplicationDelegate {
    private let io = JsonLineIO()
    private lazy var controller = NowPlayingController(io: io)

    func applicationDidFinishLaunching(_ notification: Notification) {
        controller.installRemoteCommands()

        io.onMessage = { [weak self] msg in
            guard let self else { return }
            let type = (msg["type"] as? String) ?? ""
            switch type {
            case "update":
                self.controller.updateNowPlaying(from: msg)
            case "clear":
                self.controller.clearNowPlaying()
            case "quit":
                exit(0)
            case "ping":
                self.io.send(["type": "pong"])
            default:
                self.io.send(["type": "log", "level": "warn", "message": "Unknown message type: \(type)"])
            }
        }

        io.startReading()
        io.send(["type": "ready", "protocol": 1])
    }
}

let app = NSApplication.shared
app.setActivationPolicy(.accessory)
let delegate = AppDelegate()
app.delegate = delegate
app.run()
