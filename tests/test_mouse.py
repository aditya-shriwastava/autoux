import time
from unittest.mock import Mock, patch

import pytest

from autoux.mouse import Mouse


class TestMouse:
    def setup_method(self):
        """Setup for each test method"""
        self.mock_controller = Mock()

    @patch("autoux.mouse.Controller")
    def test_mouse_initialization(self, mock_controller_class):
        """Test mouse initialization with default parameters"""
        mock_controller_class.return_value = self.mock_controller

        mouse = Mouse()

        assert mouse.cursor_hz == 50.0
        assert mouse.event_hz == 25.0
        assert mouse.cursor_vx == 0.0
        assert mouse.cursor_vy == 0.0
        assert mouse.buffer == []
        assert not mouse.done
        assert mouse.controller == self.mock_controller

        # Clean up
        mouse.cleanup()

    @patch("autoux.mouse.Controller")
    def test_mouse_initialization_custom_hz(self, mock_controller_class):
        """Test mouse initialization with custom frequencies"""
        mock_controller_class.return_value = self.mock_controller

        mouse = Mouse(cursor_hz=100.0, event_hz=50.0)

        assert mouse.cursor_hz == 100.0
        assert mouse.event_hz == 50.0

        # Clean up
        mouse.cleanup()

    @patch("autoux.mouse.Controller")
    def test_set_cursor_velocity(self, mock_controller_class):
        """Test setting cursor velocity"""
        mock_controller_class.return_value = self.mock_controller

        mouse = Mouse()
        mouse.set_cursor_velocity(10.5, -5.2)

        assert mouse.cursor_vx == 10.5
        assert mouse.cursor_vy == -5.2

        mouse.cleanup()

    @patch("autoux.mouse.Controller")
    def test_press_button_valid(self, mock_controller_class):
        """Test pressing valid mouse buttons"""
        mock_controller_class.return_value = self.mock_controller

        mouse = Mouse()

        # Test all valid buttons
        for button in ["L", "R", "M"]:
            mouse.press(button)
            assert ("press", button) in mouse.buffer

        assert len(mouse.buffer) == 3
        mouse.cleanup()

    @patch("autoux.mouse.Controller")
    def test_press_button_invalid(self, mock_controller_class):
        """Test pressing invalid mouse button raises error"""
        mock_controller_class.return_value = self.mock_controller

        mouse = Mouse()

        with pytest.raises(
            ValueError, match="Invalid button: X. Use 'L', 'R', or 'M'."
        ):
            mouse.press("X")

        mouse.cleanup()

    @patch("autoux.mouse.Controller")
    def test_release_button_valid(self, mock_controller_class):
        """Test releasing valid mouse buttons"""
        mock_controller_class.return_value = self.mock_controller

        mouse = Mouse()

        # Test all valid buttons
        for button in ["L", "R", "M"]:
            mouse.release(button)
            assert ("release", button) in mouse.buffer

        assert len(mouse.buffer) == 3
        mouse.cleanup()

    @patch("autoux.mouse.Controller")
    def test_release_button_invalid(self, mock_controller_class):
        """Test releasing invalid mouse button raises error"""
        mock_controller_class.return_value = self.mock_controller

        mouse = Mouse()

        with pytest.raises(
            ValueError, match="Invalid button: Y. Use 'L', 'R', or 'M'."
        ):
            mouse.release("Y")

        mouse.cleanup()

    @patch("autoux.mouse.Controller")
    def test_scroll_operations(self, mock_controller_class):
        """Test scroll up and down operations"""
        mock_controller_class.return_value = self.mock_controller

        mouse = Mouse()

        mouse.scroll_up()
        mouse.scroll_down()

        assert ("scroll_up", "") in mouse.buffer
        assert ("scroll_down", "") in mouse.buffer
        assert len(mouse.buffer) == 2

        mouse.cleanup()

    @patch("autoux.mouse.Controller")
    def test_get_cursor_position(self, mock_controller_class):
        """Test getting cursor position"""
        mock_controller_class.return_value = self.mock_controller
        self.mock_controller.position = (100, 200)

        mouse = Mouse()
        position = mouse.get_cursor_position()

        assert position == (100, 200)
        mouse.cleanup()

    @patch("autoux.mouse.Controller")
    def test_cursor_control_loop(self, mock_controller_class):
        """Test cursor control loop functionality"""
        mock_controller_class.return_value = self.mock_controller

        mouse = Mouse(cursor_hz=10.0)  # Use lower frequency for testing

        # Set velocity after a brief delay to ensure thread has started
        time.sleep(0.05)
        mouse.set_cursor_velocity(20.0, 30.0)

        # Let the thread run with the new velocity
        time.sleep(0.15)

        # Stop the mouse
        mouse.cleanup()

        # Verify move was called
        assert self.mock_controller.move.called

        # Check that move was called with correct velocity calculation
        calls = self.mock_controller.move.call_args_list
        assert len(calls) > 0

        # Find a call with non-zero velocity (after we set it)
        expected_dx = 20.0 // 10.0  # 2.0
        expected_dy = 30.0 // 10.0  # 3.0
        found_expected_call = False
        for call in calls:
            if call[0] == (expected_dx, expected_dy):
                found_expected_call = True
                break
        assert found_expected_call, (
            f"Expected call with ({expected_dx}, {expected_dy}) not found in "
            f"{[call[0] for call in calls]}"
        )

    @patch("autoux.mouse.Controller")
    def test_event_control_loop(self, mock_controller_class):
        """Test event control loop processes buffer"""
        from pynput.mouse import Button

        mock_controller_class.return_value = self.mock_controller

        mouse = Mouse(event_hz=20.0)  # Use lower frequency for testing

        # Add events to buffer
        mouse.press("L")
        mouse.release("L")
        mouse.scroll_up()
        mouse.scroll_down()

        # Verify events were added to buffer
        assert len(mouse.buffer) == 4

        # Let the thread process events
        time.sleep(0.3)

        # Stop the mouse
        mouse.cleanup()

        # Verify all events were processed (buffer should be empty)
        assert len(mouse.buffer) == 0

        # Verify controller methods were called
        assert self.mock_controller.press.called
        assert self.mock_controller.release.called
        assert self.mock_controller.scroll.called

        # Verify specific calls were made
        self.mock_controller.press.assert_called_with(Button.left)
        self.mock_controller.release.assert_called_with(Button.left)
        # Scroll calls: scroll_up -> (0, 1), scroll_down -> (0, -1)
        scroll_calls = self.mock_controller.scroll.call_args_list
        assert len(scroll_calls) == 2
        assert scroll_calls[0][0] == (0, 1)  # scroll_up
        assert scroll_calls[1][0] == (0, -1)  # scroll_down

    @patch("autoux.mouse.Controller")
    def test_dual_thread_architecture(self, mock_controller_class):
        """Test that both threads are created and running"""
        mock_controller_class.return_value = self.mock_controller

        mouse = Mouse()

        # Check that both threads exist and are alive
        assert mouse.cursor_thread.is_alive()
        assert mouse.event_thread.is_alive()

        # Verify threads have different targets
        assert mouse.cursor_thread._target.__name__ == "cursor_control_loop"
        assert mouse.event_thread._target.__name__ == "event_control_loop"

        mouse.cleanup()

        # Verify threads are stopped
        assert not mouse.cursor_thread.is_alive()
        assert not mouse.event_thread.is_alive()

    @patch("autoux.mouse.Controller")
    def test_buffer_fifo_order(self, mock_controller_class):
        """Test that buffer processes events in FIFO order"""
        mock_controller_class.return_value = self.mock_controller

        mouse = Mouse()

        # Add events in specific order
        mouse.press("L")
        mouse.press("R")
        mouse.release("L")
        mouse.scroll_up()
        mouse.release("R")

        # Verify buffer order
        expected_order = [
            ("press", "L"),
            ("press", "R"),
            ("release", "L"),
            ("scroll_up", ""),
            ("release", "R"),
        ]

        assert mouse.buffer == expected_order

        mouse.cleanup()

    @patch("autoux.mouse.Controller")
    def test_button_mapping(self, mock_controller_class):
        """Test that button mapping works correctly"""
        from pynput.mouse import Button

        mock_controller_class.return_value = self.mock_controller

        mouse = Mouse()

        # Verify button mapping
        assert mouse.button_map["L"] == Button.left
        assert mouse.button_map["R"] == Button.right
        assert mouse.button_map["M"] == Button.middle

        mouse.cleanup()

    @patch("autoux.mouse.Controller")
    def test_concurrent_operations(self, mock_controller_class):
        """Test that cursor movement and events can work concurrently"""
        mock_controller_class.return_value = self.mock_controller

        mouse = Mouse()

        # Set cursor velocity
        mouse.set_cursor_velocity(50.0, -25.0)

        # Add mouse events
        mouse.press("L")
        mouse.release("L")

        # Let both threads run
        time.sleep(0.2)

        mouse.cleanup()

        # Verify both cursor movement and events were processed
        assert self.mock_controller.move.called
        assert self.mock_controller.press.called
        assert self.mock_controller.release.called

    @patch("autoux.mouse.Controller")
    def test_cleanup_stops_threads(self, mock_controller_class):
        """Test that cleanup properly stops both threads"""
        mock_controller_class.return_value = self.mock_controller

        mouse = Mouse()

        # Verify threads are running
        assert mouse.cursor_thread.is_alive()
        assert mouse.event_thread.is_alive()
        assert not mouse.done

        # Cleanup
        mouse.cleanup()

        # Verify cleanup worked
        assert mouse.done
        assert not mouse.cursor_thread.is_alive()
        assert not mouse.event_thread.is_alive()
