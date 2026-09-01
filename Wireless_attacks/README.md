# Wireless Attacks — Wifite2

This module runs **[Wifite2](https://github.com/kimocoder/wifite2)**, the actively
maintained, **Python 3** successor to the old Python 2 `wifite` that used to be
bundled here (that version no longer runs on modern Python and was removed).

## Usage

```bash
bash start.sh
```

On first run the script will:

1. Clone the latest `kimocoder/wifite2` into `./wifite2`.
2. Install its Python dependencies (`rich`, `scapy`, `requests`, `chardet`, ...).
3. Launch wifite2.

If you already have `wifite` installed (e.g. from Kali's package manager), the
script uses that instead.

## Requirements

- **Root privileges** (the launcher re-runs itself with `sudo` if needed).
- A wireless adapter that supports **monitor mode** and **packet injection**.
- The aircrack-ng suite (`aircrack-ng`, `airodump-ng`, `aireplay-ng`, `airmon-ng`),
  and optionally `reaver`/`bully` (WPS), `hashcat`/`john`/`tshark` (WPA cracking).

Install the system tools on Kali:

```bash
sudo apt update
sudo apt install -y aircrack-ng reaver bully hashcat john tshark
```

## Notes

- Wifite2 is for **authorized** testing only. Only attack networks you own or have
  explicit permission to test.
- To update the bundled clone: `cd wifite2 && git pull`
