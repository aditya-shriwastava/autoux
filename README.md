# AutoUX
> AI agent that sees your screen and acts with keyboard and mouse.

## Getting Started
1. **Clone the repository**
```bash
git clone https://github.com/aditya-shriwastava/autoux.git
cd autoux
```

2. **Create and activate a virtual environment**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. **Install dependencies**
```bash
pip install .
```
Or, for development (with extra tools):
```bash
pip install -e .[dev]
```

4. **Usage**
After installation, you can run AutoUX with:
```bash
autoux
```
This will start the agent.

## Episode Recording and Replay
AutoUX includes tools for recording and replaying user interactions:

### Recording Episodes
Record screen captures and input events to an MCAP file:
```bash
record-episode [options]
```

**Example:**
```bash
record-episode --context "web_browsing_demo" --hz 10.0
```

Press `Alt+X` to stop recording.

### Replaying Episodes
Replay recorded episodes:

```bash
replay-episode path/to/episode.mcap
```
This will replay the recorded mouse and keyboard events in real-time.

### Converting to Human-Readable Format
Convert recorded MCAP files to human-readable formats:

```bash
human-readable-dump path/to/episode.mcap
```
This generates:
- `screen_capture.mp4`: Video of the recorded session
- `cursor_position.csv`: Mouse position data
- `events.csv`: Keyboard and mouse events
- `context.txt`: Episode description

**Safety Features:**
- Press any key during replay to immediately stop
- Automatic safety listener prevents runaway replays

**Note on Scroll Behavior:**
replay-episode after record-episode will replay everything exactly if mouse is used for scroll, but when touchpad is used scroll might be off by a notch.

## Docker Setup
AutoUX includes a Docker setup with Ubuntu 24.04, VNC access, and a minimal XFCE desktop environment. This containerized environment is ideal for:
- **Data collection**: Record user interactions in a consistent, isolated environment
- **Experimentation**: Test AutoUX features without affecting your host system
- **Development**: Develop and debug in a reproducible environment

### Quick Start
1. **Start the container:**
```bash
docker-compose up -d
```

2. **Access the desktop:**
Open your web browser and navigate to:
```
http://localhost:6901/vnc.html
```
Click "Connect" - no password required!

3. **Stop the container:**
```bash
docker-compose down
```
