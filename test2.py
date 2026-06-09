"""
my_pygame_app.py
================
Complete example of a Pygame game running inside Kivy via PygameWidget.

Demonstrates:
  - Game loop with delta time
  - Keyboard input (WASD / arrow keys)
  - Touch / mouse input
  - Soft keyboard toggle
  - Clean shutdown
"""

import pygame
from kivy.app import App
from kivy.core.window import Window

from widget import PygameWidget

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SURFACE_W, SURFACE_H = 480, 320
FPS = 60

PLAYER_SPEED = 200        # pixels per second
PLAYER_COLOR = (80, 200, 120)
PLAYER_RADIUS = 16
BG_COLOR = (18, 18, 28)
FONT_COLOR = (200, 200, 200)
TOUCH_COLOR = (255, 120, 60)


# ---------------------------------------------------------------------------
# Game state
# ---------------------------------------------------------------------------
class GameState:
    def __init__(self):
        self.x = SURFACE_W // 2
        self.y = SURFACE_H // 2
        self.keys_held: set[int] = set()      # pygame key constants
        self.touch_points: list[tuple[int, int]] = []
        self.last_key = ""
        self.font = None
        self.small_font = None

    def init_fonts(self):
        self.font = pygame.font.SysFont("monospace", 18)
        self.small_font = pygame.font.SysFont("monospace", 13)


# ---------------------------------------------------------------------------
# Kivy App
# ---------------------------------------------------------------------------
class MyPygameApp(App):

    def build(self):
        self.game = GameState()

        self.widget = PygameWidget(
            surface_size=(SURFACE_W, SURFACE_H),
            fps=FPS,
            size_hint=(1, 1),
        )

        # Bind all events
        self.widget.bind(on_pygame_frame=self.game_loop)
        self.widget.bind(on_pygame_keydown=self.on_key_down)
        self.widget.bind(on_pygame_keyup=self.on_key_up)
        self.widget.bind(on_pygame_touch=self.on_touch)

        # Intercept Android back button / Escape
        Window.bind(on_keyboard=self.on_back_button)

        return self.widget

    def on_start(self):
        self.game.init_fonts()

    def on_pause(self):
        # Return True to allow pause (Android); False would close the app
        return True

    def on_resume(self):
        pass

    def on_stop(self):
        self.widget.stop()
        pygame.quit()

    # ------------------------------------------------------------------
    # Back button (Android back / desktop Escape)
    # ------------------------------------------------------------------
    def on_back_button(self, window, key, *args):
        if key == 27:   # Escape / Android back
            self.widget.stop()
            pygame.quit()
            self.stop()
            return True
        return False

    # ------------------------------------------------------------------
    # Game loop — draw everything here
    # ------------------------------------------------------------------
    def game_loop(self, widget, surface: pygame.Surface, dt: float):
        game = self.game

        # --- Update player position from held keys ---
        dist = PLAYER_SPEED * dt
        if pygame.K_LEFT in game.keys_held or pygame.K_a in game.keys_held:
            game.x -= dist
        if pygame.K_RIGHT in game.keys_held or pygame.K_d in game.keys_held:
            game.x += dist
        if pygame.K_UP in game.keys_held or pygame.K_w in game.keys_held:
            game.y -= dist
        if pygame.K_DOWN in game.keys_held or pygame.K_s in game.keys_held:
            game.y += dist

        # Clamp to surface bounds
        game.x = max(PLAYER_RADIUS, min(SURFACE_W - PLAYER_RADIUS, game.x))
        game.y = max(PLAYER_RADIUS, min(SURFACE_H - PLAYER_RADIUS, game.y))

        # --- Draw background ---
        surface.fill(BG_COLOR)

        # --- Draw touch points ---
        for tx, ty in game.touch_points[-30:]:
            pygame.draw.circle(surface, TOUCH_COLOR, (tx, ty), 6)

        # --- Draw player ---
        pygame.draw.circle(surface, PLAYER_COLOR, (int(game.x), int(game.y)), PLAYER_RADIUS)

        # --- Mouse cursor indicator ---
        mx, my = widget.get_mouse_pos()
        pygame.draw.circle(surface, (255, 255, 100), (mx, my), 4)

        # --- HUD text ---
        if game.font:
            lines = [
                f"Player: ({int(game.x)}, {int(game.y)})",
                f"Mouse:  ({mx}, {my})",
                f"Key:    {game.last_key}",
            ]
            for i, line in enumerate(lines):
                surf = game.font.render(line, True, FONT_COLOR)
                surface.blit(surf, (8, 8 + i * 22))

        if game.small_font:
            hints = [
                "WASD / arrows = move",
                "Touch = drop dot",
                "K = toggle keyboard",
            ]
            for i, hint in enumerate(hints):
                surf = game.small_font.render(hint, True, (100, 100, 130))
                surface.blit(surf, (8, SURFACE_H - 14 - (len(hints) - 1 - i) * 16))

    # ------------------------------------------------------------------
    # Key events
    # ------------------------------------------------------------------
    def on_key_down(self, widget, key, scancode, codepoint, modifiers):
        self.game.last_key = key

        # Track held keys using pygame constants
        pg_key = _name_to_pg(key)
        if pg_key:
            self.game.keys_held.add(pg_key)

        # Toggle soft keyboard with K
        if key == "k":
            widget.toggle_keyboard()

    def on_key_up(self, widget, key, scancode, codepoint, modifiers):
        pg_key = _name_to_pg(key)
        if pg_key:
            self.game.keys_held.discard(pg_key)

    # ------------------------------------------------------------------
    # Touch events
    # ------------------------------------------------------------------
    def on_touch(self, widget, x, y, action):
        if action == "down":
            self.game.touch_points.append((x, y))


# ---------------------------------------------------------------------------
# Helper — key name → pygame constant
# ---------------------------------------------------------------------------
_KEY_MAP = {
    "left": pygame.K_LEFT, "right": pygame.K_RIGHT,
    "up": pygame.K_UP,     "down": pygame.K_DOWN,
    "a": pygame.K_a, "d": pygame.K_d,
    "w": pygame.K_w, "s": pygame.K_s,
    "space": pygame.K_SPACE, "spacebar": pygame.K_SPACE,
    "return": pygame.K_RETURN, "enter": pygame.K_RETURN,
    "escape": pygame.K_ESCAPE,
}

def _name_to_pg(name: str):
    return _KEY_MAP.get(name.lower())


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    MyPygameApp().run()