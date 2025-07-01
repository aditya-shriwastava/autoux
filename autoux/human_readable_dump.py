#!/usr/bin/env python3

import argparse
import csv
import io
import json
from pathlib import Path

import cv2
import numpy as np
from mcap.reader import make_reader
from PIL import Image

from .actors import CursorActor, EventActor


class HumanReadableDumper:
    def __init__(self, mcap_file: str):
        self.mcap_file = Path(mcap_file)

        # Initialize actors for cleanup
        self.cursor_actor = CursorActor(mode_of_control="position")
        self.event_actor = EventActor(immediate=True)

    def dump_human_readable(self):
        """Dump episode data in human-readable format"""
        print(f"Dumping human-readable data from: {self.mcap_file}")

        if not self.mcap_file.exists():
            raise FileNotFoundError(f"MCAP file not found: {self.mcap_file}")

        # Create output directory in data directory based on mcap filename
        data_dir = Path("data")
        output_dir = data_dir / self.mcap_file.stem
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"Creating output directory: {output_dir}")

        frames = []
        cursor_data = []
        events_data = []
        context = "screen_capture"

        print("Processing MCAP file...")

        with open(self.mcap_file, "rb") as f:
            reader = make_reader(f)

            # Extract metadata (context)
            for metadata in reader.iter_metadata():
                if metadata.name == "context" and "context" in metadata.metadata:
                    context = metadata.metadata["context"]
                    print(f"Episode context: {context}")

            for _schema, channel, message in reader.iter_messages():
                try:
                    timestamp_s = message.log_time / 1e9

                    if channel.topic == "/screen_capture":
                        # Extract raw JPEG bytes
                        jpeg_bytes = message.data
                        img = Image.open(io.BytesIO(jpeg_bytes))

                        frames.append({
                            'timestamp': timestamp_s,
                            'image': img,
                            'size': img.size
                        })
                    elif channel.topic == "/cursor_position":
                        data = json.loads(message.data.decode())
                        cursor_data.append({
                            'timestamp': timestamp_s,
                            'x': data.get('x', 0),
                            'y': data.get('y', 0)
                        })
                    elif channel.topic == "/events":
                        data = json.loads(message.data.decode())
                        events_data.append({
                            'timestamp': timestamp_s,
                            'action': data.get('action', ''),
                            'key': data.get('key', ''),
                            'device': data.get('device', '')
                        })

                except Exception as e:
                    print(f"Error processing message: {e}")
                    continue

        # Generate all output files
        self._generate_output_files(output_dir, frames, cursor_data, events_data, context)

        # Cleanup mouse controller threads
        self.cursor_actor.cleanup()
        self.event_actor.cleanup()

    def _generate_output_files(self, output_dir, frames, cursor_data, events_data, context):
        """Generate all output files in the specified directory"""
        print("Generating output files...")

        # 1. Generate screen_capture.mp4
        if frames:
            print(f"Creating video from {len(frames)} frames...")
            video_path = output_dir / "screen_capture.mp4"
            self._create_video_from_frames(frames, video_path)
        else:
            print("No screen capture frames found - skipping video creation")

        # 2. Generate cursor_position.csv (mouse positions)
        print(f"Writing cursor positions ({len(cursor_data)} entries)...")
        cursor_csv_path = output_dir / "cursor_position.csv"
        with open(cursor_csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'x', 'y'])
            for entry in cursor_data:
                writer.writerow([entry['timestamp'], entry['x'], entry['y']])
        print(f"✓ Generated cursor position CSV: {cursor_csv_path}")

        # 3. Generate events.csv
        print(f"Writing events ({len(events_data)} entries)...")
        events_csv_path = output_dir / "events.csv"
        with open(events_csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'device', 'action', 'key'])
            for event in events_data:
                writer.writerow([
                    event['timestamp'], event['device'], event['action'], event['key']
                ])
        print(f"✓ Generated events CSV: {events_csv_path}")

        # 4. Generate context.txt
        print("Writing context file...")
        context_path = output_dir / "context.txt"
        with open(context_path, 'w') as f:
            f.write(context)
        print(f"✓ Generated context file: {context_path}")

        print(f"\n✓ All files generated successfully in: {output_dir}")

    def _create_video_from_frames(self, frames, video_path):
        """Create video file from extracted frames"""
        # Sort frames by timestamp
        frames.sort(key=lambda x: x['timestamp'])

        # Calculate frame rate from timestamps
        if len(frames) > 1:
            duration = frames[-1]['timestamp'] - frames[0]['timestamp']
            fps = len(frames) / duration
            fps = max(1.0, min(fps, 60.0))  # Clamp between 1-60 fps
        else:
            fps = 10.0

        print(f"Creating video with {fps:.1f} fps")

        # Get frame dimensions from first frame
        first_frame = frames[0]['image']
        width, height = first_frame.size

        # Initialize video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(video_path), fourcc, fps, (width, height))

        try:
            total_frames = len(frames)
            for i, frame_data in enumerate(frames):
                # Show progress every 10% or every 100 frames
                if i % max(1, total_frames // 10) == 0 or i % 100 == 0:
                    progress = (i / total_frames) * 100
                    print(f"  Processing frame {i+1}/{total_frames} ({progress:.1f}%)")

                # Convert PIL Image to OpenCV format (BGR)
                pil_img = frame_data['image']
                opencv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

                # Resize if needed (ensure consistent dimensions)
                if opencv_img.shape[:2] != (height, width):
                    opencv_img = cv2.resize(opencv_img, (width, height))

                out.write(opencv_img)

            print(f"✓ Video saved to: {video_path}")

        finally:
            out.release()
            cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(
        description="Convert recorded MCAP file to human-readable format"
    )
    parser.add_argument("mcap_file", type=str,
                       help="Path to the MCAP file to convert")

    args = parser.parse_args()

    try:
        dumper = HumanReadableDumper(args.mcap_file)
        dumper.dump_human_readable()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 130  # Standard exit code for Ctrl+C
    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
