import tkinter as tk
import os
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# --- Config from .env ---
PULSE_START_TIME   = os.getenv("PULSE_START_TIME", "12:00:00")
PULSE_DURATION_SECS = int(os.getenv("PULSE_DURATION_SECS", "60"))

BG_COLOR      = "#3a3a3a"   # normal grey background
PULSE_BG      = "#1a1a1a"   # dark flash during pulse
TEXT_COLOR    = "#ffffff"
BLINK_COLOR   = "#ff4444"   # text colour during blink

BLINK_PERIOD_MS = 500        # ms – how fast the text blinks

# --- Helper ---------------------------------------------------------------

def parse_hms(s: str) -> int:
    """Return total seconds from HH:MM:SS string."""
    parts = s.strip().split(":")
    h = int(parts[0]) if len(parts) > 0 else 0
    m = int(parts[1]) if len(parts) > 1 else 0
    sec = int(parts[2]) if len(parts) > 2 else 0
    return h * 3600 + m * 60 + sec


def is_pulse_active(now: datetime) -> bool:
    current = now.hour * 3600 + now.minute * 60 + now.second
    start   = parse_hms(PULSE_START_TIME)
    end     = (start + PULSE_DURATION_SECS) % 86400

    if start + PULSE_DURATION_SECS > 86400:          # spans midnight
        return current >= start or current < end
    return start <= current < end


# --- Main Window ----------------------------------------------------------

class ClockApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Zegar")
        self.root.configure(bg=BG_COLOR)
        self.root.minsize(200, 80)

        # Single label fills the window
        self.label = tk.Label(
            root,
            text="00:00:00",
            bg=BG_COLOR,
            fg=TEXT_COLOR,
            font=("Monospace", 60, "bold"),
        )
        self.label.pack(expand=True, fill="both")

        # Bind resize to adjust font size
        self.root.bind("<Configure>", self._on_resize)

        self._blink_visible = True
        self._last_size = (0, 0)

        self._tick()

    # Responsive font ---------------------------------------------------------

    def _on_resize(self, event=None):
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        if (w, h) == self._last_size:
            return
        self._last_size = (w, h)
        # Font size = 55 % of window height, capped so it fits width too
        size_by_h = max(8, int(h * 0.55))
        # Rough estimate: monospace char ≈ 0.6 × font-size wide, 8 chars
        size_by_w = max(8, int(w / (8 * 0.62)))
        font_size = min(size_by_h, size_by_w)
        self.label.configure(font=("Monospace", font_size, "bold"))

    # Clock tick --------------------------------------------------------------

    def _tick(self):
        now = datetime.now()
        pulse = is_pulse_active(now)

        if pulse:
            # Toggle text visibility each BLINK_PERIOD_MS
            self._blink_visible = not self._blink_visible
            fg = BLINK_COLOR if self._blink_visible else BG_COLOR
            bg = PULSE_BG
        else:
            self._blink_visible = True
            fg = TEXT_COLOR
            bg = BG_COLOR

        time_str = now.strftime("%H:%M:%S")
        self.label.configure(text=time_str, fg=fg, bg=bg)
        self.root.configure(bg=bg)

        # Schedule next update
        delay = BLINK_PERIOD_MS if pulse else 200
        self.root.after(delay, self._tick)


# --- Entry point ----------------------------------------------------------

if __name__ == "__main__":
    root = tk.Tk()
    app = ClockApp(root)
    root.mainloop()
