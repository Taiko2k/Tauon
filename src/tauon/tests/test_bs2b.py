"""DSP math and behavior checks for Phazor's in-tree bs2b crossfeed header."""

from __future__ import annotations

import ctypes
import math
import shutil
import subprocess
import tempfile
from pathlib import Path

PHAZOR_DIR = Path(__file__).resolve().parents[2] / "phazor"
PRESETS = (
	("default", 700, 4.5),
	("cmoy", 700, 6.0),
	("jmeier", 650, 9.5),
)
SAMPLE_RATES = (44100, 48000, 96000)

HARNESS_C = r"""
#include <stdlib.h>
#include "bs2b.h"

bs2b_state *test_bs2b_new(void) {
	bs2b_state *s = (bs2b_state *) calloc(1, sizeof(bs2b_state));
	if (s != NULL) bs2b_state_init(s);
	return s;
}

void test_bs2b_free(bs2b_state *s) {
	free(s);
}

void test_bs2b_set_enable(bs2b_state *s, int enabled) {
	bs2b_state_set_enable(s, enabled);
}

void test_bs2b_set_params(bs2b_state *s, int fcut, float feed_db) {
	bs2b_state_set_params(s, fcut, feed_db);
}

void test_bs2b_set_mix(bs2b_state *s, float mix) {
	s->mix = mix;
}

int test_bs2b_is_active(const bs2b_state *s) {
	return bs2b_is_active(s) ? 1 : 0;
}

void test_bs2b_process(bs2b_state *s, float *frame, int channels, int sample_rate) {
	bs2b_process_frame(s, frame, channels, sample_rate);
}
"""


def _compile_harness(tmpdir: Path) -> ctypes.CDLL:
	cc = shutil.which("cc") or shutil.which("gcc") or shutil.which("clang")
	if cc is None:
		raise RuntimeError("No C compiler found to test src/phazor/bs2b.h")
	src = tmpdir / "bs2b_harness.c"
	lib_path = tmpdir / "libbs2b_harness.so"
	src.write_text(HARNESS_C, encoding="utf-8")
	subprocess.run(
		[
			cc,
			"-std=c17",
			"-Wall",
			"-Wextra",
			"-Wpedantic",
			"-Werror",
			"-shared",
			"-fPIC",
			f"-I{PHAZOR_DIR}",
			str(src),
			"-o",
			str(lib_path),
			"-lm",
		],
		check=True,
	)
	lib = ctypes.CDLL(str(lib_path))
	lib.test_bs2b_new.restype = ctypes.c_void_p
	lib.test_bs2b_free.argtypes = (ctypes.c_void_p,)
	lib.test_bs2b_set_enable.argtypes = (ctypes.c_void_p, ctypes.c_int)
	lib.test_bs2b_set_params.argtypes = (ctypes.c_void_p, ctypes.c_int, ctypes.c_float)
	lib.test_bs2b_set_mix.argtypes = (ctypes.c_void_p, ctypes.c_float)
	lib.test_bs2b_is_active.argtypes = (ctypes.c_void_p,)
	lib.test_bs2b_is_active.restype = ctypes.c_int
	lib.test_bs2b_process.argtypes = (ctypes.c_void_p, ctypes.POINTER(ctypes.c_float), ctypes.c_int, ctypes.c_int)
	return lib


def _ref_bs2b(samples: list[tuple[float, float]], srate: int, fcut: int, feed_db: float) -> list[tuple[float, float]]:
	gb_lo = feed_db * -5.0 / 6.0 - 3.0
	gb_hi = feed_db / 6.0 - 3.0
	g_lo = 10.0 ** (gb_lo / 20.0)
	g_hi = 1.0 - 10.0 ** (gb_hi / 20.0)
	fc_hi = fcut * (2.0 ** ((gb_lo - 20.0 * math.log10(g_hi)) / 12.0))

	x_lo = math.exp(-2.0 * math.pi * fcut / srate)
	b1_lo = x_lo
	a0_lo = g_lo * (1.0 - x_lo)

	x_hi = math.exp(-2.0 * math.pi * fc_hi / srate)
	b1_hi = x_hi
	a0_hi = 1.0 - g_hi * (1.0 - x_hi)
	a1_hi = -x_hi

	gain = 1.0 / (1.0 - g_hi + g_lo)
	lo = [0.0, 0.0]
	hi = [0.0, 0.0]
	prev = [0.0, 0.0]
	out: list[tuple[float, float]] = []
	for in_l, in_r in samples:
		lo[0] = a0_lo * in_l + b1_lo * lo[0]
		lo[1] = a0_lo * in_r + b1_lo * lo[1]
		hi[0] = a0_hi * in_l + a1_hi * prev[0] + b1_hi * hi[0]
		hi[1] = a0_hi * in_r + a1_hi * prev[1] + b1_hi * hi[1]
		prev[0] = in_l
		prev[1] = in_r
		out.append(((hi[0] + lo[1]) * gain, (hi[1] + lo[0]) * gain))
	return out


