"""Visualizer, showcase, and view-switching components."""

from __future__ import annotations

import ctypes
import ctypes.util
import logging
import math
import os
import random
import sys
import time
from ctypes import POINTER, c_char_p, c_float, c_int, c_uint, c_uint32, c_void_p
from pathlib import Path
from typing import Any, Protocol

import sdl3

from tauon.t_modules.t_custom import draw_layout_glyph
from tauon.t_modules.t_draw import TDraw
from tauon.t_modules.t_enums import PlayingState
from tauon.t_modules.t_extra import (
	FPSCounter,
	Timer,
	alpha_blend,
	alpha_mod,
	clean_string,
	colour_slide,
	hsl_to_rgb,
	rgb_add_hls,
	test_lumi,
)
from tauon.t_modules.t_guitar_chords import GuitarChords
from tauon.t_modules.t_menu import Menu
from tauon.t_modules.t_models import ColourRGBA, TrackClass
from tauon.t_modules.t_prefs import Prefs
from tauon.t_modules.t_state import ColoursClass, GuiVar, Input, LoadImageAsset, WhiteModImageAsset, asset_loader


class _VisualPlayer(Protocol):
	def __getattr__(self, name: str) -> Any: ...


class _VisualLyrics(Protocol):
	continuous: bool

	def render(self) -> Any: ...


class _VisualApp(Protocol):
	gui: GuiVar
	inp: Input
	ddt: TDraw
	pctl: _VisualPlayer
	prefs: Prefs
	colours: ColoursClass
	window_size: list[int]

	def __getattr__(self, name: str) -> Any: ...
def get_renderer_name(renderer: sdl3.LP_SDL_Renderer) -> str | None:
	renderer_name = sdl3.SDL_GetRendererName(renderer)
	if not renderer_name:
		logging.warning(f"SDL_GetRendererName failed: {sdl3.SDL_GetError()}")
		return None

	if isinstance(renderer_name, bytes):
		return renderer_name.decode("utf-8", errors="replace")
	return renderer_name

def renderer_name_supports_milkdrop(renderer_name: str | None) -> bool:
	if renderer_name is None:
		return True
	return renderer_name.casefold() == "opengl"

milky_ready = True
milky_error = ""
try:
	import OpenGL
	# Disable error checking as SDL can generate errors we do not otherwise catch, crashing PyOpenGL
	OpenGL.ERROR_CHECKING = False
	from OpenGL.GL import (
		GL_ACTIVE_TEXTURE,
		GL_BLEND,
		GL_CLAMP_TO_EDGE,
		GL_COLOR_ATTACHMENT0,
		GL_COLOR_BUFFER_BIT,
		GL_COMPILE_STATUS,
		GL_CURRENT_PROGRAM,
		GL_FRAGMENT_SHADER,
		GL_FRAMEBUFFER,
		GL_FRAMEBUFFER_BINDING,
		GL_FRAMEBUFFER_COMPLETE,
		GL_LINEAR,
		GL_LINK_STATUS,
		GL_PACK_ALIGNMENT,
		GL_PIXEL_UNPACK_BUFFER,
		GL_RGBA,
		GL_TEXTURE0,
		GL_TEXTURE_2D,
		GL_TEXTURE_MAG_FILTER,
		GL_TEXTURE_MIN_FILTER,
		GL_TEXTURE_WRAP_S,
		GL_TEXTURE_WRAP_T,
		GL_TRIANGLES,
		GL_UNPACK_ALIGNMENT,
		GL_UNPACK_IMAGE_HEIGHT,
		GL_UNPACK_LSB_FIRST,
		GL_UNPACK_ROW_LENGTH,
		GL_UNPACK_SKIP_IMAGES,
		GL_UNPACK_SKIP_PIXELS,
		GL_UNPACK_SKIP_ROWS,
		GL_UNPACK_SWAP_BYTES,
		GL_UNSIGNED_BYTE,
		GL_VERTEX_ARRAY_BINDING,
		GL_VERTEX_SHADER,
		GL_VIEWPORT,
		glActiveTexture,
		glAttachShader,
		glBindBuffer,
		glBindFramebuffer,
		glBindTexture,
		glBindVertexArray,
		glCheckFramebufferStatus,
		glClear,
		glClearColor,
		glCompileShader,
		glCopyTexSubImage2D,
		glCreateProgram,
		glCreateShader,
		glDeleteFramebuffers,
		glDeleteShader,
		glDeleteTextures,
		glDisable,
		glDrawArrays,
		glEnable,
		glFinish,
		glFlush,
		glFramebufferTexture2D,
		glGenFramebuffers,
		glGenTextures,
		glGenVertexArrays,
		glGetIntegerv,
		glGetProgramInfoLog,
		glGetProgramiv,
		glGetShaderInfoLog,
		glGetShaderiv,
		glGetUniformLocation,
		glIsEnabled,
		glLinkProgram,
		glPixelStorei,
		glReadPixels,
		glShaderSource,
		glTexImage2D,
		glTexParameteri,
		glUniform1i,
		glUseProgram,
		glViewport,
	)
except ModuleNotFoundError:
	logging.warning("PyOpenGL not found, Milkdrop visualizer will be disabled")
	milky_ready = False
	milky_error = "Optional module PyOpenGL is not installed"
except Exception:
	logging.exception("Unknown error importing PyOpenGL, Milkdrop visualizer will be disabled")
	milky_ready = False
	milky_error = "PyOpenGL failed to load"

def find_projectm_library() -> str | None:
	if sys.platform == "win32":
		module_dir = Path(__file__).resolve().parents[2]
		for base_dir in (module_dir, Path(sys.executable).parent, Path.cwd()):
			for dll_name in ("libprojectM-4-4.dll", "libprojectM-4.dll", "projectM-4.dll"):
				path = base_dir / dll_name
				if path.is_file():
					return str(path)
	if sys.platform == "darwin":
		base_dirs = [Path(sys.executable).parent]
		if hasattr(sys, "_MEIPASS"):
			# PyInstaller bundle: dylibs land in Contents/Frameworks
			base_dirs.append(Path(sys._MEIPASS))
		for base_dir in base_dirs:
			for dylib_name in ("libprojectM-4.4.dylib", "libprojectM-4.dylib"):
				path = base_dir / dylib_name
				if path.is_file():
					return str(path)
	for lib_name in ("projectM-4", "libprojectM-4-4", "libprojectM-4"):
		path = ctypes.util.find_library(lib_name)
		if path:
			return path
	return None

if not find_projectm_library():
	milky_ready = False
	if not milky_error:
		milky_error = "libprojectM library was not found"
