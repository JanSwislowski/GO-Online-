import pygame
import math


class ScoreLabel:
    """
    A pygame label that displays a score with animation support.

    Features:
    - Renders like a normal text label
    - increase_by_one(): bumps score by 1 with a pop/bounce animation
    - set_score(x): animates score counting up or down to x in intervals
    """

    # Animation states
    _IDLE = "idle"
    _BUMP = "bump"          # quick pop on +1
    _COUNTING = "counting"  # gradual count toward target

    def __init__(
        self,
        x: int,
        y: int,
        font: pygame.font.Font,
        color: tuple = (255, 255, 255),
        initial_score: int = 0,
        count_interval_ms: int = 50,   # ms between each +1/-1 step when counting
        bump_duration_ms: int = 300,   # ms for the +1 bump animation
        anchor: str = "topleft",       # topleft | center | midleft | midright …
    ):
        self.x = x
        self.y = y
        self.font = font
        self.color = color
        self.score = initial_score
        self._target_score = initial_score
        self.anchor = anchor

        # Counting animation
        self._count_interval = count_interval_ms
        self._count_timer = 0

        # Bump animation (scale + translate)
        self._bump_duration = bump_duration_ms
        self._bump_timer = 0
        self._bump_scale = 1.0
        self._bump_offset_y = 0.0

        self._state = self._IDLE
        self._last_ticks = pygame.time.get_ticks()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def increase_by_one(self):
        """Increment score by 1 and play the pop animation."""
        self.score += 1
        self._target_score = self.score
        self._start_bump()

    def set_score(self, target: int):
        """Animate the score counting up or down to *target*."""
        self._target_score = target
        if self._target_score != self.score:
            self._state = self._COUNTING
            self._count_timer = 0

    # ------------------------------------------------------------------
    # Update / Draw
    # ------------------------------------------------------------------

    def update(self):
        """Call every frame — dt is measured internally."""
        now = pygame.time.get_ticks()
        dt_ms = now - self._last_ticks
        self._last_ticks = now

        if self._state == self._BUMP:
            self._update_bump(dt_ms)
        elif self._state == self._COUNTING:
            self._update_counting(dt_ms)

    def draw(self, surface: pygame.Surface):
        """Render the label onto *surface*."""
        text_surf = self.font.render(str(self.score), True, self.color)

        # Apply scale from bump animation
        if self._bump_scale != 1.0:
            w = max(1, int(text_surf.get_width() * self._bump_scale))
            h = max(1, int(text_surf.get_height() * self._bump_scale))
            text_surf = pygame.transform.smoothscale(text_surf, (w, h))

        # Position using chosen anchor
        rect = text_surf.get_rect()
        setattr(rect, self.anchor, (self.x, int(self.y + self._bump_offset_y)))

        surface.blit(text_surf, rect)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _start_bump(self):
        self._state = self._BUMP
        self._bump_timer = 0

    def _update_bump(self, dt_ms: float):
        self._bump_timer += dt_ms
        t = min(self._bump_timer / self._bump_duration, 1.0)

        self._bump_scale = 1.0 + 0.35 * math.sin(math.pi * t) * (1.0 - t)
        self._bump_offset_y = -8 * math.sin(math.pi * t) * (1.0 - t)

        if t >= 1.0:
            self._bump_scale = 1.0
            self._bump_offset_y = 0.0
            self._state = self._IDLE

    def _update_counting(self, dt_ms: float):
        self._count_timer += dt_ms
        if self._count_timer >= self._count_interval:
            self._count_timer -= self._count_interval

            if self.score < self._target_score:
                self.score += 1
            elif self.score > self._target_score:
                self.score -= 1

            if self.score == self._target_score:
                self._state = self._IDLE


# ===========================================================================
# Demo — run this file directly to see it in action
# ===========================================================================

def _run_demo():
    pygame.init()
    screen = pygame.display.set_mode((520, 300))
    pygame.display.set_caption("ScoreLabel Demo")
    clock = pygame.time.Clock()

    font_large = pygame.font.SysFont("Arial", 72, bold=True)
    font_small = pygame.font.SysFont("Arial", 22)

    label = ScoreLabel(
        x=260, y=100,
        font=font_large,
        color=(255, 220, 50),
        initial_score=0,
        count_interval_ms=40,
        bump_duration_ms=280,
        anchor="center",
    )

    instructions = [
        ("SPACE", "increase_by_one()"),
        ("UP",    "set_score(score + 50)"),
        ("DOWN",  "set_score(score - 30)"),
        ("R",     "set_score(0)"),
    ]

    running = True
    while running:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    label.increase_by_one()
                elif event.key == pygame.K_UP:
                    label.set_score(label._target_score + 50)
                elif event.key == pygame.K_DOWN:
                    label.set_score(label._target_score - 30)
                elif event.key == pygame.K_r:
                    label.set_score(0)
                elif event.key == pygame.K_ESCAPE:
                    running = False

        label.update()

        screen.fill((30, 30, 45))

        hdr = font_small.render("ScoreLabel Demo", True, (180, 180, 220))
        screen.blit(hdr, (20, 20))

        label.draw(screen)

        for i, (key, action) in enumerate(instructions):
            line = font_small.render(f"[{key}]  {action}", True, (140, 140, 170))
            screen.blit(line, (20, 200 + i * 26))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    _run_demo()