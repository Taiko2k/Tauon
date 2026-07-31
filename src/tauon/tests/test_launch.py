#!/usr/bin/env python

import subprocess
import sys


def test_direct_python_launch_is_rejected() -> None:
	"""The Python package must not bypass the native SDL owner."""
	result = subprocess.run(  # noqa: S603 - The interpreter and module are fixed test inputs
		[sys.executable, "-m", "tauon"],
		capture_output=True,
		text=True,
		timeout=10,
		check=False,
	)

	assert result.returncode != 0
	assert "Tauon must be launched through the tauon-native executable" in result.stderr
