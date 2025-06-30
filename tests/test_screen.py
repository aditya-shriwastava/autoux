from unittest.mock import Mock, patch

import numpy as np
from PIL import Image

from autoux.screen import Screen


class TestScreen:
    @patch("autoux.screen.mss")
    def test_screen_initialization(self, mock_mss_class):
        """Test screen initialization"""
        mock_mss_instance = Mock()
        mock_mss_instance.monitors = [
            {
                "left": 0,
                "top": 0,
                "width": 0,
                "height": 0,
            },  # monitors[0] is all monitors
            {
                "left": 0,
                "top": 0,
                "width": 1920,
                "height": 1080,
            },  # monitors[1] is primary
        ]
        mock_mss_class.return_value = mock_mss_instance

        screen = Screen()

        assert screen.sct == mock_mss_instance
        assert screen.monitor == mock_mss_instance.monitors[1]
        mock_mss_class.assert_called_once()

    @patch("autoux.screen.mss")
    @patch("autoux.screen.Image.frombytes")
    def test_capture_without_cursor(self, mock_frombytes, mock_mss_class):
        """Test screen capture without cursor overlay"""
        # Setup mocks
        mock_mss_instance = Mock()
        mock_mss_instance.monitors = [
            {"left": 0, "top": 0, "width": 0, "height": 0},
            {"left": 0, "top": 0, "width": 1920, "height": 1080},
        ]
        mock_mss_class.return_value = mock_mss_instance

        # Mock captured image
        mock_img = Mock()
        mock_img.size = (1920, 1080)
        mock_img.rgb = b"x" * (1920 * 1080 * 3)  # Mock RGB data
        mock_mss_instance.grab.return_value = mock_img

        # Mock PIL Image
        mock_pil_img = Mock()
        mock_frombytes.return_value = mock_pil_img

        # Mock numpy array conversion
        expected_array = np.zeros((1080, 1920, 3), dtype=np.uint8)
        with patch(
            "autoux.screen.np.array", return_value=expected_array
        ) as mock_np_array:
            screen = Screen()
            result = screen.capture()

            # Verify calls
            mock_mss_instance.grab.assert_called_once_with(screen.monitor)
            mock_frombytes.assert_called_once_with("RGB", (1920, 1080), mock_img.rgb)
            mock_np_array.assert_called_once_with(mock_pil_img)

            # Verify result
            assert np.array_equal(result, expected_array)
            assert result.shape == (1080, 1920, 3)
            assert result.dtype == np.uint8

    @patch("autoux.screen.mss")
    @patch("autoux.screen.Image.frombytes")
    def test_capture_with_cursor(self, mock_frombytes, mock_mss_class):
        """Test screen capture with cursor overlay"""
        # Setup mocks
        mock_mss_instance = Mock()
        mock_mss_instance.monitors = [
            {"left": 0, "top": 0, "width": 0, "height": 0},
            {"left": 0, "top": 0, "width": 1920, "height": 1080},
        ]
        mock_mss_class.return_value = mock_mss_instance

        # Mock captured image
        mock_img = Mock()
        mock_img.size = (1920, 1080)
        mock_img.rgb = b"x" * (1920 * 1080 * 3)
        mock_mss_instance.grab.return_value = mock_img

        # Mock PIL Image
        mock_pil_img = Mock()
        mock_frombytes.return_value = mock_pil_img

        # Mock numpy array conversion
        expected_array = np.zeros((1080, 1920, 3), dtype=np.uint8)

        with patch(
            "autoux.screen.np.array", return_value=expected_array
        ) as mock_np_array:
            screen = Screen()

            # Mock draw_cursor method
            with patch.object(screen, "draw_cursor") as mock_draw_cursor:
                cursor_pos = (100, 200)
                result = screen.capture(cursor_pos=cursor_pos)

                # Verify calls
                mock_mss_instance.grab.assert_called_once_with(screen.monitor)
                mock_frombytes.assert_called_once_with(
                    "RGB", (1920, 1080), mock_img.rgb
                )
                mock_draw_cursor.assert_called_once_with(mock_pil_img, 100, 200)
                mock_np_array.assert_called_once_with(mock_pil_img)

                # Verify result
                assert np.array_equal(result, expected_array)

    def test_draw_cursor_valid_position(self):
        """Test drawing cursor at valid position"""
        # Create a test image
        test_image = Image.new("RGB", (800, 600), color="red")

        with patch("autoux.screen.mss"):
            screen = Screen()

            # Draw cursor at valid position
            screen.draw_cursor(test_image, 400, 300)

            # Convert to numpy array to check if cursor was drawn
            img_array = np.array(test_image)

            # Check that the image was modified around cursor position
            # The cursor should create black and white pixels around (400, 300)
            cursor_region = img_array[290:310, 390:410, :]

            # Should contain non-red pixels (black or white from cursor)
            red_color = np.array([255, 0, 0])
            has_non_red = not np.all(cursor_region == red_color)
            assert has_non_red, "Cursor should have been drawn on the image"

    def test_draw_cursor_edge_positions(self):
        """Test drawing cursor at edge positions"""
        test_image = Image.new("RGB", (100, 100), color="blue")

        with patch("autoux.screen.mss"):
            screen = Screen()

            # Test cursor at edges (should not crash)
            screen.draw_cursor(test_image, 0, 0)  # Top-left corner
            screen.draw_cursor(test_image, 99, 99)  # Bottom-right corner
            screen.draw_cursor(test_image, 0, 99)  # Bottom-left corner
            screen.draw_cursor(test_image, 99, 0)  # Top-right corner

            # Should complete without errors

    def test_draw_cursor_out_of_bounds(self):
        """Test drawing cursor outside image bounds"""
        test_image = Image.new("RGB", (100, 100), color="green")

        with patch("autoux.screen.mss"):
            screen = Screen()

            # Test cursor outside bounds (should not crash)
            screen.draw_cursor(test_image, -10, -10)  # Completely outside
            screen.draw_cursor(test_image, 150, 150)  # Completely outside
            screen.draw_cursor(test_image, -5, 50)  # Partially outside
            screen.draw_cursor(test_image, 50, -5)  # Partially outside

            # Should complete without errors

    def test_draw_cursor_parameters(self):
        """Test cursor drawing with specific parameters"""
        test_image = Image.new("RGB", (200, 200), color="yellow")

        with patch("autoux.screen.mss"):
            screen = Screen()

            # Mock ImageDraw to capture calls
            with patch("autoux.screen.ImageDraw.Draw") as mock_draw_class:
                mock_draw = Mock()
                mock_draw_class.return_value = mock_draw

                screen.draw_cursor(test_image, 100, 100)

                # Verify Draw was called
                mock_draw_class.assert_called_once_with(test_image)

                # Verify ellipse calls (should be called twice: white border, black fill)
                assert mock_draw.ellipse.call_count == 2

                # Check the ellipse calls
                calls = mock_draw.ellipse.call_args_list

                # First call should be white border (larger circle)
                border_call = calls[0]
                assert border_call[1]["fill"] == "white"

                # Second call should be black fill (smaller circle)
                fill_call = calls[1]
                assert fill_call[1]["fill"] == "black"

    @patch("autoux.screen.mss")
    def test_cursor_circle_dimensions(self, mock_mss_class):
        """Test that cursor circle has correct dimensions"""
        mock_mss_instance = Mock()
        mock_mss_instance.monitors = [
            {"left": 0, "top": 0, "width": 0, "height": 0},
            {"left": 0, "top": 0, "width": 100, "height": 100},
        ]
        mock_mss_class.return_value = mock_mss_instance

        test_image = Image.new("RGB", (100, 100), color="white")
        screen = Screen()

        # Test cursor drawing with known parameters
        with patch("autoux.screen.ImageDraw.Draw") as mock_draw_class:
            mock_draw = Mock()
            mock_draw_class.return_value = mock_draw

            x, y = 50, 50
            screen.draw_cursor(test_image, x, y)

            # Verify the coordinates of the ellipses
            calls = mock_draw.ellipse.call_args_list

            # Border circle (radius 8 + outline 3 = 11)
            border_coords = calls[0][0][0]
            expected_border = [(x - 11, y - 11), (x + 11, y + 11)]
            assert border_coords == expected_border

            # Fill circle (radius 8)
            fill_coords = calls[1][0][0]
            expected_fill = [(x - 8, y - 8), (x + 8, y + 8)]
            assert fill_coords == expected_fill

    @patch("autoux.screen.mss")
    @patch("autoux.screen.Image.frombytes")
    def test_capture_return_type(self, mock_frombytes, mock_mss_class):
        """Test that capture returns correct numpy array type"""
        # Setup mocks
        mock_mss_instance = Mock()
        mock_mss_instance.monitors = [
            {"left": 0, "top": 0, "width": 0, "height": 0},
            {"left": 0, "top": 0, "width": 800, "height": 600},
        ]
        mock_mss_class.return_value = mock_mss_instance

        mock_img = Mock()
        mock_img.size = (800, 600)
        mock_img.rgb = b"x" * (800 * 600 * 3)
        mock_mss_instance.grab.return_value = mock_img

        mock_pil_img = Mock()
        mock_frombytes.return_value = mock_pil_img

        # Create actual numpy array
        test_array = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)

        with patch("autoux.screen.np.array", return_value=test_array):
            screen = Screen()
            result = screen.capture()

            # Verify return type and properties
            assert isinstance(result, np.ndarray)
            assert result.dtype == np.uint8
            assert len(result.shape) == 3
            assert result.shape[2] == 3  # RGB channels

    @patch("autoux.screen.mss")
    def test_monitor_selection(self, mock_mss_class):
        """Test that the correct monitor is selected"""
        mock_mss_instance = Mock()
        mock_mss_instance.monitors = [
            {"left": 0, "top": 0, "width": 3840, "height": 2160},  # All monitors
            {"left": 0, "top": 0, "width": 1920, "height": 1080},  # Monitor 1
            {"left": 1920, "top": 0, "width": 1920, "height": 1080},  # Monitor 2
        ]
        mock_mss_class.return_value = mock_mss_instance

        screen = Screen()

        # Should select monitors[1] (primary monitor)
        assert screen.monitor == mock_mss_instance.monitors[1]
        assert screen.monitor["width"] == 1920
        assert screen.monitor["height"] == 1080

    @patch("autoux.screen.mss")
    @patch("autoux.screen.Image.frombytes")
    def test_multiple_captures(self, mock_frombytes, mock_mss_class):
        """Test multiple consecutive captures"""
        # Setup mocks
        mock_mss_instance = Mock()
        mock_mss_instance.monitors = [
            {"left": 0, "top": 0, "width": 0, "height": 0},
            {"left": 0, "top": 0, "width": 640, "height": 480},
        ]
        mock_mss_class.return_value = mock_mss_instance

        mock_img = Mock()
        mock_img.size = (640, 480)
        mock_img.rgb = b"x" * (640 * 480 * 3)
        mock_mss_instance.grab.return_value = mock_img

        # Mock PIL image with width and height attributes
        mock_pil_img = Mock()
        mock_pil_img.width = 640
        mock_pil_img.height = 480
        mock_frombytes.return_value = mock_pil_img

        test_array = np.zeros((480, 640, 3), dtype=np.uint8)

        with patch("autoux.screen.np.array", return_value=test_array):
            screen = Screen()

            # Perform multiple captures
            result1 = screen.capture()
            result2 = screen.capture(cursor_pos=(100, 100))
            result3 = screen.capture(cursor_pos=(200, 200))

            # Verify all captures work
            assert isinstance(result1, np.ndarray)
            assert isinstance(result2, np.ndarray)
            assert isinstance(result3, np.ndarray)

            # Verify grab was called multiple times
            assert mock_mss_instance.grab.call_count == 3
