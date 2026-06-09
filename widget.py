"""
pygame_kivy_widget.py
=====================
A Kivy widget that hosts a Pygame surface and bridges input/output between
the two frameworks.  Drop it into any Kivy layout and run your Pygame game
loop inside `on_pygame_frame`.

Features
--------
* Renders a pygame.Surface onto a Kivy Image widget every frame via a
  shared Texture (zero extra copies when possible).
* show_keyboard() / hide_keyboard() – toggle the soft keyboard on Android
  (and desktop IME where supported).
* Key events forwarded as pygame keyboard events (KEYDOWN / KEYUP).
* Touch / mouse events forwarded as pygame MOUSEBUTTONDOWN/UP and
  MOUSEMOTION, with coordinate mapping from Kivy → Pygame surface space.

Quick-start
-----------
    from pygame_kivy_widget import PygameWidget

    class MyApp(App):
        def build(self):
            widget = PygameWidget(size=(480, 320))
            widget.bind(on_pygame_frame=self.game_loop)
            return widget

    def game_loop(self, widget, surface, dt):
        surface.fill((30, 30, 30))
        # … your pygame drawing here …

    MyApp().run()

Requirements
------------
    pip install kivy pygame

On Android use Buildozer and add both `kivy` and `pygame` to requirements.
"""

from __future__ import annotations

import pygame
import ctypes

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics.texture import Texture
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.event import EventDispatcher
from kivy.properties import ObjectProperty, NumericProperty, BooleanProperty

# ---------------------------------------------------------------------------
# Kivy → Pygame key-code table (extend as needed)
# ---------------------------------------------------------------------------
_KIVY_TO_PYGAME_KEY: dict[str, int] = {
    "a": pygame.K_a, "b": pygame.K_b, "c": pygame.K_c, "d": pygame.K_d,
    "e": pygame.K_e, "f": pygame.K_f, "g": pygame.K_g, "h": pygame.K_h,
    "i": pygame.K_i, "j": pygame.K_j, "k": pygame.K_k, "l": pygame.K_l,
    "m": pygame.K_m, "n": pygame.K_n, "o": pygame.K_o, "p": pygame.K_p,
    "q": pygame.K_q, "r": pygame.K_r, "s": pygame.K_s, "t": pygame.K_t,
    "u": pygame.K_u, "v": pygame.K_v, "w": pygame.K_w, "x": pygame.K_x,
    "y": pygame.K_y, "z": pygame.K_z,
    "0": pygame.K_0, "1": pygame.K_1, "2": pygame.K_2, "3": pygame.K_3,
    "4": pygame.K_4, "5": pygame.K_5, "6": pygame.K_6, "7": pygame.K_7,
    "8": pygame.K_8, "9": pygame.K_9,
    "spacebar": pygame.K_SPACE, " ": pygame.K_SPACE,
    "enter": pygame.K_RETURN, "escape": pygame.K_ESCAPE,
    "backspace": pygame.K_BACKSPACE, "tab": pygame.K_TAB,
    "up": pygame.K_UP, "down": pygame.K_DOWN,
    "left": pygame.K_LEFT, "right": pygame.K_RIGHT,
    "shift": pygame.K_LSHIFT, "ctrl": pygame.K_LCTRL,
    "alt": pygame.K_LALT, "delete": pygame.K_DELETE,
    "home": pygame.K_HOME, "end": pygame.K_END,
    "pageup": pygame.K_PAGEUP, "pagedown": pygame.K_PAGEDOWN,
    "f1": pygame.K_F1, "f2": pygame.K_F2, "f3": pygame.K_F3,
    "f4": pygame.K_F4, "f5": pygame.K_F5, "f6": pygame.K_F6,
    "f7": pygame.K_F7, "f8": pygame.K_F8, "f9": pygame.K_F9,
    "f10": pygame.K_F10, "f11": pygame.K_F11, "f12": pygame.K_F12,
}

