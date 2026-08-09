"""Context-menu model and rendering subsystem."""

from __future__ import annotations

import copy
from collections.abc import Callable
from typing import TYPE_CHECKING, ClassVar, Protocol

from tauon.t_modules.t_extra import Timer, alpha_blend, coll_point, is_grey, is_light, rgb_add_hls
from tauon.t_modules.t_models import ColourRGBA
from tauon.t_modules.t_state import ColoursClass, Decorator, GuiVar, Input, MenuIcon, StateBag, asset_loader

if TYPE_CHECKING:
	from tauon.t_modules.t_draw import TDraw


class _MenuFields(Protocol):
	def add(self, rect: object, callback: Callable[..., object] | None = None) -> None: ...


class _MenuApp(Protocol):
	bag: StateBag
	gui: GuiVar
	inp: Input
	ddt: TDraw
	coll: Callable[[object], bool]
	fields: _MenuFields
	colours: ColoursClass
	window_size: list[int]
	active_pointer_window: object | None


class MenuItem:
	__slots__ = [
		"title",           # 0
		"is_sub_menu",     # 1
		"func",            # 2
		"render_func",     # 3
		"no_exit",         # 4
		"pass_ref",        # 5
		"hint",            # 6
		"icon",            # 7
		"show_test",       # 8
		"pass_ref_deco",   # 9
		"disable_test",    # 10
		"set_ref",         # 11
		"args",            # 12
		"sub_menu_number", # 13
		"sub_menu_width",  # 14
		"incrementor",     # 15
		"inc_get",         # 16
		"inc_minus",       # 17
		"inc_plus",        # 18
		"check_test",      # 19
	]
	def __init__(
		self, title: str, func, render_func: Callable[..., Decorator] | None = None, no_exit: bool = False, pass_ref: bool = False, hint=None, icon: MenuIcon | None = None, show_test: Callable[..., bool] | None = None,
		pass_ref_deco: bool = False, disable_test: Callable[..., bool] | None = None, set_ref: object | None = None, is_sub_menu: bool = False, args=None, sub_menu_number: int | None = None, sub_menu_width: int = 0,
		check_test: Callable[[], bool | None] | None = None,
	) -> None:
		self.title: str = title
		self.is_sub_menu: bool = is_sub_menu
		self.func = func
		self.render_func = render_func
		self.no_exit = no_exit
		self.pass_ref = pass_ref
		self.hint = hint
		self.icon: MenuIcon | None = icon
		self.show_test = show_test
		self.pass_ref_deco: bool = pass_ref_deco
		self.disable_test = disable_test
		self.set_ref: object | None = set_ref
		self.args = args
		self.sub_menu_number: int | None = sub_menu_number
		self.sub_menu_width: int = sub_menu_width
		# Incrementor row: a label on the left with [-] value [+] stepper buttons
		# on the right. inc_get(ref) returns the number to display; inc_minus(ref)
		# / inc_plus(ref) step it. Clicking the buttons does not close the menu;
		# clicking the label does nothing. See Menu.add_incrementor / draw_incrementor.
		self.incrementor: bool = False
		self.inc_get = None
		self.inc_minus = None
		self.inc_plus = None
		# Toggle / radio state indicator: a callable (no args) returning the
		# current on/off state. When set, the row draws a small state box
		# before the label (accent-filled when on, faint outline when off)
		# instead of the legacy "✓ " text prefix. See Menu.draw_check_box.
		self.check_test = check_test

