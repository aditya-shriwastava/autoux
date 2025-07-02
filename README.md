# AutoUX 🤖

> AI agent that sees your screen and acts with keyboard and mouse.

---

## 🚀 Quick Start with Docker

### Prerequisites

- **Docker** and **Docker Compose** must be installed on your system

### Installation Steps

#### 1. Clone the Repository
```bash
cd ~
git clone https://github.com/aditya-shriwastava/autoux.git
cd autoux
```

#### 2. Start the Docker Environment
```bash
docker-compose up -d
```

This will:
- Build the AutoUX Docker image with Ubuntu 24.04
- Install all dependencies and AutoUX tools
- Start a VNC server with XFCE desktop
- Expose web-based VNC access on port 6901

#### 3. Access the Desktop Environment
Open your web browser and navigate to:
```
http://localhost:6901/vnc.html
```
- Click **"Connect"** (no password required)
- You'll see a full Ubuntu desktop in your browser

#### 4. Install AutoUX
Open a terminal in the VNC desktop and run:
```bash
# Go to autoux project directory
cd /home/autoux/autoux
```
```bash
# Create venv
python3 -m venv .venv
```
```bash
# Source venv
source .venv/bin/activate
```
```bash
# Install autoux
pip install -e .[dev]
```

---

## 📹 Usage

### Record a Session
```bash
record-episode --context "my_first_recording"
```
- Perform your desktop tasks
- Press **`Alt+X`** to stop recording
- Recording saved to data directory

### Replay a Session
```bash
replay-episode data/latest.mcap
```

> **⚠️ Safety**: Press any key during replay to stop immediately.

> **📝 Note on Scroll Behavior**: `replay-episode` after `record-episode` will replay everything exactly if mouse is used for scroll, but when touchpad is used scroll might be off by a notch.

### Convert to Human Readable Format
```bash
human-readable-dump data/latest.mcap
```

---

## 📁 File Access

### Access Files from Host
- The `data/` directory is mounted between host and container
- All recordings are automatically available on your host system

---

## 🛑 Stop the Environment
```bash
docker-compose down
```
