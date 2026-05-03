"""Smart Mix - Análisis de BPM en segundo plano
Usa aubio para analizar los primeros 30s de audio.
Diseñado para CPUs lentas: no bloquea la UI.
"""
from __future__ import annotations
import logging
import threading
from collections import deque
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from tauon.t_modules.t_main import TrackClass

_queue: deque = deque()
_lock = threading.Lock()
_thread: threading.Thread | None = None
_running = False

def _analyse_file(filepath: str) -> float:
	"""Analiza BPM usando aubio. Retorna 0.0 si falla."""
	try:
		import aubio
		import numpy as np
		hop_s = 256
		win_s = 512
		samplerate = 44100
		max_frames = int(samplerate * 30 / hop_s)
		src = aubio.source(filepath, samplerate, hop_s)
		samplerate = src.samplerate
		tempo = aubio.tempo("default", win_s, hop_s, samplerate)
		beats = []
		for _ in range(max_frames):
			samples, read = src()
			if tempo(samples):
				beats.append(tempo.get_last_s())
			if read < hop_s:
				break
		if len(beats) < 4:
			return 0.0
		intervals = np.diff(beats)
		bpm = 60.0 / float(np.median(intervals))
		while bpm < 60:
			bpm *= 2
		while bpm > 200:
			bpm /= 2
		return round(bpm, 1)
	except Exception as e:
		logging.debug(f"t_autobpm: fallo en {filepath}: {e}")
		return 0.0

def _worker(master_library: dict, save_cb, notify_cb) -> None:
	"""Hilo de análisis: procesa la cola sin saturar CPU."""
	import time
	logging.info("t_autobpm: hilo iniciado")
	if notify_cb:
		try:
			notify_cb("Smart Mix: Analysing BPM in background...", mode="info")
		except Exception:
			pass
	while _queue:
		with _lock:
			if not _queue:
				break
			track_id = _queue.popleft()
		track = master_library.get(track_id)
		if track is None or getattr(track, "bpm", 0.0) > 0:
			continue
		filepath = str(getattr(track, "fullpath", ""))
		if not filepath or not Path(filepath).exists():
			continue
		bpm = _analyse_file(filepath)
		if bpm > 0:
			track.bpm = bpm
			logging.info(f"t_autobpm: {Path(filepath).name} = {bpm} BPM")
			if save_cb:
				try:
					save_cb()
				except Exception:
					pass
		time.sleep(0.1)
	logging.info("t_autobpm: hilo terminado")
	if notify_cb:
		try:
			notify_cb("Smart Mix: BPM analysis complete", mode="done")
		except Exception:
			pass

def queue_library(master_library: dict, save_cb=None, notify_cb=None) -> None:
	"""Añade canciones sin BPM a la cola y arranca el hilo."""
	global _thread
	count = 0
	with _lock:
		for track_id, track in master_library.items():
			if getattr(track, "bpm", 0.0) == 0.0:
				_queue.append(track_id)
				count += 1
	if count == 0:
		logging.info("t_autobpm: todas las canciones ya tienen BPM")
		return
	logging.info(f"t_autobpm: {count} canciones en cola")
	if _thread is None or not _thread.is_alive():
		_thread = threading.Thread(
			target=_worker,
			args=(master_library, save_cb, notify_cb),
			daemon=True,
			name="autobpm-worker",
		)
		_thread.start()

def queue_track(track, master_library: dict, save_cb=None) -> None:
	"""Añade una sola canción nueva a la cola."""
	global _thread
	if getattr(track, "bpm", 0.0) > 0:
		return
	track_id = next((tid for tid, t in master_library.items() if t is track), None)
	if track_id is None:
		return
	with _lock:
		if track_id not in _queue:
			_queue.append(track_id)
	if _thread is None or not _thread.is_alive():
		_thread = threading.Thread(
			target=_worker,
			args=(master_library, save_cb),
			daemon=True,
			name="autobpm-worker",
		)
		_thread.start()
