"""
Pygame Slider Class
-------------------
A reusable, customizable slider widget for Pygame applications.

Usage:
    slider = Slider(x=100, y=200, width=300, min_val=0, max_val=100, initial=50)

    # In your event loop:
    for event in pygame.event.get():
        slider.handle_event(event)

    # In your draw loop:
    slider.draw(screen)

    # Get current value:
    value = slider.value
"""

import pygame


class Slider:
    """
    A horizontal slider widget for Pygame.

    Attributes:
        value (float): Current value of the slider (read/write).
    """

    def __init__(
        self,
        x: int,
        y: int,
        width: int = 300,
        height: int = 6,
        min_val: float = 0,
        max_val: float = 100,
        initial: float = None,
        handle_radius: int = 12,
        track_color: tuple = (80, 80, 100),
        fill_color: tuple = (100, 149, 237),   # cornflower blue
        handle_color: tuple = (255, 255, 255),
        handle_border_color: tuple = (100, 149, 237),
        label: str = None,
        font: pygame.font.Font = None,
        text_color: tuple = (220, 220, 220),
        show_value: bool = True,
        value_format: str = "{:.0f}",
        step: float = None,
    ):
        """
        Args:
            x, y            : Top-left origin of the track.
            width           : Track width in pixels.
            height          : Track height in pixels.
            min_val         : Minimum value.
            max_val         : Maximum value.
            initial         : Starting value (defaults to min_val).
            handle_radius   : Radius of the draggable handle circle.
            track_color     : RGB color of the unfilled track.
            fill_color      : RGB color of the filled (left) portion of the track.
            handle_color    : RGB fill color of the handle.
            handle_border_color : RGB border color of the handle.
            label           : Optional text label drawn above the slider.
            font            : pygame.font.Font instance (created automatically if None).
            text_color      : RGB color for label and value text.
            show_value      : Whether to display the current value next to the handle.
            value_format    : Python format string used to display the value.
            step            : Snap increment (e.g. 0.5, 5, 0.1). None = continuous.
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.min_val = min_val
        self.max_val = max_val
        self.step = step
        raw = initial if initial is not None else min_val
        self._value = self._snap(raw)

        self.handle_radius = handle_radius
        self.track_color = track_color
        self.fill_color = fill_color
        self.handle_color = handle_color
        self.handle_border_color = handle_border_color

        self.label = label
        self.text_color = text_color
        self.show_value = show_value
        self.value_format = value_format

        if font is None:
            pygame.font.init()
            self.font = pygame.font.SysFont("segoeui", 14)
        else:
            self.font = font

        self._dragging = False
        self._hovered = False

    # ------------------------------------------------------------------ #
    #  Public API                                                           #
    # ------------------------------------------------------------------ #

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, v: float):
        self._value = self._snap(v)

    def _snap(self, v: float) -> float:
        """Clamp *v* to [min_val, max_val] and snap to the nearest step if set."""
        v = max(self.min_val, min(self.max_val, v))
        if self.step is not None and self.step > 0:
            steps = round((v - self.min_val) / self.step)
            v = self.min_val + steps * self.step
            # Re-clamp after rounding
            v = max(self.min_val, min(self.max_val, v))
        return v

    @property
    def normalized(self) -> float:
        """Value mapped to [0, 1]."""
        span = self.max_val - self.min_val
        return (self._value - self.min_val) / span if span != 0 else 0

    # ------------------------------------------------------------------ #
    #  Event handling                                                       #
    # ------------------------------------------------------------------ #

    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Process a Pygame event.

        Returns True if the slider consumed the event (was interacted with).
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._handle_rect().collidepoint(event.pos) or \
               self._track_rect().collidepoint(event.pos):
                self._dragging = True
                self._update_value(event.pos[0])
                return True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self._dragging:
                self._dragging = False
                return True

        elif event.type == pygame.MOUSEMOTION:
            self._hovered = self._handle_rect().collidepoint(event.pos)
            if self._dragging:
                self._update_value(event.pos[0])
                return True

        return False

    # ------------------------------------------------------------------ #
    #  Drawing                                                              #
    # ------------------------------------------------------------------ #

    def draw(self, surface: pygame.Surface):
        """Draw the slider onto *surface*."""
        cx = self._handle_cx()

        # --- Label ---
        if self.label:
            label_surf = self.font.render(self.label, True, self.text_color)
            surface.blit(label_surf, (self.x, self.y - label_surf.get_height() - 6))

        # --- Track (background) ---
        track = self._track_rect()
        pygame.draw.rect(surface, self.track_color, track, border_radius=self.height)

        # --- Fill (left portion) ---
        fill_w = cx - self.x
        if fill_w > 0:
            fill_rect = pygame.Rect(self.x, self.y, fill_w, self.height)
            pygame.draw.rect(surface, self.fill_color, fill_rect, border_radius=self.height)

        # --- Handle ---
        r = self.handle_radius + (2 if self._hovered or self._dragging else 0)
        handle_y = self.y + self.height // 2
        pygame.draw.circle(surface, self.handle_border_color, (cx, handle_y), r)
        pygame.draw.circle(surface, self.handle_color, (cx, handle_y), r - 2)

        # --- Value label ---
        if self.show_value:
            val_text = self.value_format.format(self._value)
            val_surf = self.font.render(val_text, True, self.text_color)
            surface.blit(val_surf, (cx + r + 6, handle_y - val_surf.get_height() // 2))

    # ------------------------------------------------------------------ #
    #  Internals                                                            #
    # ------------------------------------------------------------------ #

    def _handle_cx(self) -> int:
        """X-coordinate of the handle center."""
        return int(self.x + self.normalized * self.width)

    def _handle_rect(self) -> pygame.Rect:
        cx = self._handle_cx()
        cy = self.y + self.height // 2
        r = self.handle_radius
        return pygame.Rect(cx - r, cy - r, r * 2, r * 2)

    def _track_rect(self) -> pygame.Rect:
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def _update_value(self, mouse_x: int):
        ratio = (mouse_x - self.x) / self.width
        ratio = max(0.0, min(1.0, ratio))
        raw = self.min_val + ratio * (self.max_val - self.min_val)
        self._value = self._snap(raw)


# ------------------------------------------------------------------ #
#  Demo — run this file directly to see the slider in action           #
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((600, 400))
    pygame.display.set_caption("Slider Demo")
    clock = pygame.time.Clock()

    font = pygame.font.SysFont("segoeui", 14)

    sliders = [
        Slider(100, 120, width=380, min_val=0,   max_val=255, initial=128,
               label="Red",   fill_color=(200, 60, 60),  font=font,show_value=True, value_format="{:.1f}",step=0.5),
        Slider(100, 190, width=380, min_val=0,   max_val=255, initial=180,
               label="Green", fill_color=(60, 180, 60),  font=font),
        Slider(100, 260, width=380, min_val=0,   max_val=255, initial=220,
               label="Blue",  fill_color=(60, 100, 220), font=font),
        Slider(100, 330, width=380, min_val=0.0, max_val=1.0, initial=0.5,
               label="Float — step 0.1", value_format="{:.1f}", step=0.1, font=font),
    ]

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            for s in sliders:
                s.handle_event(event)

        r, g, b = (int(sliders[i].value) for i in range(3))
        screen.fill((20, 20, 30))

        # Colour swatch driven by the RGB sliders
        pygame.draw.rect(screen, (r, g, b), pygame.Rect(220, 30, 140, 60), border_radius=8)

        for s in sliders:
            s.draw(screen)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()