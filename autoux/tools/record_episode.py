#!/usr/bin/env python3
import argparse
import io
import json
import threading
import time
from datetime import datetime
from pathlib import Path

from mcap.writer import Writer
from PIL import Image
from pynput import keyboard, mouse
from pynput.keyboard import Key
from pynput.mouse import Controller as MouseController

from autoux.utils.key_map import mouse_key_map
from autoux.utils.miscellaneous import Rate
from autoux.utils.observers import ScreenObserver


class EpisodeRecorder:
    def __init__(
        self,
        context: str,
        hz: float,
        jpeg_quality: int = 75,
        verbose: bool = False,
        record_screen_with_cursor: bool = False,
    ):
        self.context = context
        self.hz = hz
        self.jpeg_quality = jpeg_quality
        self.verbose = verbose
        self.record_screen_with_cursor = record_screen_with_cursor
        self.recording = False

        # Initialize components
        self.screen = ScreenObserver()
        # Initialize mouse controller but don't start control threads during recording
        self.mouse_position_reader = MouseController()

        # Data storage
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y_%m_%d|%H:%M:%S")
        self.mcap_file = self.data_dir / f"{timestamp}.mcap"

        # MCAP writer
        self.mcap_writer = None
        self.mcap_file_handle = None

        # Event listeners
        self.mouse_listener = None
        self.keyboard_listener = None

        # Recording state
        self.start_time = None
        self.pressed_keys = set()

        # Event buffering for performance
        self.event_buffer = []
        self.buffer_lock = threading.Lock()
        self.flush_timer = None

        # Create reverse mouse key mapping for button conversion
        self.reverse_mouse_key_map = {v: k for k, v in mouse_key_map.items()}

    def setup_mcap(self):
        """Initialize MCAP file and writer"""
        self.mcap_file_handle = open(self.mcap_file, "wb")
        self.mcap_writer = Writer(self.mcap_file_handle)
        self.mcap_writer.start()

        # Define schemas for different data types
        screen_schema = self.mcap_writer.register_schema(
            name="screen_capture",
            encoding="jpeg",
            data=b""
        )

        cursor_pos_schema = self.mcap_writer.register_schema(
            name="cursor_position",
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
            name="event",
            encoding="json",
            data=json.dumps({
                "type": "object",
                "properties": {
                    "timestamp": {"type": "number"},
                    "device": {"type": "string"},
                    "key": {"type": "string"},
                    "action": {"type": "string"}
                }
            }).encode()
        )


        # Register channels
        self.screen_channel = self.mcap_writer.register_channel(
            schema_id=screen_schema,
            topic="/screen_capture",
            message_encoding="jpeg"
        )

        self.cursor_pos_channel = self.mcap_writer.register_channel(
            schema_id=cursor_pos_schema,
            topic="/cursor_position",
            message_encoding="json"
        )

        self.event_channel = self.mcap_writer.register_channel(
            schema_id=event_schema,
            topic="/events",
            message_encoding="json"
        )


    def get_timestamp(self):
        """Get timestamp relative to recording start"""
        if self.start_time is None:
            return 0.0
        return time.time() - self.start_time

    def record_context(self):
        """Record context information as metadata"""
        if self.context:
            self.mcap_writer.add_metadata(
                name="context",
                data={"context": self.context}
            )

    def record_frame(self):
        """Record a single frame of screen capture and mouse position"""
        try:
            timestamp = self.get_timestamp()
            timestamp_ns = int(timestamp * 1e9)

            # Get mouse position without active control threads
            mouse_pos = self.mouse_position_reader.position

            # Capture screen with or without cursor based on flag
            if self.record_screen_with_cursor:
                screen_img = self.screen.capture(cursor_pos=mouse_pos)
            else:
                screen_img = self.screen.capture()

            # Convert screen image to JPEG bytes
            pil_img = Image.fromarray(screen_img)
            buffer = io.BytesIO()
            pil_img.save(buffer, format='JPEG', quality=self.jpeg_quality, optimize=False)
            jpeg_bytes = buffer.getvalue()

            # Record screen capture as raw JPEG bytes
            self.mcap_writer.add_message(
                channel_id=self.screen_channel,
                log_time=timestamp_ns,
                data=jpeg_bytes,
                publish_time=timestamp_ns
            )

            # Record mouse position
            mouse_data = {
                "timestamp": timestamp,
                "x": int(mouse_pos[0]),
                "y": int(mouse_pos[1])
            }

            self.mcap_writer.add_message(
                channel_id=self.cursor_pos_channel,
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

        action = 'press' if pressed else 'release'
        button_str = self.reverse_mouse_key_map.get(button, str(button))

        event_data = {
            "timestamp": timestamp,
            "device": "mouse",
            "key": button_str,
            "action": action
        }

        # Print event if verbose mode is enabled
        if self.verbose:
            print(f"Mouse {action}: {button_str} at ({x}, {y})")

        # Buffer the event instead of writing immediately
        self.buffer_event(self.event_channel, timestamp_ns, event_data)

    def on_mouse_scroll(self, x, y, dx, dy):
        """Mouse scroll event handler"""
        if not self.recording:
            return

        timestamp = self.get_timestamp()
        timestamp_ns = int(timestamp * 1e9)

        # Determine scroll direction based on dy (vertical scroll)
        if dy > 0:
            action = "scroll"
            key = "up"
        elif dy < 0:
            action = "scroll"
            key = "down"
        else:
            # No vertical scroll, ignore horizontal for now
            return

        event_data = {
            "timestamp": timestamp,
            "device": "mouse",
            "key": key,
            "action": action
        }

        # Print event if verbose mode is enabled
        if self.verbose:
            print(f"Mouse {action} at ({x}, {y})")

        # Buffer the event instead of writing immediately
        self.buffer_event(self.event_channel, timestamp_ns, event_data)


    def on_key_press(self, key):
        """Keyboard press event handler"""
        if not self.recording:
            return

        # Add key to pressed keys set
        self.pressed_keys.add(key)

        # Check for Alt+X combination to stop recording
        alt_pressed = (
            Key.alt in self.pressed_keys or
            Key.alt_l in self.pressed_keys or
            Key.alt_r in self.pressed_keys
        )
        if alt_pressed and hasattr(key, 'char') and key.char == 'x':
            print("\nAlt+X pressed - stopping recording...")
            self.recording = False
            return

        timestamp = self.get_timestamp()
        timestamp_ns = int(timestamp * 1e9)

        # Convert key to string representation
        key_str = self.key_to_string(key)

        event_data = {
            "timestamp": timestamp,
            "device": "keyboard",
            "key": key_str,
            "action": "press"
        }

        # Print event if verbose mode is enabled
        if self.verbose:
            print(f"Keyboard press: {key_str}")

        # Buffer the event instead of writing immediately
        self.buffer_event(self.event_channel, timestamp_ns, event_data)

    def on_key_release(self, key):
        """Keyboard release event handler"""
        if not self.recording:
            return

        # Remove key from pressed keys set
        self.pressed_keys.discard(key)

        timestamp = self.get_timestamp()
        timestamp_ns = int(timestamp * 1e9)

        # Convert key to string representation
        key_str = self.key_to_string(key)

        event_data = {
            "timestamp": timestamp,
            "device": "keyboard",
            "key": key_str,
            "action": "release"
        }

        # Print event if verbose mode is enabled
        if self.verbose:
            print(f"Keyboard release: {key_str}")

        # Buffer the event instead of writing immediately
        self.buffer_event(self.event_channel, timestamp_ns, event_data)

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

    def buffer_event(self, channel_id, timestamp_ns, event_data):
        """Buffer events to reduce I/O during high-frequency operations"""
        with self.buffer_lock:
            self.event_buffer.append((channel_id, timestamp_ns, event_data))

    def flush_event_buffer(self):
        """Flush all buffered events to MCAP file except the last one"""
        events_to_flush = []
        with self.buffer_lock:
            if not self.event_buffer:
                return
            # Keep the last event in the buffer, don't flush it
            if len(self.event_buffer) > 1:
                events_to_flush = self.event_buffer[:-1].copy()
                # Keep only the last event in the buffer
                self.event_buffer = self.event_buffer[-1:]
            else:
                # If there's only one event, don't flush it
                return

        for channel_id, timestamp_ns, event_data in events_to_flush:
            self.mcap_writer.add_message(
                channel_id=channel_id,
                log_time=timestamp_ns,
                data=json.dumps(event_data).encode(),
                publish_time=timestamp_ns
            )

    def start_flush_timer(self):
        """Start periodic flushing of event buffer every 5 seconds"""
        if self.recording:
            self.flush_event_buffer()
            self.flush_timer = threading.Timer(5.0, self.start_flush_timer)
            self.flush_timer.start()

    def stop_flush_timer(self):
        """Stop the periodic flush timer"""
        if self.flush_timer:
            self.flush_timer.cancel()
            self.flush_timer = None

    def start_recording(self):
        """Start the recording session"""
        print("Starting episode recording...")
        print(f"Context: {self.context}")
        print(f"Frequency: {self.hz} Hz")
        print(f"Output file: {self.mcap_file}")
        print("Press Ctrl+C or Alt+X to stop recording")

        self.recording = True
        self.start_time = time.time()

        # Setup MCAP
        self.setup_mcap()

        # Record context
        self.record_context()

        # Start periodic buffer flushing
        self.start_flush_timer()

        # Start event listeners - ensure events pass through to system
        self.mouse_listener = mouse.Listener(
            on_click=self.on_mouse_click,
            on_scroll=self.on_mouse_scroll,
            suppress=False  # Allow events to pass through to system
        )
        self.mouse_listener.start()

        self.keyboard_listener = keyboard.Listener(
            on_press=self.on_key_press,
            on_release=self.on_key_release,
            suppress=False  # Allow events to pass through to system
        )
        self.keyboard_listener.start()

        try:
            rate = Rate(self.hz)
            while self.recording:
                if not self.record_frame():
                    break
                rate.sleep()
        except KeyboardInterrupt:
            print("\nStopping recording...")
        finally:
            self.stop_recording()

    def stop_recording(self):
        """Stop the recording session"""
        self.recording = False

        # Stop periodic flushing
        self.stop_flush_timer()

        # Stop listeners
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.keyboard_listener:
            self.keyboard_listener.stop()

        # Flush any remaining buffered events
        self.flush_event_buffer()

        # Close MCAP file
        if self.mcap_writer:
            self.mcap_writer.finish()
        if self.mcap_file_handle:
            self.mcap_file_handle.close()

        # Create symlink to latest recording
        latest_link = self.data_dir / "latest.mcap"
        if latest_link.exists() or latest_link.is_symlink():
            latest_link.unlink()
        latest_link.symlink_to(self.mcap_file.name)

        print(f"Recording saved to: {self.mcap_file}")
        print(f"Latest recording symlink: {latest_link}")


def main():
    parser = argparse.ArgumentParser(description="Record episode data for agent training")
    parser.add_argument("--context", type=str, default="",
                       help="Context description for the episode")
    parser.add_argument("--hz", type=float, default=10.0,
                       help="Recording frequency in Hz (default: 10.0)")
    parser.add_argument("--jpeg-quality", type=int, default=75,
                       help="JPEG compression quality 1-100 (default: 75, lower=faster)")
    parser.add_argument("--verbose", action="store_true",
                       help="Print events as they happen")
    parser.add_argument("--record-screen-with-cursor", action="store_true",
                       help="Record screen with cursor visible")

    args = parser.parse_args()

    recorder = EpisodeRecorder(
        args.context,
        args.hz,
        args.jpeg_quality,
        args.verbose,
        args.record_screen_with_cursor,
    )
    recorder.start_recording()


if __name__ == '__main__':
    main()