class ProjectM:
	def __init__(self, tauon: _VisualApp) -> None:
		self.tauon: _VisualApp = tauon
		self.lib = None
		self.pm_instance = None
		self.presets: list[Path] = []
		self.loaded_preset: Path | None = None
		self.load_next = None
		self.auto_frames = 0
		self.dirs: list[Path] = [
			Path("/usr/share/projectM/presets"),
			self.tauon.pctl.install_directory / "presets",
			self.tauon.user_directory / "presets"
		]
		self.timer: Timer = Timer()
		self.frame_timer: Timer = Timer()
		self.first_frame: bool = True
		self.lib_error: bool = False
		self.render_frame_fbo_available: bool = False
		self.burn_texture_available: bool = False
		self.set_frame_time_available: bool = False
		self.lib_path: Path | None = None
		self.glew = None
		# macOS: the SDL renderer's GL context is a 2.1 compatibility profile,
		# but projectM needs 3.3+ core, so it renders in its own context and
		# frames are read back to the renderer in Milky.render_readback.
		self.own_gl_context = None
		self.renderer_gl_context = None
		# Max frames projectM accepts per pcm_add_float call; refined from the
		# library in define_function_signatures. Feeding more crashes it.
		self.pcm_max_samples: int = 2048

	def load_library(self) -> None:
		"""Load projectM library using ctypes"""
		renderer_name = get_renderer_name(self.tauon.renderer)
		if renderer_name is not None and renderer_name.casefold() != "opengl":
			logging.warning(f"Not loading ProjectM because SDL renderer is {renderer_name!r}, not 'opengl'")
			self.lib_error = True
			return

		lib_name = find_projectm_library()
		if not lib_name:
			logging.warning("Could not find libprojectM-4")
			self.tauon.show_message("Package ProjectM-4 not found", "Milkdrop feature will be unavailable", mode="error")
			self.lib_error = True
			return
		try:
			self.lib = ctypes.CDLL(lib_name)
			if self.lib:
				if Path(lib_name).is_file():
					self.lib_path = Path(lib_name)
				logging.info(f"Successfully loaded: {lib_name}")
			else:
				logging.warning("Could not load libprojectM-4")
				self.lib_error = True
		except OSError:
			logging.exception("Could not load libprojectM-4")
			self.lib_error = True
		except Exception:
			logging.exception("Unkown error loading libprojectM-4")
			self.lib_error = True

	def setup_function_signatures(self) -> None:
		"""Define ctypes function signatures for basic projectM functions"""
		if not self.lib:
			return

		try:
			# projectm_create - Create projectM instance
			self.lib.projectm_create.argtypes = None
			self.lib.projectm_create.restype = c_void_p

			# # projectm_destroy - Destroy projectM instance
			self.lib.projectm_destroy.argtypes = [c_void_p]
			self.lib.projectm_destroy.restype = None

			# projectm_pcm_add_float - Add audio data
			self.lib.projectm_pcm_add_float.argtypes = [c_void_p, POINTER(c_float), c_uint, c_uint]
			self.lib.projectm_pcm_add_float.restype = None

			# projectm_pcm_get_max_samples - Max frames accepted per add call.
			# Feeding more than this overruns projectM's internal PCM buffer and
			# segfaults, which happens at track start (the vis buffer has filled
			# up) and is reached sooner at high sample rates.
			self.pcm_max_samples = 2048
			try:
				self.lib.projectm_pcm_get_max_samples.argtypes = []
				self.lib.projectm_pcm_get_max_samples.restype = ctypes.c_size_t
				max_samples = int(self.lib.projectm_pcm_get_max_samples())
				if max_samples > 0:
					self.pcm_max_samples = max_samples
			except AttributeError:
				logging.warning("projectm_pcm_get_max_samples not found, using default of 2048")

			# projectm_opengl_render_frame - Render frame
			self.lib.projectm_opengl_render_frame.argtypes = [c_void_p]
			self.lib.projectm_opengl_render_frame.restype = None

			try:
				self.lib.projectm_opengl_render_frame_fbo.argtypes = [c_void_p, c_uint32]
				self.lib.projectm_opengl_render_frame_fbo.restype = None
				self.render_frame_fbo_available = True
			except AttributeError:
				self.render_frame_fbo_available = False
				logging.warning("projectm_opengl_render_frame_fbo not found, using default framebuffer copy fallback")

			# projectm_set_window_size - Render frame
			self.lib.projectm_set_window_size.argtypes = [c_void_p, c_uint, c_uint]
			self.lib.projectm_set_window_size.restype = None

			# projectm_load_preset_file - Load specific preset file
			self.lib.projectm_load_preset_file.argtypes = [c_void_p, c_char_p, c_int]
			self.lib.projectm_load_preset_file.restype = c_int

			self.lib.projectm_set_fps.argtypes = [c_void_p, ctypes.c_int32]
			self.lib.projectm_set_fps.restype = None

			try:
				self.lib.projectm_set_frame_time.argtypes = [c_void_p, ctypes.c_double]
				self.lib.projectm_set_frame_time.restype = None
				self.set_frame_time_available = True
			except AttributeError:
				self.set_frame_time_available = False
				logging.warning("projectm_set_frame_time not found, frame timing override will be unavailable")

			self.lib.projectm_set_texture_search_paths.argtypes = [
				c_void_p,  # instance
				ctypes.POINTER(ctypes.c_char_p),  # texture_search_paths (array of strings)
				ctypes.c_size_t  # count
			]
			self.lib.projectm_set_texture_search_paths.restype = None

			try:
				self.lib.projectm_opengl_burn_texture.argtypes = [c_void_p, c_uint32, c_int, c_int, c_int, c_int]
				self.lib.projectm_opengl_burn_texture.restype = None
				self.burn_texture_available = True
			except AttributeError:
				self.burn_texture_available = False
				logging.warning("projectm_opengl_burn_texture not found, album art burn-in will be skipped")

			logging.debug("Function signatures set up successfully")

		except AttributeError as e:
			logging.warning(f"Error setting up function signatures: {e}")
			raise
		except Exception as e:
			logging.warning(f"Error setting up function signatures: {e}")
			raise

	def init_glew(self) -> bool:
		if sys.platform != "win32":
			return True

		glew_path: str | Path = "glew32.dll"
		if self.lib_path:
			candidate = self.lib_path.with_name("glew32.dll")
			if candidate.is_file():
				glew_path = candidate

		try:
			self.glew = ctypes.CDLL(str(glew_path))
			self.glew.glewInit.argtypes = []
			self.glew.glewInit.restype = c_uint
			result = self.glew.glewInit()
			if result != 0:
				logging.warning(f"GLEW initialization failed with error code {result}")
				return False
			logging.info("GLEW initialized successfully")
			return True
		except Exception:
			logging.exception("Failed to initialize GLEW")
			return False

	def set_texture_paths(self) -> None:
		path_bytes = []
		for path in self.dirs:
			if (path / "textures").is_dir():
				path_bytes.append(str(path / "textures").encode("utf-8"))
		if path_bytes:
			path_array = (ctypes.c_char_p * len(path_bytes))(*path_bytes)
			self.lib.projectm_set_texture_search_paths(self.pm_instance, path_array, len(path_bytes))
			logging.info(f"Set projectm texture paths: {path_bytes}")

	def create_own_context(self) -> bool:
		self.renderer_gl_context = sdl3.SDL_GL_GetCurrentContext()
		sdl3.SDL_GL_SetAttribute(sdl3.SDL_GL_CONTEXT_MAJOR_VERSION, 3)
		sdl3.SDL_GL_SetAttribute(sdl3.SDL_GL_CONTEXT_MINOR_VERSION, 3)
		sdl3.SDL_GL_SetAttribute(sdl3.SDL_GL_CONTEXT_PROFILE_MASK, sdl3.SDL_GL_CONTEXT_PROFILE_CORE)
		self.own_gl_context = sdl3.SDL_GL_CreateContext(self.tauon.t_window)
		if not self.own_gl_context:
			logging.error(f"Failed to create core profile GL context for projectM: {sdl3.SDL_GetError()}")
			return False
		sdl3.SDL_GL_MakeCurrent(self.tauon.t_window, self.own_gl_context)
		return True

	def make_own_context_current(self) -> None:
		sdl3.SDL_GL_MakeCurrent(self.tauon.t_window, self.own_gl_context)

	def restore_renderer_context(self) -> None:
		if self.renderer_gl_context:
			sdl3.SDL_GL_MakeCurrent(self.tauon.t_window, self.renderer_gl_context)

	@staticmethod
	def prepare_opengl() -> None:
		"""Reset pixel-unpack state inherited from SDL before projectM uploads textures.

		projectM 4.1.6 only overrides GL_UNPACK_ALIGNMENT while uploading its
		embedded textures. SDL's renderer can leave row-length/skip state or a
		pixel-unpack buffer bound, causing projectM's 256x256 noise upload to
		read beyond its 256 KiB source buffer inside Mesa.
		"""
		glBindBuffer(GL_PIXEL_UNPACK_BUFFER, 0)
		glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
		glPixelStorei(GL_UNPACK_ROW_LENGTH, 0)
		glPixelStorei(GL_UNPACK_IMAGE_HEIGHT, 0)
		glPixelStorei(GL_UNPACK_LSB_FIRST, 0)
		glPixelStorei(GL_UNPACK_SKIP_PIXELS, 0)
		glPixelStorei(GL_UNPACK_SKIP_ROWS, 0)
		glPixelStorei(GL_UNPACK_SKIP_IMAGES, 0)
		glPixelStorei(GL_UNPACK_SWAP_BYTES, 0)

	def init(self, width: int = 800, height: int = 600, preset_path=None) -> bool:
		"""Initialize projectM with basic settings"""
		if not self.lib:
			return False

		# Git version doesn't bump version :(
		# major = c_int()
		# minor = c_int()
		# patch = c_int()
		#
		# self.lib.projectm_get_version_components(byref(major), byref(minor), byref(patch))
		# print(major.value, minor.value, patch.value)
		# if major.value == 4 and minor.value < 2:
		# 	logging.warning(f"Detected libprojectm version {major.value}.{minor.value} but at least 4.2 is required")
		# 	logging.warning("Milkdrop visualiser will be unavailable")
		# 	self.lib_error = True
		# 	self.lib = None
		# 	return False

		try:
			self.setup_function_signatures()
		except Exception:
			logging.warning("Failed to bind projectm functions, milkdrop visualiser will be unavailable")
			self.lib_error = True
			self.lib = None
			return False

		if not self.init_glew():
			self.lib_error = True
			self.lib = None
			return False

		if not (self.tauon.user_directory / "presets").exists():
			(self.tauon.user_directory / "presets").mkdir()

		if sys.platform == "darwin" and not self.create_own_context():
			self.lib_error = True
			self.lib = None
			return False

		self.prepare_opengl()

		# Create projectM instance
		try:
			logging.info("init project m...")
			self.pm_instance = self.lib.projectm_create()
			if self.pm_instance:
				logging.info("ProjectM initialized successfully")
				logging.info(f"Preset path: {preset_path}")

				aud = self.tauon.aud
				if not aud:
					logging.error("Phazor not init for vis")
					return False

				aud.get_vis_side_buffer.argtypes = []
				aud.get_vis_side_buffer.restype = ctypes.POINTER(c_float)

				aud.get_vis_side_buffer_fill.argtypes = []
				aud.get_vis_side_buffer_fill.restype = ctypes.c_int

				self.rescan_presets()
				self.set_texture_paths()

				if self.tauon.prefs.loaded_preset:
					self.load_preset(self.tauon.prefs.loaded_preset)
				else:
					self.random_preset()

				return True
			logging.error("Failed to create projectM instance")
			self.lib_error = True
			self.lib = None
			return False

		except Exception as e:
			logging.exception(f"Error initializing projectM: {e}")
			self.lib_error = True
			self.lib = None
			return False
		finally:
			if self.own_gl_context:
				self.restore_renderer_context()

	def rescan_presets(self) -> None:
		def scan_folder(dir: Path) -> None:
			for item in dir.iterdir():
				if item.is_dir():
					scan_folder(item)
				elif item.suffix.lower() == ".milk":
					#logging.info(f"Found milkdrop {item.stem}")
					self.presets.append(item)

		self.presets.clear()
		for dir in self.dirs:
			if dir.is_dir():
				scan_folder(dir)

	def random_preset(self, fade: bool = False) -> None:
		#self.rescan_presets()
		if not self.presets:
			return
		choice = random.choice(self.presets)
		self.load_preset(choice, fade)

	def get_current_name(self) -> str:
		if self.loaded_preset:
			return self.loaded_preset.stem
		return "Default"

	def log_preset_load_event(self, event: str, preset: Path, fade: bool) -> None:
		try:
			log_path = self.tauon.user_directory / "milkdrop-preset-load.log"
			timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
			previous = str(self.loaded_preset) if self.loaded_preset else ""
			exists = preset.is_file()
			size = preset.stat().st_size if exists else -1
			with log_path.open("a", encoding="utf-8") as file:
				file.write(
					f"{timestamp}\t{event}\tfade={fade}\texists={exists}\tsize={size}"
					f"\tprevious={previous}\tpreset={preset}\n"
				)
				file.flush()
				os.fsync(file.fileno())
		except Exception:
			logging.exception("Failed to write Milkdrop preset load log")

	def load_preset(self, preset: Path, fade: bool = False) -> None:
		self.log_preset_load_event("LOADING", preset, fade)
		self.loaded_preset = preset
		self.tauon.prefs.loaded_preset = preset
		logging.info(f"Loading preset: {preset.stem}")
		if not self.lib or not self.pm_instance:
			# Not initialised (visualiser off or unavailable); the preset is
			# remembered in prefs and loads on next init
			return
		self.prepare_opengl()
		self.lib.projectm_load_preset_file(self.pm_instance, str(preset).encode("utf-8"), fade)
		self.log_preset_load_event("LOADED_OK", preset, fade)
		self.auto_frames = 0
		self.timer.set()

	def render_frame(self, framebuffer=None) -> bool:
		"""Render a projectM frame"""
		if not self.pm_instance:
			return False

		if self.load_next:
			if self.load_next == "random":
				self.random_preset()
			else:
				self.load_preset(self.load_next)
			self.load_next = None

		just_faded = False
		fps = int(self.tauon.milky.fps.get())
		if fps and self.tauon.prefs.auto_milk and self.auto_frames > 30 * self.tauon.milky.fps.get():
			if self.timer.get() > 30:
				self.random_preset(fade=True)
				just_faded = True

		# if self.first_frame:
		# 	self.frame_timer.set()
		# 	self.lib.projectm_set_frame_time(self.pm_instance, 0.0)
		# 	self.first_frame = False
		# else:
		# 	t = self.frame_timer.get()
		# 	t = t * 1
		# 	self.lib.projectm_set_frame_time(self.pm_instance, t)

		# feed audio
		aud = self.tauon.aud
		f = aud.get_vis_side_buffer_fill()
		if f > 200:
			buffer_p = aud.get_vis_side_buffer()
			frames = f // 2
			if frames > self.pcm_max_samples:
				# Feed only the most recent samples; passing more than projectM's
				# internal PCM buffer holds overruns it and crashes. This is hit
				# at track start (buffer has filled) and sooner at high rates.
				offset = (frames - self.pcm_max_samples) * 2
				buffer_p = ctypes.cast(
					ctypes.addressof(buffer_p.contents) + offset * ctypes.sizeof(c_float),
					POINTER(c_float))
				frames = self.pcm_max_samples
			self.lib.projectm_pcm_add_float(self.pm_instance, buffer_p, frames, 2)
			aud.reset_vis_side_buffer()

		self.lib.projectm_set_window_size(self.pm_instance, int(self.tauon.gui.main_art_box[2]), int(self.tauon.gui.main_art_box[3]))
		#self.tauon.gui.delay_frame(0.016)

		if self.tauon.pctl.playing_state in (PlayingState.PLAYING, PlayingState.URL_STREAM) or just_faded:
			try:
				if not fps or fps < 1:
					fps = 1

				self.lib.projectm_set_fps(self.pm_instance, fps)
				if self.render_frame_fbo_available:
					self.lib.projectm_opengl_render_frame_fbo(self.pm_instance, framebuffer)
				else:
					saved_fbo = glGetIntegerv(GL_FRAMEBUFFER_BINDING)
					saved_viewport = glGetIntegerv(GL_VIEWPORT)
					try:
						if framebuffer is not None:
							glBindFramebuffer(GL_FRAMEBUFFER, framebuffer)
						glViewport(0, 0, int(self.tauon.gui.main_art_box[2]), int(self.tauon.gui.main_art_box[3]))
						self.lib.projectm_opengl_render_frame(self.pm_instance)
					finally:
						glBindFramebuffer(GL_FRAMEBUFFER, saved_fbo)
						glViewport(
							int(saved_viewport[0]),
							int(saved_viewport[1]),
							int(saved_viewport[2]),
							int(saved_viewport[3]),
						)
			except Exception as e:
				logging.warning(f"Error rendering frame: {e}")

			self.auto_frames += 1
		return True
