import pygame
import math
pygame.init()

font=pygame.font.SysFont("TimesNewRoman", 18)
fontmid=pygame.font.SysFont("TimesNewRoman", 30)
font_big=pygame.font.SysFont("TimesNewRoman", 40)
def add_vectors(v1, v2):
    return (v1[0] + v2[0], v1[1] + v2[1])


class TextBox:
    """
    A Pygame text input box with:
    - Polish character support (ą ć ę ł ń ó ś ź ż and uppercase)
    - Cursor movement via LEFT / RIGHT arrow keys
    - UP / DOWN arrow keys move between wrapped lines (wrap mode only)
    - HOME / END jump to start / end of line (or whole text in single-line)
    - Ctrl+LEFT / Ctrl+RIGHT jump word-by-word
    - Hold BACKSPACE to delete repeatedly (initial delay then fast repeat)
    - Scrolling viewport when text is longer than the box (single-line mode)
    - word-wrap=True: text wraps onto new lines, box height grows automatically

    Constructor parameters
    ----------------------
    x, y, width, height  – position and base size
    wrap                 – if True text wraps and height grows to fit content
    font / font_size
    max_length           – 0 = unlimited
    placeholder
    color_inactive / color_active / color_bg / color_text /
    color_cursor / color_placeholder
    border_radius / border_width / padding

    Public API
    ----------
    handle_event(event)  – call in your event loop
    update()             – call once per frame
    draw(surface)        – render the widget
    get_text() -> str    – current text (newlines preserved in wrap mode)
    set_text(text)       – programmatically set text
    clear()              – empty the box
    """

    POLISH_CHARS = set("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ")

    _REPEAT_DELAY = 400   # ms before key-repeat starts
    _REPEAT_RATE  = 45    # ms between repeats

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        wrap: bool = False,
        font=None,
        font_size: int = 24,
        max_length: int = 0,
        placeholder: str = "",
        color_inactive:    tuple = (160, 160, 175),
        color_active:      tuple = (80, 120, 255),
        color_bg:          tuple = (245, 245, 250),
        color_text:        tuple = (30, 30, 40),
        color_cursor:      tuple = (80, 120, 255),
        color_placeholder: tuple = (180, 180, 195),
        border_radius: int = 6,
        border_width:  int = 2,
        padding:       int = 8,
    ):
        self._base_x      = x
        self._base_y      = y
        self._base_width  = width
        self._base_height = height
        self.wrap         = wrap

        # rect is kept up-to-date; in wrap mode height grows
        self.rect = pygame.Rect(x, y, width, height)

        self.max_length  = max_length
        self.placeholder = placeholder

        self.color_inactive    = color_inactive
        self.color_active      = color_active
        self.color_bg          = color_bg
        self.color_text        = color_text
        self.color_cursor      = color_cursor
        self.color_placeholder = color_placeholder
        self.border_radius     = border_radius
        self.border_width      = border_width
        self.padding           = padding

        self.font = font if font is not None else self._load_default_font(font_size)
        self._line_h = self.font.get_linesize()

        # text & cursor
        self._text:   str = ""
        self._cursor: int = 0          # absolute char index into _text

        # cursor blink
        self.active:           bool = False
        self._cursor_visible:  bool = True
        self._cursor_timer:    int  = 0
        self._cursor_blink_ms: int  = 500

        # hold-key repeat
        self._held_key:       object = None
        self._held_key_time:  int    = 0
        self._next_repeat_at: int    = 0
        self._in_repeat:      bool   = False

        # single-line scroll (only used when wrap=False)
        self._scroll: int = 0

    # ----------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------

    def handle_event(self, event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN:
            newly_active = self.rect.collidepoint(event.pos)
            if newly_active and not self.active:
                self._reset_blink()
            elif newly_active and self.wrap:
                # click-to-position cursor in wrap mode
                self._cursor = self._pos_to_cursor(event.pos)
            self.active = newly_active

        if not self.active:
            return

        if event.type == pygame.KEYDOWN:
            self._on_keydown(event)

        if event.type == pygame.KEYUP:
            if event.key == self._held_key:
                self._held_key = None

    def update(self) -> None:
        now = pygame.time.get_ticks()

        if now - self._cursor_timer >= self._cursor_blink_ms:
            self._cursor_visible = not self._cursor_visible
            self._cursor_timer   = now

        if self.active and self._held_key is not None:
            if not self._in_repeat:
                if now >= self._next_repeat_at:
                    self._in_repeat      = True
                    self._next_repeat_at = now + self._REPEAT_RATE
                    self._apply_key(self._held_key)
            else:
                while now >= self._next_repeat_at:
                    self._next_repeat_at += self._REPEAT_RATE
                    self._apply_key(self._held_key)

        # keep rect.height in sync when wrapping
        if self.wrap:
            self._sync_height()

    def draw(self, surface) -> None:
        if self.wrap:
            self._draw_wrap(surface)
        else:
            self._draw_single(surface)

    def get_text(self) -> str:
        return self._text

    def set_text(self, text: str) -> None:
        self._text   = text
        self._cursor = len(text)
        self._scroll = 0
        if self.wrap:
            self._sync_height()

    def clear(self) -> None:
        self._text   = ""
        self._cursor = 0
        self._scroll = 0
        if self.wrap:
            self._sync_height()

    # ----------------------------------------------------------------
    # Drawing – single-line (scroll) mode
    # ----------------------------------------------------------------

    def _draw_single(self, surface) -> None:
        pygame.draw.rect(surface, self.color_bg, self.rect,
                         border_radius=self.border_radius)
        border_color = self.color_active if self.active else self.color_inactive
        pygame.draw.rect(surface, border_color, self.rect,
                         width=self.border_width,
                         border_radius=self.border_radius)

        inner_x = self.rect.x + self.padding
        inner_y = self.rect.y + (self.rect.height - self.font.get_height()) // 2
        max_w   = self.rect.width - 2 * self.padding

        if not self._text and self.placeholder and not self.active:
            surface.blit(self.font.render(self.placeholder, True,
                                          self.color_placeholder), (inner_x, inner_y))
            return

        cursor_px = self.font.size(self._text[:self._cursor])[0]

        if cursor_px - self._scroll > max_w:
            self._scroll = cursor_px - max_w
        elif cursor_px - self._scroll < 0:
            self._scroll = cursor_px

        clip = pygame.Rect(inner_x, self.rect.y + self.border_width,
                           max_w, self.rect.height - 2 * self.border_width)
        old_clip = surface.get_clip()
        surface.set_clip(clip)

        surface.blit(self.font.render(self._text, True, self.color_text),
                     (inner_x - self._scroll, inner_y))

        if self.active and self._cursor_visible:
            cx = inner_x + cursor_px - self._scroll
            pygame.draw.line(surface, self.color_cursor,
                             (cx, inner_y),
                             (cx, inner_y + self.font.get_height() - 1), 2)

        surface.set_clip(old_clip)

    # ----------------------------------------------------------------
    # Drawing – wrap mode
    # ----------------------------------------------------------------

    def _draw_wrap(self, surface) -> None:
        pygame.draw.rect(surface, self.color_bg, self.rect,
                         border_radius=self.border_radius)
        border_color = self.color_active if self.active else self.color_inactive
        pygame.draw.rect(surface, border_color, self.rect,
                         width=self.border_width,
                         border_radius=self.border_radius)

        inner_x = self.rect.x + self.padding
        inner_y = self.rect.y + self.padding
        max_w   = self.rect.width - 2 * self.padding

        if not self._text and self.placeholder and not self.active:
            surface.blit(self.font.render(self.placeholder, True,
                                          self.color_placeholder), (inner_x, inner_y))
            return

        lines            = self._wrap_text(self._text, max_w)
        cur_line, cur_col = self._cursor_line_col(lines)

        for li, line in enumerate(lines):
            y = inner_y + li * self._line_h
            surface.blit(self.font.render(line, True, self.color_text),
                         (inner_x, y))

        # draw cursor
        if self.active and self._cursor_visible:
            cl   = lines[cur_line] if lines else ""
            cx   = inner_x + self.font.size(cl[:cur_col])[0]
            cy   = inner_y + cur_line * self._line_h
            pygame.draw.line(surface, self.color_cursor,
                             (cx, cy),
                             (cx, cy + self.font.get_height() - 1), 2)

    # ----------------------------------------------------------------
    # Height management (wrap mode)
    # ----------------------------------------------------------------

    def _sync_height(self) -> None:
        max_w = self._base_width - 2 * self.padding
        lines = self._wrap_text(self._text, max_w) if self._text else [""]
        needed = len(lines) * self._line_h + 2 * self.padding
        new_h  = max(self._base_height, needed)
        self.rect = pygame.Rect(self._base_x, self._base_y,
                                self._base_width, new_h)

    # ----------------------------------------------------------------
    # Wrap helper
    # ----------------------------------------------------------------

    def _wrap_text(self, text: str, max_w: int) -> list:
        """
        Word-wrap *text* into lines that fit within *max_w* pixels.
        Hard newlines (\\n) in the text are also respected.
        Returns a list of strings (may be empty strings for blank lines).
        """
        result = []
        for paragraph in text.split("\n"):
            if not paragraph:
                result.append("")
                continue
            words = paragraph.split(" ")
            line  = ""
            for word in words:
                # a single word wider than max_w: character-break it
                if self.font.size(word)[0] > max_w:
                    if line:
                        result.append(line)
                        line = ""
                    chunk = ""
                    for ch in word:
                        if self.font.size(chunk + ch)[0] <= max_w:
                            chunk += ch
                        else:
                            result.append(chunk)
                            chunk = ch
                    line = chunk
                    continue

                test = (line + " " + word).strip()
                if self.font.size(test)[0] <= max_w:
                    line = test
                else:
                    if line:
                        result.append(line)
                    line = word
            result.append(line)
        return result if result else [""]

    def _wrap_text_with_meta(self, text: str, max_w: int):
        """
        Same as _wrap_text but also returns, for each line, how many
        characters from *text* it consumed (its 'char width' in the
        original string).  This is used by the cursor converters so
        they know exactly how many source characters each visual line
        accounts for — soft-wrapped lines consume only len(line) chars
        (no separator), while hard-newline breaks consume len(line)+1.

        Returns: list of (line_str, chars_consumed)
        """
        result  = []   # (line_str, chars_consumed)
        paragraphs = text.split("\n")
        for pi, paragraph in enumerate(paragraphs):
            hard_newline = pi < len(paragraphs) - 1   # True except last paragraph
            if not paragraph:
                # empty paragraph = bare \n in source
                result.append(("", 1 if hard_newline else 0))
                continue
            words = paragraph.split(" ")
            line  = ""
            for word in words:
                if self.font.size(word)[0] > max_w:
                    if line:
                        result.append((line, len(line)))   # soft break – no extra char
                        line = ""
                    chunk = ""
                    for ch in word:
                        if self.font.size(chunk + ch)[0] <= max_w:
                            chunk += ch
                        else:
                            result.append((chunk, len(chunk)))  # soft break
                            chunk = ch
                    line = chunk
                    continue

                test = (line + " " + word).strip()
                if self.font.size(test)[0] <= max_w:
                    line = test
                else:
                    if line:
                        result.append((line, len(line)))    # soft break
                    line = word

            # last line of this paragraph
            if hard_newline:
                result.append((line, len(line) + 1))   # +1 for the \n character
            else:
                result.append((line, len(line)))        # no separator at end of text

        return result if result else [("", 0)]

    # ----------------------------------------------------------------
    # Cursor ↔ line/col conversion (wrap mode)
    # ----------------------------------------------------------------

    def _cursor_line_col(self, lines: list) -> tuple:
        """
        Return (line_index, col_in_line) for self._cursor.
        *lines* is the plain list from _wrap_text(); we re-derive meta
        internally so callers don't need to change.
        """
        max_w = self._base_width - 2 * self.padding
        meta  = self._wrap_text_with_meta(self._text, max_w)
        pos   = 0
        for li, (line, consumed) in enumerate(meta):
            end = pos + len(line)
            if self._cursor <= end:
                return li, self._cursor - pos
            pos += consumed
        return len(meta) - 1, len(meta[-1][0]) if meta else 0

    def _line_col_to_cursor(self, lines: list, line_i: int, col: int) -> int:
        """Inverse of _cursor_line_col."""
        max_w = self._base_width - 2 * self.padding
        meta  = self._wrap_text_with_meta(self._text, max_w)
        pos   = 0
        for i, (line, consumed) in enumerate(meta):
            if i == line_i:
                return pos + max(0, min(col, len(line)))
            pos += consumed
        return len(self._text)

    def _pos_to_cursor(self, mouse_pos) -> int:
        """Click-to-cursor: find the closest character to a mouse position."""
        max_w  = self._base_width - 2 * self.padding
        lines  = self._wrap_text(self._text, max_w)
        ix     = self._base_x + self.padding
        iy     = self._base_y + self.padding
        rel_y  = mouse_pos[1] - iy
        li     = max(0, min(len(lines) - 1, rel_y // self._line_h))
        line   = lines[li]
        rel_x  = mouse_pos[0] - ix
        best_col = len(line)
        for col in range(len(line) + 1):
            if self.font.size(line[:col])[0] >= rel_x:
                best_col = col
                break
        return self._line_col_to_cursor(lines, li, best_col)

    # ----------------------------------------------------------------
    # Key handling
    # ----------------------------------------------------------------

    def _on_keydown(self, event) -> None:
        key = event.key
        repeatable = {
            pygame.K_BACKSPACE,
            pygame.K_LEFT, pygame.K_RIGHT,
            pygame.K_UP, pygame.K_DOWN,
            pygame.K_HOME, pygame.K_END,
        }
        self._apply_key(key, event=event)
        self._reset_blink()
        if key in repeatable:
            self._held_key       = key
            self._held_key_time  = pygame.time.get_ticks()
            self._next_repeat_at = self._held_key_time + self._REPEAT_DELAY
            self._in_repeat      = False

    def _apply_key(self, key, event=None) -> None:
        ctrl = pygame.key.get_mods() & pygame.KMOD_CTRL

        if key == pygame.K_BACKSPACE:
            self._do_backspace(ctrl)

        elif key == pygame.K_LEFT:
            self._cursor = self._word_left() if ctrl else max(0, self._cursor - 1)

        elif key == pygame.K_RIGHT:
            self._cursor = (self._word_right() if ctrl
                            else min(len(self._text), self._cursor + 1))

        elif key == pygame.K_HOME:
            if self.wrap:
                max_w = self._base_width - 2 * self.padding
                lines = self._wrap_text(self._text, max_w)
                li, _  = self._cursor_line_col(lines)
                self._cursor = self._line_col_to_cursor(lines, li, 0)
            else:
                self._cursor = 0

        elif key == pygame.K_END:
            if self.wrap:
                max_w = self._base_width - 2 * self.padding
                lines = self._wrap_text(self._text, max_w)
                li, _  = self._cursor_line_col(lines)
                self._cursor = self._line_col_to_cursor(lines, li, len(lines[li]))
            else:
                self._cursor = len(self._text)

        elif key == pygame.K_UP and self.wrap:
            self._move_cursor_vertical(-1)

        elif key == pygame.K_DOWN and self.wrap:
            self._move_cursor_vertical(+1)

        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if self.wrap:
                # insert a real newline character
                if self.max_length == 0 or len(self._text) < self.max_length:
                    self._text    = self._text[:self._cursor] + "\n" + self._text[self._cursor:]
                    self._cursor += 1
                    self._sync_height()
            else:
                self.active    = False
                self._held_key = None

        elif event is not None:
            char = event.unicode
            if char and self._is_accepted(char):
                if self.max_length == 0 or len(self._text) < self.max_length:
                    self._text    = self._text[:self._cursor] + char + self._text[self._cursor:]
                    self._cursor += 1
                    if self.wrap:
                        self._sync_height()

    def _move_cursor_vertical(self, direction: int) -> None:
        """Move cursor up (-1) or down (+1) one visual line, preserving column."""
        max_w  = self._base_width - 2 * self.padding
        lines  = self._wrap_text(self._text, max_w)
        li, col = self._cursor_line_col(lines)
        # pixel offset of current column (preserve x visually)
        cur_px = self.font.size(lines[li][:col])[0]

        new_li = li + direction
        if new_li < 0 or new_li >= len(lines):
            return

        # find the closest column in the target line to the same x pixel
        target_line = lines[new_li]
        best_col    = len(target_line)
        for c in range(len(target_line) + 1):
            if self.font.size(target_line[:c])[0] >= cur_px:
                best_col = c
                break
        self._cursor = self._line_col_to_cursor(lines, new_li, best_col)

    def _do_backspace(self, ctrl: bool) -> None:
        if ctrl:
            new_pos      = self._word_left()
            self._text   = self._text[:new_pos] + self._text[self._cursor:]
            self._cursor = new_pos
        else:
            if self._cursor > 0:
                self._text    = self._text[:self._cursor - 1] + self._text[self._cursor:]
                self._cursor -= 1
        if self.wrap:
            self._sync_height()

    def _word_left(self) -> int:
        pos = self._cursor
        while pos > 0 and self._text[pos - 1] in (" ", "\n"):
            pos -= 1
        while pos > 0 and self._text[pos - 1] not in (" ", "\n"):
            pos -= 1
        return pos

    def _word_right(self) -> int:
        pos  = self._cursor
        size = len(self._text)
        while pos < size and self._text[pos] not in (" ", "\n"):
            pos += 1
        while pos < size and self._text[pos] in (" ", "\n"):
            pos += 1
        return pos

    def _reset_blink(self) -> None:
        self._cursor_visible = True
        self._cursor_timer   = pygame.time.get_ticks()

    @staticmethod
    def _load_default_font(size: int):
        for name in ("dejavusans", "freesans", "liberationsans",
                     "arial", "calibri", "segoeui", "noto"):
            f = pygame.font.SysFont(name, size)
            if f:
                return f
        return pygame.font.Font(None, size)

    @staticmethod
    def _is_accepted(char: str) -> bool:
        if char in TextBox.POLISH_CHARS:
            return True
        return len(char) == 1 and char.isprintable()

class Button:
    """
    A polished Pygame button with click animations, hover effects,
    and support for a text label, an image, or both side-by-side.

    Animation layers
    ----------------
    1. Hover  – smoothly brightens background and lifts with a shadow
    2. Press  – shrinks slightly (scale-down) and darkens instantly
    3. Release ripple – an expanding translucent circle fades out
    4. Idle   – subtle breathing pulse on the shadow (optional)

    Constructor
    -----------
    x, y, width, height  – position and size
    label                – text string (may be "" or None)
    image                – pygame.Surface (optional icon/image)
    image_size           – (w, h) to scale image to; None = use as-is
    callback             – callable invoked on successful click (optional)

    Style knobs
    -----------
    font / font_size     – label font
    color_bg             – base background colour
    color_hover          – background on hover
    color_press          – background while pressed
    color_text           – label colour
    color_ripple         – ripple colour (alpha handled internally)
    border_radius        – corner rounding
    border_width         – 0 = no border
    border_color         – border colour
    padding_x/y          – inner padding
    icon_gap             – gap between icon and label (pixels)
    shadow               – draw drop shadow
    shadow_color         – shadow rgba

    Public API
    ----------
    handle_event(event)  – call in your event loop
    update()             – call once per frame
    draw(surface)        – render
    is_hovered()         – bool
    enable() / disable() – toggle interactive state
    """

    # Animation timing (seconds)
    _HOVER_SPEED = 8.0  # lerp speed for hover colour transition
    _RIPPLE_LIFE = 0.45  # seconds a ripple lives
    _PRESS_SCALE = 0.94  # scale factor while pressed
    _SHADOW_NORMAL = 4  # shadow blur radius at rest
    _SHADOW_HOVER = 8  # shadow blur radius on hover

    def __init__(
            self,
            x: int,
            y: int,
            width: int,
            height: int,
            label: str = "",
            image: "pygame.Surface | None" = None,
            image_size: "tuple[int,int] | None" = None,
            callback=None,
            # style
            font=None,
            font_size: int = 22,
            color_bg: tuple = (255, 255, 255),
            color_hover: tuple = (230, 238, 255),
            color_press: tuple = (200, 215, 245),
            color_text: tuple = (30, 35, 60),
            color_ripple: tuple = (100, 140, 255),
            border_radius: int = 10,
            border_width: int = 2,
            border_color: tuple = (180, 195, 230),
            padding_x: int = 18,
            padding_y: int = 10,
            icon_gap: int = 10,
            shadow: bool = True,
            shadow_color: tuple = (80, 100, 160, 60),
            enabled: bool = True,
            pos_type="topleft"

    ):
        if pos_type=="center":
            x -= width//2
        if pos_type=="centery":
            y -= height//2
        self._base_rect = pygame.Rect(x, y, width, height)
        self.rect = self._base_rect.copy()

        self.label = label or ""
        self.callback = callback
        self.enabled = enabled

        # colours
        self._color_bg = color_bg
        self._color_hover = color_hover
        self._color_press = color_press
        self._color_text = color_text
        self._color_ripple = color_ripple
        self._border_radius = border_radius
        self._border_width = border_width
        self._border_color = border_color
        self._padding_x = padding_x
        self._padding_y = padding_y
        self._icon_gap = icon_gap
        self._shadow = shadow
        self._shadow_color = shadow_color

        # font
        if font is not None:
            self._font = font
        else:
            self._font = self._load_font(font_size)

        # image / icon
        if image is not None and image_size is not None:
            self._image = pygame.transform.smoothscale(image, image_size)
        else:
            self._image = image

        # animation state
        self._hovered: bool = False
        self._pressed: bool = False
        self._hover_t: float = 0.0  # 0=normal, 1=fully hovered
        self._scale: float = 1.0
        self._ripples: list = []  # [(cx,cy,birth_time)]
        self._clock_ref: int = pygame.time.get_ticks()

        # disabled style
        self._alpha_disabled = 120

    # ----------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------

    def handle_event(self, event) -> bool:
        """
        Feed a pygame event.
        Returns True if the button was clicked (and callback fired).
        """
        if not self.enabled:
            return False

        if event.type == pygame.MOUSEMOTION:
            self._hovered = self._base_rect.collidepoint(event.pos)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._base_rect.collidepoint(event.pos):
                self._pressed = True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            was_pressed = self._pressed
            self._pressed = False
            if was_pressed and self._base_rect.collidepoint(event.pos):
                # Spawn ripple at click position
                self._ripples.append({
                    "cx": event.pos[0] - self._base_rect.x,
                    "cy": event.pos[1] - self._base_rect.y,
                    "born": pygame.time.get_ticks() / 1000.0,
                })
                if self.callback:
                    self.callback()
                return True
        return False

    def update(self) -> None:
        """Call once per frame."""
        now = pygame.time.get_ticks() / 1000.0
        dt = now - self._clock_ref / 1000.0
        self._clock_ref = pygame.time.get_ticks()

        # Smooth hover lerp
        target = 1.0 if (self._hovered and not self._pressed) else 0.0
        self._hover_t += (target - self._hover_t) * min(1.0, self._HOVER_SPEED * dt)

        # Scale spring
        target_scale = self._PRESS_SCALE if self._pressed else 1.0
        self._scale += (target_scale - self._scale) * min(1.0, 18.0 * dt)

        # Prune dead ripples
        self._ripples = [r for r in self._ripples
                         if now - r["born"] < self._RIPPLE_LIFE]

    def draw(self, surface: pygame.Surface) -> None:
        """Render the button."""
        now = pygame.time.get_ticks() / 1000.0

        # Compute scaled rect (centred on base rect)
        cx = self._base_rect.centerx
        cy = self._base_rect.centery
        sw = int(self._base_rect.width * self._scale)
        sh = int(self._base_rect.height * self._scale)
        draw_rect = pygame.Rect(cx - sw // 2, cy - sh // 2, sw, sh)

        # ── draw onto an intermediate surface so we can alpha-fade when disabled
        buf = pygame.Surface((self._base_rect.width, self._base_rect.height),
                             pygame.SRCALPHA)
        local_rect = pygame.Rect(0, 0, sw, sh)
        local_rect.center = (self._base_rect.width // 2,
                             self._base_rect.height // 2)

        # Current background colour (lerp between normal and hover/press)
        if self._pressed:
            bg = self._color_press
        else:
            bg = self._lerp_color(self._color_bg, self._color_hover, self._hover_t)

        # ── shadow ──────────────────────────────────────────────────
        if self._shadow:
            shadow_alpha = int(self._shadow_color[3] if len(self._shadow_color) > 3 else 60)
            blur = int(self._lerp(self._SHADOW_NORMAL, self._SHADOW_HOVER, self._hover_t))
            for b in range(blur, 0, -1):
                sc = (
                    max(0, min(255, self._shadow_color[0])),
                    max(0, min(255, self._shadow_color[1])),
                    max(0, min(255, self._shadow_color[2])),
                    max(0, int(shadow_alpha * b / blur * 0.4)),
                )
                sr = local_rect.inflate(b * 2, b * 2).move(0, b)
                pygame.draw.rect(buf, sc, sr,
                                 border_radius=self._border_radius + b)

        # ── body ────────────────────────────────────────────────────
        pygame.draw.rect(buf, (*bg, 255), local_rect,
                         border_radius=self._border_radius)

        # ── ripples (clipped to body) ────────────────────────────────
        if self._ripples:
            ripple_surf = pygame.Surface(
                (self._base_rect.width, self._base_rect.height), pygame.SRCALPHA)
            for r in self._ripples:
                age = now - r["born"]
                progress = age / self._RIPPLE_LIFE  # 0→1
                max_r = math.hypot(self._base_rect.width,
                                   self._base_rect.height) * 0.75
                radius = int(max_r * self._ease_out(progress))
                alpha = int(180 * (1.0 - progress))
                pygame.draw.circle(
                    ripple_surf,
                    (max(0, min(255, self._color_ripple[0])),
                     max(0, min(255, self._color_ripple[1])),
                     max(0, min(255, self._color_ripple[2])),
                     max(0, min(255, alpha))),
                    (int(r["cx"] * self._scale +
                         self._base_rect.width * (1 - self._scale) / 2),
                     int(r["cy"] * self._scale +
                         self._base_rect.height * (1 - self._scale) / 2)),
                    radius,
                )
            # Mask ripple to the button body shape
            mask_surf = pygame.Surface(
                (self._base_rect.width, self._base_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(mask_surf, (255, 255, 255, 255), local_rect,
                             border_radius=self._border_radius)
            ripple_surf.blit(mask_surf, (0, 0),
                             special_flags=pygame.BLEND_RGBA_MIN)
            buf.blit(ripple_surf, (0, 0))

        # ── border ──────────────────────────────────────────────────
        if self._border_width:
            pygame.draw.rect(buf,
                             (max(0, min(255, self._border_color[0])),
                              max(0, min(255, self._border_color[1])),
                              max(0, min(255, self._border_color[2])),
                              255),
                             local_rect,
                             width=self._border_width,
                             border_radius=self._border_radius)

        # ── content (icon + label) ──────────────────────────────────
        self._draw_content(buf, local_rect)

        # ── disabled overlay ────────────────────────────────────────
        if not self.enabled:
            overlay = pygame.Surface(
                (self._base_rect.width, self._base_rect.height), pygame.SRCALPHA)
            overlay.fill((255, 255, 255, 255 - self._alpha_disabled))
            buf.blit(overlay, (0, 0))

        surface.blit(buf, draw_rect.topleft)

    def is_hovered(self) -> bool:
        return self._hovered and self.enabled

    def enable(self) -> None:
        self.enabled = True

    def disable(self) -> None:
        self.enabled = False

    # ----------------------------------------------------------------
    # Private helpers
    # ----------------------------------------------------------------

    def _draw_content(self, buf: pygame.Surface, rect: pygame.Rect) -> None:
        """Render icon and/or label, centred inside rect."""
        pieces = []  # list of surfaces to blit left-to-right

        if self._image is not None:
            pieces.append(self._image)

        label_surf = None
        if self.label:
            color = self._color_text if self.enabled else (*self._color_text[:3],)
            label_surf = self._font.render(self.label, True, color)
            pieces.append(label_surf)

        if not pieces:
            return

        gap = self._icon_gap if len(pieces) > 1 else 0
        total_w = sum(p.get_width() for p in pieces) + gap * (len(pieces) - 1)
        total_h = max(p.get_height() for p in pieces)

        x = rect.centerx - total_w // 2
        y = rect.centery - total_h // 2

        for i, piece in enumerate(pieces):
            py = y + (total_h - piece.get_height()) // 2
            buf.blit(piece, (x, py))
            x += piece.get_width() + gap

    @staticmethod
    def _lerp(a: float, b: float, t: float) -> float:
        return a + (b - a) * max(0.0, min(1.0, t))

    @staticmethod
    def _lerp_color(c1: tuple, c2: tuple, t: float) -> tuple:
        t = max(0.0, min(1.0, t))
        return tuple(max(0, min(255, int(a + (b - a) * t))) for a, b in zip(c1[:3], c2[:3]))

    @staticmethod
    def _ease_out(t: float) -> float:
        return 1.0 - (1.0 - t) ** 3

    @staticmethod
    def _load_font(size: int):
        for name in ("dejavusans", "freesans", "liberationsans",
                     "segoeui", "calibri", "noto"):
            f = pygame.font.SysFont(name, size)
            if f:
                return f
        return pygame.font.Font(None, size)


class Label:
    """
    A Pygame label widget for displaying text or an image (or both).

    Features
    --------
    - Text with full Polish character support
    - Optional icon/image beside the text
    - Horizontal and vertical alignment
    - Word-wrap with a fixed max width
    - Optional background, border, and padding
    - Smooth fade-in on first draw (optional)
    - Chainable set_text() / set_image() for live updates

    Constructor
    -----------
    x, y            – top-left position
    text            – string to display (may contain Polish characters)
    image           – pygame.Surface icon (optional)
    image_size      – (w,h) to scale image to; None = use as-is
    max_width       – wrap text at this pixel width (0 = no wrap)
    align           – horizontal text alignment: "left" | "center" | "right"
    valign          – vertical alignment inside a fixed height: "top"|"center"|"bottom"
    fixed_height    – lock widget height (0 = auto)

    Style knobs
    -----------
    font / font_size
    color_text
    color_bg        – None = transparent background
    color_border    – None = no border
    border_width
    border_radius
    padding_x / padding_y
    icon_gap        – pixels between icon and text
    icon_side       – "left" | "right"
    line_spacing    – extra pixels between wrapped lines
    fade_in         – True = alpha fades from 0 → 255 on first draw

    Public API
    ----------
    draw(surface)
    set_text(text)  → self
    set_image(surf, size=None) → self
    set_color(color) → self
    get_rect() → pygame.Rect   (bounding box of the whole widget)
    """

    def __init__(
        self,
        x: int,
        y: int,
        text: str = "",
        image: "pygame.Surface | None" = None,
        image_size: "tuple[int,int] | None" = None,
        max_width:  int   = 0,
        align:      str   = "left",
        valign:     str   = "top",
        fixed_height: int = 0,
        # style
        font=None,
        font_size:    int   = 22,
        color_text:   tuple = (30, 32, 45),
        color_bg:     "tuple | None" = None,
        color_border: "tuple | None" = None,
        border_width: int   = 1,
        border_radius: int  = 6,
        padding_x:    int   = 0,
        padding_y:    int   = 0,
        icon_gap:     int   = 8,
        icon_side:    str   = "left",
        line_spacing: int   = 4,
        fade_in:      bool  = False,
        pos_type:      str   = "topleft",
    ):
        self._x            = x
        self._y            = y
        self._text         = text
        self._max_width    = max_width
        self._align        = align
        self._valign       = valign
        self._fixed_height = fixed_height
        self._color_text   = color_text
        self._color_bg     = color_bg
        self._color_border = color_border
        self._border_width = border_width
        self._border_radius = border_radius
        self._padding_x    = padding_x
        self._padding_y    = padding_y
        self._icon_gap     = icon_gap
        self._icon_side    = icon_side
        self._line_spacing = line_spacing
        # font
        self._font = font if font is not None else self._load_font(font_size)

        # image
        self._image = self._scale_image(image, image_size)

        # fade-in
        self._alpha      = 0 if fade_in else 255
        self._fade_in    = fade_in
        fade_time=1
        self._fade_speed = int(255/fade_time)   # alpha units per second

        # cache (rebuilt on set_text / set_image)
        self._dirty   = True
        self._cache:  "pygame.Surface | None" = None

        self._last_tick = pygame.time.get_ticks()
        w,h=self.get_rect().size
        if pos_type == "center":
            self._x-=w//2
            self._y-=h//2
        if pos_type=="leftcenter":
            self._y-=h//2
        if pos_type=="center_top":
            self._x-=w//2
        if pos_type=="right_top":
            self._x-=w
        if pos_type=="right_center":
            self._x-=w
            self._y-=h//2
        self._rect.topleft = (self._x, self._y)


    # ----------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------
    def move_y(self, dy: int):
        self._y+=dy
        self._rect.topleft = (self._x, self._y)
    def set_y(self, y: int):
        self._y=y
        self._rect.topleft = (self._x, self._y)

    def set_text(self, text: str) -> "Label":
        self._text  = text
        self._dirty = True
        return self
    def set_pos(self, x: int, y: int):
        self._x = x
        self._y = y
        self._rect.x=x
        self._rect.centery=y

        return self

    def set_image(self, surf: "pygame.Surface | None",
                  size: "tuple[int,int] | None" = None) -> "Label":
        self._image = self._scale_image(surf, size)
        self._dirty = True
        return self

    def set_color(self, color: tuple) -> "Label":
        self._color_text = color
        self._dirty      = True
        return self

    def get_rect(self) -> pygame.Rect:
        self._ensure_cache()
        return self._rect.copy()

    def draw(self, surface: pygame.Surface) -> None:
        """Render the label onto *surface*."""
        now = pygame.time.get_ticks()
        dt  = (now - self._last_tick) / 1000.0
        self._last_tick = now

        # Fade-in alpha
        if self._alpha < 255:
            self._alpha = min(255, self._alpha + int(self._fade_speed * dt))

        self._ensure_cache()

        if self._alpha < 255:
            tmp = self._cache.copy()
            tmp.set_alpha(self._alpha)
            surface.blit(tmp, self._rect.topleft)
        else:
            surface.blit(self._cache, self._rect.topleft)

    # ----------------------------------------------------------------
    # Cache / rendering
    # ----------------------------------------------------------------

    def _ensure_cache(self) -> None:
        if not self._dirty:
            return
        self._dirty = False
        self._cache = self._render()

    def _render(self) -> pygame.Surface:
        """Build and return a Surface with everything composited."""

        # 1. Render text lines
        lines      = self._wrap_text()
        line_surfs = [self._font.render(l, True, self._color_text) for l in lines]
        self.first_line_w=line_surfs[0].get_width() if line_surfs else 0

        line_h     = self._font.get_linesize()
        text_w     = max((s.get_width() for s in line_surfs), default=0)
        text_h     = max(len(line_surfs) * (line_h + self._line_spacing) - self._line_spacing, 0)

        # 2. Image dimensions
        img_w = img_h = 0
        if self._image is not None:
            img_w = self._image.get_width()
            img_h = self._image.get_height()

        # 3. Content bounding box (icon + gap + text, or just one)
        if self._image and self._text:
            content_w = img_w + self._icon_gap + text_w
            content_h = max(img_h, text_h)
        elif self._image:
            content_w, content_h = img_w, img_h
        else:
            content_w, content_h = text_w, text_h

        # 4. Widget size
        widget_w = content_w + 2 * self._padding_x
        widget_h = content_h + 2 * self._padding_y
        if self._fixed_height:
            widget_h = self._fixed_height

        # 5. Surface
        surf = pygame.Surface((max(1, widget_w), max(1, widget_h)), pygame.SRCALPHA)

        # 6. Background
        if self._color_bg is not None:
            pygame.draw.rect(surf, (*self._color_bg, 255),
                             surf.get_rect(), border_radius=self._border_radius)

        # 7. Layout icon + text inside padded content area
        avail_h  = widget_h - 2 * self._padding_y
        # vertical start of content block
        if self._valign == "center":
            vy = self._padding_y + (avail_h - content_h) // 2
        elif self._valign == "bottom":
            vy = widget_h - self._padding_y - content_h
        else:
            vy = self._padding_y

        # horizontal start of content block
        avail_w = widget_w - 2 * self._padding_x
        cx = self._padding_x  # left edge of content block (align handles lines below)

        # Place icon
        if self._image is not None:
            icon_y = vy + (content_h - img_h) // 2
            if self._icon_side == "left":
                surf.blit(self._image, (cx, icon_y))
                text_x0 = cx + img_w + self._icon_gap
            else:   # right – place text first, icon after
                text_x0 = cx
                # icon placed after text block
                icon_x  = cx + text_w + self._icon_gap
                surf.blit(self._image, (icon_x, icon_y))
        else:
            text_x0 = cx

        # Place each text line
        for i, ls in enumerate(line_surfs):
            ly = vy + i * (line_h + self._line_spacing) + (content_h - text_h) // 2

            if self._align == "center":
                lx = text_x0 + (text_w - ls.get_width()) // 2
            elif self._align == "right":
                lx = text_x0 + text_w - ls.get_width()
            else:
                lx = text_x0
            surf.blit(ls, (lx, ly))

        # 8. Border
        if self._color_border is not None and self._border_width:
            pygame.draw.rect(surf, (*self._color_border, 255),
                             surf.get_rect(),
                             width=self._border_width,
                             border_radius=self._border_radius)

        self._rect = pygame.Rect(self._x, self._y, widget_w, widget_h)
        return surf

    def _wrap_text(self) -> list:
        """Split _text into lines respecting max_width (and hard newlines)."""
        if not self._text:
            return [""]
        hard_lines = self._text.split(r"\n")
        if not self._max_width:
            return hard_lines
        result = []
        for hard in hard_lines:
            words  = hard.split(" ")
            line   = ""
            for word in words:
                test = (line + " " + word).strip()
                if self._font.size(test)[0] <= self._max_width:
                    line = test
                else:
                    if line:
                        result.append(line)
                    line = word
            result.append(line)
        return result or [""]

    # ----------------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------------

    @staticmethod
    def _scale_image(surf, size):
        if surf is None:
            return None
        if size is not None:
            return pygame.transform.smoothscale(surf, size)
        return surf

    @staticmethod
    def _load_font(size: int):
        for name in ("dejavusans", "freesans", "liberationsans",
                     "segoeui", "calibri", "noto"):
            f = pygame.font.SysFont(name, size)
            if f:
                return f
        return pygame.font.Font(None, size)
class Icon:
    """
    A circular avatar widget that clips any image into a circle,
    with click detection, hover highlight, press animation, and
    an optional ripple effect on click.

    Constructor
    -----------
    x, y            – centre position of the circle
    radius          – circle radius in pixels
    image           – pygame.Surface to display (cropped + scaled to fit)
    callback        – callable fired on click (optional)

    Style knobs
    -----------
    border_color    – ring colour (None = no ring)
    border_width    – ring thickness in pixels
    border_hover    – ring colour on hover (None = same as border_color)
    color_highlight – overlay tint on hover (RGBA)
    color_ripple    – ripple colour (RGB)
    shadow          – draw a soft drop-shadow behind the circle
    shadow_color    – shadow colour (RGBA)
    badge_text      – short string drawn in a small badge (e.g. "3")
    badge_color     – badge background colour
    badge_text_color
    fade_in         – alpha fades 0 → 255 on first draw

    Public API
    ----------
    handle_event(event) → bool   (True if clicked)
    update()
    draw(surface)
    set_image(surf)     → self
    is_hovered() → bool
    enable() / disable()
    """

    _RIPPLE_LIFE   = 0.50   # seconds
    _HOVER_SPEED   = 9.0    # lerp speed
    _PRESS_SCALE   = 0.91
    _FADE_SPEED    = 380    # alpha / second

    def __init__(
        self,
        x: int,
        y: int,
        radius: int,
        image: "pygame.Surface | None" = None,
        callback=None,
        # style
        border_color:      "tuple | None" = (255, 255, 255),
        border_width:      int            = 3,
        border_hover:      "tuple | None" = None,
        color_highlight:   tuple          = (255, 255, 255, 55),
        color_ripple:      tuple          = (255, 255, 255),
        shadow:            bool           = True,
        shadow_color:      tuple          = (0, 0, 0, 60),
        badge_text:        str            = "",
        badge_color:       tuple          = (230, 50, 60),
        badge_text_color:  tuple          = (255, 255, 255),
        enabled:           bool           = True,
        fade_in:           bool           = False,
    ):
        self._cx        = x
        self._cy        = y
        self._radius    = radius
        self._callback  = callback
        self.enabled    = enabled

        self._border_color     = border_color
        self._border_width     = border_width
        self._border_hover     = border_hover or border_color
        self._color_highlight  = color_highlight
        self._color_ripple     = color_ripple
        self._shadow           = shadow
        self._shadow_color     = shadow_color
        self._badge_text       = badge_text
        self._badge_color      = badge_color
        self._badge_text_color = badge_text_color

        # Circular image cache
        self._source_image: "pygame.Surface | None" = None
        self._circle_surf:  "pygame.Surface | None" = None
        if image is not None:
            self._bake_circle(image)

        # Badge font
        badge_font_size = max(10, radius // 2)
        self._badge_font = self._load_font(badge_font_size)

        # Animation state
        self._hovered:      bool  = False
        self._pressed:      bool  = False
        self._hover_t:      float = 0.0
        self._scale:        float = 1.0
        self._ripples:      list  = []

        # Fade-in
        self._alpha      = 0 if fade_in else 255
        self._fade_in    = fade_in

        self._last_tick  = pygame.time.get_ticks()

    # ----------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------

    def handle_event(self, event,mouse_delta=(0,0)) -> bool:
        """Feed a pygame event. Returns True if the icon was clicked."""
        if not self.enabled:
            return False
        mouse_pos=add_vectors(pygame.mouse.get_pos(),mouse_delta)
        if event.type == pygame.MOUSEMOTION:
            self._hovered = self._hit(mouse_pos)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._hit(mouse_pos):
                self._pressed = True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            was_pressed   = self._pressed
            self._pressed = False
            if was_pressed and self._hit(mouse_pos):
                self._ripples.append({
                    "born": pygame.time.get_ticks() / 1000.0,
                })
                if self._callback:
                    self._callback()
                return True
        return False

    def update(self) -> None:
        """Call once per frame."""
        now  = pygame.time.get_ticks() / 1000.0
        dt   = (now - self._last_tick / 1000.0 if hasattr(self, "_last_tick")
                else 0.016)
        self._last_tick = pygame.time.get_ticks()

        # Fade-in
        if self._alpha < 255:
            self._alpha = min(255, self._alpha + int(self._FADE_SPEED * dt))

        # Hover lerp
        target_h = 1.0 if (self._hovered and not self._pressed) else 0.0
        self._hover_t += (target_h - self._hover_t) * min(1.0, self._HOVER_SPEED * dt)

        # Scale spring
        target_s = self._PRESS_SCALE if self._pressed else 1.0
        self._scale += (target_s - self._scale) * min(1.0, 20.0 * dt)

        # Prune dead ripples
        self._ripples = [r for r in self._ripples
                         if now - r["born"] < self._RIPPLE_LIFE]

    def draw(self, surface: pygame.Surface) -> None:
        """Render the icon onto *surface*."""
        now = pygame.time.get_ticks() / 1000.0

        # Scaled radius and centre
        sr  = int(self._radius * self._scale)
        cx, cy = self._cx, self._cy

        # Work on a buffer big enough for shadow bleed
        pad = self._radius + 12
        buf_size = (pad * 2, pad * 2)
        buf  = pygame.Surface(buf_size, pygame.SRCALPHA)
        bcx, bcy = pad, pad   # local centre

        # ── shadow ────────────────────────────────────────────────
        if self._shadow:
            sa   = self._shadow_color[3] if len(self._shadow_color) > 3 else 60
            blur = 7 + int(4 * self._hover_t)
            for b in range(blur, 0, -1):
                sc = (*self._shadow_color[:3],
                      max(0, int(sa * b / blur * 0.5)))
                pygame.draw.circle(buf, sc,
                                   (bcx, bcy + b), sr + b)

        # ── image circle ──────────────────────────────────────────
        if self._circle_surf is not None:
            scaled = pygame.transform.smoothscale(
                self._circle_surf,
                (sr * 2, sr * 2),
            )
            buf.blit(scaled, (bcx - sr, bcy - sr))
        else:
            # Fallback grey circle
            pygame.draw.circle(buf, (180, 180, 190), (bcx, bcy), sr)

        # ── hover highlight overlay ────────────────────────────────
        if self._hover_t > 0.01:
            hl_alpha = int(self._color_highlight[3] * self._hover_t)
            hl_surf  = pygame.Surface((sr * 2, sr * 2), pygame.SRCALPHA)
            pygame.draw.circle(hl_surf, (*self._color_highlight[:3], hl_alpha),
                               (sr, sr), sr)
            buf.blit(hl_surf, (bcx - sr, bcy - sr))

        # ── ripples ───────────────────────────────────────────────
        for r in self._ripples:
            age      = now - r["born"]
            progress = age / self._RIPPLE_LIFE
            rr       = int(sr * self._ease_out(progress))
            alpha    = int(200 * (1.0 - progress))
            rsurf    = pygame.Surface((sr * 2, sr * 2), pygame.SRCALPHA)
            pygame.draw.circle(rsurf, (*self._color_ripple, alpha),
                               (sr, sr), rr)
            # mask to circle shape
            mask = pygame.Surface((sr * 2, sr * 2), pygame.SRCALPHA)
            pygame.draw.circle(mask, (255, 255, 255, 255), (sr, sr), sr)
            rsurf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            buf.blit(rsurf, (bcx - sr, bcy - sr))

        # ── border ring ───────────────────────────────────────────
        if self._border_color and self._border_width:
            bc = self._lerp_color(self._border_color,
                                  self._border_hover,
                                  self._hover_t)
            pygame.draw.circle(buf, (*bc, 255),
                               (bcx, bcy), sr,
                               width=self._border_width)

        # ── disabled overlay ──────────────────────────────────────
        if not self.enabled:
            ov = pygame.Surface(buf_size, pygame.SRCALPHA)
            pygame.draw.circle(ov, (255, 255, 255, 140), (bcx, bcy), sr)
            buf.blit(ov, (0, 0))

        # ── blit buffer to screen ─────────────────────────────────
        if self._alpha < 255:
            buf.set_alpha(self._alpha)
        surface.blit(buf, (cx - pad, cy - pad))

        # ── badge (drawn directly on screen, not scaled) ──────────
        if self._badge_text:
            self._draw_badge(surface)

    def set_image(self, surf: "pygame.Surface | None") -> "Icon":
        self._bake_circle(surf)
        return self

    def is_hovered(self) -> bool:
        return self._hovered and self.enabled

    def enable(self)  -> None:  self.enabled = True
    def disable(self) -> None:  self.enabled = False

    def set_badge(self, text: str) -> "Icon":
        self._badge_text = text
        return self

    # ----------------------------------------------------------------
    # Private helpers
    # ----------------------------------------------------------------

    def _hit(self, pos) -> bool:
        """True if *pos* is inside the circle."""
        dx, dy = pos[0] - self._cx, pos[1] - self._cy
        return math.hypot(dx, dy) <= self._radius

    def _bake_circle(self, surf: pygame.Surface) -> None:
        """
        Pre-render the image clipped to a circle of diameter 2*_radius.
        We store it at native size; draw() smoothscales to the current scale.
        """
        d    = self._radius * 2
        self._source_image = surf

        # Scale source to fill the circle
        sw, sh = surf.get_size()
        scale  = max(d / sw, d / sh)
        nw, nh = int(sw * scale), int(sh * scale)
        scaled = pygame.transform.smoothscale(surf, (nw, nh))

        # Centre-crop
        ox = (nw - d) // 2
        oy = (nh - d) // 2
        cropped = scaled.subsurface(pygame.Rect(ox, oy, d, d)).copy()

        # Apply circular mask
        circle_surf = pygame.Surface((d, d), pygame.SRCALPHA)
        pygame.draw.circle(circle_surf, (255, 255, 255, 255), (d // 2, d // 2), d // 2)
        cropped = cropped.convert_alpha()
        cropped.blit(circle_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

        self._circle_surf = cropped

    def _draw_badge(self, surface: pygame.Surface) -> None:
        txt  = self._badge_font.render(self._badge_text, True, self._badge_text_color)
        tw, th = txt.get_size()
        br   = max(tw, th) // 2 + 5
        bx   = self._cx + int(self._radius * 0.68)
        by   = self._cy - int(self._radius * 0.68)
        pygame.draw.circle(surface, self._badge_color, (bx, by), br)
        pygame.draw.circle(surface, (255, 255, 255), (bx, by), br, width=2)
        surface.blit(txt, (bx - tw // 2, by - th // 2))

    @staticmethod
    def _lerp_color(c1, c2, t):
        if c1 is None or c2 is None:
            return c1 or c2
        t = max(0.0, min(1.0, t))
        return tuple(int(a + (b - a) * t) for a, b in zip(c1[:3], c2[:3]))

    @staticmethod
    def _ease_out(t: float) -> float:
        return 1.0 - (1.0 - t) ** 3

    @staticmethod
    def _load_font(size: int):
        for name in ("dejavusans", "freesans", "liberationsans",
                     "segoeui", "calibri", "noto"):
            f = pygame.font.SysFont(name, size)
            if f:
                return f
        return pygame.font.Font(None, size)

class Picker:
    def __init__(self, x, y, width, height, options, font):
        self.rect = pygame.Rect(x, y, width, height)
        self.options = options
        self.selected_index = 0
        self.font = font

        self.is_open = False
        self.animation_progress = 0  # 0 = closed, 1 = open
        self.animation_speed = 0.2

        self.option_height = height
        self.bg_color = (100, 100, 100)  # not transparent
        self.text_color = (0, 0, 0)
        self.hover_index = -1

    def handle_event(self, event,mp=(0,0)):
        mp=pygame.mouse.get_pos() if mp==(0,0) else mp
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(mp):
                self.is_open = not self.is_open
            elif self.is_open:
                for i, option_rect in enumerate(self.get_option_rects()):
                    if option_rect.collidepoint(mp):
                        self.selected_index = i
                        self.is_open = False
                self.is_open=False
    def get_selected(self):
        return self.options[self.selected_index]

    def update(self,mp=(0,0)):
        # animation
        target = 1 if self.is_open else 0
        if self.animation_progress < target:
            self.animation_progress = min(target, self.animation_progress + self.animation_speed)
        elif self.animation_progress > target:
            self.animation_progress = max(target, self.animation_progress - self.animation_speed)

        # hover
        if self.is_open:
            mouse_pos = pygame.mouse.get_pos()
            self.hover_index = -1
            for i, rect in enumerate(self.get_option_rects()):
                if rect.collidepoint(mouse_pos):
                    self.hover_index = i
        else:
            self.hover_index = -1

    def draw(self, surface):
        # draw selected
        pygame.draw.rect(surface, self.bg_color, self.rect, border_radius=8)
        text = self.font.render(self.options[self.selected_index], True, self.text_color)
        surface.blit(text, text.get_rect(center=self.rect.center))

        # draw dropdown with animation
        if self.animation_progress > 0:
            total_height = int(len(self.options) * self.option_height * self.animation_progress)
            dropdown_rect = pygame.Rect(
                self.rect.x,
                self.rect.y + self.rect.height,
                self.rect.width,
                total_height
            )

            pygame.draw.rect(surface, self.bg_color, dropdown_rect, border_radius=8)

            for i, option in enumerate(self.options):
                option_rect = pygame.Rect(
                    self.rect.x,
                    self.rect.y + self.rect.height + i * self.option_height,
                    self.rect.width,
                    self.option_height
                )

                if option_rect.bottom > dropdown_rect.bottom:
                    break

                if i == self.hover_index:
                    pygame.draw.rect(surface, (220, 220, 220), option_rect,border_radius=8)

                text = self.font.render(option, True, self.text_color)
                surface.blit(text, text.get_rect(center=option_rect.center))

    def get_option_rects(self):
        rects = []
        for i in range(len(self.options)):
            rects.append(pygame.Rect(
                self.rect.x,
                self.rect.y + self.rect.height + i * self.option_height,
                self.rect.width,
                self.option_height
            ))
        return rects

from  functions import alpha_surface,update_board,check_legal_move,ch_score_board

class Board:
    def __init__(self,x,y,width,height,tiles_x,tiles_y,stone_ratio,player="black"):
        if tiles_x<2 or tiles_y<2:
            raise ValueError("tiles_x and tiles_y must be at least 2")
        tiles_x=int(tiles_x)
        tiles_y=int(tiles_y)
        self.rect=pygame.Rect(x,y,width,height)
        self.tiles_x=tiles_x
        self.tiles_y=tiles_y
        self.board=[[-1 for _ in range(tiles_y)] for _ in range(tiles_x)]
        self.tile_width=width/(tiles_x-1)
        self.tile_height=height/(tiles_y-1)
        #woody palete
        self.color=(200,170,120)
        self.border_color=(150,120,80)
        stone_w=int(self.tile_width*stone_ratio)*2
        stone_h=int(self.tile_height*stone_ratio)*2

        self.black_stone_img=pygame.transform.smoothscale(pygame.image.load("images/black.png"),(stone_w,stone_h)).convert_alpha()
        self.white_stone_img=pygame.transform.smoothscale(pygame.image.load("images/white.png"),(stone_w,stone_h)).convert_alpha()
        self.stones=[self.black_stone_img,self.white_stone_img]
        if player=="White":
            self.stone=self.white_stone_img
            self.player=1
        else:
            self.stone=self.black_stone_img
            self.player=0

        self.white_ter=[]
        self.black_ter=[]
        self.show_ter=0

        self.pressed=False

        self.turn=False


    def draw(self,surface):
        pygame.draw.rect(surface,self.color,self.rect)
        line_border=2
        for i in range(self.tiles_x):
            x=self.rect.x+i*self.tile_width
            pygame.draw.line(surface,self.border_color,(x,self.rect.y),(x,self.rect.y+self.rect.height),line_border)
        for j in range(self.tiles_y):
            y=self.rect.y+j*self.tile_height
            pygame.draw.line(surface,self.border_color,(self.rect.x,y),(self.rect.x+self.rect.width,y),line_border)
        #draw stones
        for i in range(self.tiles_x):
            for j in range(self.tiles_y):
                if self.board[i][j]!=-1:
                    x=self.rect.x+i*self.tile_width
                    y=self.rect.y+j*self.tile_height
                    stone=self.stones[self.board[i][j]]
                    stone_rect=stone.get_rect(center=(x,y))
                    surface.blit(stone,stone_rect)
        alpha=100
        if self.pressed:
            pos=self.get_hovered(pygame.mouse.get_pos())
            if pos!=-1:
                x=self.rect.x+pos[0]*self.tile_width
                y=self.rect.y+pos[1]*self.tile_height
                stone=self.stones[self.player]
                rect=stone.get_rect(center=(x,y))
                surface.blit(alpha_surface(stone,alpha),rect)
        # draw ter
        if not self.show_ter:
            return
        white=(200,200,200)
        black=(20,20,20)
        for i in range(self.tiles_x):
            for j in range(self.tiles_y):
                if (i,j) in self.white_ter or (i,j) in self.black_ter:
                    x=self.rect.x+i*self.tile_width
                    y=self.rect.y+j*self.tile_height
                    stone=self.stones[self.player]
                    rect=stone.get_rect(center=(x,y))
                    color=white if (i,j) in self.white_ter else black
                    pygame.draw.rect(surface,color,rect)
                if (i,j) in self.white_ter and (i,j) in self.black_ter:
                    print("error",(i,j))


    def get_hovered(self,mp):
        r=self.tile_width/2*1.42
        mn=999999
        mni=-1
        for i in range(self.tiles_x):
            for j in range(self.tiles_y):
                x=self.rect.x+i*self.tile_width
                y=self.rect.y+j*self.tile_height
                dist=math.hypot(mp[0]-x,mp[1]-y)
                if dist<r and dist<mn:
                    mn=dist
                    mni=(i,j)
        return mni
    def check_legal(self,pos):
        if pos==-1 or self.board[pos[0]][pos[1]]!=-1:
            return False
        if not check_legal_move(self.board,pos[0],pos[1],self.player):
            return False
        return True
    def place(self,pos,player):

        self.board[pos[0]][pos[1]]=player
        update_board(self.board,player)

        score=ch_score_board(self.board)
        self.white_ter=score[1]
        self.black_ter=score[2]
    def get_score(self,white_bias,black_bias):
        return ch_score_board(self.board)[0]+black_bias-white_bias

    def update(self):
        mc=pygame.mouse.get_pressed()[0]
        mp=pygame.mouse.get_pos()
        if mc:
            self.pressed=True
        elif self.pressed:
            self.pressed=False
            pos=self.get_hovered(mp)
            if self.check_legal(pos) and self.turn:
                self.place(pos,self.player)
                return pos
    def set_move(self,pos):
        self.place(pos,1^self.player)


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
from functions import darken_rgb
class SimpleButton:
    def __init__(self,x,y,width,height,color,img_file,padding,call_back=lambda: print("button pressed")):
        self.rect=pygame.Rect(x,y,width,height)
        self.color=color
        self.img=pygame.transform.smoothscale(pygame.image.load(img_file),(height-2*padding,height-2*padding)).convert_alpha()
        self.call_back=call_back
        self.active=False
    def draw(self,surface):
        r=5
        darken=0.6
        pygame.draw.rect(surface,self.color if not self.active else darken_rgb(self.color,darken),self.rect,border_radius=r)
        img_rect=self.img.get_rect(center=self.rect.center)
        surface.blit(self.img,img_rect)
    def set_pos_center(self,pos):
        self.rect.center=pos
    def handle_event(self,event,mouse_delta=(0,0)):

        if event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
            pos=add_vectors(pygame.mouse.get_pos(),mouse_delta)
            if self.rect.collidepoint(pos):
                self.active=True
        elif event.type==pygame.MOUSEBUTTONUP and event.button==1:
            pos=add_vectors(pygame.mouse.get_pos(),mouse_delta)
            if self.active and self.rect.collidepoint(pos):
                self.call_back()
            self.active=False



class Server_snippet:
    def __init__(self,x,y,width,height,user,font,callback,room_id):
        self.room_id=room_id
        self.rect=pygame.Rect(x,y,width,height)
        self.user=Label(x+10,y+height//2-10,text=user,color_text=(220,220,255),font=font)
        self.button_cx=x+width-50
        self.user_x=x+10
        self.button=SimpleButton(x+width-90,y+height//2-15,70,30,(70,130,180),"images/play.png",5,call_back=callback)
        self.color=(50,50,50)
    def draw(self,surface):
        r=3
        pygame.draw.rect(surface,self.color,self.rect,border_radius=r)
        pygame.draw.rect(surface,darken_rgb(self.color,0.8),self.rect.inflate(-4,-4),border_radius=r)

        self.button.set_pos_center((self.button_cx,self.rect.centery))
        self.user.set_pos(self.user_x,self.rect.centery)
        self.user.draw(surface)
        self.button.draw(surface)
    def handle_event(self,event,mouse_delta=(0,0)):
        self.button.handle_event(event,mouse_delta)
    def set_y(self,y):
        self.rect.y=y

class ServerList:
    def __init__(self,width,height,x,y):
        self.surface=pygame.Surface((width,height))
        self.rect=self.surface.get_rect(topleft=(x,y))
        self.servers=[]
        lh=100
        self.legend_rect=pygame.Rect(0,0,width,lh)
        self.legend_label=Label(self.legend_rect.centerx,self.legend_rect.centery,text="Available Servers",color_text=(220,220,255),font=fontmid,pos_type="center")

        self.padding=10

        self.color=(80,80,80)
        self.second_color=(50,50,50)
        self.spadding=6

    def draw(self,surface):
        b=5
        r=5
        pygame.draw.rect(self.surface,self.color,self.surface.get_rect(),border_radius=r)
        server_rect=pygame.Rect(self.padding,self.legend_rect.bottom,self.rect.width-2*self.padding,self.rect.height-self.legend_rect.height-self.padding)
        pygame.draw.rect(self.surface,self.second_color,server_rect)
        for x in self.servers:
            x.draw(self.surface)
        pygame.draw.rect(self.surface,self.color,self.legend_rect,border_radius=r)
        self.legend_label.draw(self.surface)
        pygame.draw.rect(self.surface,darken_rgb(self.color,0.4),self.surface.get_rect(),b,border_radius=r)

        surface.blit(self.surface,self.rect.topleft)
    def add_server(self,user,join_callback,room_id):
        h=50
        y=self.legend_rect.bottom+self.spadding
        if self.servers:
            y=self.servers[-1].rect.bottom+self.spadding
        paddingx=self.padding+self.spadding
        snippet=Server_snippet(paddingx,y,self.rect.width-2*paddingx,h,user,font,join_callback,room_id)
        self.servers.append(snippet)
    def handle_event(self,event):
        for server in self.servers:
            server.handle_event(event,(-self.rect.x,-self.rect.y))

class Picker2:
    def __init__(self,cx,y,width,height,font,options=[],color=(50,50,50),chosen_color=(100,100,100),text_color=(255,255,255)):
        x=cx-width/2
        self.rect=pygame.Rect(x,y,width,height)
        self.options=options
        self.color=color
        self.chosen_color=chosen_color
        self.text_color=text_color
        self.chosen=0
        self.height=height
        self.font=font
    def draw(self,surface):
        w=self.rect.width/len(self.options)
        r=4
        for i,option in enumerate(self.options):
            color=self.chosen_color if i==self.chosen else self.color
            option_rect=pygame.Rect(self.rect.x+i*w,self.rect.y,w,self.height)
            if i==0:
                pygame.draw.rect(surface, color, option_rect, border_top_left_radius=r, border_bottom_left_radius=r)
            elif i==len(self.options)-1:
                pygame.draw.rect(surface, color, option_rect, border_top_right_radius=r, border_bottom_right_radius=r)
            else:
                pygame.draw.rect(surface,color,option_rect)
            label=Label(option_rect.centerx,option_rect.centery,text=option,color_text=self.text_color,font=self.font,pos_type="center")
            label.draw(surface)
    def update(self):
        if pygame.mouse.get_pressed()[0]:
            mouse_pos=pygame.mouse.get_pos()
            if self.rect.collidepoint(mouse_pos):
                w=self.rect.width/len(self.options)
                clicked_option=int((mouse_pos[0]-self.rect.x)/w)
                self.chosen=clicked_option
    def get_selected(self):
        return self.options[self.chosen]
    def rest(self):
        self.chosen=0


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
    def change_color(self,color):
        self.color=color
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
            if abs(self.score-self._target_score)<1:
                self.score=self._target_score
            if self.score == self._target_score:
                self._state = self._IDLE

class Pass_confirm:
    def __init__(self,width,height,x,y,pass_turn_func, back_to_game):
        self.rect=pygame.Rect(x,y,width,height)
        button_w=85
        button_h=50
        paddingx=20
        paddingY=20
        self.confirm_button=SimpleButton(x+paddingx,y+height-button_h-paddingY,button_w,button_h,(0,200,0),"images/confirm.png",5,call_back=pass_turn_func)
        self.cancel_button=SimpleButton(x+width-button_w-paddingx,y+height-button_h-paddingY,button_w,button_h,(200,0,0),"images/deny.png",5,call_back=back_to_game)
        y2=40
        padding=10
        self.label=Label(width//2+x,y+y2,"Na pewno chcesz spasować?",max_width=width-padding*2,font=fontmid,color_text=(200,200,200),pos_type="center",)
        self.color=(100,100,100)
        self.second_color=(0,0,0)
    def handle_event(self,event):
        self.confirm_button.handle_event(event)
        self.cancel_button.handle_event(event)
    def draw(self,surface):
        r=10
        pygame.draw.rect(surface,self.color,self.rect,border_radius=r)
        pygame.draw.rect(surface,self.second_color,self.rect,border_radius=r,width=5)
        self.cancel_button.draw(surface)
        self.confirm_button.draw(surface)
        self.label.draw(surface)
import random
class Go_particles:
    def __init__(self,White,Black,white_target,black_target,min_vel,max_vel,white_func,black_func):
        self.particles=[]
        self.w=White
        self.b=Black
        self.wt=white_target
        self.bt=black_target
        self.mv=min_vel
        self.mxv=max_vel

        self.white_func=white_func
        self.black_func=black_func
    def add_particle(self,x,y,color):
        t=self.wt if color=="White" else self.bt
        self.particles.append(Particle1(x,y,random.randint(self.mv,self.mxv),t[0],t[1],color))
    def update(self):
        for i in range(len(self.particles)-1,-1,-1):
            j=self.particles[i]
            j.update()
            if not j.alive:
                if j.info=="White":
                    self.white_func()
                else:
                    self.black_func()
                self.particles.pop(i)
    def draw(self,surface):
        for j in self.particles:
            img=self.w if j.info=="White" else self.b
            rect=img.get_rect()
            rect.center=j.get_pos()
            surface.blit(img,rect)

class Particle1:
    def __init__(self,x,y,init_vel,tx,ty,info=None):
        self.pos=pygame.Vector2(x,y)

        self.vel=pygame.Vector2(init_vel,0)
        self.vel=self.vel.rotate(random.randint(0,360-1))
        print(self.vel)
        self.tx=tx
        self.ty=ty
        self.info =info
        self.alive=True
    def update_vel(self):
        a=0.5
        base=1.5
        l=pygame.Vector2(self.tx-self.pos.x,self.ty-self.pos.y).length()
        if l==0:
            self.alive=False
            return

        factor=math.log(base,l)+a
        acc=pygame.Vector2(self.tx-self.pos.x,self.ty-self.pos.y)
        acc.scale_to_length(factor)
        self.vel+=acc
        self.vel.scale_to_length(min(8,self.vel.length()))
    def get_pos(self):
        return self.pos.x,self.pos.y
    def update(self):
        if self.alive==False:
            return
        self.pos+=self.vel
        self.update_vel()
        if pygame.Vector2(self.tx-self.pos.x,self.ty-self.pos.y).length()<=self.vel.length():
            self.alive=False