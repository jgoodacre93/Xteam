#!/usr/bin/env python3

import os
import sys
import subprocess
import re
import datetime
import shutil

BANNER = """
\033[1;36m╔══════════════════════════════════════════════════════════════╗
║         \033[1;37mOSINT Email Harvester - theHarvester Module\033[1;36m         ║
╚══════════════════════════════════════════════════════════════╝\033[0m
"""

def clear_screen():
    os.system("clear || cls")

def check_theharvester():
    if shutil.which("theHarvester") or shutil.which("theharvester"):
        return True
    return False

def prompt_install():
    print("\033[1;31m[!] theHarvester is not installed.\033[0m")
    while True:
        choice = input("\033[1;33m[?] Do you want to install it now? (y/n): \033[0m").strip().lower()
        if choice not in ("y", "yes"):
            print("\033[1;31m[!] Cannot proceed without theHarvester.\033[0m")
            return False

        print("\033[1;34m[*] Attempting installation...\033[0m")
        prefix = []
        try:
            if os.geteuid() != 0:
                if shutil.which("sudo"):
                    prefix = ["sudo"]
        except AttributeError:
            # Windows or environment without geteuid; do not use sudo
            prefix = []

        # Try apt-get if available
        if shutil.which("apt-get"):
            try:
                subprocess.run(prefix + ["apt-get", "update"], check=True)
                subprocess.run(prefix + ["apt-get", "install", "-y", "theharvester"], check=True)
            except subprocess.CalledProcessError as e:
                print(f"\033[1;31m[!] apt-get installation failed: {e}\033[0m")
            # re-check
            if check_theharvester():
                print("\033[1;32m[+] theHarvester installed successfully.\033[0m")
                return True

        # Prepare pip binary decision early
        pip_bin = shutil.which("pip3") or shutil.which("pip")
        # Fallback: try pip3/pip
        if pip_bin:
            try:
                print("\033[1;34m[*] Trying pip install theHarvester...\033[0m")
                subprocess.run([pip_bin, "install", "theHarvester"], check=True)
            except subprocess.CalledProcessError as e:
                print(f"\033[1;31m[!] pip installation failed: {e}\033[0m")
            if check_theharvester():
                print("\033[1;32m[+] theHarvester installed successfully via pip.\033[0m")
                return True

        # Last resort: try installing from git if git is present
        if shutil.which("git"):
            try:
                print("\033[1;34m[*] Trying git install from source...\033[0m")
                tmpdir = "/tmp/theharvester_install"
                if os.path.exists(tmpdir):
                    shutil.rmtree(tmpdir)
                subprocess.run(["git", "clone", "https://github.com/laramies/theHarvester.git", tmpdir], check=True)
                if os.path.exists(os.path.join(tmpdir, "setup.py")):
                    if pip_bin:
                        subprocess.run([pip_bin, "install", tmpdir], check=True)
                    else:
                        # fallback to python -m pip
                        subprocess.run([sys.executable, "-m", "pip", "install", tmpdir], check=True)
            except Exception as e:
                print(f"\033[1;31m[!] git install failed: {e}\033[0m")
            if check_theharvester():
                print("\033[1;32m[+] theHarvester installed successfully from source.\033[0m")
                return True

        # If we reach here, installation failed. Ask user whether to retry.
        retry = input("\033[1;33m[?] Installation failed. Retry? (y/n): \033[0m").strip().lower()
        if retry in ("y", "yes"):
            continue
        else:
            print("\033[1;31m[!] Installation aborted by user.\033[0m")
            return False

def get_domain():
    while True:
        domain = input("\033[1;37m[?] Enter target domain (e.g., example.com): \033[0m").strip()
        if re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*\.[a-zA-Z]{2,}$', domain):
            return domain
        print("\033[1;31m[!] Invalid domain format. Try again.\033[0m")

def run_harvester(domain):
    cmd = ["theHarvester", "-d", domain, "-b", "google,bing,linkedin", "-l", "100"]
    print(f"\033[1;34m[*] Running: {' '.join(cmd)}\033[0m\n")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        print("\033[1;31m[!] Command timed out after 300 seconds.\033[0m")
        return "", "timeout"
    except Exception as e:
        print(f"\033[1;31m[!] Error running theHarvester: {e}\033[0m")
        return "", str(e)

def extract_emails(output):
    emails = set()
    for line in output.splitlines():
        line = line.strip()
        if re.match(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$', line):
            emails.add(line.lower())
    return sorted(emails)

def print_table(emails):
    if not emails:
        print("\033[1;33m[!] No emails found.\033[0m")
        return

    width = 42
    print("\n")
    print(f"\033[1;32m╔{'═' * width}╗\033[0m")
    print(f"\033[1;32m║{'':<{width}}║\033[0m")
    print(f"\033[1;32m║{'  EMAIL ADDRESSES FOUND':<{width}}║\033[0m")
    print(f"\033[1;32m║{'':<{width}}║\033[0m")
    print(f"\033[1;32m╠{'═' * width}╣\033[0m")

    for i, email in enumerate(emails, 1):
        print(f"\033[1;32m║\033[0m  {i:>2}. {email:<{width - 5}} \033[1;32m║\033[0m")

    print(f"\033[1;32m║{'':<{width}}║\033[0m")
    print(f"\033[1;32m╚{'═' * width}╝\033[0m")
    print(f"\033[1;36m[*] Total emails found: {len(emails)}\033[0m\n")

def save_report(domain, emails):
    reports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
    os.makedirs(reports_dir, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"harvest_{domain.replace('.', '_')}_{timestamp}.txt"
    filepath = os.path.join(reports_dir, filename)

    with open(filepath, "w") as f:
        f.write("Xteam OSINT Email Harvester Report\n")
        f.write(f"{'='*50}\n")
        f.write(f"Target Domain : {domain}\n")
        f.write(f"Date          : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("Sources       : Google, Bing, LinkedIn\n")
        f.write(f"{'='*50}\n\n")
        if emails:
            for i, email in enumerate(emails, 1):
                f.write(f"{i}. {email}\n")
            f.write(f"\nTotal: {len(emails)} email(s)\n")
        else:
            f.write("No emails found.\n")

    print(f"\033[1;34m[*] Report saved to: {filepath}\033[0m")
    return filepath

def main():
    clear_screen()
    print(BANNER)

    if not check_theharvester():
        if not prompt_install():
            sys.exit(1)
        if not check_theharvester():
            print("\033[1;31m[!] theHarvester still not found after installation.\033[0m")
            sys.exit(1)

    domain = get_domain()
    print(f"\n\033[1;36m[*] Target domain set to: {domain}\033[0m\n")

    stdout, stderr = run_harvester(domain)

    if stderr and stderr != "timeout":
        print("\033[1;33m[!] Warnings/Errors from theHarvester:\033[0m")
        print(stderr[:500])

    print("\n\033[1;34m[*] Parsing results...\033[0m")
    emails = extract_emails(stdout)

    print_table(emails)
    save_report(domain, emails)

    input("\033[1;37m[?] Press Enter to return to menu...\033[0m")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n\033[1;31m[!] Interrupted by user.\033[0m")
        sys.exit(0)
