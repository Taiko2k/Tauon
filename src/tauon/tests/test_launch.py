#!/usr/bin/env python

import subprocess
import sys
import time


def test_launch_main_script() -> None:
	"""Test that Tauon launches without crashing."""
	proc = subprocess.Popen(  # noqa: S603 - We care not to verify input here
		[sys.executable, "-m", "tauon"],
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE,
	)

	try:
		# Give it a moment to initialize
		time.sleep(1)
		assert proc.poll() is None, "Tauon exited early"
	finally:
		# Clean up process
		proc.terminate()
		try:
			proc.wait(timeout=2)
		except subprocess.TimeoutExpired:
			proc.kill()
