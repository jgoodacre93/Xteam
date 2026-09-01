# Xteam - Advanced Phishing Module (Gophish)

> **FOR AUTHORIZED SECURITY TESTING AND SECURITY AWARENESS TRAINING ONLY.**
> Only use against targets you own or have explicit written permission to test.
> Unauthorized phishing is illegal in most jurisdictions.

This module wraps the open-source [Gophish](https://github.com/gophish/gophish)
phishing-simulation framework so you can run a simulated campaign directly from
Xteam without touching the Gophish web UI.

## What it does

1. **Installs Gophish** if it is not present (official GitHub release, auto-detected arch).
2. **Starts the Gophish server** and prints the admin URL (`https://localhost:3333`)
   and the **auto-generated admin password** (read from `config.json`).
3. **Asks for your inputs**:
   - target email list (CSV: `firstname,lastname,email`)
   - landing page template from `phishing_templates/`
   - SMTP sending details, campaign name, subject, public phishing URL
4. **Generates `gophish_api.py`** – a small Python helper that drives the
   Gophish REST API to build the group, landing page, email template, SMTP
   profile, and to launch the campaign.
5. **Shows a live view**: tails `gophish.log` for campaign events and polls the
   API every 15 s for **open/click rates**.

Everything is non-interactive under the hood (`pkg install -y` / `apt-get install -y`,
`nohup` server start). Works on **Termux** and **Kali Linux**; the phishing server
is moved to port **8080** automatically when running as a non-root user.

## Usage

```bash
cd phishing
chmod +x phishing.sh
bash phishing.sh
```

### CSV format

```
firstname,lastname,email
Jane,Doe,jane@example.com
John,Smith,john@example.com
```

A 2-column `name,email` format is also accepted.

### Landing page templates

Drop `.html` files into `phishing_templates/`. Templates support the Gophish
variables `{{.URL}}` (tracked per-recipient link) and `{{.Tracker}}` (tracking
pixel). See `generic_login.html` / `generic_download.html` for examples.

### SMTP

You need a real SMTP relay to send email (e.g. an SMTP server you control).
The SMTP profile is created through the API with `ignore_cert_errors` enabled.

### Live rates

After launch, the script tails the Gophish log and periodically prints:

```
[rates] 14:03:22 | In Progress  | sent=5   opened=2 ( 40%) clicked=1 ( 20%) submitted=0
```

## Files

```
phishing/
├── phishing.sh               # main module
├── gophish_api.py            # generated Python API helper
├── phishing_templates/       # landing page templates
│   ├── generic_login.html
│   └── generic_download.html
├── gophish/                  # downloaded Gophish binary
├── config.json               # Gophish runtime config (auto-generated)
├── gophish.log               # Gophish log (tailed for live rates)
└── gophish.db                # SQLite DB (campaigns/results)
```

## Wiring into Xteam.sh

To make the main Xteam menu launch this module, point option **3 (Phishing
hacks)** at it, e.g.:

```bash
elif [ $ch -eq 3 ]; then
    cd "$HOME/Xteam/phishing"
    bash phishing.sh
    exit
fi
```

## Disclaimer

This module is provided for educational purposes and authorized security
awareness programs. The operators of Xteam are not responsible for misuse.
