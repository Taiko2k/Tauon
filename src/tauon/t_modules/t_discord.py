from __future__ import annotations

import asyncio
import builtins
import json
import logging
import threading
import time
import urllib.parse
from collections import deque
from typing import Optional

import requests

try:
    from pypresence import ActivityType, Presence, StatusDisplayType
except Exception:
    ActivityType      = None  # type: ignore
    Presence          = None  # type: ignore
    StatusDisplayType = None  # type: ignore

_LFM_CACHE_MAX = 256
_RPC_WINDOW_S            = 15.0
_RPC_BUDGET              = 3
_DEBOUNCE_S              = 0.25
_MIN_UPDATE_GAP_S        = 15.0
_MIN_UPDATE_GAP_CHANGE_S = 1.5
_POLL_INTERVAL_S         = 1


def build_lastfm_track_url(artist: Optional[str], title: Optional[str]) -> Optional[str]:
    a = (artist or "").strip()
    t = (title or "").strip()
    if a and t:
        return (
            f"https://www.last.fm/music/{urllib.parse.quote(a, safe='')}/"
            f"_/{urllib.parse.quote(t, safe='')}"
        )
    query = f"{a} {t}".strip()
    if query:
        return "https://www.last.fm/search/tracks?q=" + urllib.parse.quote(query, safe="")
    return None


def resolve_lastfm_button_url_async(main, artist: Optional[str], title: Optional[str]) -> Optional[str]:
    a = (artist or "").strip()
    t = (title or "").strip()
    query = f"{a} {t}".strip()
    if not query:
        return None
    search_url = "https://www.last.fm/search/tracks?q=" + urllib.parse.quote(query, safe="")
    if not a or not t:
        return search_url
    cache_key = (a.casefold(), t.casefold())
    cache:   dict           = main.__dict__.setdefault("_discord_lastfm_url_cache",   {})
    pending: set            = main.__dict__.setdefault("_discord_lastfm_url_pending", set())
    lock:    threading.Lock = main.__dict__.setdefault("_discord_lastfm_url_lock",    threading.Lock())
    with lock:
        val = cache.get(cache_key)
        if val is not None:
            return val
        if cache_key in pending:
            return None
        pending.add(cache_key)

    def _resolve() -> None:
        track_url = build_lastfm_track_url(a, t)
        resolved  = search_url
        if track_url:
            try:
                resp = requests.get(track_url, timeout=4, allow_redirects=True)
                if resp.status_code < 400 and "last.fm" in resp.url:
                    resolved = track_url
            except Exception:
                pass
        with lock:
            if len(cache) >= _LFM_CACHE_MAX:
                try:
                    cache.pop(next(iter(cache)))
                except StopIteration:
                    pass
            cache[cache_key] = resolved
            pending.discard(cache_key)

    threading.Thread(target=_resolve, daemon=True).start()
    return None


