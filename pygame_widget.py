import pygame
from kivy.app import App
from kivy.uix.image import Image
from kivy.graphics.texture import Texture
from kivy.clock import Clock
from kivy.core.window import Window


# ---------------------------------------------------------------------------
# Global fake input state
# ---------------------------------------------------------------------------

_mouse_pos     = (0, 0)
_mouse_buttons = (False, False, False)
_pressed_keys  = {}   # pygame_keycode -> True


def _fake_mouse_get_pos():
    return _mouse_pos

def _fake_mouse_get_pressed():
    return _mouse_buttons

def _fake_key_get_pressed():
    result = [False] * 512
    for k in _pressed_keys:
        if 0 <= k < 512:
            result[k] = True
    return result

# Patch pygame before your game code imports it
pygame.mouse.get_pos     = _fake_mouse_get_pos
pygame.mouse.get_pressed = _fake_mouse_get_pressed
pygame.key.get_pressed   = _fake_key_get_pressed


# ---------------------------------------------------------------------------
# Key name mapping  (Kivy name -> pygame constant)
# ---------------------------------------------------------------------------

_KEY_MAP = {
    'enter':      pygame.K_RETURN,
    'numpadenter': pygame.K_KP_ENTER,
    'escape':     pygame.K_ESCAPE,
    'backspace':  pygame.K_BACKSPACE,
    'spacebar':   pygame.K_SPACE,
    'tab':        pygame.K_TAB,
    'up':         pygame.K_UP,
    'down':       pygame.K_DOWN,
    'left':       pygame.K_LEFT,
    'right':      pygame.K_RIGHT,
    'shift':      pygame.K_LSHIFT,
    'rshift':     pygame.K_RSHIFT,
    'ctrl':       pygame.K_LCTRL,
    'rctrl':      pygame.K_RCTRL,
    'alt':        pygame.K_LALT,
    'ralt':       pygame.K_RALT,
    'capslock':   pygame.K_CAPSLOCK,
    'delete':     pygame.K_DELETE,
    'insert':     pygame.K_INSERT,
    'home':       pygame.K_HOME,
    'end':        pygame.K_END,
    'pageup':     pygame.K_PAGEUP,
    'pagedown':   pygame.K_PAGEDOWN,
    'f1':  pygame.K_F1,  'f2':  pygame.K_F2,  'f3':  pygame.K_F3,
    'f4':  pygame.K_F4,  'f5':  pygame.K_F5,  'f6':  pygame.K_F6,
    'f7':  pygame.K_F7,  'f8':  pygame.K_F8,  'f9':  pygame.K_F9,
    'f10': pygame.K_F10, 'f11': pygame.K_F11, 'f12': pygame.K_F12,
}

def _kivy_to_pygame_key(name: str) -> int:
    if name in _KEY_MAP:
        return _KEY_MAP[name]
    if len(name) == 1:          # a-z, 0-9, punctuation
        return ord(name)
    return 0                    # unknown — ignored


# ---------------------------------------------------------------------------
# PygameWidget
# ---------------------------------------------------------------------------

