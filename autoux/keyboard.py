import time
from threading import Thread

from pynput.keyboard import Controller, Key


class Keyboard:
    def __init__(self, control_hz: float = 25.0):
        self.control_hz = control_hz

        self.controller = Controller()
        self.control_thread = Thread(target=self.control_loop)

        # Human-readable key map
        self.KEY_MAP = {
            'alt': Key.alt_l,
            'alt_l': Key.alt_l,
            'alt_r': Key.alt_l,
            'backspace': Key.backspace,
            'caps_lock': Key.caps_lock,
            'cmd': Key.cmd_l,
            'cmd_l': Key.cmd_l,
            'cmd_r': Key.cmd_l,
            'ctrl': Key.ctrl_l,
            'ctrl_l': Key.ctrl_l,
            'ctrl_r': Key.ctrl_l,
            'delete': Key.delete,
            'down': Key.down,
            'end': Key.end,
            'enter': Key.enter,
            'esc': Key.esc,
            'f1': Key.f1,
            'f2': Key.f2,
            'f3': Key.f3,
            'f4': Key.f4,
            'f5': Key.f5,
            'f6': Key.f6,
            'f7': Key.f7,
            'f8': Key.f8,
            'f9': Key.f9,
            'f10': Key.f10,
            'f11': Key.f11,
            'f12': Key.f12,
            'home': Key.home,
            'left': Key.left,
            'page_down': Key.page_down,
            'page_up': Key.page_up,
            'right': Key.right,
            'shift': Key.shift_l,
            'shift_l': Key.shift_l,
            'shift_r': Key.shift_l,
            'space': Key.space,
            'tab': Key.tab,
            'up': Key.up,
            # Alphanumeric and printable ASCII keys
            # Lowercase letters
            'a': 'a', 'b': 'b', 'c': 'c', 'd': 'd', 'e': 'e', 'f': 'f', 'g': 'g', 'h': 'h',
            'i': 'i', 'j': 'j', 'k': 'k', 'l': 'l', 'm': 'm', 'n': 'n', 'o': 'o', 'p': 'p',
            'q': 'q', 'r': 'r', 's': 's', 't': 't', 'u': 'u', 'v': 'v', 'w': 'w', 'x': 'x',
            'y': 'y', 'z': 'z',
            # Uppercase letters
            'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D', 'E': 'E', 'F': 'F', 'G': 'G', 'H': 'H',
            'I': 'I', 'J': 'J', 'K': 'K', 'L': 'L', 'M': 'M', 'N': 'N', 'O': 'O', 'P': 'P',
            'Q': 'Q', 'R': 'R', 'S': 'S', 'T': 'T', 'U': 'U', 'V': 'V', 'W': 'W', 'X': 'X',
            'Y': 'Y', 'Z': 'Z',
            # Numbers
            '0': '0', '1': '1', '2': '2', '3': '3', '4': '4', '5': '5', '6': '6', '7': '7',
            '8': '8', '9': '9',
            # Symbols
            '`': '`', '~': '~', '!': '!', '@': '@', '#': '#', '$': '$', '%': '%', '^': '^',
            '&': '&', '*': '*', '(': '(', ')': ')', '-': '-', '_': '_', '=': '=', '+': '+',
            '[': '[', ']': ']', '{': '{', '}': '}', '\\': '\\', '|': '|', ';': ';', ':': ':',
            '\'': '\'', '"': '"', ',': ',', '<': '<', '.': '.', '>': '>', '/': '/', '?': '?',
            ' ': ' '
        }

        self.buffer: list[tuple[str, str]] = []
        self.done = False
        self.control_thread.start()

    def control_loop(self):
        while not self.done:
            if len(self.buffer) > 0:
                action, key = self.buffer.pop(0)
                if action == 'press':
                    self.controller.press(self.KEY_MAP[key])
                elif action == 'release':
                    self.controller.release(self.KEY_MAP[key])
            time.sleep(1 / self.control_hz)

    def press_key(self, key: str):
        """
        Press a key on the keyboard.
        key: The key to press
        """
        self.buffer.append(('press', key))

    def release_key(self, key: str):
        """
        Release a key on the keyboard.
        key: The key to release
        """
        self.buffer.append(('release', key))

    def cleanup(self):
        self.done = True
        self.control_thread.join()
