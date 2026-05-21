import tkinter as tk
import os
import time
import math
import json
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
BTN_COLOR   = "#555555"
BTN_ACTIVE  = "#777777"

ZOOM_PERIOD    = 2.0   # seconds per font-zoom cycle
ZOOM_AMPLITUDE = 0.25  # ±25 % font oscillation
WIN_SCALE      = 3.0   # window grows to 3× home size during pulse
BOUNCE_SPEED   = 300   # px/s

HOME_POS_FILE  = "/app/home_pos.json"   # persisted via docker volume

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


def load_home() -> dict | None:
    try:
        with open(HOME_POS_FILE) as f:
            return json.load(f)
    except Exception:
        return None


def save_home(x: int, y: int, w: int, h: int):
    try:
        with open(HOME_POS_FILE, "w") as f:
            json.dump({"x": x, "y": y, "w": w, "h": h}, f)
    except Exception as e:
        print(f"[WARN] Nie można zapisać home_pos.json: {e}")


# --- Main Window -----------------------------------------------------------

class ClockApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Zegar")
        self.root.configure(bg=BG_COLOR)
        self.root.minsize(180, 70)

        # --- Layout: clock label + save-position button ---
        self.label = tk.Label(
            root,
            text="00:00",
            bg=BG_COLOR,
            fg=TEXT_COLOR,
            font=("Monospace", 60, "bold"),
        )
        self.label.pack(expand=True, fill="both")

        self.save_btn = tk.Button(
            root,
            text="📌 Zapisz pozycję",
            command=self._save_position,
            bg=BTN_COLOR,
            fg="#cccccc",
            activebackground=BTN_ACTIVE,
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            pady=4,
            cursor="hand2",
            font=("Monospace", 9),
        )
        self.save_btn.pack(fill="x", side="bottom")

        self.root.bind("<Configure>", self._on_resize)

        # Internal state
        self._base_font   = 60
        self._last_size   = (0, 0)
        self._blink_show  = True
        self._bouncing    = False

        # Bounce position
        self._bounce_x    = 0.0
        self._bounce_y    = 0.0
        self._vel_x       = BOUNCE_SPEED
        self._vel_y       = BOUNCE_SPEED * 0.7
        self._last_bounce = time.monotonic()

        # Home geometry (position + size): loaded from file or set after render
        self._home: dict | None = load_home()

        # Apply saved home geometry on startup
        self.root.after(200, self._apply_home_on_start)
        self._tick()

    # Startup ----------------------------------------------------------------

    def _apply_home_on_start(self):
        self.root.update_idletasks()
        if self._home:
            h = self._home
            self.root.geometry(f"{h['w']}x{h['h']}+{h['x']}+{h['y']}")
        else:
            # No saved position: use current position as default home
            self._snapshot_home()
        # Initialise bounce start coords from current position
        self._bounce_x    = float(self.root.winfo_x())
        self._bounce_y    = float(self.root.winfo_y())
        self._last_bounce = time.monotonic()

    # Save-position button ---------------------------------------------------

    def _save_position(self):
        self.root.update_idletasks()
        self._snapshot_home()
        # Flash button as feedback
        self.save_btn.configure(bg="#30a030", text="✔ Zapisano!")
        self.root.after(1500, lambda: self.save_btn.configure(
            bg=BTN_COLOR, text="📌 Zapisz pozycję"))

    def _snapshot_home(self):
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        self._home = {"x": x, "y": y, "w": w, "h": h}
        save_home(x, y, w, h)

    # Responsive base font ---------------------------------------------------

    def _recalc_base(self, w, h):
        by_h = max(8, int(h * 0.55))
        by_w = max(8, int(w / (5 * 0.62)))
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

    # Bounce -----------------------------------------------------------------

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

        if self._bounce_x < 0:
            self._bounce_x = 0.0
            self._vel_x = abs(self._vel_x)
        elif self._bounce_x + ww > sw:
            self._bounce_x = float(sw - ww)
            self._vel_x = -abs(self._vel_x)

        if self._bounce_y < 0:
            self._bounce_y = 0.0
            self._vel_y = abs(self._vel_y)
        elif self._bounce_y + wh > sh:
            self._bounce_y = float(sh - wh)
            self._vel_y = -abs(self._vel_y)

        self.root.geometry(f"+{int(self._bounce_x)}+{int(self._bounce_y)}")

    def _restore_home(self):
        """Return window to saved home geometry."""
        if self._home:
            h = self._home
            self.root.geometry(f"{h['w']}x{h['h']}+{h['x']}+{h['y']}")
            self._bounce_x = float(h["x"])
            self._bounce_y = float(h["y"])
        else:
            # Fallback: centre of screen
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            ww = self.root.winfo_width()
            wh = self.root.winfo_height()
            cx, cy = (sw - ww) // 2, (sh - wh) // 2
            self.root.geometry(f"+{cx}+{cy}")
            self._bounce_x, self._bounce_y = float(cx), float(cy)

    # Main loop --------------------------------------------------------------

    def _tick(self):
        now   = datetime.now()
        pulse = is_pulse_active(now)

        if pulse:
            # --- Font zoom (sine) ---
            phase     = (time.monotonic() % ZOOM_PERIOD) / ZOOM_PERIOD
            zoom      = 1.0 + ZOOM_AMPLITUDE * math.sin(phase * 2 * math.pi)
            font_size = max(8, int(self._base_font * zoom))

            # --- Blink colour ---
            self._blink_show = not self._blink_show
            fg = BLINK_COLOR if self._blink_show else PULSE_BG
            bg = PULSE_BG

            # --- Window: grow to WIN_SCALE × home size, then bounce ---
            if not self._bouncing and self._home:
                hw = self._home["w"]
                hh = self._home["h"]
                big_w = int(hw * WIN_SCALE)
                big_h = int(hh * WIN_SCALE)
                # Clamp to screen
                sw = self.root.winfo_screenwidth()
                sh = self.root.winfo_screenheight()
                big_w = min(big_w, sw)
                big_h = min(big_h, sh)
                # Place enlarged window at home position (top-left stays)
                sx = self._home["x"]
                sy = self._home["y"]
                self.root.geometry(f"{big_w}x{big_h}+{sx}+{sy}")
                self._bounce_x    = float(sx)
                self._bounce_y    = float(sy)
                self._last_bounce = time.monotonic()
                self._bouncing    = True
            elif self._bouncing:
                self._step_bounce()

        else:
            font_size        = self._base_font
            self._blink_show = True
            fg               = TEXT_COLOR
            bg               = BG_COLOR

            if self._bouncing:
                self._bouncing = False
                self._restore_home()

        self.label.configure(
            text=now.strftime("%H:%M"),
            fg=fg,
            bg=bg,
            font=("Monospace", font_size, "bold"),
        )
        self.save_btn.configure(bg=BTN_COLOR if not pulse else PULSE_BG,
                                fg="#cccccc" if not pulse else "#555555")
        self.root.configure(bg=bg)

        self.root.after(50 if pulse else 200, self._tick)


# --- Entry point -----------------------------------------------------------

if __name__ == "__main__":
    root = tk.Tk()
    ClockApp(root)
    root.mainloop()
