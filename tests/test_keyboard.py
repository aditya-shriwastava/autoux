import time
from unittest.mock import Mock, patch

from autoux.keyboard import Keyboard


class TestKeyboard:
    def setup_method(self):
        """Setup for each test method"""
        self.mock_controller = Mock()

    @patch("autoux.keyboard.Controller")
    def test_keyboard_initialization(self, mock_controller_class):
        """Test keyboard initialization with default parameters"""
        mock_controller_class.return_value = self.mock_controller

        keyboard = Keyboard()

        assert keyboard.control_hz == 25.0
        assert keyboard.buffer == []
        assert not keyboard.done
        assert keyboard.controller == self.mock_controller
        assert keyboard.control_thread.is_alive()

        # Clean up
        keyboard.cleanup()

    @patch("autoux.keyboard.Controller")
    def test_keyboard_initialization_custom_hz(self, mock_controller_class):
        """Test keyboard initialization with custom frequency"""
        mock_controller_class.return_value = self.mock_controller

        keyboard = Keyboard(control_hz=50.0)

        assert keyboard.control_hz == 50.0
        assert keyboard.control_thread.is_alive()

        # Clean up
        keyboard.cleanup()

    @patch("autoux.keyboard.Controller")
    def test_press_key_special_keys(self, mock_controller_class):
        """Test pressing special keys"""
        mock_controller_class.return_value = self.mock_controller

        keyboard = Keyboard()

        # Test special keys
        special_keys = ["ctrl", "alt", "shift", "enter", "esc", "tab", "space"]
        for key in special_keys:
            keyboard.press_key(key)
            assert ("press", key) in keyboard.buffer

        assert len(keyboard.buffer) == len(special_keys)
        keyboard.cleanup()

    @patch("autoux.keyboard.Controller")
    def test_press_key_alphanumeric(self, mock_controller_class):
        """Test pressing alphanumeric keys"""
        mock_controller_class.return_value = self.mock_controller

        keyboard = Keyboard()

        # Test lowercase letters
        for char in "abcdefghijklmnopqrstuvwxyz":
            keyboard.press_key(char)
            assert ("press", char) in keyboard.buffer

        # Test uppercase letters
        for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            keyboard.press_key(char)
            assert ("press", char) in keyboard.buffer

        # Test numbers
        for char in "0123456789":
            keyboard.press_key(char)
            assert ("press", char) in keyboard.buffer

        keyboard.cleanup()

    @patch("autoux.keyboard.Controller")
    def test_press_key_symbols(self, mock_controller_class):
        """Test pressing symbol keys"""
        mock_controller_class.return_value = self.mock_controller

        keyboard = Keyboard()

        # Test common symbols
        symbols = ["!", "@", "#", "$", "%", "^", "&", "*", "(", ")", "-", "_", "=", "+"]
        for symbol in symbols:
            keyboard.press_key(symbol)
            assert ("press", symbol) in keyboard.buffer

        keyboard.cleanup()

    @patch("autoux.keyboard.Controller")
    def test_release_key_special_keys(self, mock_controller_class):
        """Test releasing special keys"""
        mock_controller_class.return_value = self.mock_controller

        keyboard = Keyboard()

        # Test special keys
        special_keys = ["ctrl", "alt", "shift", "enter", "esc", "tab", "space"]
        for key in special_keys:
            keyboard.release_key(key)
            assert ("release", key) in keyboard.buffer

        assert len(keyboard.buffer) == len(special_keys)
        keyboard.cleanup()

    @patch("autoux.keyboard.Controller")
    def test_release_key_alphanumeric(self, mock_controller_class):
        """Test releasing alphanumeric keys"""
        mock_controller_class.return_value = self.mock_controller

        keyboard = Keyboard()

        # Test letters and numbers
        test_keys = "abcABC123"
        for key in test_keys:
            keyboard.release_key(key)
            assert ("release", key) in keyboard.buffer

        keyboard.cleanup()

    @patch("autoux.keyboard.Controller")
    def test_key_mapping_special_keys(self, mock_controller_class):
        """Test that special keys are mapped correctly"""
        from pynput.keyboard import Key

        mock_controller_class.return_value = self.mock_controller

        keyboard = Keyboard()

        # Test key mappings
        assert keyboard.KEY_MAP["ctrl"] == Key.ctrl
        assert keyboard.KEY_MAP["alt"] == Key.alt
        assert keyboard.KEY_MAP["shift"] == Key.shift
        assert keyboard.KEY_MAP["enter"] == Key.enter
        assert keyboard.KEY_MAP["esc"] == Key.esc
        assert keyboard.KEY_MAP["tab"] == Key.tab
        assert keyboard.KEY_MAP["space"] == Key.space
        assert keyboard.KEY_MAP["backspace"] == Key.backspace
        assert keyboard.KEY_MAP["delete"] == Key.delete

        keyboard.cleanup()

    @patch("autoux.keyboard.Controller")
    def test_key_mapping_function_keys(self, mock_controller_class):
        """Test that function keys are mapped correctly"""
        from pynput.keyboard import Key

        mock_controller_class.return_value = self.mock_controller

        keyboard = Keyboard()

        # Test function keys
        for i in range(1, 13):
            f_key = f"f{i}"
            expected_key = getattr(Key, f_key)
            assert keyboard.KEY_MAP[f_key] == expected_key

        keyboard.cleanup()

    @patch("autoux.keyboard.Controller")
    def test_key_mapping_alphanumeric(self, mock_controller_class):
        """Test that alphanumeric keys are mapped correctly"""
        mock_controller_class.return_value = self.mock_controller

        keyboard = Keyboard()

        # Test that alphanumeric keys map to themselves
        for char in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789":
            assert keyboard.KEY_MAP[char] == char

        keyboard.cleanup()

    @patch("autoux.keyboard.Controller")
    def test_control_loop_processes_buffer(self, mock_controller_class):
        """Test that control loop processes buffer events"""
        from pynput.keyboard import Key

        mock_controller_class.return_value = self.mock_controller

        keyboard = Keyboard(control_hz=20.0)  # Use lower frequency for testing

        # Add events to buffer
        keyboard.press_key("a")
        keyboard.release_key("a")
        keyboard.press_key("ctrl")
        keyboard.release_key("ctrl")

        # Verify events were added to buffer
        assert len(keyboard.buffer) == 4

        # Let the thread process events
        time.sleep(0.3)

        # Stop the keyboard
        keyboard.cleanup()

        # Verify all events were processed (buffer should be empty)
        assert len(keyboard.buffer) == 0

        # Verify controller methods were called
        assert self.mock_controller.press.called
        assert self.mock_controller.release.called

        # Verify specific calls were made
        press_calls = self.mock_controller.press.call_args_list
        release_calls = self.mock_controller.release.call_args_list

        assert len(press_calls) == 2  # 'a' and 'ctrl'
        assert len(release_calls) == 2  # 'a' and 'ctrl'

        # Check that correct keys were pressed/released
        assert press_calls[0][0][0] == "a"  # First press was 'a'
        assert release_calls[0][0][0] == "a"  # First release was 'a'
        assert press_calls[1][0][0] == Key.ctrl  # Second press was ctrl
        assert release_calls[1][0][0] == Key.ctrl  # Second release was ctrl

    @patch("autoux.keyboard.Controller")
    def test_buffer_fifo_order(self, mock_controller_class):
        """Test that buffer processes events in FIFO order"""
        mock_controller_class.return_value = self.mock_controller

        keyboard = Keyboard()

        # Add events in specific order
        keyboard.press_key("a")
        keyboard.press_key("b")
        keyboard.release_key("a")
        keyboard.press_key("c")
        keyboard.release_key("b")
        keyboard.release_key("c")

        # Verify buffer order
        expected_order = [
            ("press", "a"),
            ("press", "b"),
            ("release", "a"),
            ("press", "c"),
            ("release", "b"),
            ("release", "c"),
        ]

        assert keyboard.buffer == expected_order

        keyboard.cleanup()

    @patch("autoux.keyboard.Controller")
    def test_thread_architecture(self, mock_controller_class):
        """Test that control thread is created and running"""
        mock_controller_class.return_value = self.mock_controller

        keyboard = Keyboard()

        # Check that thread exists and is alive
        assert keyboard.control_thread.is_alive()

        # Verify thread has correct target
        assert keyboard.control_thread._target.__name__ == "control_loop"

        keyboard.cleanup()

        # Verify thread is stopped
        assert not keyboard.control_thread.is_alive()

    @patch("autoux.keyboard.Controller")
    def test_cleanup_stops_thread(self, mock_controller_class):
        """Test that cleanup properly stops the thread"""
        mock_controller_class.return_value = self.mock_controller

        keyboard = Keyboard()

        # Verify thread is running
        assert keyboard.control_thread.is_alive()
        assert not keyboard.done

        # Cleanup
        keyboard.cleanup()

        # Verify cleanup worked
        assert keyboard.done
        assert not keyboard.control_thread.is_alive()

    @patch("autoux.keyboard.Controller")
    def test_mixed_key_operations(self, mock_controller_class):
        """Test mixed press/release operations with different key types"""
        mock_controller_class.return_value = self.mock_controller

        keyboard = Keyboard()

        # Mix of operations
        keyboard.press_key("ctrl")
        keyboard.press_key("a")
        keyboard.release_key("a")
        keyboard.release_key("ctrl")
        keyboard.press_key("1")
        keyboard.press_key("!")
        keyboard.release_key("!")
        keyboard.release_key("1")

        # Verify correct sequence
        expected_sequence = [
            ("press", "ctrl"),
            ("press", "a"),
            ("release", "a"),
            ("release", "ctrl"),
            ("press", "1"),
            ("press", "!"),
            ("release", "!"),
            ("release", "1"),
        ]

        assert keyboard.buffer == expected_sequence
        keyboard.cleanup()

    @patch("autoux.keyboard.Controller")
    def test_arrow_keys(self, mock_controller_class):
        """Test arrow key functionality"""
        from pynput.keyboard import Key

        mock_controller_class.return_value = self.mock_controller

        keyboard = Keyboard()

        # Test arrow keys
        arrow_keys = ["up", "down", "left", "right"]
        for key in arrow_keys:
            keyboard.press_key(key)
            keyboard.release_key(key)

        # Verify mapping
        assert keyboard.KEY_MAP["up"] == Key.up
        assert keyboard.KEY_MAP["down"] == Key.down
        assert keyboard.KEY_MAP["left"] == Key.left
        assert keyboard.KEY_MAP["right"] == Key.right

        keyboard.cleanup()

    @patch("autoux.keyboard.Controller")
    def test_modifier_keys(self, mock_controller_class):
        """Test modifier key functionality"""
        from pynput.keyboard import Key

        mock_controller_class.return_value = self.mock_controller

        keyboard = Keyboard()

        # Test modifier keys
        modifiers = {
            "ctrl": Key.ctrl_l,
            "alt": Key.alt_l,
            "shift": Key.shift_l,
            "cmd": Key.cmd_l,
            "ctrl_l": Key.ctrl_l,
            "ctrl_r": Key.ctrl_l,
            "alt_l": Key.alt_l,
            "alt_r": Key.alt_l,
            "shift_l": Key.shift_l,
            "shift_r": Key.shift_l,
        }

        for key_name, expected_key in modifiers.items():
            assert keyboard.KEY_MAP[key_name] == expected_key
            keyboard.press_key(key_name)
            keyboard.release_key(key_name)

        keyboard.cleanup()

    @patch("autoux.keyboard.Controller")
    def test_concurrent_key_presses(self, mock_controller_class):
        """Test that multiple keys can be pressed concurrently"""
        mock_controller_class.return_value = self.mock_controller

        keyboard = Keyboard(control_hz=30.0)

        # Simulate holding multiple keys
        keyboard.press_key("ctrl")
        keyboard.press_key("shift")
        keyboard.press_key("a")

        # Let some processing happen
        time.sleep(0.2)

        # Release keys
        keyboard.release_key("a")
        keyboard.release_key("shift")
        keyboard.release_key("ctrl")

        # Let processing complete
        time.sleep(0.2)

        keyboard.cleanup()

        # Verify all operations were processed
        assert len(keyboard.buffer) == 0
        assert self.mock_controller.press.call_count == 3
        assert self.mock_controller.release.call_count == 3

    @patch("autoux.keyboard.Controller")
    def test_key_map_completeness(self, mock_controller_class):
        """Test that KEY_MAP contains expected keys"""
        mock_controller_class.return_value = self.mock_controller

        keyboard = Keyboard()

        # Test that important keys exist in KEY_MAP
        required_keys = ["a", "ctrl", "shift", "enter", "space", "tab"]
        for key in required_keys:
            assert key in keyboard.KEY_MAP, f"Key '{key}' missing from KEY_MAP"

        # Test that alphanumeric keys map correctly
        for char in "abcABC123":
            assert keyboard.KEY_MAP[char] == char

        keyboard.cleanup()
