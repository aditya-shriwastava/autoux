#!/usr/bin/env python3

import argparse
import json
import time
from datetime import datetime
from pathlib import Path

from mcap.writer import Writer
from PIL import Image
from pynput import keyboard, mouse

from .mouse import Mouse
from .screen import Screen


class EpisodeRecorder:
    def __init__(self, context: str, hz: float):
        self.context = context
        self.hz = hz
        self.recording = False

        # Initialize components
        self.screen = Screen()
        self.mouse_controller = Mouse()

        # Data storage
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.mcap_file = self.data_dir / f"record_{timestamp}.mcap"

        # MCAP writer
        self.mcap_writer = None
        self.mcap_file_handle = None

        # Event listeners
        self.mouse_listener = None
        self.keyboard_listener = None

        # Recording state
        self.start_time = None

    def setup_mcap(self):
        """Initialize MCAP file and writer"""
        self.mcap_file_handle = open(self.mcap_file, "wb")
        self.mcap_writer = Writer(self.mcap_file_handle)
        self.mcap_writer.start()

        # Define schemas for different data types
        screen_schema = self.mcap_writer.register_schema(
            name="screen_capture",
            encoding="json",
            data=json.dumps({
                "type": "object",
                "properties": {
                    "timestamp": {"type": "number"},
                    "width": {"type": "integer"},
                    "height": {"type": "integer"},
                    "data": {"type": "string"}  # base64 encoded image
                }
            }).encode()
        )

        mouse_pos_schema = self.mcap_writer.register_schema(
            name="mouse_position",
            encoding="json",
            data=json.dumps({
                "type": "object",
                "properties": {
                    "timestamp": {"type": "number"},
                    "x": {"type": "integer"},
                    "y": {"type": "integer"}
                }
            }).encode()
        )

        event_schema = self.mcap_writer.register_schema(
            name="input_event",
            encoding="json",
            data=json.dumps({
                "type": "object",
                "properties": {
                    "timestamp": {"type": "number"},
                    "device": {"type": "string"},
                    "key_or_button": {"type": "string"},
                    "action": {"type": "string"}
                }
            }).encode()
        )

        context_schema = self.mcap_writer.register_schema(
            name="context",
            encoding="json",
            data=json.dumps({
                "type": "object",
                "properties": {
                    "context": {"type": "string"}
                }
            }).encode()
        )

        # Register channels
        self.screen_channel = self.mcap_writer.register_channel(
            schema_id=screen_schema,
            topic="/screen_capture",
            message_encoding="json"
        )

        self.mouse_pos_channel = self.mcap_writer.register_channel(
            schema_id=mouse_pos_schema,
            topic="/mouse_position",
            message_encoding="json"
        )

        self.event_channel = self.mcap_writer.register_channel(
            schema_id=event_schema,
            topic="/input_events",
            message_encoding="json"
        )

        self.context_channel = self.mcap_writer.register_channel(
            schema_id=context_schema,
            topic="/context",
            message_encoding="json"
        )

    def get_timestamp(self):
        """Get timestamp relative to recording start"""
        if self.start_time is None:
            return 0.0
        return time.time() - self.start_time

    def record_context(self):
        """Record context information"""
        timestamp_ns = int(self.get_timestamp() * 1e9)
        context_data = {
            "context": self.context
        }

        self.mcap_writer.add_message(
            channel_id=self.context_channel,
            log_time=timestamp_ns,
            data=json.dumps(context_data).encode(),
            publish_time=timestamp_ns
        )

    def record_frame(self):
        """Record a single frame of screen capture and mouse position"""
        try:
            timestamp = self.get_timestamp()
            timestamp_ns = int(timestamp * 1e9)

            # Get mouse position
            mouse_pos = self.mouse_controller.get_cursor_position()

            # Capture screen without cursor
            screen_img = self.screen.capture()

            # Convert screen image to base64 for storage
            import base64
            import io

            pil_img = Image.fromarray(screen_img)
            buffer = io.BytesIO()
            pil_img.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode()

            # Record screen capture
            screen_data = {
                "timestamp": timestamp,
                "width": screen_img.shape[1],
                "height": screen_img.shape[0],
                "data": img_base64
            }

            self.mcap_writer.add_message(
                channel_id=self.screen_channel,
                log_time=timestamp_ns,
                data=json.dumps(screen_data).encode(),
                publish_time=timestamp_ns
            )

            # Record mouse position
            mouse_data = {
                "timestamp": timestamp,
                "x": int(mouse_pos[0]),
                "y": int(mouse_pos[1])
            }

            self.mcap_writer.add_message(
                channel_id=self.mouse_pos_channel,
                log_time=timestamp_ns,
                data=json.dumps(mouse_data).encode(),
                publish_time=timestamp_ns
            )

        except Exception as e:
            print(f"Error recording frame: {e}")
            return False
        return True

    def on_mouse_click(self, x, y, button, pressed):
        """Mouse click event handler"""
        if not self.recording:
            return

        timestamp = self.get_timestamp()
        timestamp_ns = int(timestamp * 1e9)

        button_map = {
            mouse.Button.left: 'L',
            mouse.Button.right: 'R',
            mouse.Button.middle: 'M'
        }

        action = 'press' if pressed else 'release'
        button_str = button_map.get(button, str(button))

        event_data = {
            "timestamp": timestamp,
            "device": "mouse",
            "key_or_button": button_str,
            "action": action
        }

        self.mcap_writer.add_message(
            channel_id=self.event_channel,
            log_time=timestamp_ns,
            data=json.dumps(event_data).encode(),
            publish_time=timestamp_ns
        )

    def on_mouse_scroll(self, x, y, dx, dy):
        """Mouse scroll event handler"""
        if not self.recording:
            return

        timestamp = self.get_timestamp()
        timestamp_ns = int(timestamp * 1e9)

        # Handle vertical scroll
        if dy != 0:
            scroll_dir = 1 if dy > 0 else -1
            event_data = {
                "timestamp": timestamp,
                "device": "mouse",
                "key_or_button": str(scroll_dir),
                "action": "scroll"
            }

            self.mcap_writer.add_message(
                channel_id=self.event_channel,
                log_time=timestamp_ns,
                data=json.dumps(event_data).encode(),
                publish_time=timestamp_ns
            )

    def on_key_press(self, key):
        """Keyboard press event handler"""
        if not self.recording:
            return

        timestamp = self.get_timestamp()
        timestamp_ns = int(timestamp * 1e9)

        # Convert key to string representation
        key_str = self.key_to_string(key)

        event_data = {
            "timestamp": timestamp,
            "device": "keyboard",
            "key_or_button": key_str,
            "action": "press"
        }

        self.mcap_writer.add_message(
            channel_id=self.event_channel,
            log_time=timestamp_ns,
            data=json.dumps(event_data).encode(),
            publish_time=timestamp_ns
        )

    def on_key_release(self, key):
        """Keyboard release event handler"""
        if not self.recording:
            return

        timestamp = self.get_timestamp()
        timestamp_ns = int(timestamp * 1e9)

        # Convert key to string representation
        key_str = self.key_to_string(key)

        event_data = {
            "timestamp": timestamp,
            "device": "keyboard",
            "key_or_button": key_str,
            "action": "release"
        }

        self.mcap_writer.add_message(
            channel_id=self.event_channel,
            log_time=timestamp_ns,
            data=json.dumps(event_data).encode(),
            publish_time=timestamp_ns
        )

    def key_to_string(self, key):
        """Convert pynput key to string representation"""
        try:
            # Handle special keys
            if hasattr(key, 'name'):
                return key.name
            # Handle character keys
            elif hasattr(key, 'char') and key.char is not None:
                return key.char
            else:
                return str(key)
        except:
            return str(key)

    def start_recording(self):
        """Start the recording session"""
        print("Starting episode recording...")
        print(f"Context: {self.context}")
        print(f"Frequency: {self.hz} Hz")
        print(f"Output file: {self.mcap_file}")
        print("Press Ctrl+C to stop recording")

        self.recording = True
        self.start_time = time.time()

        # Setup MCAP
        self.setup_mcap()

        # Record context
        self.record_context()

        # Start event listeners
        self.mouse_listener = mouse.Listener(
            on_click=self.on_mouse_click,
            on_scroll=self.on_mouse_scroll
        )
        self.mouse_listener.start()

        self.keyboard_listener = keyboard.Listener(
            on_press=self.on_key_press,
            on_release=self.on_key_release
        )
        self.keyboard_listener.start()

        try:
            # Main recording loop - keep screen capture on main thread
            last_frame_time = time.time()
            while self.recording:
                current_time = time.time()
                if current_time - last_frame_time >= (1.0 / self.hz):
                    if not self.record_frame():
                        break
                    last_frame_time = current_time
                time.sleep(0.001)  # Small sleep to prevent busy waiting
        except KeyboardInterrupt:
            print("\nStopping recording...")
            self.stop_recording()

    def stop_recording(self):
        """Stop the recording session"""
        self.recording = False

        # Stop listeners
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.keyboard_listener:
            self.keyboard_listener.stop()

        # Close MCAP file
        if self.mcap_writer:
            self.mcap_writer.finish()
        if self.mcap_file_handle:
            self.mcap_file_handle.close()

        # Cleanup mouse controller
        self.mouse_controller.cleanup()

        print(f"Recording saved to: {self.mcap_file}")


def main():
    parser = argparse.ArgumentParser(description="Record episode data for agent training")
    parser.add_argument("--context", type=str, default="",
                       help="Context description for the episode")
    parser.add_argument("--hz", type=float, default=10.0,
                       help="Recording frequency in Hz (default: 10.0)")

    args = parser.parse_args()

    recorder = EpisodeRecorder(args.context, args.hz)
    recorder.start_recording()


if __name__ == '__main__':
    main()