class Milky:
	def __init__(self, tauon: _VisualApp) -> None:
		self.tauon:    _VisualApp = tauon
		self.pctl: Any = tauon.pctl
		self.gui:     GuiVar = tauon.gui
		self.ddt:      TDraw = tauon.ddt
		self.coll          = tauon.coll
		self.inp:      Input = tauon.inp
		self.renderer      = tauon.renderer
		self.ready: bool = False
		self.render_texture = None
		self.gl_texture_id = None
		self.framebuffer = None
		self.loaded_size = None
		self.fps = FPSCounter(window_size=10, min_update_interval=0.1, max_frame_time=0.5)
		self.cut_out_blend_mode = None  # composed lazily on first use (shader fallback)
		self._last_keyed = False  # whether the last real frame was blitted keyed (Cut Out shader)

		# Cut Out key pass: a GL shader copies the visualiser frame into a
		# second texture with alpha keyed from brightness, leaving the projectM
		# texture untouched (it feeds back into subsequent frames).
		self.key_texture_id = None
		self.key_framebuffer = None
		self.key_render_texture = None
		self.key_program = None
		self.key_vao = None
		self.key_failed: bool = False  # shader unavailable, use blend-mode fallback

		self.readback_buffer = None  # CPU frame buffer for the dedicated-context path

		self.projectm = ProjectM(tauon)

	@property
	def available(self) -> bool:
		"""False when PyOpenGL/libprojectM are missing or the renderer isn't OpenGL"""
		return milky_ready

	def burn(self, target_track: TrackClass) -> None:
		if not self.ready:
			return
		if not self.projectm.burn_texture_available:
			return
		if self.projectm.own_gl_context:
			# Burn needs the SDL renderer to draw into a GL-wrapped texture,
			# which can't be shared with projectM's dedicated context
			return

		w = int(self.tauon.gui.main_art_box[2])
		h = int(self.tauon.gui.main_art_box[3])

		sdl3.SDL_SetRenderTarget(self.renderer, self.render_texture)

		self.tauon.album_art_gen.display(target_track, (0, 0), (w, h), fast=False)
		sdl3.SDL_SetRenderTarget(self.renderer, self.gui.main_texture)

		sdl3.SDL_FlushRenderer(self.renderer)
		context = sdl3.SDL_GL_GetCurrentContext()
		sdl3.SDL_GL_MakeCurrent(self.tauon.t_window, context)
		saved_fbo = glGetIntegerv(GL_FRAMEBUFFER_BINDING)

		glBindFramebuffer(GL_FRAMEBUFFER, self.framebuffer)
		self.projectm.lib.projectm_opengl_burn_texture(self.projectm.pm_instance, self.gl_texture_id, 0, 0, w, h)

		glBindFramebuffer(GL_FRAMEBUFFER, 0)
		glBindTexture(GL_TEXTURE_2D, 0)
		glBindFramebuffer(GL_FRAMEBUFFER, saved_fbo)
		glFlush()
		glFinish()

	def render(self, discard: bool = False) -> None:
		if not milky_ready:
			# PyOpenGL missing, no libprojectM, or non-OpenGL renderer. prefs.milk
			# can still be set (stale config); rendering would NameError on the
			# module-level GL imports.
			return
		if self.projectm.lib_error is True:
			return

		ddt = self.ddt
		x = self.tauon.gui.main_art_box[0]
		y = self.tauon.gui.main_art_box[1]
		w = self.tauon.gui.main_art_box[2]
		h = self.tauon.gui.main_art_box[3]

		srect = sdl3.SDL_FRect(x, y, w, h)

		#print(f"OpenGL Version: {glGetString(GL_VERSION).decode()}")

		if not self.ready:
			saved_target = sdl3.SDL_GetRenderTarget(self.renderer)
			sdl3.SDL_SetRenderTarget(self.renderer, None)
			sdl3.SDL_FlushRenderer(self.renderer)
			context = sdl3.SDL_GL_GetCurrentContext()
			if not context:
				logging.error("Cannot initialize projectM: SDL has no current OpenGL context")
				sdl3.SDL_SetRenderTarget(self.renderer, saved_target)
				self.projectm.lib_error = True
				return
			# SDL may create or switch its GL context while submitting queued work.
			# Capture it after the flush and make it current immediately before
			# projectM creates GL resources; a stale context crashes Mesa here.
			if not sdl3.SDL_GL_MakeCurrent(self.tauon.t_window, context):
				logging.error(f"Cannot initialize projectM: {sdl3.SDL_GetError()}")
				sdl3.SDL_SetRenderTarget(self.renderer, saved_target)
				self.projectm.lib_error = True
				return
			saved_fbo_init = glGetIntegerv(GL_FRAMEBUFFER_BINDING)
			glBindFramebuffer(GL_FRAMEBUFFER, 0)
			self.projectm.load_library()
			self.projectm.init()
			glBindFramebuffer(GL_FRAMEBUFFER, saved_fbo_init)
			sdl3.SDL_SetRenderTarget(self.renderer, saved_target)
			if self.projectm.lib:
				self.ready = True
		if self.projectm.lib_error is True:
			return

		# Paused: re-blit the last rendered frame instead of asking projectM for a
		# fresh one. With playback paused there's no audio buffer driving it, so
		# projectM hands back an empty (transparent) frame — blitted opaque, that
		# punches a transparent hole through the segment. Re-showing the cached
		# texture keeps the visualiser frozen on a still frame instead.
		if not discard and self.tauon.pctl.playing_state == PlayingState.PAUSED \
				and self.render_texture is not None and self.loaded_size == (w, h):
			self._blit_still(srect)
			return

		if self.projectm.own_gl_context:
			self.render_readback(w, h, srect, discard)
			return

		sdl3.SDL_FlushRenderer(self.renderer)
		saved_fbo = glGetIntegerv(GL_FRAMEBUFFER_BINDING)

		if (w, h) != self.loaded_size:

			self.loaded_size = (w, h)
			sdl3.SDL_ClearError()
			context = sdl3.SDL_GL_GetCurrentContext()
			sdl3.SDL_GL_MakeCurrent(self.tauon.t_window, context)

			if self.render_texture:
				sdl3.SDL_DestroyTexture(self.render_texture)
				glDeleteTextures(1, [self.gl_texture_id])
				glDeleteFramebuffers(1, [self.framebuffer])
			if self.key_render_texture:
				sdl3.SDL_DestroyTexture(self.key_render_texture)
				glDeleteTextures(1, [self.key_texture_id])
				glDeleteFramebuffers(1, [self.key_framebuffer])
				self.key_render_texture = None
				self.key_texture_id = None
				self.key_framebuffer = None

			gl_texture_id = glGenTextures(1)
			glBindTexture(GL_TEXTURE_2D, gl_texture_id)
			self.gl_texture_id = gl_texture_id

			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

			glTexImage2D(
				GL_TEXTURE_2D, 0, GL_RGBA, int(w), int(h), 0, GL_RGBA, GL_UNSIGNED_BYTE, None)

			# Step 3: Create framebuffer for rendering
			self.framebuffer = glGenFramebuffers(1)
			glBindFramebuffer(GL_FRAMEBUFFER, self.framebuffer)
			glFramebufferTexture2D(
				GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, gl_texture_id, 0)

			# Check framebuffer completeness
			if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
				print("Framebuffer not complete!")

			glBindFramebuffer(GL_FRAMEBUFFER, 0)
			glBindTexture(GL_TEXTURE_2D, 0)

			props = sdl3.SDL_CreateProperties()
			# Set properties to wrap the OpenGL texture
			sdl3.SDL_SetNumberProperty(props, sdl3.SDL_PROP_TEXTURE_CREATE_OPENGL_TEXTURE_NUMBER, gl_texture_id)
			sdl3.SDL_SetNumberProperty(props, sdl3.SDL_PROP_TEXTURE_CREATE_WIDTH_NUMBER, int(w))
			sdl3.SDL_SetNumberProperty(props, sdl3.SDL_PROP_TEXTURE_CREATE_HEIGHT_NUMBER, int(h))
			#sdl3.SDL_SetNumberProperty(props, sdl3.SDL_PROP_TEXTURE_CREATE_FORMAT_NUMBER, sdl3.SDL_PIXELFORMAT_RGBA8888)
			sdl3.SDL_SetNumberProperty(props, sdl3.SDL_PROP_TEXTURE_CREATE_ACCESS_NUMBER, sdl3.SDL_TEXTUREACCESS_TARGET)

			# Create SDL texture from the OpenGL texture
			self.render_texture = sdl3.SDL_CreateTextureWithProperties(self.renderer, props)

		if self.projectm.render_frame_fbo_available:
			sdl3.SDL_FlushRenderer(self.renderer)
			glBindFramebuffer(GL_FRAMEBUFFER, self.framebuffer)
			self.projectm.render_frame(self.framebuffer)
		else:
			current_target = sdl3.SDL_GetRenderTarget(self.renderer)
			sdl3.SDL_SetRenderTarget(self.renderer, None)
			sdl3.SDL_FlushRenderer(self.renderer)
			glBindFramebuffer(GL_FRAMEBUFFER, 0)
			self.projectm.render_frame()
			glBindTexture(GL_TEXTURE_2D, self.gl_texture_id)
			glCopyTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, 0, 0, int(w), int(h))
			glBindTexture(GL_TEXTURE_2D, 0)
			glClearColor(0.0, 0.0, 0.0, 0.0)
			glClear(GL_COLOR_BUFFER_BIT)
			sdl3.SDL_SetRenderTarget(self.renderer, current_target)

		# Cut Out: run the key shader over the fresh frame. It samples the
		# projectM texture (read-only — projectM feeds it back into subsequent
		# frames) and writes a copy with alpha keyed from brightness into
		# key_texture_id, which is blitted below instead.
		keyed = False
		if not discard and self.tauon.prefs.milk_cut_out and not self.key_failed:
			keyed = self._run_key_pass(w, h)
		if not discard:
			self._last_keyed = keyed  # remembered so a paused re-blit picks the right texture

		glBindFramebuffer(GL_FRAMEBUFFER, saved_fbo)
		glFlush()
		glFinish()
		if not discard:
			if keyed:
				# The shader writes straight (unmultiplied) colour with a
				# luminance alpha; premultiplied "over" keeps the visualiser's
				# own brightness while black fades to the album art beneath.
				sdl3.SDL_SetTextureBlendMode(self.key_render_texture, sdl3.SDL_BLENDMODE_BLEND_PREMULTIPLIED)
				sdl3.SDL_RenderTexture(self.renderer, self.key_render_texture, None, srect)
			else:
				if self.tauon.prefs.milk_cut_out:
					# Shader unavailable: approximate the key in fixed function.
					sdl3.SDL_SetTextureBlendMode(self.render_texture, self._ensure_cut_out_blend())
				else:
					sdl3.SDL_SetTextureBlendMode(self.render_texture, sdl3.SDL_BLENDMODE_NONE)
				sdl3.SDL_RenderTexture(self.renderer, self.render_texture, None, srect)
		self.fps.tick()

	def _ensure_cut_out_blend(self):
		"""Lazily compose the fixed-function Cut Out blend (shader fallback):
		out = src * src + dst * (1 - src) — the source colour acts as its own
		per-channel matte."""
		if self.cut_out_blend_mode is None:
			self.cut_out_blend_mode = sdl3.SDL_ComposeCustomBlendMode(
				sdl3.SDL_BLENDFACTOR_SRC_COLOR,
				sdl3.SDL_BLENDFACTOR_ONE_MINUS_SRC_COLOR,
				sdl3.SDL_BLENDOPERATION_ADD,
				sdl3.SDL_BLENDFACTOR_ZERO,
				sdl3.SDL_BLENDFACTOR_ONE,
				sdl3.SDL_BLENDOPERATION_ADD)
		return self.cut_out_blend_mode

	def _blit_still(self, srect) -> None:
		"""Re-blit the last rendered visualiser frame (used while paused) without
		asking projectM for a new one. Mirrors the blend selection of the two
		render paths' blits so a paused frame looks identical to a live one."""
		if self.projectm.own_gl_context:
			# Readback path always blits render_texture (no shader key), flipped.
			if self.tauon.prefs.milk_cut_out:
				sdl3.SDL_SetTextureBlendMode(self.render_texture, self._ensure_cut_out_blend())
			else:
				sdl3.SDL_SetTextureBlendMode(self.render_texture, sdl3.SDL_BLENDMODE_NONE)
			sdl3.SDL_RenderTextureRotated(
				self.renderer, self.render_texture, None, srect, 0.0, None, sdl3.SDL_FLIP_VERTICAL)
			return
		if self._last_keyed and self.key_render_texture is not None:
			sdl3.SDL_SetTextureBlendMode(self.key_render_texture, sdl3.SDL_BLENDMODE_BLEND_PREMULTIPLIED)
			sdl3.SDL_RenderTexture(self.renderer, self.key_render_texture, None, srect)
		else:
			if self.tauon.prefs.milk_cut_out:
				sdl3.SDL_SetTextureBlendMode(self.render_texture, self._ensure_cut_out_blend())
			else:
				sdl3.SDL_SetTextureBlendMode(self.render_texture, sdl3.SDL_BLENDMODE_NONE)
			sdl3.SDL_RenderTexture(self.renderer, self.render_texture, None, srect)

	def render_readback(self, w, h, srect, discard: bool = False) -> None:
		"""Dedicated-context path (macOS): projectM renders into an FBO in its
		own core profile GL context, and the frame is read back to CPU and
		uploaded to a streaming SDL texture, since GL textures can't be shared
		between a core context and the renderer's 2.1 compatibility context."""
		pm = self.projectm
		sdl3.SDL_FlushRenderer(self.renderer)

		if (w, h) != self.loaded_size:
			self.loaded_size = (w, h)

			if self.render_texture:
				sdl3.SDL_DestroyTexture(self.render_texture)
			self.render_texture = sdl3.SDL_CreateTexture(
				self.renderer, sdl3.SDL_PIXELFORMAT_RGBA32,
				sdl3.SDL_TEXTUREACCESS_STREAMING, int(w), int(h))
			self.readback_buffer = (ctypes.c_ubyte * (int(w) * int(h) * 4))()

			pm.make_own_context_current()
			if self.gl_texture_id:
				glDeleteTextures(1, [self.gl_texture_id])
				glDeleteFramebuffers(1, [self.framebuffer])

			self.gl_texture_id = glGenTextures(1)
			glBindTexture(GL_TEXTURE_2D, self.gl_texture_id)
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
			glTexImage2D(
				GL_TEXTURE_2D, 0, GL_RGBA, int(w), int(h), 0, GL_RGBA, GL_UNSIGNED_BYTE, None)

			self.framebuffer = glGenFramebuffers(1)
			glBindFramebuffer(GL_FRAMEBUFFER, self.framebuffer)
			glFramebufferTexture2D(
				GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.gl_texture_id, 0)
			if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
				logging.error("projectM framebuffer not complete")
			glBindFramebuffer(GL_FRAMEBUFFER, 0)
			glBindTexture(GL_TEXTURE_2D, 0)
		else:
			pm.make_own_context_current()

		try:
			pm.render_frame(self.framebuffer)

			glBindFramebuffer(GL_FRAMEBUFFER, self.framebuffer)
			glPixelStorei(GL_PACK_ALIGNMENT, 1)
			glReadPixels(0, 0, int(w), int(h), GL_RGBA, GL_UNSIGNED_BYTE, self.readback_buffer)
			glBindFramebuffer(GL_FRAMEBUFFER, 0)
			glFlush()
		finally:
			pm.restore_renderer_context()

		if not discard:
			sdl3.SDL_UpdateTexture(
				self.render_texture, None,
				ctypes.cast(self.readback_buffer, ctypes.c_void_p), int(w) * 4)
			if self.tauon.prefs.milk_cut_out:
				sdl3.SDL_SetTextureBlendMode(self.render_texture, self._ensure_cut_out_blend())
			else:
				sdl3.SDL_SetTextureBlendMode(self.render_texture, sdl3.SDL_BLENDMODE_NONE)
			# GL frames are bottom-up relative to SDL
			sdl3.SDL_RenderTextureRotated(
				self.renderer, self.render_texture, None, srect, 0.0, None, sdl3.SDL_FLIP_VERTICAL)
		self.fps.tick()

	# ------------------------------------------------- Cut Out key pass

	# Fullscreen-triangle vertex stage (no vertex buffer needed) + a fragment
	# stage that keys out blacks and greys only: neutral pixels fade by
	# brightness, but any hint of chroma (max - min channel) makes the pixel
	# opaque even at low luminance, so dim coloured content still covers the
	# art. Narrow smoothstep ramps keep the key edges from shimmering.
	KEY_VERTEX_SRC = """
	#version 330 core
	out vec2 uv;
	void main() {
		vec2 p = vec2(float((gl_VertexID << 1) & 2), float(gl_VertexID & 2));
		uv = p;
		gl_Position = vec4(p * 2.0 - 1.0, 0.0, 1.0);
	}
	"""

	KEY_FRAGMENT_SRC = """
	#version 330 core
	in vec2 uv;
	out vec4 frag;
	uniform sampler2D tex;
	void main() {
		vec3 c = texture(tex, uv).rgb;
		float hi = max(c.r, max(c.g, c.b));
		float chroma = hi - min(c.r, min(c.g, c.b));
		float a = max(smoothstep(0.01, 0.20, hi), smoothstep(0.02, 0.06, chroma));
		frag = vec4(c, a);
	}
	"""

	def _init_key_program(self) -> bool:
		"""Compile the key shader once. On any failure mark key_failed so render
		falls back to the fixed-function blend approximation."""
		if self.key_program is not None:
			return True
		try:
			program = glCreateProgram()
			for source, kind in ((self.KEY_VERTEX_SRC, GL_VERTEX_SHADER), (self.KEY_FRAGMENT_SRC, GL_FRAGMENT_SHADER)):
				shader = glCreateShader(kind)
				glShaderSource(shader, source)
				glCompileShader(shader)
				if not glGetShaderiv(shader, GL_COMPILE_STATUS):
					raise RuntimeError(f"Shader compile failed: {glGetShaderInfoLog(shader)}")
				glAttachShader(program, shader)
				glDeleteShader(shader)
			glLinkProgram(program)
			if not glGetProgramiv(program, GL_LINK_STATUS):
				raise RuntimeError(f"Shader link failed: {glGetProgramInfoLog(program)}")
			# Core profiles require a bound VAO to draw, even with no attributes
			self.key_vao = glGenVertexArrays(1)
			glUseProgram(program)
			glUniform1i(glGetUniformLocation(program, "tex"), 0)
			glUseProgram(0)
			self.key_program = program
			return True
		except Exception:
			logging.exception("Failed to build Milkdrop key shader, using blend-mode fallback")
			self.key_failed = True
			return False

	def _ensure_key_target(self, w: int | float, h: int | float) -> bool:
		"""Create the keyed copy's texture + framebuffer + SDL wrapper at the
		current size (torn down with the main target on resize)."""
		if self.key_render_texture:
			return True
		try:
			self.key_texture_id = glGenTextures(1)
			glBindTexture(GL_TEXTURE_2D, self.key_texture_id)
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
			glTexImage2D(
				GL_TEXTURE_2D, 0, GL_RGBA, int(w), int(h), 0, GL_RGBA, GL_UNSIGNED_BYTE, None)
			self.key_framebuffer = glGenFramebuffers(1)
			glBindFramebuffer(GL_FRAMEBUFFER, self.key_framebuffer)
			glFramebufferTexture2D(
				GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.key_texture_id, 0)
			complete = glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE
			glBindFramebuffer(GL_FRAMEBUFFER, 0)
			glBindTexture(GL_TEXTURE_2D, 0)
			if not complete:
				raise RuntimeError("Key framebuffer not complete")

			props = sdl3.SDL_CreateProperties()
			sdl3.SDL_SetNumberProperty(props, sdl3.SDL_PROP_TEXTURE_CREATE_OPENGL_TEXTURE_NUMBER, self.key_texture_id)
			sdl3.SDL_SetNumberProperty(props, sdl3.SDL_PROP_TEXTURE_CREATE_WIDTH_NUMBER, int(w))
			sdl3.SDL_SetNumberProperty(props, sdl3.SDL_PROP_TEXTURE_CREATE_HEIGHT_NUMBER, int(h))
			sdl3.SDL_SetNumberProperty(props, sdl3.SDL_PROP_TEXTURE_CREATE_ACCESS_NUMBER, sdl3.SDL_TEXTUREACCESS_TARGET)
			self.key_render_texture = sdl3.SDL_CreateTextureWithProperties(self.renderer, props)
			if not self.key_render_texture:
				raise RuntimeError(f"SDL_CreateTextureWithProperties failed: {sdl3.SDL_GetError()}")
			return True
		except Exception:
			logging.exception("Failed to create Milkdrop key target, using blend-mode fallback")
			self.key_failed = True
			return False

	def _run_key_pass(self, w: int | float, h: int | float) -> bool:
		"""Render the keyed copy. Caller restores the framebuffer binding; all
		other touched GL state is saved and restored here."""
		if not self._init_key_program() or not self._ensure_key_target(w, h):
			return False
		saved_viewport = glGetIntegerv(GL_VIEWPORT)
		saved_program = glGetIntegerv(GL_CURRENT_PROGRAM)
		saved_vao = glGetIntegerv(GL_VERTEX_ARRAY_BINDING)
		saved_active = glGetIntegerv(GL_ACTIVE_TEXTURE)
		blend_was_on = glIsEnabled(GL_BLEND)
		try:
			glBindFramebuffer(GL_FRAMEBUFFER, self.key_framebuffer)
			glViewport(0, 0, int(w), int(h))
			glDisable(GL_BLEND)
			glUseProgram(self.key_program)
			glBindVertexArray(self.key_vao)
			glActiveTexture(GL_TEXTURE0)
			glBindTexture(GL_TEXTURE_2D, self.gl_texture_id)
			glDrawArrays(GL_TRIANGLES, 0, 3)
			glBindTexture(GL_TEXTURE_2D, 0)
			return True
		except Exception:
			logging.exception("Milkdrop key pass failed, using blend-mode fallback")
			self.key_failed = True
			return False
		finally:
			glBindVertexArray(int(saved_vao))
			glUseProgram(int(saved_program))
			glActiveTexture(int(saved_active))
			if blend_was_on:
				glEnable(GL_BLEND)
			glViewport(
				int(saved_viewport[0]),
				int(saved_viewport[1]),
				int(saved_viewport[2]),
				int(saved_viewport[3]),
			)
