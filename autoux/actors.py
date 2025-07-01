import time
from threading import Thread

from pynput.keyboard import Controller as KeyboardController
from pynput.mouse import Controller as MouseController

from .key_map import keyboard_key_map, mouse_key_map


class CursorActor:
    def __init__(self, cursor_hz: float = 50.0):
        """
        cursor_hz: cursor movement control frequency in Hz
        """
        self.cursor_hz = cursor_hz
        self.controller = MouseController()
        self.cursor_thread = Thread(target=self.cursor_control_loop)

        # State variables
        self.done = False
        self.cursor_vx = 0.0
        self.cursor_vy = 0.0

        self.cursor_thread.start()

    def cursor_control_loop(self):
        while not self.done:
            self.controller.move(
                self.cursor_vx // self.cursor_hz,
                self.cursor_vy // self.cursor_hz
            )
            time.sleep(1 / self.cursor_hz)

    def set_cursor_velocity(self, vx, vy):
        """
        Set the mouse cursor velocity.
        """
        self.cursor_vx = vx
        self.cursor_vy = vy

    def cleanup(self):
        self.done = True
        self.cursor_thread.join()


class EventActor:
    def __init__(self, event_hz: float = 25.0):
        """
        event_hz: event processing frequency in Hz
        """
        self.event_hz = event_hz

        self.keyboard_controller = KeyboardController()
        self.mouse_controller = MouseController()
        self.event_thread = Thread(target=self.event_control_loop)


        self.buffer: list[tuple[str, str, str]] = []  # (device, action, key)
        self.done = False
        self.event_thread.start()

    def event_control_loop(self):
        while not self.done:
            if len(self.buffer) > 0:
                device, action, key_or_button = self.buffer.pop(0)
                
                if device == 'keyboard':
                    if action == 'press':
                        self.keyboard_controller.press(keyboard_key_map[key_or_button])
                    elif action == 'release':
                        self.keyboard_controller.release(keyboard_key_map[key_or_button])
                        
                elif device == 'mouse':
                    if action == 'press':
                        self.mouse_controller.press(mouse_key_map[key_or_button])
                    elif action == 'release':
                        self.mouse_controller.release(mouse_key_map[key_or_button])
                    elif action == 'scroll_up':
                        self.mouse_controller.scroll(0, 1)
                    elif action == 'scroll_down':
                        self.mouse_controller.scroll(0, -1)
                        
            time.sleep(1 / self.event_hz)

    def press(self, device: str, key: str):
        """
        device: 'keyboard' or 'mouse'
        key: For keyboard, any key from keyboard_key_map
             For mouse, any key from mouse_key_map
        """
        if device == 'mouse':
            if key not in mouse_key_map:
                raise ValueError(f"Invalid mouse key: {key}")
            self.buffer.append(('mouse', 'press', key))
        elif device == 'keyboard':
            if key not in keyboard_key_map:
                raise ValueError(f"Invalid keyboard key: {key}")
            self.buffer.append(('keyboard', 'press', key))
        else:
            raise ValueError(f"Invalid device: {device}. Use 'keyboard' or 'mouse'.")

    def release(self, device: str, key: str):
        """
        device: 'keyboard' or 'mouse'
        key: For keyboard, any key from keyboard_key_map
             For mouse, any key from mouse_key_map
        """
        if device == 'mouse':
            if key not in mouse_key_map:
                raise ValueError(f"Invalid mouse button: {key}.")
            self.buffer.append(('mouse', 'release', key))
        elif device == 'keyboard':
            if key not in keyboard_key_map:
                raise ValueError(f"Invalid keyboard key: {key}")
            self.buffer.append(('keyboard', 'release', key))
        else:
            raise ValueError(f"Invalid device: {device}. Use 'keyboard' or 'mouse'.")

    def scroll_up(self):
        """
        Scroll the mouse wheel up.
        """
        self.buffer.append(('mouse', 'scroll_up', ''))

    def scroll_down(self):
        """
        Scroll the mouse wheel down.
        """
        self.buffer.append(('mouse', 'scroll_down', ''))

    def cleanup(self):
        self.done = True
        self.event_thread.join()
