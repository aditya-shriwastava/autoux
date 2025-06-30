import time
from threading import Thread

from pynput.mouse import Controller, Button


class Mouse:
    def __init__(self, cursor_hz: float = 50.0, event_hz: float = 25.0):
        """
        cursor_hz: cursor movement control frequency in Hz
        event_hz: mouse event processing frequency in Hz
        """
        self.cursor_hz = cursor_hz
        self.event_hz = event_hz

        self.controller = Controller()

        self.cursor_thread = Thread(target=self.cursor_control_loop)
        self.event_thread = Thread(target=self.event_control_loop)

        self.button_map = {
            'L': Button.left,
            'R': Button.right,
            'M': Button.middle
        }

        # State variables
        self.done = False
        self.cursor_vx = 0.0
        self.cursor_vy = 0.0
        self.buffer: list[tuple[str, str]] = []

        self.cursor_thread.start()
        self.event_thread.start()

    def cursor_control_loop(self):
        while not self.done:
            self.controller.move(
                self.cursor_vx // self.cursor_hz, 
                self.cursor_vy // self.cursor_hz
            )
            time.sleep(1 / self.cursor_hz)

    def event_control_loop(self):
        while not self.done:
            if len(self.buffer) > 0:
                action, button = self.buffer.pop(0)
                if action == 'press':
                    self.controller.press(self.button_map[button])
                elif action == 'release':
                    self.controller.release(self.button_map[button])
                elif action == 'scroll_up':
                    self.controller.scroll(0, 1)
                elif action == 'scroll_down':
                    self.controller.scroll(0, -1)
            time.sleep(1 / self.event_hz)

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
        self.buffer.append(('press', button))

    def release(self, button: str):
        """
        Release the mouse button. Accepts 'L', 'R', or 'M'.
        """
        if button not in self.button_map:
            raise ValueError(f"Invalid button: {button}. Use 'L', 'R', or 'M'.")
        self.buffer.append(('release', button))

    def scroll_up(self):
        """
        Scroll the mouse wheel up.
        """
        self.buffer.append(('scroll_up', ''))

    def scroll_down(self):
        """
        Scroll the mouse wheel down.
        """
        self.buffer.append(('scroll_down', ''))

    def get_cursor_position(self):
        return self.controller.position

    def cleanup(self):
        self.done = True
        self.cursor_thread.join()
        self.event_thread.join()