# Kivy mouse button index → pygame button number
_KIVY_TO_PYGAME_BTN: dict[str, int] = {
    "left": 1, "middle": 2, "right": 3,
    "scrollup": 4, "scrolldown": 5,
}


class PygameWidget(BoxLayout):
    """
    A Kivy widget that hosts a Pygame surface.

    Parameters
    ----------
    surface_size : tuple[int, int]
        Pixel dimensions of the Pygame surface (default: matches widget size).
    fps : int
        Target frames per second for the internal Clock (default: 60).
    keyboard_visible : bool
        Whether the soft keyboard starts visible (default: False).

    Events
    ------
    on_pygame_frame(widget, surface, dt)
        Fired every frame.  Draw to *surface* here.
    on_pygame_keydown(widget, key, scancode, codepoint, modifiers)
        Fired when a key is pressed (mirrors Kivy's on_key_down signature).
    on_pygame_keyup(widget, key, scancode, codepoint, modifiers)
        Fired when a key is released.
    on_pygame_touch(widget, touch_x, touch_y, action)
        Fired on touch / mouse events.  *action* is one of
        ``"down"``, ``"move"``, ``"up"``.
    """

    # ------------------------------------------------------------------
    # Kivy properties
    # ------------------------------------------------------------------
    fps = NumericProperty(60)
    keyboard_visible = BooleanProperty(False)

    # ------------------------------------------------------------------
    # Kivy event declarations
    # ------------------------------------------------------------------
    def __init__(self, surface_size: tuple[int, int] | None = None,
                 fps: int = 60, keyboard_visible: bool = False, **kwargs):
        self.register_event_type("on_pygame_frame")
        self.register_event_type("on_pygame_keydown")
        self.register_event_type("on_pygame_keyup")
        self.register_event_type("on_pygame_touch")

        super().__init__(orientation="vertical", **kwargs)

        self.fps = fps
        self.keyboard_visible = keyboard_visible

        # --- Pygame init (display-less; we own the surface) ---
        if not pygame.get_init():
            pygame.init()
        # Prevent pygame from opening its own OS window
        import os
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

        self._surface_size = surface_size  # resolved in on_size
        self._mouse_pos: tuple[int, int] = (0, 0)
        self._surface: pygame.Surface | None = None
        self._texture: Texture | None = None

        # --- Kivy image widget that shows the texture ---
        self._image = Image(allow_stretch=True, keep_ratio=False)
        self.add_widget(self._image)

        # --- Keyboard ---
        self._kb = None  # Kivy keyboard handle
        if keyboard_visible:
            self.show_keyboard()

        # --- Window-level key bindings (desktop) ---
        Window.bind(on_key_down=self._on_window_key_down)
        Window.bind(on_key_up=self._on_window_key_up)

        # --- Touch bindings ---
        self._image.bind(on_touch_down=self._on_touch_down)
        self._image.bind(on_touch_move=self._on_touch_move)
        self._image.bind(on_touch_up=self._on_touch_up)

        # --- Frame clock ---
        self._clock_event = Clock.schedule_interval(self._tick, 1.0 / self.fps)

        # Resolve surface once size is known
        self.bind(size=self._init_surface)

    # ------------------------------------------------------------------
    # Surface / texture management
    # ------------------------------------------------------------------
    def _init_surface(self, *_args):
        w, h = self._surface_size or (int(self.width) or 320, int(self.height) or 240)
        w, h = max(w, 1), max(h, 1)
        self._surface = pygame.Surface((w, h))
        self._texture = Texture.create(size=(w, h), colorfmt="rgb", bufferfmt="ubyte")
        self._image.texture = self._texture

    def _upload_surface(self):
        """Blit the current pygame surface into the Kivy texture."""
        if self._surface is None or self._texture is None:
            return
        # The third arg `True` flips vertically so Pygame top-left matches OpenGL bottom-left
        raw = pygame.image.tostring(self._surface, "RGB", True)
        self._texture.blit_buffer(raw, colorfmt="rgb", bufferfmt="ubyte")
        self._image.canvas.ask_update()

    # ------------------------------------------------------------------
    # Clock tick
    # ------------------------------------------------------------------
    def _tick(self, dt: float):
        if self._surface is None:
            return
        # Drain pygame's own event queue (keeps it healthy; we bridge separately)
        pygame.event.pump()
        # Fire the user's drawing callback
        self.dispatch("on_pygame_frame", self._surface, dt)
        self._upload_surface()

    # ------------------------------------------------------------------
    # Default no-op handlers (required by Kivy event system)
    # ------------------------------------------------------------------
    def on_pygame_frame(self, surface, dt):
        pass

    def on_pygame_keydown(self, key, scancode, codepoint, modifiers):
        pass

    def on_pygame_keyup(self, key, scancode, codepoint, modifiers):
        pass

    def on_pygame_touch(self, touch_x, touch_y, action):
        pass

    # ------------------------------------------------------------------
    # Keyboard helpers
    # ------------------------------------------------------------------
    def show_keyboard(self):
        """Request the soft / system keyboard."""
        if self._kb is None:
            self._kb = Window.request_keyboard(self._kb_closed, self)
            self._kb.bind(on_key_down=self._on_kb_key_down)
            self._kb.bind(on_key_up=self._on_kb_key_up)
        self.keyboard_visible = True

    def hide_keyboard(self):
        """Release / dismiss the soft keyboard."""
        if self._kb is not None:
            self._kb.release()
            self._kb = None
        self.keyboard_visible = False

    def toggle_keyboard(self):
        """Toggle soft keyboard visibility."""
        if self.keyboard_visible:
            self.hide_keyboard()
        else:
            self.show_keyboard()

    def _kb_closed(self):
        self._kb = None
        self.keyboard_visible = False

    # ------------------------------------------------------------------
    # Key event bridging (Kivy keyboard widget → pygame events)
    # ------------------------------------------------------------------
    def _on_kb_key_down(self, keyboard, keycode, text, modifiers):
        self._bridge_key(keycode, modifiers, down=True)
        self.dispatch("on_pygame_keydown", keycode[1], keycode[0], text, modifiers)

    def _on_kb_key_up(self, keyboard, keycode):
        self._bridge_key(keycode, [], down=False)
        self.dispatch("on_pygame_keyup", keycode[1], keycode[0], "", [])

    # Window-level fallback for desktop (works even without keyboard widget)
    def _on_window_key_down(self, window, key, scancode, codepoint, modifiers):
        keyname = pygame.key.name(key) if key < 256 else str(key)
        self.dispatch("on_pygame_keydown", keyname, scancode, codepoint, modifiers)
        self._inject_pygame_key(key, scancode, codepoint, modifiers, down=True)

    def _on_window_key_up(self, window, key, scancode):
        self.dispatch("on_pygame_keyup", pygame.key.name(key) if key < 256 else str(key),
                      scancode, "", [])
        self._inject_pygame_key(key, scancode, "", [], down=False)

    def _bridge_key(self, keycode, modifiers, *, down: bool):
        """Translate a Kivy keycode tuple → pygame KEYDOWN/KEYUP event."""
        raw_key, key_name = keycode
        pg_key = _KIVY_TO_PYGAME_KEY.get(key_name.lower(), pygame.K_UNKNOWN)
        mods = _kivy_mods_to_pygame(modifiers)
        etype = pygame.KEYDOWN if down else pygame.KEYUP
        event = pygame.event.Event(etype, {
            "key": pg_key,
            "scancode": raw_key,
            "unicode": key_name if len(key_name) == 1 else "",
            "mod": mods,
        })
        pygame.event.post(event)

    def _inject_pygame_key(self, kivy_key, scancode, codepoint, modifiers, *, down: bool):
        pg_key = kivy_key if kivy_key < 256 else pygame.K_UNKNOWN
        mods = _kivy_mods_to_pygame(modifiers)
        etype = pygame.KEYDOWN if down else pygame.KEYUP
        event = pygame.event.Event(etype, {
            "key": pg_key,
            "scancode": scancode or 0,
            "unicode": codepoint or "",
            "mod": mods,
        })
        pygame.event.post(event)

    # ------------------------------------------------------------------
    # Touch / mouse event bridging
    # ------------------------------------------------------------------
    def _map_touch(self, touch) -> tuple[int, int]:
        """
        Convert Kivy window coordinates → Pygame surface pixel coordinates.
        Accounts for widget position and surface scale.
        """
        if self._surface is None:
            return (int(touch.x), int(touch.y))

        # Widget bounding box in window coords
        wx, wy = self._image.to_window(*self._image.pos)
        ww, wh = self._image.size

        # Normalised position within the image widget (0..1)
        nx = (touch.x - wx) / max(ww, 1)
        ny = (touch.y - wy) / max(wh, 1)
        # Clamp
        nx = max(0.0, min(1.0, nx))
        ny = max(0.0, min(1.0, ny))

        sw, sh = self._surface.get_size()
        # Kivy Y is bottom-up; pygame Y is top-down
        px = int(nx * sw)
        py = int((1.0 - ny) * sh)
        return (px, py)

    def _post_mouse_event(self, pos, etype, button=1):
        event = pygame.event.Event(etype, {
            "pos": pos,
            "button": button,
            "buttons": (1, 0, 0),
        })
        pygame.event.post(event)

    def _on_touch_down(self, widget, touch):
        if not self._image.collide_point(*touch.pos):
            return False
        pos = self._map_touch(touch)
        self._mouse_pos = pos
        btn = _KIVY_TO_PYGAME_BTN.get(getattr(touch, "button", "left"), 1)
        self._post_mouse_event(pos, pygame.MOUSEBUTTONDOWN, btn)
        self.dispatch("on_pygame_touch", pos[0], pos[1], "down")
        return True

    def _on_touch_move(self, widget, touch):
        if not self._image.collide_point(*touch.pos):
            return False
        pos = self._map_touch(touch)
        self._mouse_pos = pos
        event = pygame.event.Event(pygame.MOUSEMOTION, {
            "pos": pos,
            "rel": (0, 0),
            "buttons": (1, 0, 0),
        })
        pygame.event.post(event)
        self.dispatch("on_pygame_touch", pos[0], pos[1], "move")
        return True

    def _on_touch_up(self, widget, touch):
        pos = self._map_touch(touch)
        btn = _KIVY_TO_PYGAME_BTN.get(getattr(touch, "button", "left"), 1)
        self._post_mouse_event(pos, pygame.MOUSEBUTTONUP, btn)
        self.dispatch("on_pygame_touch", pos[0], pos[1], "up")
        return True

    def get_mouse_pos(self) -> tuple[int, int]:
        """
        Return the last known mouse / touch position in Pygame surface
        pixel coordinates.  Equivalent to pygame.mouse.get_pos() but
        correctly mapped to the surface resolution regardless of widget size.
        """
        return self._mouse_pos

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def stop(self):
        """Call this when you want to shut down the widget cleanly."""
        self._clock_event.cancel()
        self.hide_keyboard()
        Window.unbind(on_key_down=self._on_window_key_down)
        Window.unbind(on_key_up=self._on_window_key_up)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _kivy_mods_to_pygame(modifiers: list[str]) -> int:
    mods = 0
    if "shift" in modifiers:
        mods |= pygame.KMOD_SHIFT
    if "ctrl" in modifiers:
        mods |= pygame.KMOD_CTRL
    if "alt" in modifiers:
        mods |= pygame.KMOD_ALT
    if "meta" in modifiers or "super" in modifiers:
        mods |= pygame.KMOD_META
    return mods