def discord_loop_entrypoint(main) -> None:
    try:
        from tauon.t_modules.t_main import PlayingState
    except Exception:
        PlayingState = None  # type: ignore

    prefs = main.prefs
    gui   = main.gui
    pctl  = main.pctl

    if Presence is None or ActivityType is None or StatusDisplayType is None:
        logging.warning("pypresence unavailable; Discord RPC disabled")
        prefs.discord_active     = False
        prefs.disconnect_discord = False
        gui.discord_status       = "Not connected"
        gui.update += 1
        if hasattr(main, "_discord_loop_guard_lock"):
            with main._discord_loop_guard_lock:
                main._discord_loop_guard_running = False
        return

    prefs.discord_active = True
    gui.discord_status   = "Standby"
    gui.update += 1

    wakeup: threading.Event = main.__dict__.setdefault("_discord_wakeup_event", threading.Event())

    CLIENT_ID = "954253873160286278"

    rpc: Optional[Presence] = None
    connected            = False
    next_reconnect_at    = 0.0
    reconnect_delay      = 2.0
    consecutive_failures = 0

    last_sent_sig         = ""
    last_sent_at          = 0.0
    pending_sig           = ""
    pending_since         = 0.0
    last_sent_track_index = -1

    last_playing_state = False
    last_track_index   = -1
    start_time         = time.time()
    last_prefs_sig: tuple = ()

    cached_art_track_index = -1
    cached_large_image     = "tauon-standard"
    cached_small_image     = None
    last_art_lookup        = 0.0

    last_debug_state  = None
    _update_times: deque[float] = deque()

    def _rpc_budget_ok(now: float) -> bool:
        while _update_times and now - _update_times[0] > _RPC_WINDOW_S:
            _update_times.popleft()
        return len(_update_times) < _RPC_BUDGET

    def log(msg: str) -> None:
        logging.info("[DiscordRPC] %s", msg)

    def set_status(status: str) -> None:
        if gui.discord_status != status:
            gui.discord_status = status
            gui.update += 1

    def safe_text(text: str, fallback: str = "…") -> str:
        clean = " ".join((text or "").split()).strip() or fallback
        return clean[:120]

    def reset_asyncio_loop(current_loop: asyncio.AbstractEventLoop) -> asyncio.AbstractEventLoop:
        try:
            if current_loop and not current_loop.is_closed():
                current_loop.close()
        except Exception:
            pass
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        return new_loop

    def _try_clear() -> None:
        try:
            rpc.clear()
        except Exception:
            try:
                rpc.clear(main.pid)
            except Exception:
                pass

    def close_rpc() -> None:
        nonlocal rpc, connected
        if rpc is not None:
            try:
                _try_clear()
            except Exception:
                pass
            try:
                rpc.close()
            except Exception:
                pass
            rpc = None
        connected = False

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        while True:
            poll_interval = _POLL_INTERVAL_S

            prefs_sig = (
                getattr(prefs, "discord_card_layout",         "title_artist"),
                getattr(prefs, "discord_member_list_display", "song"),
                prefs.discord_clean_title,
                prefs.discord_lastfm_button,
                prefs.discord_show_tauon_button,
            )
            force_update = prefs_sig != last_prefs_sig
            if force_update:
                log(f"Preferences changed: {prefs_sig}")
                last_prefs_sig = prefs_sig
                pending_since  = 0.0

            if prefs.disconnect_discord or not prefs.discord_enable:
                if connected and rpc is not None and prefs.disconnect_discord:
                    try:
                        _try_clear()
                    except Exception:
                        logging.exception("Error clearing Discord presence on shutdown")
                close_rpc()
                prefs.disconnect_discord = False
                set_status("Not connected")
                log("Discord loop exiting")
                break

            now = time.time()

            if not connected:
                if now < next_reconnect_at:
                    wakeup.wait(timeout=0.25)
                    wakeup.clear()
                    continue

                if consecutive_failures >= 3:
                    log("Multiple failures — resetting asyncio loop before retry")
                    loop = reset_asyncio_loop(loop)
                    consecutive_failures = 0

                try:
                    rpc = Presence(CLIENT_ID)
                    rpc.connect()
                    connected            = True
                    reconnect_delay      = 2.0
                    consecutive_failures = 0
                    last_sent_sig        = ""
                    last_sent_at         = 0.0
                    set_status("Connected")
                    log("Connected to Discord RPC")
                except Exception as exc:
                    consecutive_failures += 1
                    close_rpc()
                    next_reconnect_at = now + reconnect_delay
                    reconnect_delay   = min(reconnect_delay * 1.8, 45.0)
                    log(f"Connection failed ({consecutive_failures}): {exc}")
                    set_status(builtins._("Reconnecting to Discord..."))
                    wakeup.wait(timeout=0.25)
                    wakeup.clear()
                    continue

            if not pctl.playing_ready():
                tr        = None
                state_now = None
            else:
                tr        = pctl.playing_object()
                state_now = pctl.playing_state

            is_playing = (
                state_now in (PlayingState.PLAYING, PlayingState.URL_STREAM)
                if PlayingState is not None and state_now is not None
                else False
            )
            is_idle = tr is None or (
                PlayingState is not None
                and state_now not in (
                    PlayingState.PLAYING,
                    PlayingState.PAUSED,
                    PlayingState.URL_STREAM,
                )
            )

            if is_idle:
                payload: dict = {
                    "activity_type":       ActivityType.LISTENING,
                    "status_display_type": StatusDisplayType.STATE,
                    "pid":                 main.pid,
                    "details":             "Tauon Music Box",
                    "state":               "Idle",
                    "large_image":         "tauon-standard",
                }
            else:
                current_index = (
                    main.radiobox.song_key
                    if state_now == PlayingState.URL_STREAM
                    else tr.index
                )

                if is_playing:
                    if current_index != last_track_index or not last_playing_state:
                        start_time = now - pctl.playing_time
                    elif abs(start_time - (now - pctl.playing_time)) > 1.0:
                        start_time = now - pctl.playing_time

                raw_title = tr.title or builtins._("Unknown Track")
                if prefs.discord_clean_title:
                    try:
                        title_for_presence = main.clean_track_title(raw_title)
                    except Exception:
                        title_for_presence = raw_title
                else:
                    title_for_presence = raw_title

                artist = tr.artist or builtins._("Unknown Artist")

                if state_now == PlayingState.URL_STREAM:
                    album = main.radiobox.loaded_station.get("title", tr.album) if tr.album else None
                else:
                    al    = (tr.album or "").lower()
                    album = (
                        None
                        if al and al in ((tr.title or "").lower(), (tr.artist or "").lower())
                        else tr.album
                    )
                if album and len(album) == 1:
                    album += " "

                if current_index != cached_art_track_index or (now - last_art_lookup) > 25:
                    cached_art_track_index = current_index
                    last_art_lookup        = now
                    cached_large_image     = "tauon-standard"
                    cached_small_image     = None
                    if state_now != PlayingState.URL_STREAM:
                        try:
                            url = main.get_album_art_url(tr)
                            if url:
                                cached_large_image = url
                                cached_small_image = "tauon-standard"
                        except Exception:
                            logging.exception("Discord cover art lookup failed")

                card_layout = getattr(prefs, "discord_card_layout", "title_artist")
                if card_layout == "artist_title":
                    details       = safe_text(artist,             builtins._("Unknown Artist"))
                    state_text    = safe_text(title_for_presence, builtins._("Unknown Track"))
                    details_holds = "artist"
                else:
                    details       = safe_text(title_for_presence, builtins._("Unknown Track"))
                    state_text    = safe_text(artist,             builtins._("Unknown Artist"))
                    details_holds = "song"

                member_list    = getattr(prefs, "discord_member_list_display", "song")
                status_display = (
                    StatusDisplayType.DETAILS
                    if member_list == details_holds
                    else StatusDisplayType.STATE
                )

                buttons: list[dict] = []
                if prefs.discord_lastfm_button:
                    lfm_url = resolve_lastfm_button_url_async(main, tr.artist, tr.title)
                    if lfm_url:
                        buttons.append({"label": "🔎 Track Info", "url": lfm_url})
                if prefs.discord_show_tauon_button:
                    buttons.append({"label": "🌐 Tauon", "url": "https://tauonmusicbox.rocks/"})

                payload = {
                    "activity_type":       ActivityType.LISTENING,
                    "status_display_type": status_display,
                    "pid":                 main.pid,
                    "details":             details,
                    "state":               state_text,
                    "large_image":         cached_large_image,
                    "small_image":         cached_small_image,
                }

                if buttons:
                    payload["buttons"] = buttons[:2]
                if is_playing:
                    payload["start"] = int(start_time)
                    if state_now != PlayingState.URL_STREAM:
                        payload["end"] = int(start_time + tr.length)
                if album and state_now != PlayingState.URL_STREAM:
                    payload["large_text"] = safe_text(album, "Tauon")
                if cached_small_image:
                    payload["small_text"] = "Tauon"

                debug_state = (current_index, str(state_now), is_playing)
                if debug_state != last_debug_state:
                    log(f"Track/state changed idx={current_index} state={state_now} playing={is_playing}")
                    last_debug_state = debug_state

                last_track_index   = current_index
                last_playing_state = is_playing

            sig_idx = -1
            if not is_idle:
                try:
                    sig_idx = int(current_index)
                except Exception:
                    sig_idx = -1
            payload_sig = json.dumps(payload, sort_keys=True, default=str) + f"::idx={sig_idx}"

            track_changed = sig_idx >= 0 and sig_idx != last_sent_track_index

            if payload_sig != pending_sig:
                pending_sig   = payload_sig
                pending_since = (now - _DEBOUNCE_S) if track_changed else now

            time_since_change = now - pending_since
            time_since_sent   = now - last_sent_at

            min_gap = (
                0.0
                if last_sent_at == 0.0
                else _MIN_UPDATE_GAP_CHANGE_S if track_changed else _MIN_UPDATE_GAP_S
            )

            rate_ok = _rpc_budget_ok(now) and time_since_sent >= min_gap

            ready_to_send = (
                pending_sig != last_sent_sig
                and time_since_change >= _DEBOUNCE_S
                and rate_ok
            )

            if force_update and pending_sig != last_sent_sig and rate_ok:
                ready_to_send = True

            if ready_to_send:
                try:
                    rpc.update(**payload)
                    _update_times.append(now)
                    last_sent_sig         = payload_sig
                    last_sent_at          = now
                    last_sent_track_index = sig_idx
                    consecutive_failures  = 0
                    set_status("Connected")
                except Exception as exc:
                    consecutive_failures += 1
                    log(f"RPC update failed ({consecutive_failures}): {exc}; will reconnect")
                    close_rpc()
                    next_reconnect_at = time.time() + reconnect_delay
                    reconnect_delay   = min(reconnect_delay * 1.8, 45.0)
                    set_status(builtins._("Reconnecting to Discord..."))
                    wakeup.wait(timeout=0.5)
                    wakeup.clear()
                    continue

            if pending_sig != last_sent_sig and not rate_ok and _update_times:
                budget_opens_at = _update_times[0] + _RPC_WINDOW_S
                sleep_time = max(0.05, min(poll_interval, budget_opens_at - now))
                if sleep_time > 1.0:
                    set_status(builtins._("Waiting for Discord rate limit…"))
                wakeup.wait(timeout=sleep_time)
            else:
                wakeup.wait(timeout=poll_interval)
            wakeup.clear()

    except Exception as exc:
        log(f"Fatal error in Discord RPC loop: {exc}")
        set_status(builtins._("Error - Discord not running?"))
        prefs.disconnect_discord = False

    finally:
        close_rpc()
        try:
            if loop and not loop.is_closed():
                loop.close()
        except Exception:
            pass
        prefs.discord_active = False
        set_status("Not connected")
        if hasattr(main, "_discord_loop_guard_lock"):
            with main._discord_loop_guard_lock:
                main._discord_loop_guard_running = False
