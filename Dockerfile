FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:1
ENV VNC_PORT=5901
ENV NO_VNC_PORT=6901
ENV VNC_COL_DEPTH=24
ENV VNC_RESOLUTION=1920x1080

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # X11 and VNC
    xvfb \
    x11vnc \
    novnc \
    websockify \
    # Desktop environment (minimal XFCE4)
    xfce4 \
    xfce4-terminal \
    xfwm4 \
    xfdesktop4 \
    # System utilities
    dbus-x11 \
    sudo \
    wget \
    curl \
    locales \
    # Python and build tools
    python3.12 \
    python3.12-dev \
    python3.12-venv \
    build-essential \
    # Libraries for autoux dependencies
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxinerama1 \
    libxi6 \
    libxrandr2 \
    libxcursor1 \
    libxtst6 \
    libgl1 \
    libglx-mesa0 \
    libglib2.0-0 \
    libsm6 \
    libxkbcommon-x11-0 \
    libgbm1 \
    # Additional tools
    firefox \
    vim \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set locale
RUN locale-gen en_US.UTF-8
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8

# Create user with sudo privileges
RUN useradd -m -s /bin/bash -G sudo autoux && \
    echo 'autoux:autoux' | chpasswd && \
    echo 'autoux ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

# Create necessary directories
RUN mkdir -p /home/autoux/.config/xfce4 /home/autoux/autoux

# Create startup script
RUN cat > /home/autoux/startup.sh << 'EOF'
#!/bin/bash
# Setup environment
export USER=autoux
export HOME=/home/autoux
export XDG_RUNTIME_DIR=/tmp/runtime-autoux
mkdir -p ${XDG_RUNTIME_DIR}
chmod 700 ${XDG_RUNTIME_DIR}

# Start DBus
sudo service dbus start

# Clean up old locks
sudo rm -rf /tmp/.X* /tmp/.x*

# Start Xvfb
Xvfb :1 -screen 0 ${VNC_RESOLUTION}x${VNC_COL_DEPTH} &
sleep 3

# Start window manager and desktop
DISPLAY=:1 dbus-launch xfwm4 --replace &
sleep 1
DISPLAY=:1 xfdesktop &
sleep 2

# Start VNC server without password
x11vnc -display :1 -nopw -rfbport 5901 -shared -forever -repeat -xkb -noxdamage &
sleep 2

# Start noVNC
websockify --web=/usr/share/novnc/ ${NO_VNC_PORT} localhost:${VNC_PORT} &

echo "VNC Server started on port ${VNC_PORT}"
echo "noVNC Web UI available at http://localhost:${NO_VNC_PORT}/vnc.html"
echo ""
echo "=========================================="
echo "✓ AutoUX container is ready!"
echo "✓ Access the desktop at: http://localhost:6901/vnc.html"
echo "✓ No password required - just click 'Connect'"
echo "✓ AutoUX code mounted at /home/autoux/autoux"
echo "=========================================="

# Keep container running
tail -f /dev/null
EOF

RUN chmod +x /home/autoux/startup.sh

# Add venv to PATH (will be created at runtime)
ENV PATH="/home/autoux/autoux/.venv/bin:$PATH"

# Switch to non-root user
USER autoux
WORKDIR /home/autoux

# Expose ports
EXPOSE ${VNC_PORT}
EXPOSE ${NO_VNC_PORT}

# Set entry point
CMD ["/home/autoux/startup.sh"]