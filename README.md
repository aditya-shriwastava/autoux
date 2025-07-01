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

Press `Ctrl+C` to stop recording.

### Replaying Episodes
Replay recorded episodes or convert them to human-readable formats:

#### Replay an Episode
```bash
replay-episode path/to/episode.mcap
```
This will replay the recorded mouse and keyboard events in real-time.

#### Convert to Human-Readable Format
```bash
replay-episode path/to/episode.mcap --dump-human-readable
```
This generates:
- `screen_capture.mp4`: Video of the recorded session
- `cursor_position.csv`: Mouse position data
- `events.csv`: Keyboard and mouse events
- `context.txt`: Episode description

**Safety Features:**
- Press any key during replay to immediately stop
- Automatic safety listener prevents runaway replays

## Development

### Running Tests
To run the full test suite:
```bash
pytest
```

To run tests with verbose output:
```bash
pytest -v
```

### Code Quality

#### Checking for linting issues:
```bash
ruff check
```

#### Auto-fixing linting issues:
```bash
ruff check --fix
```

#### Code formatting:
```bash
ruff format
```

#### Running all quality checks:
```bash
ruff check && ruff format --check
```
