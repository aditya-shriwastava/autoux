#!/usr/bin/env python3

import argparse
import json
import time
from pathlib import Path

from mcap.reader import make_reader
from pynput import keyboard, mouse

from autoux.utils.actors import CursorActor, EventActor


class EpisodeReplayer:
    def __init__(self, mcap_file: str):
        self.mcap_file = Path(mcap_file)
        self.replaying = False
        self.stop_requested = False

        # Initialize controllers
        self.cursor_actor = CursorActor(mode_of_control="position")
        self.event_actor = EventActor(immediate=True)
        self.keyboard_controller = keyboard.Controller()
        self.mouse_hardware = mouse.Controller()

        # Safety listener
        self.safety_listener = None
        self.currently_replaying_keyboard = False

        # Track pressed keys and mouse buttons to ensure proper cleanup
        self.pressed_keys = set()  # Stores tuples of (device, key)

        # Episode data
        self.events = []
        self.start_time = None

    def load_episode_data(self):
        """Load and parse episode data from MCAP file"""
        print(f"Loading episode data from: {self.mcap_file}")

        if not self.mcap_file.exists():
            raise FileNotFoundError(f"MCAP file not found: {self.mcap_file}")

        events = []

        with open(self.mcap_file, "rb") as f:
            reader = make_reader(f)

            # Extract metadata (context)
            for metadata in reader.iter_metadata():
                if metadata.name == "context" and "context" in metadata.metadata:
                    print(f"Episode context: {metadata.metadata['context']}")

            for _schema, channel, message in reader.iter_messages():
                try:
                    if channel.topic == "/screen_capture":
                        # Skip screen capture data in replay (raw JPEG bytes)
                        continue

                    data = json.loads(message.data.decode())

                    if channel.topic == "/events":
                        events.append({
                            'type': 'input_event',
                            'timestamp': data['timestamp'],
                            'device': data['device'],
                            'key': data['key'],
                            'action': data['action']
                        })
                    elif channel.topic == "/cursor_position":
                        events.append({
                            'type': 'cursor_position',
                            'timestamp': data['timestamp'],
                            'x': data['x'],
                            'y': data['y']
                        })

                except Exception as e:
                    print(f"Error parsing message: {e}")
                    continue

        # Sort events by timestamp
        self.events = sorted(events, key=lambda x: x['timestamp'])
        print(f"Loaded {len(self.events)} events")

        if not self.events:
            raise ValueError("No events found in MCAP file")

    def on_safety_key_press(self, key):
        """Safety key press handler - stops replay on any key press"""
        if self.replaying and not self.currently_replaying_keyboard:
            print(f"\nSafety stop triggered by key press: {key}")
            self.stop_requested = True
            return False  # Stop listener

    def start_safety_listener(self):
        """Start the safety key listener"""
        self.safety_listener = keyboard.Listener(on_press=self.on_safety_key_press)
        self.safety_listener.start()

    def stop_safety_listener(self):
        """Stop the safety key listener"""
        if self.safety_listener:
            self.safety_listener.stop()

    def replay_event(self, event):
        """Replay an input event using EventActor"""
        device = event['device']
        key = event['key']
        action = event['action']

        try:
            # Flag that we're replaying keyboard events to avoid false safety triggers
            if device == 'keyboard':
                self.currently_replaying_keyboard = True

            if action == 'press':
                self.event_actor.press(device, key)
                # Track both keyboard and mouse presses
                self.pressed_keys.add((device, key))
            elif action == 'release':
                self.event_actor.release(device, key)
                # Remove released keys/buttons from tracking
                self.pressed_keys.discard((device, key))
            elif action == 'scroll':
                self.event_actor.scroll(key)

            # Small delay for keyboard events and clear flag
            if device == 'keyboard':
                time.sleep(0.01)
                self.currently_replaying_keyboard = False

        except Exception as e:
            print(f"Error replaying {device} event: {e}")
            # Ensure we clean up the keyboard state even if there's an error
            if device == 'keyboard':
                self.currently_replaying_keyboard = False
            # If there was an error during press, remove from tracking
            if action == 'press' and (device, key) in self.pressed_keys:
                self.pressed_keys.discard((device, key))

    def start_replay(self):
        """Start replaying the episode"""
        print("Starting episode replay...")
        print("Press ANY key to stop replay immediately")
        print("Starting in 3 seconds...")

        # Give user time to prepare
        for i in range(3, 0, -1):
            print(f"{i}...")
            time.sleep(1)

        print("Replay started!")

        self.replaying = True
        self.stop_requested = False

        # Start safety listener
        self.start_safety_listener()

        try:
            # Get the first timestamp as reference
            if self.events:
                start_timestamp = self.events[0]['timestamp']
                replay_start_time = time.time()

                for event in self.events:
                    if self.stop_requested:
                        break

                    # Calculate when this event should occur
                    event_delay = event['timestamp'] - start_timestamp
                    target_time = replay_start_time + event_delay

                    # Wait until it's time for this event
                    current_time = time.time()
                    if target_time > current_time:
                        time.sleep(target_time - current_time)

                    # Check again if stop was requested during sleep
                    if self.stop_requested:
                        break

                    # Execute the event
                    if event['type'] == 'input_event':
                        self.replay_event(event)
                    elif event['type'] == 'cursor_position':
                        self.cursor_actor.set_cursor_position(event['x'], event['y'])

                if self.stop_requested:
                    print("Replay stopped by user")
                else:
                    print("Replay completed successfully")

        except Exception as e:
            print(f"Error during replay: {e}")
        finally:
            self.stop_replay()

    def release_all_pressed_keys(self):
        """Release all currently pressed keys and mouse buttons to prevent stuck inputs"""
        if self.pressed_keys:
            print(f"Releasing {len(self.pressed_keys)} pressed inputs...")
            # Create a copy to avoid modification during iteration
            for device, key in list(self.pressed_keys):
                try:
                    self.event_actor.release(device, key)
                    print(f"Released {device} {key}")
                except Exception as e:
                    print(f"Error releasing {device} {key}: {e}")
            self.pressed_keys.clear()

    def stop_replay(self):
        """Stop the replay session"""
        self.replaying = False
        self.stop_requested = True

        # Release all pressed keys first to prevent stuck keys
        self.release_all_pressed_keys()

        # Stop safety listener
        self.stop_safety_listener()

        # Cleanup mouse controller
        self.cursor_actor.cleanup()
        self.event_actor.cleanup()

        print("Replay session ended")


def main():
    parser = argparse.ArgumentParser(description="Replay episode data from MCAP file")
    parser.add_argument("mcap_file", type=str,
                       help="Path to the MCAP file to replay")

    args = parser.parse_args()

    replayer = None
    try:
        replayer = EpisodeReplayer(args.mcap_file)
        replayer.load_episode_data()
        replayer.start_replay()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        # Ensure cleanup happens on Ctrl+C
        if replayer and replayer.replaying:
            replayer.stop_replay()
        return 130  # Standard exit code for Ctrl+C
    except Exception as e:
        print(f"Error: {e}")
        # Ensure cleanup happens on any error
        if replayer and replayer.replaying:
            replayer.stop_replay()
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
