FROM ubuntu:24.04

SHELL ["/bin/bash", "-c"]

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
    # Additional libraries for Firefox
    libdbus-glib-1-2 \
    libgtk-3-0 \
    libx11-xcb1 \
    libxt6 \
    # Additional developer tools
    vim \
    nano \
    htop \
    tree \
    jq \
    net-tools \
    iputils-ping \
    # Media and productivity apps
    vlc \
    gedit \
    # Screenshot and recording tools
    flameshot \
    kazam \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Firefox from Mozilla binary (Ubuntu 24.04 uses snap by default which doesn't work in containers)
RUN cd /tmp && \
    wget -O firefox.tar.xz "https://download.mozilla.org/?product=firefox-latest&os=linux64&lang=en-US" && \
    tar -xf firefox.tar.xz -C /opt/ && \
    ln -sf /opt/firefox/firefox /usr/bin/firefox && \
    rm firefox.tar.xz

# Create Firefox desktop file and set as default browser
RUN cat > /usr/share/applications/firefox.desktop << 'EOF'
[Desktop Entry]
Version=1.0
Name=Firefox
Comment=Web Browser
Keywords=Internet;WWW;Browser;Web;Explorer
Exec=/usr/bin/firefox %u
Terminal=false
X-MultipleArgs=false
Type=Application
Icon=firefox
Categories=GNOME;GTK;Network;WebBrowser;
MimeType=text/html;text/xml;application/xhtml+xml;application/xml;application/rss+xml;application/rdf+xml;image/gif;image/jpeg;image/png;x-scheme-handler/http;x-scheme-handler/https;x-scheme-handler/ftp;x-scheme-handler/chrome;video/webm;application/x-xpinstall;
StartupNotify=true
EOF

# Update XFCE web browser to use Firefox
RUN cat > /usr/share/applications/xfce4-web-browser.desktop << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Exec=/usr/bin/firefox %u
Icon=firefox
StartupNotify=true
Terminal=false
Categories=Network;X-XFCE;X-Xfce-Toplevel;
OnlyShowIn=XFCE;
X-XFCE-MimeType=x-scheme-handler/http;x-scheme-handler/https;
X-AppStream-Ignore=True
Name=Web Browser
Comment=Browse the web
EOF

# Update desktop database
RUN update-desktop-database

# Set locale
RUN locale-gen en_US.UTF-8
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8

# Create user with sudo privileges - use host user ID to avoid permission issues
ARG USER_ID=1000
ARG GROUP_ID=1000
RUN getent group ${GROUP_ID} || groupadd -g ${GROUP_ID} autoux; \
    if id -u ${USER_ID} >/dev/null 2>&1; then \
        usermod -l autoux -d /home/autoux -m $(getent passwd ${USER_ID} | cut -d: -f1) && \
        groupmod -n autoux $(getent group ${GROUP_ID} | cut -d: -f1); \
    else \
        useradd -m -u ${USER_ID} -g ${GROUP_ID} -s /bin/bash autoux; \
    fi && \
    usermod -aG sudo autoux && \
    echo 'autoux:autoux' | chpasswd && \
    echo 'autoux ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

# Create necessary directories
RUN mkdir -p /home/autoux/.config/xfce4 /home/autoux/autoux && \
    chown -R autoux:autoux /home/autoux

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