class MilkPresetChooser:
	"""Full-screen Milkdrop preset picker (the MilkDrop menu's "Choose Preset").

	Lists every scanned preset as compact labels in top-to-bottom columns over
	a translucent backdrop (same look as the search overlay). Clicking a label
	loads that preset; clicking the backdrop, Escape or right-click closes.
	Favorited presets get a gold star in the label gutter. The mouse wheel
	scrolls whole columns when there are more than fit the window.

	Input never leaks to the UI underneath: handle_input runs early in the
	frame (dream-room style), captures the pointer state for the overlay and
	then mutes it, so every other component sees no clicks and an off-screen
	cursor. It can run more than once per frame (event + motion passes), so it
	only latches state; render() consumes the latched click/wheel.
	"""

	def __init__(self, tauon: _VisualApp) -> None:
		self.tauon: _VisualApp = tauon
		self.gui:  GuiVar = tauon.gui
		self.inp:   Input = tauon.inp
		self.ddt:   TDraw = tauon.ddt
		self.active: bool = False
		self.scroll_cols: int = 0
		self._presets: list[Path] = []  # alphabetical snapshot taken on activate
		self._mouse: tuple[float, float] = (-1.0, -1.0)
		self._click: bool = False
		self._wheel: float = 0.0

	def activate(self) -> None:
		pm = self.tauon.milky.projectm
		if not pm.presets:
			pm.rescan_presets()
		if not pm.presets:
			self.tauon.show_message(_("No Milkdrop presets found"))
			return
		self._presets = sorted(pm.presets, key=lambda p: p.stem.casefold())
		self.active = True
		self.scroll_cols = 0
		self._click = False
		self._wheel = 0.0
		self._mouse = (self.inp.mouse_position[0], self.inp.mouse_position[1])
		self.gui.request_frame()

	def close(self) -> None:
		self.active = False
		self._click = False
		self._wheel = 0.0
		self.gui.request_frame()

	def handle_input(self) -> None:
		if not self.active:
			return
		inp = self.inp
		if inp.key_esc_press:
			inp.key_esc_press = False
			self.close()
			return
		if inp.right_click:
			self.close()
		if inp.mouse_position[0] > -2000:
			self._mouse = (inp.mouse_position[0], inp.mouse_position[1])
		if inp.mouse_click:
			self._click = True
		self._wheel += inp.mouse_wheel
		inp.mouse_click = False
		inp.d_mouse_click = False
		inp.right_click = False
		inp.middle_click = False
		inp.mouse_wheel = 0
		inp.input_text = ""
		inp.mouse_position[0] = -3000.0
		inp.mouse_position[1] = -3000.0

	def render(self) -> None:
		if not self.active:
			return
		gui = self.gui
		ddt = self.ddt
		pm = self.tauon.milky.projectm
		presets = self._presets
		if not presets:
			self.close()
			return

		w = self.tauon.window_size[0]
		h = self.tauon.window_size[1]
		ddt.rect((0, 0, w, h), ColourRGBA(3, 3, 3, 235))
		ddt.text_background_colour = ColourRGBA(12, 12, 12, 255)

		pad = round(12 * gui.scale)
		row_h = round(13 * gui.scale)
		col_w = round(150 * gui.scale)
		star_w = ddt.get_text_w("★", 10) + round(4 * gui.scale)  # label gutter, keeps columns aligned
		rows = max(1, (h - pad * 2) // row_h)
		n_cols = -(-len(presets) // rows)  # ceil
		vis_cols = max(1, (w - pad) // col_w)

		if self._wheel:
			self.scroll_cols -= int(self._wheel)
			self._wheel = 0.0
		self.scroll_cols = max(0, min(self.scroll_cols, max(0, n_cols - vis_cols)))

		mx, my = self._mouse
		click = self._click
		self._click = False
		on_label = False

		favorites = self.tauon.prefs.milk_favorite_presets
		text_colour = ColourRGBA(200, 200, 200, 255)
		hover_colour = ColourRGBA(255, 255, 255, 255)
		gold = ColourRGBA(244, 209, 66, 255)

		for col in range(vis_cols):
			start = (self.scroll_cols + col) * rows
			if start >= len(presets):
				break
			x = pad + col * col_w
			for row, preset in enumerate(presets[start:start + rows]):
				y = pad + row * row_h
				rect = (x, y, col_w - round(6 * gui.scale), row_h)
				hover = rect[0] <= mx < rect[0] + rect[2] and rect[1] <= my < rect[1] + rect[3]
				# Hover highlight: just brighten the label text
				if preset == pm.loaded_preset:
					colour = ColourRGBA(255, 230, 120, 255) if hover else gold
				else:
					colour = hover_colour if hover else text_colour
				if str(preset) in favorites:
					ddt.text((x + 1, y - round(1 * gui.scale)), "★", gold, 10)
				ddt.text(
					(x + star_w, y - round(1 * gui.scale)), preset.stem, colour, 10,
					max_w=rect[2] - star_w - round(4 * gui.scale))
				if click and hover:
					pm.load_next = preset
					on_label = True
					self.close()
		if click and not on_label:
			self.close()
class Showcase:
	def __init__(self, tauon: _VisualApp, timed_lyrics_edit: _VisualLyrics) -> None:
		self.tauon:                       _VisualApp = tauon
		self.inp:                         Input = tauon.inp
		self.gui:                        GuiVar = tauon.gui
		self.ddt:                         TDraw = tauon.ddt
		self.coll                               = tauon.coll
		self.pctl:                    Any = tauon.pctl
		self.prefs:                       Prefs = tauon.prefs
		self.colours:              ColoursClass = tauon.colours
		self.renderer                           = tauon.renderer
		self.lyrics_ren:              Any = tauon.lyrics_ren
		self.window_size:             list[int] = tauon.window_size
		self.guitar_chords:        GuitarChords = tauon.guitar_chords
		self.showcase_view_menu:           Menu = tauon.showcase_view_menu
		self.smooth_scroll:        Any = tauon.smooth_scroll
		self.timed_lyrics_edit: _VisualLyrics = timed_lyrics_edit
		#self.lastfm_artist = None
		self.artist_mode: bool = False

	def render(self) -> None:
		if self.gui.timed_lyrics_edit_view:
			self.timed_lyrics_edit.render()
			return

		self.gui.timed_lyrics_editing_now = False
		self.timed_lyrics_edit.continuous = False
		box = int(self.window_size[1] * 0.4 + 120 * self.gui.scale)
		box = min(self.window_size[0] // 2, box)

		wide_art = self.prefs.showcase_wide_art and self.window_size[0] >= 500 * self.gui.scale
		hide_art = False
		if self.window_size[0] < 900 * self.gui.scale and not wide_art:
			hide_art = True

		x = int(self.window_size[0] * 0.15)
		y = int((self.window_size[1] / 2) - (box / 2)) - 10 * self.gui.scale

		if hide_art:
			box = 45 * self.gui.scale
		elif self.window_size[1] / self.window_size[0] > 0.7:
			x = int(self.window_size[0] * 0.07)

		bbg = rgb_add_hls(self.colours.lyrics_panel_background, 0, 0.05, 0)  # [255, 255, 255, 18]
		bfg = rgb_add_hls(self.colours.lyrics_panel_background, 0, 0.09, 0)  # [255, 255, 255, 30]
		bft = self.colours.grey(235)
		bbt = self.colours.grey(200)

		t1 = self.colours.grey(250)

		self.gui.vis_4_colour = None
		self.gui.draw_vis4_top = False
		light_mode = False
		if self.colours.lm:
			bbg = self.colours.vis_colour
			bfg = alpha_blend(ColourRGBA(255, 255, 255, 60), self.colours.vis_colour)
			bft = self.colours.grey(250)
			bbt = self.colours.grey(245)

		if test_lumi(self.colours.lyrics_panel_background) < 0.7:
			light_mode = True
			t1 = self.colours.grey(30)
			self.gui.vis_4_colour = ColourRGBA(40, 40, 40, 255)

		self.ddt.rect((0, self.gui.panelY, self.window_size[0], self.window_size[1] - self.gui.panelY), self.colours.lyrics_panel_background)

		# if not self.prefs.shuffle_lock:
		# 	if draw.button(_("Return"), 25 * self.gui.scale, self.window_size[1] - self.gui.panelBY - 40 * self.gui.scale,
		# 			text_highlight_colour=bft, text_colour=bbt, backgound_colour=bbg,
		# 			background_highlight_colour=bfg):
		# 		self.gui.switch_showcase_off = True
		# 		self.gui.update += 1
		# 		self.gui.update_layout = True

		# self.ddt.force_gray = True

		if self.pctl.playing_state == PlayingState.URL_STREAM and not self.tauon.radiobox.dummy_track.title:
			if not self.pctl.tag_meta:
				y = int(self.window_size[1] / 2) - 60 - self.gui.scale
				self.ddt.text((self.window_size[0] // 2, y, 2), self.pctl.url, self.colours.side_bar_line2, 317)
			else:
				w = self.window_size[0] - (x + box) - 30 * self.gui.scale
				x = int((self.window_size[0]) / 2)

				y = int(self.window_size[1] / 2) - 60 - self.gui.scale
				self.ddt.text((x, y, 2), self.pctl.tag_meta, self.colours.side_bar_line1, 216, w)
		else:
			if len(self.pctl.track_queue) < 1:
				self.ddt.alpha_bg = False
				return

			# if self.pctl.draw.button("Return", 20, self.gui.panelY + 5, bg=colours.grey(30)):
			# 	pass

			if self.gui.force_showcase_index >= 0:
				if self.pctl.draw.button(
					_("Playing"), 25 * self.gui.scale, self.gui.panelY + 20 * self.gui.scale, text_highlight_colour=bft,
					text_colour=bbt, background_colour=bbg, background_highlight_colour=bfg):
					self.gui.force_showcase_index = -1
					self.ddt.force_gray = False

			if self.gui.force_showcase_index >= 0:
				index = self.gui.force_showcase_index
				track = self.pctl.master_library[index]
			elif self.pctl.playing_state == PlayingState.URL_STREAM:
				track = self.tauon.radiobox.dummy_track
			else:
				index = self.pctl.track_queue[self.pctl.queue_step]
				track = self.pctl.master_library[index]

			if wide_art:
				available_h = self.window_size[1] - self.gui.panelY - self.gui.panelBY
				box_w = min(round(self.window_size[0] * 0.756), round(954 * self.gui.scale))
				box_w = max(round(280 * self.gui.scale), box_w)
				box_h = round(box_w * 0.45)
				max_box_h = max(round(160 * self.gui.scale), available_h - round(150 * self.gui.scale))
				if box_h > max_box_h:
					box_h = max_box_h
					box_w = round(box_h / 0.45)
				x = round((self.window_size[0] - box_w) / 2)
				y = round(self.gui.panelY + max(round(22 * self.gui.scale), (available_h - box_h - round(108 * self.gui.scale)) / 2))
				draw_showcase_art_box(self.tauon, track, x, y, box_w, box_h)

				meta_gap = round(34 * self.gui.scale)
				meta_block_h = round(78 * self.gui.scale)
				meta_area_top = y + box_h + meta_gap
				meta_area_bottom = self.window_size[1] - self.gui.panelBY - round(14 * self.gui.scale)
				meta_y = meta_area_top
				if meta_area_bottom > meta_area_top + meta_block_h:
					meta_y = round(meta_area_top + ((meta_area_bottom - meta_area_top - meta_block_h) / 2))
				meta_w = min(box_w, self.window_size[0] - round(60 * self.gui.scale))
				meta_x = round(self.window_size[0] / 2)
				title = clean_string(track.filename) if track.title == "" else track.title
				self.ddt.text((meta_x, meta_y, 2), title, t1, 219, meta_w)
				meta_y += round(32 * self.gui.scale)
				if track.artist:
					self.ddt.text((meta_x, meta_y, 2), track.artist, alpha_mod(t1, 210), 316, meta_w)
					meta_y += round(23 * self.gui.scale)
				if track.album:
					album_line = track.album
					if track.date:
						album_line = f"{album_line} - {track.date}"
					self.ddt.text((meta_x, meta_y, 2), album_line, alpha_mod(t1, 160), 14, meta_w)
				elif track.date:
					self.ddt.text((meta_x, meta_y, 2), track.date, alpha_mod(t1, 160), 14, meta_w)
				self.gui.showed_title = True
				self.ddt.alpha_bg = False
				self.ddt.force_gray = False
				return

			if not hide_art:
				draw_showcase_art_box(self.tauon, track, x, y, box)

			# Check for lyrics if auto setting
			self.tauon.test_auto_lyrics(track)

			self.gui.draw_vis4_top = False

			if self.gui.panelY < self.inp.mouse_position[1] < self.window_size[1] - self.gui.panelBY:
				if self.inp.mouse_wheel != 0:
					scroll_distance = self.smooth_scroll.scroll("showcase", 35*self.gui.scale)
					self.lyrics_ren.lyrics_position += scroll_distance
				if self.inp.right_click:
					# track = self.pctl.playing_object()
					if track is not None:
						self.showcase_view_menu.activate(track)

			gcx = x + box + int(self.window_size[0] * 0.15) + 10 * self.gui.scale
			gcx -= 100 * self.gui.scale
			# TODO (Flynn): work out the logic for full size static lyrics generating
			timed_ready = False
			if True and self.prefs.show_lyrics_showcase:
				timed_ready = self.tauon.timed_lyrics_ren.generate(track)

			if timed_ready and track.lyrics:
				# if not self.prefs.guitar_chords or self.guitar_chords.test_ready_status(track) != 1:
				# 	line = _("Prefer synced")
				# 	if self.prefs.prefer_synced_lyrics:
				# 		line = _("Prefer static")
				# 	if self.pctl.draw.button(line, 25 * self.gui.scale, self.window_size[1] - self.gui.panelBY - 70 * self.gui.scale,
				# 			text_highlight_colour=bft, text_colour=bbt, background_colour=bbg,
				# 			background_highlight_colour=bfg):
				# 		self.prefs.prefer_synced_lyrics ^= True

				timed_ready = self.prefs.prefer_synced_lyrics

			if self.prefs.guitar_chords and track.title and self.prefs.show_lyrics_showcase and self.guitar_chords.render(track, gcx, y):
				if not self.guitar_chords.auto_scroll:
					if self.pctl.draw.button(
						_("Auto-Scroll"), 25 * self.gui.scale, self.window_size[1] - self.gui.panelBY - 70 * self.gui.scale,
						text_highlight_colour=bft, text_colour=bbt, background_colour=bbg,
						background_highlight_colour=bfg):
						self.guitar_chords.auto_scroll = True
			elif True and self.prefs.show_lyrics_showcase and timed_ready:
				w = self.window_size[0] - (x + box) - round(30 * self.gui.scale)
				h = (self.window_size[1] - self.gui.panelBY) - self.gui.panelY
				self.tauon.timed_lyrics_ren.render(track.index, gcx, y, w=w, h=h)
			elif track.lyrics == "" or not self.prefs.show_lyrics_showcase:
				w = self.window_size[0] - (x + box) - round(30 * self.gui.scale)
				x = int(x + box + (self.window_size[0] - x - box) / 2)

				if hide_art:
					x = self.window_size[0] // 2

				# x = int((self.window_size[0]) / 2)
				y = int(self.window_size[1] / 2) - round(60 * self.gui.scale)

				if track.artist == "" and track.title == "":
					self.ddt.text((x, y, 2), clean_string(track.filename), t1, 216, w)
				else:
					self.ddt.text((x, y, 2), track.artist, t1, 20, w)
					y += round(48 * self.gui.scale)

					if self.window_size[0] < 700 * self.gui.scale:
						if len(track.title) < 30:
							self.ddt.text((x, y, 2), track.title, t1, 220, w)
						elif len(track.title) < 40:
							self.ddt.text((x, y, 2), track.title, t1, 217, w)
						else:
							self.ddt.text((x, y, 2), track.title, t1, 213, w)

					elif len(track.title) < 35:
						self.ddt.text((x, y, 2), track.title, t1, 220, w)
					elif len(track.title) < 50:
						self.ddt.text((x, y, 2), track.title, t1, 219, w)
					else:
						self.ddt.text((x, y, 2), track.title, t1, 216, w)

				self.gui.spec4_rec.x = x - (self.gui.spec4_rec.w // 2)
				self.gui.spec4_rec.y = y + round(50 * self.gui.scale)

				if self.prefs.showcase_vis and self.window_size[1] > 369 and not self.tauon.search_over.active \
				and self.pctl.playing_state != PlayingState.URL_STREAM:
					if self.gui.message_box or not self.tauon.is_level_zero(include_menus=True):
						self.render_vis()
					else:
						self.gui.draw_vis4_top = True
			else:
				x += box + int(self.window_size[0] * 0.15) + 10 * self.gui.scale
				x -= 100 * self.gui.scale
				w = self.window_size[0] - x - 30 * self.gui.scale

				if self.inp.key_up_press and not (self.inp.key_ctrl_down or self.inp.key_shift_down or self.inp.key_shiftr_down):
					self.lyrics_ren.lyrics_position += 35 * self.gui.scale
				if self.inp.key_down_press and not (self.inp.key_ctrl_down or self.inp.key_shift_down or self.inp.key_shiftr_down):
					self.lyrics_ren.lyrics_position -= 35 * self.gui.scale

				self.lyrics_ren.test_update(track)
				tw, th = self.ddt.get_text_wh(self.lyrics_ren.text + "\n", 17, w, True)

				self.lyrics_ren.lyrics_position = max(self.lyrics_ren.lyrics_position, th * -1 + 100 * self.gui.scale)
				self.lyrics_ren.lyrics_position = min(self.lyrics_ren.lyrics_position, 70 * self.gui.scale)

				self.lyrics_ren.render(
					x,
					y + self.lyrics_ren.lyrics_position,
					w,
					int(self.window_size[1] - 100 * self.gui.scale),
					0)

		self.ddt.alpha_bg = False
		self.ddt.force_gray = False

	def render_vis(self, top: bool = False) -> None:
		sdl3.SDL_SetRenderTarget(self.renderer, self.gui.spec4_tex)
		sdl3.SDL_SetRenderDrawColor(self.renderer, 0, 0, 0, 0)
		sdl3.SDL_RenderClear(self.renderer)

		bx = 0
		by = 50 * self.gui.scale

		if self.gui.vis_4_colour is not None:
			sdl3.SDL_SetRenderDrawColor(
				self.renderer, self.gui.vis_4_colour.r, self.gui.vis_4_colour.g, self.gui.vis_4_colour.b, self.gui.vis_4_colour.a)

		if (self.pctl.playing_time < 0.5 and (self.pctl.playing_state in (PlayingState.PLAYING, PlayingState.URL_STREAM))) or (
				self.pctl.playing_state == PlayingState.STOPPED and self.gui.spec4_array.count(0) != len(self.gui.spec4_array)):
			self.gui.request_frame()
			self.gui.level_update = True

			for i in range(len(self.gui.spec4_array)):
				self.gui.spec4_array[i] -= 0.1
				self.gui.spec4_array[i] = max(self.gui.spec4_array[i], 0)

		if not top and (self.pctl.playing_state in (PlayingState.PLAYING, PlayingState.URL_STREAM)):
			self.gui.request_frame()

		slide = 0.7
		for i, bar in enumerate(self.gui.spec4_array):

			# We won't draw higher bars that may not move
			if i > 40:
				break

			# Scale input amplitude to pixel distance (Applying a slight exponentional)
			dis = (2 + math.pow(bar / (2 + slide), 1.5))
			slide -= 0.03  # Set a slight bias for higher bars

			# Define colour for bar
			if self.gui.vis_4_colour is None:
				self.tauon.set_colour(
					hsl_to_rgb(
						0.7 + min(0.15, (bar / 150)) + self.pctl.total_playtime / 300, min(0.9, 0.7 + (dis / 300)),
						min(0.9, 0.7 + (dis / 600))))

			# Define bar size and draw
			self.gui.bar4.x = int(bx)
			self.gui.bar4.y = round(by - dis * self.gui.scale)
			self.gui.bar4.w = round(2 * self.gui.scale)
			self.gui.bar4.h = round(dis * 2 * self.gui.scale)

			sdl3.SDL_RenderFillRect(self.renderer, self.gui.bar4)

			# Set distance between bars
			bx += 8 * self.gui.scale

		if top:
			sdl3.SDL_SetRenderTarget(self.renderer, None)
		else:
			sdl3.SDL_SetRenderTarget(self.renderer, self.gui.main_texture)

		# sdl3.SDL_SetRenderDrawBlendMode(self.renderer, sdl3.SDL_BLENDMODE_BLEND)
		sdl3.SDL_RenderTexture(self.renderer, self.gui.spec4_tex, None, self.gui.spec4_rec)
class ColourPulse2:
	"""Animates colour between two colours"""

	def __init__(self, tauon: _VisualApp) -> None:
		self.gui = tauon.gui
		self.timer = Timer()
		self.in_timer = Timer()
		self.out_timer = Timer()
		self.out_timer.start = 0
		self.active: bool = False

	def get(self, hit: bool, on: bool, off: bool, low_hls: ColourRGBA, high_hls: ColourRGBA) -> ColourRGBA:
		if on:
			return high_hls
			# rgb = colorsys.hls_to_rgb(high_hls[0], high_hls[1], high_hls[2])
			# return [int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255), 255]
		if off:
			return low_hls
			# rgb = colorsys.hls_to_rgb(low_hls[0], low_hls[1], low_hls[2])
			# return [int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255), 70]

		ani_time = 0.15

		if hit is True and self.active is False:
			self.active = True
			self.in_timer.set()

			out_time = self.out_timer.get()
			if out_time < ani_time:
				self.in_timer.force_set(ani_time - out_time)

		elif hit is False and self.active is True:
			self.active = False
			self.out_timer.set()

			in_time = self.in_timer.get()
			if in_time < ani_time:
				self.out_timer.force_set(ani_time - in_time)

		pro = 0.5
		if self.active:
			time = self.in_timer.get()
			if time <= 0:
				pro = 0
			elif time >= ani_time:
				pro = 1
			else:
				pro = time / ani_time
				self.gui.request_frame()
		else:
			time = self.out_timer.get()
			if time <= 0:
				pro = 1
			elif time >= ani_time:
				pro = 0
			else:
				pro = 1 - (time / ani_time)
				self.gui.request_frame()

		return colour_slide(low_hls, high_hls, pro, 1)
class DrawnIcon:
	"""A programmatically-drawn icon (no SVG asset) usable with ViewBox.button.
	Exposes scale-aware .w/.h and a render(x, y, colour) like an image asset."""

	def __init__(self, tauon: _VisualApp, base_w: int, base_h: int, draw) -> None:
		self.tauon = tauon
		self.base_w = base_w
		self.base_h = base_h
		self._draw = draw

	@property
	def w(self) -> int:
		return round(self.base_w * self.tauon.gui.scale)

	@property
	def h(self) -> int:
		return round(self.base_h * self.tauon.gui.scale)

	def render(self, x: float, y: float, colour: ColourRGBA, renderer=None) -> None:
		self._draw(self.tauon, x, y, self.w, self.h, colour)
class ViewBox:

	def __init__(self, tauon: _VisualApp, reload: bool = False) -> None:
		self.tauon   = tauon
		self.gui     = tauon.gui
		self.ddt     = tauon.ddt
		self.coll    = tauon.coll
		self.prefs   = tauon.prefs
		self.x_menu  = tauon.x_menu
		self.fields  = tauon.fields
		self.colours = tauon.colours
		self.x: int = 0
		self.y = tauon.gui.panelY
		self.w = 52 * tauon.gui.scale
		self.h = 260 * tauon.gui.scale  # sized for the option list (incl. Custom Layout)
		self.active: bool = False

		self.border = 3 * tauon.gui.scale

		self.tracks_img   = asset_loader(tauon.bag, tauon.bag.loaded_asset_dc, "tracks.png", True)
		self.side_img     = asset_loader(tauon.bag, tauon.bag.loaded_asset_dc, "tracks+side.png", True)
		self.gallery1_img = asset_loader(tauon.bag, tauon.bag.loaded_asset_dc, "gallery1.png", True)
		self.gallery2_img = asset_loader(tauon.bag, tauon.bag.loaded_asset_dc, "gallery2.png", True)
		self.combo_img    = asset_loader(tauon.bag, tauon.bag.loaded_asset_dc, "combo.png", True)
		self.lyrics_img   = asset_loader(tauon.bag, tauon.bag.loaded_asset_dc, "lyrics.png", True)
		#self.editor_img   = asset_loader(tauon.bag, tauon.bag.loaded_asset_dc, "lyrics-editor.png", True)
		self.gallery2_img = asset_loader(tauon.bag, tauon.bag.loaded_asset_dc, "gallery2.png", True)
		self.radio_img    = asset_loader(tauon.bag, tauon.bag.loaded_asset_dc, "radio.png", True)
		self.custom_img   = DrawnIcon(tauon, 30, 19, _draw_custom_layout_icon)
		# self.artist_img = asset_loader(tauon.bag, tauon.bag.loaded_asset_dc, "artist.png", True)

		# _ .15 0
		self.tracks_colour     = ColourPulse2(tauon=tauon)  # (0.5) # .5 .6 .75
		self.side_colour       = ColourPulse2(tauon=tauon)  # (0.55) # .55 .6 .75
		self.gallery1_colour   = ColourPulse2(tauon=tauon)  # (0.6) # .6 .6 .75
		self.radio_colour      = ColourPulse2(tauon=tauon)  # (0.6) # .6 .6 .75
		# self.combo_colour    = ColourPulse(0.75)
		self.lyrics_colour     = ColourPulse2(tauon=tauon)  # (0.7)
		self.editor_colour     = ColourPulse2(tauon=tauon)  # (0.7)
		# self.gallery2_colour = ColourPulse(0.65)
		self.custom_colour     = ColourPulse2(tauon=tauon)
		self.artist_colour     = ColourPulse2(tauon=tauon)  # (0.2)

		self.on_colour = ColourRGBA(255, 190, 50, 255)
		self.over_colour = ColourRGBA(255, 190, 50, 255)
		self.off_colour = self.colours.grey(40)

		self.spring_loading_timer: Timer = Timer()
		self.can_be_spring_clicked: bool = False
		self.springing: bool             = False

		if not reload:
			tauon.gui.combo_was_album = False

	def activate(self, x: int) -> None:
		self.x = x
		self.active = True
		self.clicked = False

		self.tracks_colour.out_timer.force_set(10)
		self.side_colour.out_timer.force_set(10)
		self.gallery1_colour.out_timer.force_set(10)
		self.radio_colour.out_timer.force_set(10)
		# self.combo_colour.out_timer.force_set(10)
		self.lyrics_colour.out_timer.force_set(10)
		# self.gallery2_colour.out_timer.force_set(10)
		self.artist_colour.out_timer.force_set(10)

		self.tracks_colour.active = False
		self.side_colour.active = False
		self.gallery1_colour.active = False
		self.radio_colour.active = False
		# self.combo_colour.active = False
		self.lyrics_colour.active = False
		# self.gallery2_colour.active = False
		self.artist_colour.active = False

		self.col_force_off = False

		# self.gui.level_2_click = False
		self.gui.request_frame()

		self.spring_loading_timer.set()
		self.can_be_spring_clicked = True

	def button(
		self, x: float, y: float, asset: WhiteModImageAsset | LoadImageAsset, test, colour_get: ColourPulse2 | None = None, name: str = "Unknown", animate: bool = True, low: ColourRGBA = ColourRGBA(0,0,0,255), high: ColourRGBA = ColourRGBA(0,0,0,255)):
		"""PSA for anyone making a new button function: use fields.add(rect) to make the gui
		refresh when you pan the mouse over it
		"""
		on = test()
		# In custom mode the Custom Layout button is the active "view"; the other
		# layout icons shouldn't stay highlighted.
		if self.gui.custom_mode and test is not self.custom_layout:
			on = False
		rect = [
			x - 8 * self.gui.scale,
			y - 8 * self.gui.scale,
			asset.w + 16 * self.gui.scale,
			asset.h + 16 * self.gui.scale]
		self.fields.add(rect)

		colour = self.on_colour if on else self.off_colour

		fun = None
		col = False
		if self.coll(rect):
			self.tauon.tool_tip.test(x + asset.w + 10 * self.gui.scale, y - 15 * self.gui.scale, name)

			col = True
			if self.gui.level_2_click or (self.springing and not self.tauon.inp.mouse_down):
				fun = test
				self.x_menu.active = False
			if colour_get is None:
				colour = self.over_colour

		colour = colour_get.get(col, on, not on and not animate, low, high)

		# if "+" in name:
		# 	colour = cctest.get(col, on, [0, 0.2, 0.0], [0, 0.8, 0.8])

		# if not on and not animate:
		# 	colour = self.off_colour

		asset.render(x, y, colour)

		return fun

	def tracks(self, hit: bool = False) -> bool | None:
		if hit is False:
			return self.prefs.album_mode is False and \
				self.gui.combo_mode is False and \
				self.gui.rsp is False

		if not (self.prefs.album_mode is False and \
			self.gui.combo_mode is False and \
			self.gui.rsp is False):
			if self.x_menu.active:
				self.x_menu.close_next_frame = True

		self.tauon.view_tracks()
		return None

	def side(self, hit: bool = False) -> bool | None:
		if hit is False:
			return self.prefs.album_mode is False and \
				self.gui.combo_mode is False and \
				self.gui.rsp is True
		if not (self.prefs.album_mode is False and \
			self.gui.combo_mode is False and \
			self.gui.rsp is True):
			if self.x_menu.active:
				self.x_menu.close_next_frame = True

		self.tauon.view_standard_meta()
		return None

	def _set_side_panel_left(self, left: bool) -> None:
		# Flip the metadata side panel to the requested side, refreshing layout
		# only when the value actually changes.
		if self.prefs.side_panel_left != left:
			self.prefs.side_panel_left = left
			self.gui.update_layout = True
			self.gui.request_frame()

	def side_normal(self, hit: bool = False) -> bool | None:
		# "Tracks + Art" with the metadata side panel on its default (right) side.
		if hit is False:
			return self.side(False) and not self.prefs.side_panel_left
		self._set_side_panel_left(False)
		self.side(True)
		return None

	def side_reversed(self, hit: bool = False) -> bool | None:
		# "Tracks + Art" with the metadata side panel mirrored to the left side.
		if hit is False:
			return self.side(False) and self.prefs.side_panel_left
		self._set_side_panel_left(True)
		self.side(True)
		return None

	def gallery1(self, hit: bool = False) -> bool | None:
		if hit is False:
			return self.prefs.album_mode is True  # and self.gui.show_playlist is True

		if self.prefs.album_mode and not self.gui.combo_mode:
			self.gui.hide_tracklist_in_gallery ^= True
			self.gui.rspw = self.gui.pref_gallery_w
			self.gui.update_layout = True
			# self.x_menu.active = False
			self.x_menu.close_next_frame = True
			# Menu.active = False
			return None

		if self.x_menu.active:
			self.x_menu.close_next_frame = True

		self.tauon.force_album_view()
		return None

	def radio(self, hit: bool = False) -> bool | None:
		if hit is False:
			return self.gui.radio_view

		if not self.gui.radio_view:
			self.tauon.enter_radio_view()
		else:
			self.tauon.exit_combo(restore=True)

		if self.x_menu.active:
			self.x_menu.close_next_frame = True
		return None

	def lyrics(self, hit: bool = False) -> bool | None:
		if hit is False:
			return self.gui.showcase_mode and not self.gui.timed_lyrics_edit_view

		if not self.gui.showcase_mode:
			if self.gui.radio_view:
				self.gui.was_radio = True
			self.tauon.enter_showcase_view()

		elif self.gui.was_radio:
			self.tauon.enter_radio_view()
		elif self.gui.timed_lyrics_edit_view:
			self.gui.timed_lyrics_edit_view = False
		else:
			self.tauon.exit_combo(restore=True)
		if self.x_menu.active:
			self.x_menu.close_next_frame = True
		return None

	def activate_synced_lyric_editor(self) -> None:
		self.editor(hit = True)

	def editor(self, hit: bool = False) -> bool | None:
		if hit is False:
			return self.gui.showcase_mode and self.gui.timed_lyrics_edit_view

		if not self.gui.showcase_mode:
			if self.gui.radio_view:
				self.gui.was_radio = True
			self.tauon.enter_showcase_view(timed_lyrics_edit=True)

		elif self.gui.was_radio:
			self.tauon.enter_radio_view()
		elif not self.gui.timed_lyrics_edit_view:
			self.gui.timed_lyrics_edit_view = True
		else:
			self.tauon.exit_combo(restore=True)
		if self.x_menu.active:
			self.x_menu.close_next_frame = True
		return None

	def col(self, hit: bool = False) -> bool | None:
		if hit is False:
			return self.gui.set_mode

		if not self.gui.set_mode and self.gui.combo_mode:
			self.tauon.exit_combo()

		if self.prefs.album_mode and self.gui.plw < 550 * self.gui.scale:
			self.tauon.toggle_album_mode()

		self.tauon.toggle_library_mode()
		return None

	def artist_info(self, hit: bool = False) -> bool | None:
		if hit is False:
			return self.gui.artist_info_panel

		self.gui.artist_info_panel ^= True
		self.gui.update_layout = True
		return None

	def custom_layout(self, hit: bool = False) -> bool | None:
		if hit is False:
			return self.gui.custom_mode  # active indicator
		# Toggle: clicking again exits custom mode, revealing the previous view
		# (custom mode is an overlay, so the underlying layout is unchanged).
		if self.gui.custom_mode:
			self.tauon.custom.exit_mode()
		else:
			self.tauon.custom.enter()
		if self.x_menu.active:
			self.x_menu.close_next_frame = True
		return None

	def _custom_cycle_slots(self) -> list[int]:
		"""Slot indexes worth cycling through: the non-blank custom layouts."""
		custom = self.tauon.custom
		if not custom._loaded:
			custom.load_slots()
		return [i for i, s in enumerate(custom.slots) if not custom._is_blank_tree(s)]

	def cycle(self, reverse: bool = False) -> None:
		"""Step to the next/previous layout: Tracks → Tracks + Art → Gallery →
		Showcase → each (non-blank) custom layout slot → back to Tracks."""
		custom = self.tauon.custom
		slots = self._custom_cycle_slots()

		if self.gui.custom_mode:
			try:
				idx = slots.index(custom.active_slot)
			except ValueError:
				idx = -1  # active slot is blank: step out of custom either way
			if not reverse:
				if idx != -1 and idx + 1 < len(slots):
					custom.enter(slots[idx + 1])
					return
				custom.exit_mode()
				self.tracks(True)
			else:
				if idx > 0:
					custom.enter(slots[idx - 1])
					return
				custom.exit_mode()
				# The underlying preset may already be showcase (custom mode is
				# an overlay); lyrics(True) would toggle it back off.
				if not self.lyrics():
					self.lyrics(True)
			return

		if not reverse:
			if self.tracks():
				self.side(True)
			elif self.side():
				self.gallery1(True)
			elif self.gallery1():
				self.lyrics(True)
			elif self.lyrics() and slots:
				custom.enter(slots[0])
			else:
				self.tracks(True)
		elif self.tracks():
			if slots:
				custom.enter(slots[-1])
			else:
				self.lyrics(True)
		elif self.lyrics():
			self.gallery1(True)
		elif self.gallery1():
			self.side(True)
		else:
			self.tracks(True)

	def render(self) -> None:
		gui     = self.gui
		ddt     = self.ddt
		colours = self.colours
		if self.prefs.shuffle_lock:
			self.active = False
			self.clicked = False
			return

		if not self.active:
			return

		# rect = [self.x, self.y, self.w, self.h]
		# if x_menu.clicked or inp.mouse_click:
		if self.clicked:
			gui.level_2_click = True
		self.clicked = False

		self.springing = self.can_be_spring_clicked and self.spring_loading_timer.get() > 0.3

		x = self.x - 40 * gui.scale

		vr = [x, gui.panelY, self.w, self.h]
		# vr = [x, gui.panelY, 52 * gui.scale, 220 * gui.scale]

		border_colour = colours.menu_tab  # colours.grey(30)
		if colours.lm:
			ddt.rect((vr[0], vr[1], vr[2] + round(4 * gui.scale), vr[3]), border_colour)
		else:
			ddt.rect(
				(vr[0] - round(4 * gui.scale), vr[1], vr[2] + round(8 * gui.scale),
				vr[3] + round(4 * gui.scale)), border_colour)
		ddt.rect(vr, colours.menu_background)

		x += 7 * gui.scale
		y = gui.panelY + 14 * gui.scale

		func = None

		# low = (0, .15, 0)
		# low = (0, .40, 0)
		# low = rgb_to_hls(*alpha_blend(colours.menu_icons, colours.menu_background)[:3])  # fix me
		low = alpha_blend(colours.menu_icons, colours.menu_background)

		# if colours.lm:
		#     low = (0, 0.5, 0)

		# ----
		#logging.info(hls_to_rgb(.55, .6, .75))
		high = ColourRGBA(76, 183, 229, 255)  # (.55, .6, .75)
		if colours.lm:
			# high = (.55, .75, .75)
			high = ColourRGBA(63, 63, 63, 255)

		test = self.button(x, y, self.side_img, self.side, self.side_colour, _("Tracks + Art"), low=low, high=high)
		if test is not None:
			func = test

		# ----

		y += 40 * gui.scale

		high = ColourRGBA(76, 137, 229, 255)  # (.6, .6, .75)
		if colours.lm:
			# high = (.6, .80, .85)
			high = ColourRGBA(63, 63, 63, 255)

		if gui.hide_tracklist_in_gallery:
			test = self.button(
				x - round(1 * gui.scale), y, self.gallery2_img, self.gallery1, self.gallery1_colour,
				_("Gallery"), low=low, high=high)
		else:
			test = self.button(
				x, y, self.gallery1_img, self.gallery1, self.gallery1_colour, _("Gallery"), low=low, high=high)
		if test is not None:
			func = test

		# ---

		y += 40 * gui.scale

		high = ColourRGBA(76, 229, 229, 255)
		if colours.lm:
			# high = (.5, .7, .65)
			high = ColourRGBA(63, 63, 63, 255)

		test = self.button(
			x + 3 * gui.scale, y, self.tracks_img, self.tracks, self.tracks_colour, _("Tracks only"),
			low=low, high=high)
		if test is not None:
			func = test

		# ---

		y += 45 * gui.scale

		high = ColourRGBA(107, 76, 229, 255)
		if colours.lm:
			# high = (.7, .75, .75)
			high = ColourRGBA(63, 63, 63, 255)

		test = self.button(
			x + 4 * gui.scale, y, self.lyrics_img, self.lyrics, self.lyrics_colour,
			_("Showcase + Lyrics"), low=low, high=high)
		if test is not None:
			func = test

		# --

		# y += 45 * gui.scale
		#
		# high = ColourRGBA(81, 231, 0, 255)
		# if colours.lm:
		# 	# high = (.7, .75, .75)
		# 	high = ColourRGBA(63, 63, 63, 255)
		#
		# test = self.button(
		# 	x + 4 * gui.scale, y, self.editor_img, self.editor, self.editor_colour,
		# 	_("Lyrics Editor"), low=low, high=high)
		# if test is not None:
		# 	func = test

		# --

		y += 40 * gui.scale

		high = ColourRGBA(92, 86, 255, 255)
		if colours.lm:
			# high = (.7, .75, .75)
			high = ColourRGBA(63, 63, 63, 255)

		test = self.button(
			x + 3 * gui.scale, y, self.radio_img, self.radio, self.radio_colour, _("Radio"), low=low, high=high)
		if test is not None:
			func = test

		# --

		# -- Custom Layout --

		y += 45 * gui.scale

		high = ColourRGBA(170, 225, 90, 255)  # lime accent for the Custom Layout option
		if colours.lm:
			high = ColourRGBA(63, 63, 63, 255)

		test = self.button(
			x + 4 * gui.scale, y, self.custom_img, self.custom_layout, self.custom_colour,
			_("Custom Layout"), low=low, high=high)
		if test is not None:
			func = test

		if func is not None:
			# Switching to any other layout exits custom mode (the custom button
			# itself toggles it).
			if func is not self.custom_layout and gui.custom_mode:
				self.tauon.custom.exit_mode()
			func(True)

		if gui.level_2_click and self.coll(vr):
			self.x_menu.clicked = False

		gui.level_2_click = False
		if not self.x_menu.active:
			self.active = False

		self.can_be_spring_clicked = self.can_be_spring_clicked and self.tauon.inp.mouse_down
def draw_showcase_art_box(
	tauon: _VisualApp,
	track: TrackClass,
	x: int | float,
	y: int | float,
	box_w: int | float,
	box_h: int | float | None = None,
) -> None:
	gui = tauon.gui
	inp = tauon.inp
	ddt = tauon.ddt
	if box_h is None:
		box_h = box_w
	rect = (x, y, box_w, box_h)
	gui.main_art_box = rect

	ddt.rect(
		(
			x - round(2 * gui.scale),
			y - round(2 * gui.scale),
			box_w + round(4 * gui.scale),
			box_h + round(4 * gui.scale),
		),
		ColourRGBA(60, 60, 60, 135),
	)
	ddt.rect(rect, tauon.colours.playlist_panel_background)
	tauon.style_overlay.hole_punches.append(sdl3.SDL_FRect(round(x), round(y), round(box_w), round(box_h)))

	tauon.album_art_gen.display(track, (x, y), (box_w, box_h))
	show_vis = False

	if tauon.prefs.milk and tauon.pctl.playing_state in (PlayingState.PLAYING, PlayingState.URL_STREAM, PlayingState.PAUSED):
		if tauon.pctl.a_time < 1.3:
			if 1 < tauon.pctl.a_time < 1.3:
				tauon.milky.render(discard=True)
				tauon.milky.burn(track)
		else:
			tauon.milky.render()
			show_vis = True
		if tauon.pctl.playing_state != PlayingState.PAUSED:
			# Re-arm the next frame while the visualiser animates (the flag
			# clears at frame start, so a mid-draw request means one more frame);
			# the central pacer caps the rate at the display refresh rate.
			gui.request_frame()

	tauon.fields.add(rect)
	if tauon.coll(rect) and tauon.is_level_zero(False):
		if inp.mouse_click and inp.key_focused == 0:
			if show_vis:
				tauon.milky.projectm.load_next = "random"
			else:
				tauon.album_art_gen.cycle_offset(track)
				if tauon.pctl.mpris:
					tauon.pctl.mpris.update(force=True)

		if inp.right_click:
			if tauon.prefs.milk:
				tauon.milky_menu.activate(in_reference=track)
			else:
				tauon.picture_menu.activate(in_reference=track)
			inp.right_click = False
def _draw_custom_layout_icon(tauon: _VisualApp, x: float, y: float, w: float, h: float, colour: ColourRGBA) -> None:
	"""Draw the Custom Layout glyph for the View Switcher (shared with the corner
	edit button)."""
	draw_layout_glyph(tauon.ddt, tauon.gui.scale, x, y, w, h, colour)
