import time
from threading import Thread
from enum import Enum

from pynput.mouse import Controller, Button

class Mouse:
    class MouseButton(Enum):
        LEFT = -1
        RIGHT = 0
        MIDDLE = 1

    def __init__(self, control_hz: float = 50.0):
        """
        control_hz: mouse control frequency in Hz
        """
        self.control_hz = control_hz

        self.controller = Controller()

        self.control_thread = Thread(target=self.control_loop)

        self.button_map = {
            'L': Button.left,
            'R': Button.right,
            'M': Button.middle
        }

        # State variables
        self.done = False
        self.cursor_vx = 0.0
        self.cursor_vy = 0.0

        self.control_thread.start()

    def control_loop(self):
        while not self.done:
            self.controller.move(
                self.cursor_vx // self.control_hz, 
                self.cursor_vy // self.control_hz
            )

            time.sleep(1 / self.control_hz)

    def set_cursor_velocity(self, vx, vy):
        """
        Set the mouse cursor velocity.
        """
        self.cursor_vx = vx
        self.cursor_vy = vy

    def press(self, button: str):
        """
        Press the mouse button. Accepts 'L', 'R', or 'M'.
        """
        if button not in self.button_map:
            raise ValueError(f"Invalid button: {button}. Use 'L', 'R', or 'M'.")
        self.controller.press(self.button_map[button])

    def release(self, button: str):
        """
        Release the mouse button. Accepts 'L', 'R', or 'M'.
        """
        if button not in self.button_map:
            raise ValueError(f"Invalid button: {button}. Use 'L', 'R', or 'M'.")
        self.controller.release(self.button_map[button])

    def scroll(self, x, y):
        """
        Scroll the mouse wheel by x and y.
        """
        self.controller.scroll(x, y)

    def cleanup(self):
        """
        Clean up the mouse.
        """
        self.done = True
        self.control_thread.join()