class Menu:
	"""Right click context menu generator"""

	# TODO(Martin): Global class vars!
	switch = 0
	count = switch + 1
	instances: ClassVar[list[Menu]] = []
	active = False

	def rescale(self) -> None:
		self.vertical_size = round(self.base_v_size * self.gui.scale)
		self.h = self.vertical_size
		self.w = self.request_width * self.gui.scale
		if self.gui.scale == 2:
			self.w += 15

	def __init__(self, tauon: _MenuApp, width: int, show_icons: bool = False) -> None:
		self.tauon:           _MenuApp = tauon
		self.gui:            GuiVar = tauon.gui
		self.inp:             Input = tauon.inp
		self.ddt:             TDraw = tauon.ddt
		self.coll                   = tauon.coll
		self.fields:         _MenuFields = tauon.fields
		self.colours:  ColoursClass = tauon.colours
		self.window_size: list[int] = tauon.window_size

		self.base_v_size = 22
		self.active: bool = False
		self.request_width: int = width
		self.close_next_frame: bool = False
		# True while the click currently being processed dismissed this menu (a
		# press outside its popup window). Lets toggle buttons skip reopening on
		# the same click; reset on the next button-down event.
		self.click_dismissed: bool = False
		self.clicked: bool = False
		self.pos: list[float] = [0, 0]
		self.rescale()

		self.reference: object | None = 0
		self.items: list[MenuItem | None] = []
		self.subs: list[list[MenuItem]] = []
		self.selected = -1
		self.up: bool = False
		self.down: bool = False
		self.font = 412
		self.show_icons: bool = show_icons
		self.sub_arrow = MenuIcon(asset_loader(tauon.bag, tauon.bag.loaded_asset_dc, "sub.png", True))

		self.id = Menu.count
		self.break_height = round(4 * tauon.gui.scale)

		Menu.count += 1

		self.sub_number:     int = 0
		self.sub_active:     int = -1
		self.sub_y_position: int = 0
		Menu.instances.append(self)

		self.spring_loading_timer: Timer = Timer()
		self.can_be_spring_clicked: bool = False

		# When set (popup-menu mode), the menu draws into this SecondaryWindow's
		# renderer/ddt instead of the main window, and self.pos is treated as
		# local to that window. None means draw inline in the main window.
		self.popup_window = None
		# Screen-relative anchor (offset from the main window's top-left) where
		# the popup window should appear, recorded at activate() time.
		self.popup_anchor: list[int] = [0, 0]
		# When True the anchor marks the menu's BOTTOM edge (opens upward) - used
		# for bottom-panel menus like the playback menu.
		self.popup_bottom_anchor: bool = False
		# Decided in activate(): True => draw in a separate popup window (the menu
		# or a submenu would otherwise spill outside the main window); False =>
		# draw inline in the main window (the common case).
		self.use_popup: bool = False

	@property
	def render_ddt(self) -> TDraw:
		return self.popup_window.ddt if self.popup_window is not None else self.ddt

	@property
	def render_renderer(self):
		"""Renderer to draw image assets on (None = main renderer)."""
		return self.popup_window.renderer if self.popup_window is not None else None

	@property
	def pointer(self) -> list[int]:
		"""Pointer position to hit-test the menu against.

		In popup mode the menu is drawn (and the pointer reported) in the popup
		window's own local pixel space, kept entirely separate from the main
		window's inp.mouse_position. Only the popup the pointer is actually in
		(tauon.active_pointer_window) reports a real position; the other menu
		window reports off-screen so its items don't false-hover or false-click
		from a stale pointer.
		"""
		win = self.popup_window
		if win is not None:
			if win is self.tauon.active_pointer_window:
				return list(win.last_local)
			return [-100000, -100000]
		return self.inp.mouse_position

	def deco(self, _value: object | None = None) -> Decorator:
		return Decorator(self.colours.menu_text, self.colours.menu_background, None)

	def click(self) -> None:
		self.clicked = True
		# cheap hack to prevent scroll bar from being activated when closing menu
		self.inp.click_location = [0, 0]

	def add(self, menu_item: MenuItem) -> None:
		if menu_item.render_func is None:
			menu_item.render_func = self.deco
		self.items.append(menu_item)

	def add_incrementor(self, title: str, get_value, on_minus, on_plus, show_test=None) -> None:
		"""Add an incrementor row: label on the left, a [-] value [+] stepper on
		the right. get_value/on_minus/on_plus are each called with the menu's
		reference. The stepper buttons don't close the menu; the label is inert."""
		item = MenuItem(title, lambda *_args: None, show_test=show_test)
		item.render_func = self.deco
		item.incrementor = True
		item.inc_get = get_value
		item.inc_minus = on_minus
		item.inc_plus = on_plus
		self.items.append(item)

	def add_incrementor_to_sub(self, sub_menu_index: int, title: str, get_value, on_minus, on_plus, show_test=None) -> None:
		"""Incrementor row (see add_incrementor), appended to a submenu."""
		item = MenuItem(title, lambda *_args: None, show_test=show_test)
		item.render_func = self.deco
		item.incrementor = True
		item.inc_get = get_value
		item.inc_minus = on_minus
		item.inc_plus = on_plus
		self.subs[sub_menu_index].append(item)

	def br(self) -> None:
		self.items.append(None)

	def add_sub(self, title: str, width: int, show_test=None) -> None:
		self.items.append(MenuItem(title, self.deco, sub_menu_width=width, show_test=show_test, is_sub_menu=True, sub_menu_number=self.sub_number))
		self.sub_number += 1
		self.subs.append([])

	def add_to_sub(self, sub_menu_index: int, menu_item: MenuItem) -> None:
		if menu_item.render_func is None:
			menu_item.render_func = self.deco
		self.subs[sub_menu_index].append(menu_item)

	def test_item_active(self, item: MenuItem) -> bool:
		return not (item.show_test is not None and item.show_test(self.reference) is False)

	def is_item_disabled(self, item: MenuItem) -> bool | None:
		if item.disable_test is not None:
			if item.pass_ref_deco:
				return item.disable_test(self.reference)
			return item.disable_test()
		return None

	def draw_check_box(self, item: MenuItem, x: float, y: float) -> float:
		"""Draw the toggle/radio state box for an item with check_test at the
		label position: a small square filled with the theme's toggle accent
		when on, a faint outline when off (dimmed when the item is disabled).
		Returns the width the label should shift right to clear it.
		"""
		gui = self.gui
		ddt = self.render_ddt
		colours = self.colours
		s = round(9 * gui.scale)
		bx = round(x)
		by = round(y + (self.h - s) / 2)
		disabled = bool(self.is_item_disabled(item))
		if item.check_test():
			c = colours.toggle_box_on
			if disabled:
				c = colours.menu_text_disabled
			ddt.rect((bx, by, s, s), ColourRGBA(c.r, c.g, c.b, 150 if disabled else 255))
		else:
			line = colours.menu_text_disabled if disabled else colours.menu_text
			c = ColourRGBA(line.r, line.g, line.b, 70)
			b = max(1, round(1 * gui.scale))
			ddt.rect((bx, by, s, b), c)
			ddt.rect((bx, by + s - b, s, b), c)
			ddt.rect((bx, by + b, b, s - b * 2), c)
			ddt.rect((bx + s - b, by + b, b, s - b * 2), c)
		return s + round(7 * gui.scale)

	def render_icon(self, x: float, y: float, icon: MenuIcon | None, selected: bool, fx: Decorator) -> None:
		colours = self.colours
		gui     = self.gui
		renderer = self.render_renderer
		if colours.lm:
			selected = True

		if icon is not None:
			x += icon.xoff * gui.scale
			y += icon.yoff * gui.scale

			colour: ColourRGBA | None = None

			if icon.base_asset is None:
				# Colourise mode
				if icon.colour_callback is not None:  # and icon.colour_callback() is not None:
					colour = icon.colour_callback()
				elif selected and fx.text_colour != colours.menu_text_disabled:
					colour = icon.colour

				if colour is None and icon.base_asset_mod:
					colour = colours.menu_icons
					# if colours.lm:
					#	 colour = ColourRGBA(160, 160, 160, 255)
					icon.base_asset_mod.render(x, y, colour, renderer=renderer)
					return

				if colour is None:
					# colour = ColourRGBA(145, 145, 145, 70)
					colour = colours.menu_icons  # ColourRGBA(255, 255, 255, 35)
					# colour = ColourRGBA(50, 50, 50, 255)

				icon.asset.render(x, y, colour, renderer=renderer)
			else:
				if not is_grey(colours.menu_background):
					return  # Since these are currently pre-rendered greyscale, they are
					# Incompatible with coloured backgrounds. Fix TODO
				if selected and fx.text_colour == colours.menu_text_disabled:
					icon.base_asset.render(x, y, renderer=renderer)
					return

				# Pre-rendered mode
				if icon.mode_callback is not None:
					if icon.mode_callback():
						icon.asset.render(x, y, renderer=renderer)
					else:
						icon.base_asset.render(x, y, renderer=renderer)
				elif selected:
					icon.asset.render(x, y, renderer=renderer)
				else:
					icon.base_asset.render(x, y, renderer=renderer)

	def draw_incrementor(self, item: MenuItem, x_run: float, y_run: float, bg: ColourRGBA, ytoff: float, width: float) -> float:
		"""Draw an incrementor row's right side: [-] value [+]. Handles clicks on
		the two square stepper buttons (which don't close the menu). ``width`` is
		the row width (main column or submenu). Returns the x of the left edge of
		the minus button so the caller can bound the label.
		"""
		gui     = self.gui
		ddt     = self.render_ddt
		colours = self.colours
		scale   = gui.scale

		bs = int(self.h)                             # square button side = full row height
		by = int(y_run)
		plus_x  = int(x_run + width - bs)            # flush with the row's right edge
		num_w   = round(26 * scale)
		num_x   = plus_x - num_w
		minus_x = int(num_x - bs)

		dark = not (is_light(bg) or colours.lm)
		glyph_c = rgb_add_hls(bg, 0, 0.55 if dark else -0.55, 0)

		def button(bx: int, plus: bool) -> None:
			r = (bx, by, bs, bs)
			self.fields.add(r)
			hover = coll_point(self.pointer, r)
			face = rgb_add_hls(bg, 0, (0.16 if hover else 0.09) if dark else (-0.16 if hover else -0.09), 0)
			ddt.rect(r, face)
			gl = round(bs * 0.44)                    # glyph arm length
			gt = max(1, round(1.5 * scale))          # glyph thickness
			cx, cy = bx + bs / 2, by + bs / 2
			ddt.rect((round(cx - gl / 2), round(cy - gt / 2), gl, gt), glyph_c)
			if plus:
				ddt.rect((round(cx - gt / 2), round(cy - gl / 2), gt, gl), glyph_c)
			if hover and self.clicked:
				cb = item.inc_plus if plus else item.inc_minus
				if cb is not None:
					cb(self.reference)
					gui.request_frame()

		button(minus_x, False)
		button(plus_x, True)

		value = item.inc_get(self.reference) if item.inc_get is not None else ""
		ddt.text((round(num_x + num_w / 2), int(y_run + ytoff), 2), str(value), colours.menu_text, self.font, bg=bg)

		return minus_x

	def render(self) -> None:
		tauon   = self.tauon
		gui     = self.gui
		ddt     = self.render_ddt
		inp     = self.inp
		colours = self.colours

		if self.active:
			if Menu.switch != self.id:
				self.active = False

				for menu in Menu.instances:
					if menu.active:
						break
				else:
					Menu.active = False

				return



			# ytoff = 3
			y_run = round(self.pos[1])
			to_call = None

			# if window_size[1] < 250 * gui.scale:
			#	 self.h = round(14 * gui.scale)
			#	 ytoff = -1 * gui.scale
			# else:
			self.h = self.vertical_size
			ytoff = round(self.h * 0.71 - 13 * gui.scale)

			x_run = self.pos[0]

			# In popup-window mode the window is sized to fit the menu and the
			# compositor keeps it on-screen, so the in-window column-wrap / flip
			# behaviour below must be disabled by using effectively-infinite bounds.
			if self.popup_window is not None:
				bounds = (1 << 24, 1 << 24)
			else:
				bounds = self.window_size

			springing = self.can_be_spring_clicked and self.spring_loading_timer.get() > 0.3

			for i in range(len(self.items)):
				#logging.info(self.items[i])

				# Draw menu break
				if self.items[i] is None:
					if is_light(colours.menu_background):
						break_colour = rgb_add_hls(colours.menu_background, 0, -0.1, -0.1)
					else:
						break_colour = rgb_add_hls(colours.menu_background, 0, 0.06, 0)

					rect = (x_run, y_run, self.w, self.break_height - 1)
					if coll_point(self.pointer, rect):
						self.clicked = False

					ddt.rect_a((x_run, y_run), (self.w, self.break_height), colours.menu_background)

					ddt.rect_a((x_run, y_run + 2 * gui.scale), (self.w, 2 * gui.scale), break_colour)

					# Draw tab
					ddt.rect_a((x_run, y_run), (4 * gui.scale, self.break_height), colours.menu_tab)
					y_run += self.break_height

					continue

				if self.test_item_active(self.items[i]) is False:
					continue
				# if self.items[i][1] is False and self.items[i][8] is not None:
				#	 if self.items[i][8](1) == False:
				#		 continue

				# Get properties for menu item
				if self.items[i].render_func is not None:
					if self.items[i].pass_ref_deco:
						fx = self.items[i].render_func(self.reference)
					else:
						fx = self.items[i].render_func()
				else:
					fx = self.deco()

				label = fx.text if fx.text is not None else self.items[i].title

				# Show text as disabled if disable_test() passes
				if self.is_item_disabled(self.items[i]):
					fx.text_colour = colours.menu_text_disabled

				# Draw item background, black by default
				ddt.rect_a((x_run, y_run), (self.w, self.h), fx.bg_colour)
				bg = fx.bg_colour

				# Detect if mouse is over this item
				selected = False
				rect = (x_run, y_run, self.w, self.h - 1)
				self.fields.add(rect)

				if coll_point(self.pointer, (x_run, y_run, self.w, self.h - 1)):
					ddt.rect_a((x_run, y_run), (self.w, self.h), colours.menu_highlight_background)  # [15, 15, 15, 255]
					selected = True
					bg = alpha_blend(colours.menu_highlight_background, bg)

					# Call menu items callback if clicked
					if self.items[i].incrementor:
						pass  # stepper buttons handled after the label; label/row click is inert
					elif self.items[i].is_sub_menu is False:
						if self.clicked or (springing and not self.inp.right_down and not self.inp.mouse_down ):
							to_call = i
							if self.items[i].set_ref is not None:
								self.reference = self.items[i].set_ref
							self.inp.mouse_down = False
							self.close_next_frame = True
							gui.request_frame()
						if springing:
							self.sub_active = -1
					elif self.clicked or springing:
						self.clicked = False
						self.sub_active = self.items[i].sub_menu_number
						self.sub_y_position = y_run

				# Draw tab
				ddt.rect_a((x_run, y_run), (4 * gui.scale, self.h), colours.menu_tab)

				# Draw Icon
				x = 12 * gui.scale
				if self.items[i].is_sub_menu is False and self.show_icons:
					icon = self.items[i].icon
					self.render_icon(x_run + x, y_run + 5 * gui.scale, icon, selected, fx)

				if self.show_icons:
					x += 25 * gui.scale

				# Toggle / radio state box
				if self.items[i].check_test is not None:
					x += self.draw_check_box(self.items[i], x_run + x, y_run)

				# Draw arrow icon for sub menu
				if self.items[i].is_sub_menu is True:
					if is_light(bg) or colours.lm:
						colour = rgb_add_hls(bg, 0, -0.6, -0.1)
					else:
						colour = rgb_add_hls(bg, 0, 0.1, 0)

					if self.sub_active == self.items[i].func:
						if is_light(bg) or colours.lm:
							colour = rgb_add_hls(bg, 0, -0.8, -0.1)
						else:
							colour = rgb_add_hls(bg, 0, 0.40, 0)

					# colour = ColourRGBA(50, 50, 50, 255)
					# if selected:
					#	 colour = ColourRGBA(150, 150, 150, 255)
					# if self.sub_active == self.items[i][2]:
					#	 colour = ColourRGBA(150, 150, 150, 255)
					self.sub_arrow.asset.render(x_run + self.w - 13 * gui.scale, y_run + 7 * gui.scale, colour, renderer=self.render_renderer)

				# Render the items label (narrowed to clear the stepper for incrementors)
				if self.items[i].incrementor:
					left_bound = self.draw_incrementor(self.items[i], x_run, y_run, bg, ytoff, self.w)
					label_max_w = max(1, int(left_bound - (x_run + x) - 6 * gui.scale))
					# Swallow any click on this row so the menu stays open: the label
					# is inert and only the stepper buttons act (handled above in
					# draw_incrementor), so a click anywhere else here does nothing.
					if coll_point(self.pointer, (x_run, y_run, self.w, self.h - 1)):
						self.clicked = False
				else:
					label_max_w = self.w - (x + 9 * gui.scale)
				ddt.text((x_run + x, y_run + ytoff), label, fx.text_colour, self.font, max_w=label_max_w, bg=bg)

				# Render the items hint
				if self.items[i].hint is not None and not self.items[i].incrementor:

					if is_light(bg) or colours.lm:
						hint_colour = rgb_add_hls(bg, 0, -0.30, -0.3)
					else:
						hint_colour = rgb_add_hls(bg, 0, 0.15, 0)

					# colo = alpha_blend(ColourRGBA(255, 255, 255, 50), bg)
					ddt.text((x_run + self.w - 5, y_run + ytoff, 1), self.items[i].hint, hint_colour, self.font, bg=bg)

				y_run += self.h

				if y_run > bounds[1] - self.h:
					direc = 1
					if self.pos[0] > bounds[0] // 2:
						direc = -1
					x_run += self.w * direc
					y_run = self.pos[1]

				# Inline mode: draw the active submenu beside its parent item here
				# (popup mode draws it into its own window via draw_popup_menus).
				# Placement only guarantees the main column fits, so a submenu
				# that would overflow flips to the left side / clamps upward.
				if self.popup_window is None and self.sub_active > -1 \
						and self.items[i].is_sub_menu and self.sub_active == self.items[i].sub_menu_number:
					sub_w, sub_h = self.submenu_size()
					sx = x_run + self.w
					if sx + sub_w > bounds[0]:
						sx = x_run - sub_w
					sy = min(self.sub_y_position, bounds[1] - sub_h)
					self.render_submenu(int(sx), int(max(0, sy)))

			# Process Click Actions
			if to_call is not None and not self.is_item_disabled(self.items[to_call]):
				if self.items[to_call].pass_ref:
					self.items[to_call].func(self.reference)
				else:
					self.items[to_call].func()

			if self.clicked or inp.key_esc_press or self.close_next_frame:
				self.close_next_frame = False
				self.active = False
				self.clicked = False

				inp.last_click_location[0] = 0
				inp.last_click_location[1] = 0

				for menu in Menu.instances:
					if menu.active:
						break
				else:
					Menu.active = False

				# Render the menu outline
				# ddt.rect_a(self.pos, (self.w, self.h * len(self.items)), colours.grey(40))
			self.can_be_spring_clicked = self.can_be_spring_clicked and ( self.inp.right_down or self.inp.mouse_down )

	def activate(self, in_reference: object = 0, position: list[int] | None = None, bottom_anchor: bool = False) -> None:
		Menu.active = True

		if position is not None:
			self.pos = [position[0], position[1]]
		else:
			self.pos = [copy.deepcopy(self.inp.mouse_position[0]), copy.deepcopy(self.inp.mouse_position[1])]

		# If activated from within a local view space (e.g. a Custom Layout widget
		# being rendered reframed), the position is in that local space; convert it
		# to real screen coordinates. Identity when no transform is active.
		self.pos = list(self.inp.to_screen(self.pos[0], self.pos[1]))

		self.reference = in_reference
		Menu.switch = self.id
		self.sub_active = -1
		self.popup_window = None

		# Decide placement: a menu opens down-right from the anchor (or upward for
		# a bottom-anchored menu). If the main column would extend past the window
		# at that natural position, it pops out into its own popup window instead
		# of being flipped/shifted to fit inside. Judged by the main column only:
		# an inline submenu that would overflow flips left / clamps up at render
		# time - sizing for the worst-case submenu here sent menus into a popup
		# even when there was plenty of room for the menu itself.
		gui = self.gui
		win_w, win_h = self.window_size[0], self.window_size[1]
		main_w, main_h = self.popup_size()
		anchor = [int(self.pos[0]), int(self.pos[1])]
		self.popup_bottom_anchor = bottom_anchor

		if bottom_anchor:
			# Opens upward: the anchor marks the bottom edge.
			self.use_popup = (anchor[0] + main_w > win_w) or (anchor[1] - main_h < gui.panelY)
		else:
			self.use_popup = (anchor[0] + main_w > win_w) or (anchor[1] + main_h > win_h)

		if self.use_popup:
			# Popup mode: anchor the popup window at the requested point; the
			# compositor keeps it on-screen, so no in-window repositioning needed.
			self.popup_anchor = anchor
			self.pos = [0, 0]
		else:
			# Inline mode: it fits at the natural position, so draw there as-is
			# (no flip/shift). A bottom-anchored menu draws its column above the
			# anchor.
			self.pos = [anchor[0], anchor[1] - main_h if bottom_anchor else anchor[1]]

		self.spring_loading_timer.set()
		self.can_be_spring_clicked = True
		self.active = True

	def popup_size(self) -> tuple[int, int]:
		"""Pixel size the popup window needs to fit this menu's main column.

		Submenus are drawn in their own window (see submenu_size /
		render_submenu), so they are not included here.
		"""
		gui = self.gui
		w = int(self.w)
		h = 0
		for item in self.items:
			if item is None:
				h += self.break_height
			elif self.test_item_active(item):
				h += self.h

		return max(1, w), max(1, h + round(2 * gui.scale))

	def submenu_size(self) -> tuple[int, int]:
		"""Pixel size of the currently active submenu's own popup window."""
		gui = self.gui
		if not (-1 < self.sub_active < len(self.subs)):
			return 1, 1
		sub_w = 0
		for item in self.items:
			if item is not None and item.is_sub_menu and item.sub_menu_number == self.sub_active:
				sub_w = int(item.sub_menu_width * gui.scale)
				break
		shown = sum(
			1 for s in self.subs[self.sub_active]
			if s.show_test is None or s.show_test(self.reference)
		)
		return max(1, sub_w), max(1, shown * self.h + round(2 * gui.scale))

	def render_submenu(self, ox: int = 0, oy: int = 0) -> None:
		"""Draw the active submenu with its top-left at (ox, oy).

		Mirrors the main item rendering for the active submenu's items. For a
		popup submenu (ox, oy) = (0, 0) (its own window's local origin); for an
		inline submenu they are absolute coordinates in the main window beside
		the parent item. Drawing/hit-testing follow self.render_ddt / self.pointer
		so the same code serves both modes.
		"""
		if not (-1 < self.sub_active < len(self.subs)):
			return

		gui     = self.gui
		ddt     = self.render_ddt
		colours = self.colours

		ytoff = round(self.h * 0.71 - 13 * gui.scale)
		# Snapshot which items are visible ONCE up front. A no_exit toggle fires
		# its func mid-render, which flips its show_test pair; re-evaluating per
		# item would then reveal the pair member later in the same pass, shifting
		# every row below down for one frame. Freezing the list avoids that.
		sub_items = [
			s for s in self.subs[self.sub_active]
			if s.show_test is None or s.show_test(self.reference)
		]
		sub_w = self.submenu_size()[0]

		springing = self.can_be_spring_clicked and self.spring_loading_timer.get() > 0.3

		# Left text inset depends on whether any item in this submenu has an icon.
		xoff = 0
		for item in sub_items:
			if item.icon is not None:
				xoff = 24 * gui.scale
				break

		row = 0
		for item in sub_items:
			y = oy + row * self.h

			if item.render_func is not None:
				fx = item.render_func(self.reference) if item.pass_ref_deco else item.render_func()
			else:
				fx = self.deco()

			ddt.rect_a((ox, y), (sub_w, self.h), fx.bg_colour)
			self.fields.add((ox, y, sub_w, self.h - 1))

			bg = colours.menu_background
			this_select = False
			if coll_point(self.pointer, (ox, y, sub_w, self.h - 1)):
				ddt.rect_a((ox, y), (sub_w, self.h), colours.menu_highlight_background)
				bg = alpha_blend(colours.menu_highlight_background, bg)
				this_select = True

				if item.incrementor:
					pass  # stepper buttons handled after the label; label/row click is inert
				elif not self.is_item_disabled(item):
					# no_exit items act only on a discrete click and keep the menu
					# open (the spring-loaded path would re-fire a toggle every frame
					# while the button is held). Normal items also fire on spring.
					if item.no_exit:
						fire = self.clicked
					else:
						fire = self.clicked or (springing and not self.inp.right_down and not self.inp.mouse_down)
					if fire:
						if item.args is not None:
							item.func(self.reference, item.args)
						elif item.pass_ref:
							item.func(self.reference)
						else:
							item.func()
						if item.no_exit:
							self.clicked = False  # keep the menu (and submenu) open
						else:
							self.close_next_frame = True
						gui.request_frame()

			label = fx.text if fx.text is not None else item.title
			if self.is_item_disabled(item):
				fx.text_colour = colours.menu_text_disabled

			self.render_icon(ox + 11 * gui.scale, y + 5 * gui.scale, item.icon, this_select, fx)
			text_x = ox + 10 * gui.scale + xoff
			# Toggle / radio state box
			if item.check_test is not None:
				text_x += self.draw_check_box(item, text_x, y)
			if item.incrementor:
				left_bound = self.draw_incrementor(item, ox, y, bg, ytoff, sub_w)
				label_max_w = max(1, int(left_bound - text_x - 6 * gui.scale))
				# Swallow any click on this row so the menu stays open (label inert).
				if coll_point(self.pointer, (ox, y, sub_w, self.h - 1)):
					self.clicked = False
				ddt.text((text_x, y + ytoff), label, fx.text_colour, self.font, max_w=label_max_w, bg=bg)
			else:
				ddt.text((text_x, y + ytoff), label, fx.text_colour, self.font, bg=bg)
			ddt.rect_a((ox, y), (4 * gui.scale, self.h), colours.menu_tab)

			row += 1


def close_all_menus() -> None:
	for menu in Menu.instances:
		menu.active = False
	Menu.active = False
