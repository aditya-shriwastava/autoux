import numpy as np
from mss import mss
from PIL import Image, ImageDraw


class ScreenObserver:
    def __init__(self):
        self.sct = mss()
        self.monitor = self.sct.monitors[1]

    def capture(self, cursor_pos: tuple[int, int] = None):
        """
        Capture the primary monitor and return a NumPy array (H, W, 3 RGB, dtype=uint8),
        with the mouse cursor overlaid if cursor_pos is not None.
        """
        img = self.sct.grab(self.monitor)
        pil_img = Image.frombytes(
            'RGB',
            img.size,
            img.rgb
        )

        if cursor_pos is not None:
            self.draw_cursor(pil_img, cursor_pos[0], cursor_pos[1])

        return np.array(pil_img)

    def draw_cursor(self, image: Image.Image, x: int, y: int):
        """
        Draw a circular cursor: black fill with thick white border at the given relative
        position on the provided PIL image.
        """
        circle_radius = 8
        outline_width = 3
        if 0 <= x < image.width and 0 <= y < image.height:
            draw = ImageDraw.Draw(image)
            # Draw white border (outer circle)
            draw.ellipse([
                (x - circle_radius - outline_width, y - circle_radius - outline_width),
                (x + circle_radius + outline_width, y + circle_radius + outline_width)
            ], fill="white")
            # Draw black filled circle (inner)
            draw.ellipse([
                (x - circle_radius, y - circle_radius),
                (x + circle_radius, y + circle_radius)
            ], fill="black")