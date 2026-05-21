import tkinter as tk
import os
import time
import math
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# --- Config from .env ---
PULSE_START_TIME    = os.getenv("PULSE_START_TIME", "12:00:00")
PULSE_DURATION_SECS = int(os.getenv("PULSE_DURATION_SECS", "60"))

BG_COLOR    = "#3a3a3a"
PULSE_BG    = "#1a1a1a"
TEXT_COLOR  = "#ffffff"
BLINK_COLOR = "#ff4444"

ZOOM_PERIOD    = 2.0   # seconds per full zoom cycle
ZOOM_AMPLITUDE = 0.25  # ±25 % of base font size

# Window bouncing speed (pixels per second)
BOUNCE_SPEED = 300

# --- Helpers ---------------------------------------------------------------

def parse_hms(s: str) -> int:
    parts = s.strip().split(":")
    h   = int(parts[0]) if len(parts) > 0 else 0
    m   = int(parts[1]) if len(parts) > 1 else 0
    sec = int(parts[2]) if len(parts) > 2 else 0
    return h * 3600 + m * 60 + sec


def is_pulse_active(now: datetime) -> bool:
    current = now.hour * 3600 + now.minute * 60 + now.second
    start   = parse_hms(PULSE_START_TIME)
    end     = (start + PULSE_DURATION_SECS) % 86400
    if start + PULSE_DURATION_SECS > 86400:
        return current >= start or current < end
    return start <= current < end


# --- Main Window -----------------------------------------------------------

class ClockApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Zegar")
        self.root.configure(bg=BG_COLOR)
        self.root.minsize(180, 70)

        self.label = tk.Label(
            root,
            text="00:00",
            bg=BG_COLOR,
            fg=TEXT_COLOR,
            font=("Monospace", 60, "bold"),
        )
        self.label.pack(expand=True, fill="both")

        self.root.bind("<Configure>", self._on_resize)

        self._base_font  = 60
        self._last_size  = (0, 0)
        self._blink_show = True

        # Bouncing state — initialised after the window is visible
        self._bounce_x    = 0.0
        self._bounce_y    = 0.0
        self._vel_x       = BOUNCE_SPEED      # px/s
        self._vel_y       = BOUNCE_SPEED * 0.7
        self._last_bounce = time.monotonic()
        self._bouncing    = False             # True only while pulsing

        # Wait for the window to appear, then snapshot its start position
        self.root.after(200, self._init_bounce_pos)
        self._tick()

    def _init_bounce_pos(self):
        self.root.update_idletasks()
        self._bounce_x = float(self.root.winfo_x())
        self._bounce_y = float(self.root.winfo_y())
        self._last_bounce = time.monotonic()

    # Responsive base font size -----------------------------------------------

    def _recalc_base(self, w, h):
        by_h = max(8, int(h * 0.55))
        by_w = max(8, int(w / (5 * 0.62)))   # "HH:MM" = 5 chars
        return min(by_h, by_w)

    def _on_resize(self, event=None):
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        if (w, h) == self._last_size:
            return
        self._last_size = (w, h)
        self._base_font = self._recalc_base(w, h)
        if not is_pulse_active(datetime.now()):
            self.label.configure(font=("Monospace", self._base_font, "bold"))

    # Bouncing logic ----------------------------------------------------------

    def _step_bounce(self):
        now  = time.monotonic()
        dt   = now - self._last_bounce
        self._last_bounce = now

        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        ww = self.root.winfo_width()
        wh = self.root.winfo_height()

        self._bounce_x += self._vel_x * dt
        self._bounce_y += self._vel_y * dt

        # Bounce off screen edges
        if self._bounce_x < 0:
            self._bounce_x = 0
            self._vel_x = abs(self._vel_x)
        elif self._bounce_x + ww > sw:
            self._bounce_x = float(sw - ww)
            self._vel_x = -abs(self._vel_x)

        if self._bounce_y < 0:
            self._bounce_y = 0
            self._vel_y = abs(self._vel_y)
        elif self._bounce_y + wh > sh:
            self._bounce_y = float(sh - wh)
            self._vel_y = -abs(self._vel_y)

        self.root.geometry(f"+{int(self._bounce_x)}+{int(self._bounce_y)}")

    def _stop_bounce(self):
        """Snap window back to screen centre when pulsing ends."""
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        ww = self.root.winfo_width()
        wh = self.root.winfo_height()
        cx = (sw - ww) // 2
        cy = (sh - wh) // 2
        self.root.geometry(f"+{cx}+{cy}")
        self._bounce_x = float(cx)
        self._bounce_y = float(cy)

    # Main update loop --------------------------------------------------------

    def _tick(self):
        now   = datetime.now()
        pulse = is_pulse_active(now)

        if pulse:
            # --- Zoom ---
            phase     = (time.monotonic() % ZOOM_PERIOD) / ZOOM_PERIOD
            zoom      = 1.0 + ZOOM_AMPLITUDE * math.sin(phase * 2 * math.pi)
            font_size = max(8, int(self._base_font * zoom))

            # --- Blink ---
            self._blink_show = not self._blink_show
            fg = BLINK_COLOR if self._blink_show else PULSE_BG
            bg = PULSE_BG

            # --- Bounce ---
            if not self._bouncing:
                # First tick of a new pulse — snapshot current position
                self._bounce_x    = float(self.root.winfo_x())
                self._bounce_y    = float(self.root.winfo_y())
                self._last_bounce = time.monotonic()
                self._bouncing    = True
            self._step_bounce()

        else:
            font_size        = self._base_font
            self._blink_show = True
            fg               = TEXT_COLOR
            bg               = BG_COLOR

            if self._bouncing:
                self._bouncing = False
                self._stop_bounce()

        self.label.configure(
            text=now.strftime("%H:%M"),
            fg=fg,
            bg=bg,
            font=("Monospace", font_size, "bold"),
        )
        self.root.configure(bg=bg)

        self.root.after(50 if pulse else 200, self._tick)


# --- Entry point -----------------------------------------------------------

if __name__ == "__main__":
    root = tk.Tk()
    ClockApp(root)
    root.mainloop()
