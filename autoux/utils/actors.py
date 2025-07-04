import time
from threading import Thread

from pynput.keyboard import Controller as KeyboardController
from pynput.mouse import Controller as MouseController

from autoux.utils.key_map import keyboard_key_map, mouse_key_map


class CursorActor:
    def __init__(self, cursor_hz: float = 50.0, mode_of_control: str = "position"):
        """
        cursor_hz: cursor movement control frequency in Hz
        mode_of_control: "position" or "velocity" control mode
        """
        self.cursor_hz = cursor_hz
        self.mode_of_control = mode_of_control
        self.controller = MouseController()

        # State variables
        self.done = False
        self.cursor_vx = 0.0
        self.cursor_vy = 0.0

        # Only start cursor thread if in velocity mode
        if self.mode_of_control == "velocity":
            self.cursor_thread = Thread(target=self.cursor_control_loop)
            self.cursor_thread.start()
        else:
            self.cursor_thread = None

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
        if self.mode_of_control != "velocity":
            print("Warning: set_cursor_velocity called in position mode - operation ignored")
            return

        self.cursor_vx = vx
        self.cursor_vy = vy

    def set_cursor_position(self, x, y):
        """
        Set the mouse cursor to absolute position.
        """
        self.controller.position = (x, y)

    def cleanup(self):
        self.done = True
        if self.cursor_thread is not None:
            self.cursor_thread.join()


class EventActor:
    def __init__(self, event_hz: float = 25.0, immediate: bool = False):
        """
        event_hz: event processing frequency in Hz
        immediate: If True, execute events immediately without buffering
        """
        self.event_hz = event_hz
        self.immediate = immediate

        self.keyboard_controller = KeyboardController()
        self.mouse_controller = MouseController()

        self.buffer: list[tuple[str, str, str]] = []  # (device, action, key)
        self.done = False

        # Only start event thread if not in immediate mode
        if not self.immediate:
            self.event_thread = Thread(target=self.event_control_loop)
            self.event_thread.start()
        else:
            self.event_thread = None

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
                    elif action == 'scroll':
                        if key_or_button == 'up':
                            self.mouse_controller.scroll(0, 1)
                        elif key_or_button == 'down':
                            self.mouse_controller.scroll(0, -1)

            time.sleep(1 / self.event_hz)

    def execute_immediately(self, device: str, action: str, key: str):
        """Execute an event immediately without buffering"""
        if device == 'keyboard':
            if action == 'press':
                self.keyboard_controller.press(keyboard_key_map[key])
            elif action == 'release':
                self.keyboard_controller.release(keyboard_key_map[key])
        elif device == 'mouse':
            if action == 'press':
                self.mouse_controller.press(mouse_key_map[key])
            elif action == 'release':
                self.mouse_controller.release(mouse_key_map[key])
            elif action == 'scroll':
                if key == 'up':
                    self.mouse_controller.scroll(0, 1)
                elif key == 'down':
                    self.mouse_controller.scroll(0, -1)

    def press(self, device: str, key: str):
        """
        device: 'keyboard' or 'mouse'
        key: For keyboard, any key from keyboard_key_map
             For mouse, any key from mouse_key_map
        """
        if device == 'mouse':
            if key not in mouse_key_map:
                raise ValueError(f"Invalid mouse key: {key}")
        elif device == 'keyboard':
            if key not in keyboard_key_map:
                raise ValueError(f"Invalid keyboard key: {key}")
        else:
            raise ValueError(f"Invalid device: {device}. Use 'keyboard' or 'mouse'.")

        if self.immediate:
            self.execute_immediately(device, 'press', key)
        else:
            self.buffer.append((device, 'press', key))

    def release(self, device: str, key: str):
        """
        device: 'keyboard' or 'mouse'
        key: For keyboard, any key from keyboard_key_map
             For mouse, any key from mouse_key_map
        """
        if device == 'mouse':
            if key not in mouse_key_map:
                raise ValueError(f"Invalid mouse button: {key}.")
        elif device == 'keyboard':
            if key not in keyboard_key_map:
                raise ValueError(f"Invalid keyboard key: {key}")
        else:
            raise ValueError(f"Invalid device: {device}. Use 'keyboard' or 'mouse'.")

        if self.immediate:
            self.execute_immediately(device, 'release', key)
        else:
            self.buffer.append((device, 'release', key))

    def scroll(self, direction: str):
        """
        Scroll the mouse wheel in specified direction.
        direction: 'up' or 'down'
        """
        if direction not in ['up', 'down']:
            raise ValueError(f"Invalid scroll direction: {direction}. Use 'up' or 'down'.")

        if self.immediate:
            self.execute_immediately('mouse', 'scroll', direction)
        else:
            self.buffer.append(('mouse', 'scroll', direction))

    def cleanup(self):
        self.done = True
        if self.event_thread is not None:
            self.event_thread.join()
