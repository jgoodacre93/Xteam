#!/usr/bin/env python3

import json
import os
import sys
import subprocess
import shutil
import datetime
import platform

DEPENDENCIES_FILE = "dependencies.json"
LOG_FILE = "setup_log.txt"
REQUIREMENTS_FILE = "requirements.txt"

# Global log file handle
log_handle = None

def log(message):
    global log_handle
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)
    if log_handle:
        log_handle.write(line + "\n")
        log_handle.flush()

def init_log():
    global log_handle
    log_handle = open(LOG_FILE, "a", encoding="utf-8")
    log("=" * 60)
    log("Xteam Auto-Setup Started")
    log(f"System: {platform.system()} {platform.release()}")
    log(f"Architecture: {platform.machine()}")
    log("=" * 60)

def detect_package_manager():
    if shutil.which("pkg"):
        return "pkg"
    return "apt"

def is_tool_installed(tool_name):
    return shutil.which(tool_name) is not None

def progress_bar(iteration, total, length=40):
    percent = (f"{100 * (iteration / float(total)):.1f}")
    filled = int(length * iteration // total)
    bar = "█" * filled + "-" * (length - filled)
    return f"|{bar}| {percent}%"

def run_command(cmd, shell=False, capture_output=True):
    try:
        result = subprocess.run(
            cmd,
            shell=shell,
            capture_output=capture_output,
            text=True,
            timeout=600
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def install_apt(package, progress_index, total_tools):
    if not package:
        return True, "No apt package specified"
    log(f"Installing {package} via apt...")
    success, stdout, stderr = run_command(["apt-get", "install", "-y", package])
    if success:
        log(f"[+] Successfully installed {package}")
    else:
        log(f"[-] Failed to install {package}: {stderr[:200]}")
    return success, stderr

def install_pkg(package, progress_index, total_tools):
    if not package:
        return True, "No pkg package specified"
    log(f"Installing {package} via pkg...")
    success, stdout, stderr = run_command(["pkg", "install", "-y", package])
    if success:
        log(f"[+] Successfully installed {package}")
    else:
        log(f"[-] Failed to install {package}: {stderr[:200]}")
    return success, stderr

def install_git_tool(name, url, progress_index, total_tools):
    log(f"Cloning {name} from {url}...")
    success, stdout, stderr = run_command(["git", "clone", url, name])
    if success:
        log(f"[+] Successfully cloned {name}")
    else:
        log(f"[-] Failed to clone {name}: {stderr[:200]}")
    return success, stderr

def install_evilginx2(progress_index, total_tools):
    log("Installing Evilginx2 from source...")
    install_dir = "evilginx2"
    if os.path.exists(install_dir):
        log(f"[!] Directory {install_dir} already exists, skipping clone")
        return True, "Already exists"
    
    success, stdout, stderr = run_command([
        "git", "clone", "https://github.com/kgretzky/evilginx2.git", install_dir
    ])
    if not success:
        log(f"[-] Failed to clone evilginx2: {stderr[:200]}")
        return False, stderr
    
    log("[+] Cloned evilginx2, building...")
    if not os.path.isdir(install_dir):
        return False, "Clone directory not found"
    
    old_cwd = os.getcwd()
    try:
        os.chdir(install_dir)
        success, stdout, stderr = run_command(["make", "-j4"])
        if success:
            log("[+] Evilginx2 built successfully")
            return True, "Built successfully"
        else:
            log(f"[-] Build failed: {stderr[:200]}")
            return False, stderr
    finally:
        os.chdir(old_cwd)

def install_nuclei(progress_index, total_tools):
    log("Installing Nuclei from Go...")
    if is_tool_installed("nuclei"):
        log("[=] Nuclei is already installed, skipping")
        return True, "Already installed"
    
    gopath = os.environ.get("GOPATH", os.path.expanduser("~/go"))
    go_bin = os.path.join(gopath, "bin")
    os.environ["PATH"] = os.environ.get("PATH", "") + os.pathsep + go_bin
    
    success, stdout, stderr = run_command(
        ["go", "install", "-v", "github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest"],
        shell=False
    )
    if success:
        log("[+] Nuclei installed successfully via go install")
        return True, "Installed successfully"
    else:
        log(f"[-] Failed to install Nuclei: {stderr[:200]}")
        return False, stderr

def install_pip_requirements():
    if not os.path.exists(REQUIREMENTS_FILE):
        log(f"[!] {REQUIREMENTS_FILE} not found, skipping pip install")
        return True, "File not found"
    
    log(f"Running pip3 install -r {REQUIREMENTS_FILE}...")
    success, stdout, stderr = run_command([sys.executable, "-m", "pip", "install", "-r", REQUIREMENTS_FILE])
    if success:
        log("[+] Python requirements installed successfully")
    else:
        log(f"[-] Failed to install Python requirements: {stderr[:200]}")
    return success, stderr

def main():
    global log_handle
    
    print("=" * 60)
    print("Xteam Auto-Setup Tool")
    print("=" * 60)
    print()
    
    init_log()
    
    if not os.path.exists(DEPENDENCIES_FILE):
        log(f"[!] {DEPENDENCIES_FILE} not found!")
        print(f"[!] {DEPENDENCIES_FILE} not found!")
        sys.exit(1)
    
    with open(DEPENDENCIES_FILE, encoding="utf-8") as f:
        deps = json.load(f)
    
    tools = deps.get("tools", [])
    pkg_manager = detect_package_manager()
    log(f"Detected package manager: {pkg_manager}")
    print(f"[*] Detected package manager: {pkg_manager}")
    print()
    
    installed = []
    failed = []
    skipped = []
    
    total = len(tools)
    
    for idx, tool in enumerate(tools):
        name = tool.get("name", "unknown")
        tool_type = tool.get("type", "binary")
        
        print(f"\n[{idx + 1}/{total}] Checking {name}...")
        log(f"Checking tool: {name} (type: {tool_type})")
        
        if is_tool_installed(name):
            log(f"[=] {name} is already installed, skipping")
            skipped.append(name)
            print(f"[=] {name} already installed")
            continue
        
        print(f"[!] {name} not found, installing...")
        
        success = False
        msg = ""
        
        if tool_type == "binary":
            if pkg_manager == "apt":
                success, msg = install_apt(tool.get("apt"), idx, total)
            else:
                success, msg = install_pkg(tool.get("pkg"), idx, total)
        elif tool_type == "git":
            success, msg = install_git_tool(name, tool.get("url"), idx, total)
        elif tool_type == "custom":
            handler = tool.get("handler")
            if handler == "install_evilginx2":
                success, msg = install_evilginx2(idx, total)
            elif handler == "install_nuclei":
                success, msg = install_nuclei(idx, total)
            else:
                log(f"[-] Unknown custom handler: {handler}")
                success = False
                msg = f"Unknown handler: {handler}"
        else:
            log(f"[-] Unknown tool type: {tool_type}")
            success = False
            msg = f"Unknown type: {tool_type}"
        
        if success:
            installed.append(name)
        else:
            failed.append({"name": name, "reason": msg[:200]})
    
    # Install pip requirements
    print("\n" + "=" * 60)
    print("[*] Installing Python requirements...")
    pip_success, pip_msg = install_pip_requirements()
    if pip_success:
        installed.append("pip-requirements")
    else:
        failed.append({"name": "pip-requirements", "reason": pip_msg[:200]})
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"[+] Successfully installed: {len(installed)}")
    for item in installed:
        print(f"    - {item}")
    print(f"\n[-] Failed: {len(failed)}")
    for item in failed:
        print(f"    - {item['name']}: {item['reason']}")
    print(f"\n[=] Skipped (already installed): {len(skipped)}")
    for item in skipped:
        print(f"    - {item}")
    print("=" * 60)
    
    log("=" * 60)
    log("SUMMARY")
    log(f"Installed: {len(installed)} - {', '.join(installed)}")
    log(f"Failed: {len(failed)}")
    for item in failed:
        log(f"  - {item['name']}: {item['reason']}")
    log(f"Skipped: {len(skipped)} - {', '.join(skipped)}")
    log("=" * 60)
    log("Xteam Auto-Setup Completed")
    log("=" * 60)
    
    if log_handle:
        log_handle.close()
    
    return 0 if not failed else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n[!] Setup interrupted by user")
        if log_handle:
            log_handle.close()
        sys.exit(1)
