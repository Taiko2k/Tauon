import sys
from pathlib import Path

from setuptools import setup
from setuptools.command.build import build as _build
from setuptools.command.sdist import sdist as _sdist

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compile_translations import main as compile_translations


class BuildWithTranslations(_build):
	"""Run compile_translations before standard build."""

	def run(self) -> None:
		compile_translations()
		super().run()


class SdistWithTranslations(_sdist):
	"""Ensure translations are compiled in sdist tarball."""

	def run(self) -> None:
		compile_translations()
		super().run()

_ = setup(
	cmdclass={
		"build": BuildWithTranslations,
		"sdist": SdistWithTranslations,
	},
)
