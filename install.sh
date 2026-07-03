#!/bin/bash
# ShortLink Bypass — one-liner install
# Usage: curl -sL https://git.io/shortlink-bypass | bash

set -e

INSTALL_DIR="${1:-/usr/local/bin}"
SCRIPT_URL="https://raw.githubusercontent.com/KaramelliS/shortlink-bypass/master/shortlink_bypass/bypass.py"

echo "[*] Installing ShortLink Bypass to $INSTALL_DIR..."

if [ ! -d "$INSTALL_DIR" ]; then
    echo "[!] Directory $INSTALL_DIR does not exist, trying ~/.local/bin"
    INSTALL_DIR="$HOME/.local/bin"
    mkdir -p "$INSTALL_DIR"
fi

# Download the script
if command -v curl &> /dev/null; then
    curl -sL "$SCRIPT_URL" -o "$INSTALL_DIR/shortlink-bypass"
elif command -v wget &> /dev/null; then
    wget -q "$SCRIPT_URL" -O "$INSTALL_DIR/shortlink-bypass"
else
    echo "[-] Neither curl nor wget found. Install one first."
    exit 1
fi

chmod +x "$INSTALL_DIR/shortlink-bypass"

# Also download the shortener list
LIST_URL="https://raw.githubusercontent.com/KaramelliS/shortlink-bypass/master/shorteners.txt"
if command -v curl &> /dev/null; then
    curl -sL "$LIST_URL" -o "$INSTALL_DIR/../shorteners.txt" 2>/dev/null || true
else
    wget -q "$LIST_URL" -O "$INSTALL_DIR/../shorteners.txt" 2>/dev/null || true
fi

echo "[+] Installed! Run: shortlink-bypass https://ay.live/EXAMPLE"
