#!/bin/bash
# ============================================================
# Xteam - Wireless Attacks (Wifite2)
# ------------------------------------------------------------
# Launches the latest maintained Wifite2 (kimocoder/wifite2).
# Wifite2 is the actively maintained, Python 3 successor to the
# old Python 2 "wifite" that was previously bundled here.
#
# If `wifite` is not already installed, the latest version is
# cloned from https://github.com/kimocoder/wifite2 and its Python
# dependencies are installed before launch.
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WIFITE_DIR="$SCRIPT_DIR/wifite2"
WIFITE_GIT_URL="https://github.com/kimocoder/wifite2.git"

# Colors
Red="\033[1;31m"; Green="\033[1;32m"; Yellow="\033[1;33m"
Cyan="\033[1;36m"; White="\033[0m"

echo -e "${Cyan}╔══════════════════════════════════════════════════════════════╗${White}"
echo -e "${Cyan}║${White}              ${Yellow}Wifite2 - Wireless Attacks${Cyan}                    ║${White}"
echo -e "${Cyan}╚══════════════════════════════════════════════════════════════╝${White}"
echo ""

# Wifite must run as root
if [ "$(id -u)" -ne 0 ]; then
    echo -e "${Yellow}[*] Wifite requires root privileges. Re-launching with sudo...${White}"
    exec sudo bash "$0" "$@"
fi

# Locate an existing wifite binary
WIFITE_BIN="$(command -v wifite 2>/dev/null || true)"

# If not installed, fetch the latest maintained wifite2
if [ -z "$WIFITE_BIN" ]; then
    if [ ! -d "$WIFITE_DIR/.git" ]; then
        echo -e "${Yellow}[*] Wifite2 not found. Cloning the latest maintained version...${White}"
        git clone --depth 1 "$WIFITE_GIT_URL" "$WIFITE_DIR" || {
            echo -e "${Red}[!] Failed to clone Wifite2 from $WIFITE_GIT_URL${White}"
            exit 1
        }
    fi

    echo -e "${Yellow}[*] Installing Wifite2 Python dependencies...${White}"
    if [ -f "$WIFITE_DIR/requirements.txt" ]; then
        pip3 install --user --break-system-packages -r "$WIFITE_DIR/requirements.txt" \
            || pip3 install --user -r "$WIFITE_DIR/requirements.txt" \
            || echo -e "${Red}[!] Dependency install failed (continue anyway).${White}"
    fi

    cd "$WIFITE_DIR" || exit 1
    echo -e "${Green}[+] Starting Wifite2...${White}"
    echo ""
    exec python3 wifite.py "$@"
else
    echo -e "${Green}[+] Using system wifite: $WIFITE_BIN${White}"
    echo ""
    exec "$WIFITE_BIN" "$@"
fi