def test_bs2b_impulse_and_dc_gain() -> None:
	with tempfile.TemporaryDirectory() as tmp:
		lib = _compile_harness(Path(tmp))
		for _name, fcut, feed_db in PRESETS:
			for srate in SAMPLE_RATES:
				state = lib.test_bs2b_new()
				try:
					lib.test_bs2b_set_params(state, fcut, ctypes.c_float(feed_db))
					lib.test_bs2b_set_enable(state, 1)
					lib.test_bs2b_set_mix(state, ctypes.c_float(1.0))

					# Left-channel impulse matches the reference equation within 1e-5
					impulse = [(1.0, 0.0)] + [(0.0, 0.0)] * 63
					ref = _ref_bs2b(impulse, srate, fcut, feed_db)
					buf = (ctypes.c_float * 2)()
					for (in_l, in_r), (exp_l, exp_r) in zip(impulse, ref, strict=True):
						buf[0] = in_l
						buf[1] = in_r
						lib.test_bs2b_process(state, buf, 2, srate)
						assert abs(buf[0] - exp_l) < 1e-5
						assert abs(buf[1] - exp_r) < 1e-5

					# Steady-state DC mono gain is unity (0 dB)
					for _ in range(srate // 4):
						buf[0] = 0.5
						buf[1] = 0.5
						lib.test_bs2b_process(state, buf, 2, srate)
					assert abs(buf[0] - 0.5) < 1e-4
					assert abs(buf[1] - 0.5) < 1e-4

					# Steady-state DC left-only crossfeed ratio matches -feed_db
					for _ in range(srate // 4):
						buf[0] = 1.0
						buf[1] = 0.0
						lib.test_bs2b_process(state, buf, 2, srate)
					measured_db = 20.0 * math.log10(buf[0] / buf[1])
					assert abs(measured_db - feed_db) < 0.05
				finally:
					lib.test_bs2b_free(state)


def test_bs2b_bypass_and_ramp() -> None:
	with tempfile.TemporaryDirectory() as tmp:
		lib = _compile_harness(Path(tmp))
		state = lib.test_bs2b_new()
		try:
			# Disabled: bit-identical output
			buf = (ctypes.c_float * 2)(0.75, -0.25)
			lib.test_bs2b_process(state, buf, 2, 48000)
			assert buf[0] == 0.75 and buf[1] == -0.25

			# Enabled on non-stereo layouts: bit-identical output
			lib.test_bs2b_set_enable(state, 1)
			mono = (ctypes.c_float * 1)(0.6)
			mono_before = mono[0]
			lib.test_bs2b_process(state, mono, 1, 48000)
			assert mono[0] == mono_before
			surround = (ctypes.c_float * 6)(0.1, 0.2, 0.3, 0.4, 0.5, 0.6)
			surround_before = [surround[i] for i in range(6)]
			lib.test_bs2b_process(state, surround, 6, 48000)
			assert [surround[i] for i in range(6)] == surround_before

			# Smooth ramp-in over ~20 ms at 48 kHz (960 samples), then ramp-out to inactive
			prev_r = 0.0
			for _ in range(960):
				buf[0] = 1.0
				buf[1] = 0.0
				lib.test_bs2b_process(state, buf, 2, 48000)
				assert abs(buf[1] - prev_r) < 0.02
				prev_r = buf[1]
			assert prev_r > 0.2

			lib.test_bs2b_set_enable(state, 0)
			assert lib.test_bs2b_is_active(state) == 1
			for _ in range(965):
				buf[0] = 1.0
				buf[1] = 0.0
				lib.test_bs2b_process(state, buf, 2, 48000)
			assert lib.test_bs2b_is_active(state) == 0
			assert buf[0] == 1.0 and buf[1] == 0.0
		finally:
			lib.test_bs2b_free(state)


if __name__ == "__main__":
	test_bs2b_impulse_and_dc_gain()
	test_bs2b_bypass_and_ramp()
	print("all bs2b tests passed")