class PygameWidget(Image):
    """
    Drop-in Kivy widget that:
      - runs your pygame drawing on an offscreen Surface
      - streams it to a Kivy texture at a chosen FPS
      - forwards touch events as pygame MOUSEBUTTONDOWN/UP + patches get_pos
      - forwards keyboard events as pygame KEYDOWN/UP   + patches get_pressed
      - fires a pygame QUIT event (and calls on_pygame_quit) on window close
    """

    def __init__(self, surface_size, fps=60, **kwargs):
        super().__init__(
            allow_stretch=True,
            keep_ratio=False,
            **kwargs
        )

        # ---- pygame headless init ----------------------------------------
        pygame.init()
        self.pg_surface = pygame.Surface(surface_size)

        # ---- keyboard -------------------------------------------------------
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_key_down)
        self._keyboard.bind(on_key_up=self._on_key_up)

        # ---- window close ---------------------------------------------------
        Window.bind(on_request_close=self._on_window_close)

        # ---- render loop ----------------------------------------------------
        Clock.schedule_interval(self._tick, 1.0 / fps)

    # ------------------------------------------------------------------
    # Override this in your subclass (or monkey-patch after instantiation)
    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface):
        """Called every frame. Draw everything onto `surface`."""
        pass                        # replace with your game's draw logic

    def on_pygame_quit(self):
        """Called when the user closes the window / presses Back on Android."""
        App.get_running_app().stop()

    # ------------------------------------------------------------------
    # Internal: render tick
    # ------------------------------------------------------------------

    def _tick(self, dt):
        self.draw(self.pg_surface)
        self._surface_to_texture()

    def _surface_to_texture(self):
        w, h = self.pg_surface.get_size()
        raw  = pygame.image.tostring(self.pg_surface, 'RGBA', True)
        tex  = Texture.create(size=(w, h), colorfmt='rgba')
        tex.blit_buffer(raw, colorfmt='rgba', bufferfmt='ubyte')
        self.texture = tex

    # ------------------------------------------------------------------
    # Touch → pygame mouse events
    # ------------------------------------------------------------------

    def _touch_to_pg(self, touch):
        """Convert Kivy touch coords to pygame surface coords."""
        # Kivy origin is bottom-left; pygame is top-left
        # Also scale in case the widget is not the same size as the surface
        if self.width == 0 or self.height == 0:
            return (0, 0)
        sw, sh = self.pg_surface.get_size()
        x = int((touch.x - self.x) / self.width  * sw)
        y = int((1.0 - (touch.y - self.y) / self.height) * sh)
        return (x, y)

    def on_touch_down(self, touch):
        global _mouse_pos, _mouse_buttons
        _mouse_pos     = self._touch_to_pg(touch)
        _mouse_buttons = (True, False, False)
        pygame.event.post(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            pos=_mouse_pos,
            button=1,
        ))
        return True     # consume event

    def on_touch_move(self, touch):
        global _mouse_pos
        _mouse_pos = self._touch_to_pg(touch)
        pygame.event.post(pygame.event.Event(
            pygame.MOUSEMOTION,
            pos=_mouse_pos,
            rel=(0, 0),
            buttons=(1, 0, 0),
        ))
        return True

    def on_touch_up(self, touch):
        global _mouse_pos, _mouse_buttons
        _mouse_pos     = self._touch_to_pg(touch)
        _mouse_buttons = (False, False, False)
        pygame.event.post(pygame.event.Event(
            pygame.MOUSEBUTTONUP,
            pos=_mouse_pos,
            button=1,
        ))
        return True

    # ------------------------------------------------------------------
    # Keyboard → pygame key events
    # ------------------------------------------------------------------

    def _keyboard_closed(self):
        if self._keyboard:
            self._keyboard.unbind(on_key_down=self._on_key_down)
            self._keyboard.unbind(on_key_up=self._on_key_up)
            self._keyboard = None

    def _on_key_down(self, keyboard, keycode, text, modifiers):
        k = _kivy_to_pygame_key(keycode[1])
        _pressed_keys[k] = True
        pygame.event.post(pygame.event.Event(
            pygame.KEYDOWN,
            key=k,
            unicode=text or '',
            mod=0,
        ))
        return True

    def _on_key_up(self, keyboard, keycode, *args):
        k = _kivy_to_pygame_key(keycode[1])
        _pressed_keys.pop(k, None)
        pygame.event.post(pygame.event.Event(
            pygame.KEYUP,
            key=k,
            mod=0,
        ))
        return True

    # ------------------------------------------------------------------
    # Window close / Android back button
    # ------------------------------------------------------------------

    def _on_window_close(self, *args):
        pygame.event.post(pygame.event.Event(pygame.QUIT))
        self.on_pygame_quit()
        return True     # prevent Kivy from closing immediately on desktop


# ---------------------------------------------------------------------------
# Example usage
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    from kivy.app import App

    class MyGame(PygameWidget):
        def __init__(self, **kwargs):
            super().__init__(surface_size=(800, 600), fps=60, **kwargs)
            self.font = pygame.font.SysFont(None, 48)

        def draw(self, surface):
            # --- put your real game draw code here ---
            surface.fill((30, 30, 30))
            mx, my = pygame.mouse.get_pos()
            pygame.draw.circle(surface, (255, 80, 80), (mx, my), 20)
            label = self.font.render(f'touch: {mx}, {my}', True, (255, 255, 255))
            surface.blit(label, (10, 10))


    from kivy.core.window import Window


    class DemoApp(App):
        def build(self):
            Window.fullscreen = 'auto'  # uses device's native resolution
            return MyGame(size_hint=(1, 1))

    DemoApp().run()
