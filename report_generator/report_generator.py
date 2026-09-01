#!/usr/bin/env python3
"""
Xteam Report Generator
Scans module report directories, merges data, and generates unified reports.
"""

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
except ImportError:
    print("[!] Jinja2 is not installed. Run: pip3 install jinja2")
    sys.exit(1)

try:
    import weasyprint
except ImportError:
    weasyprint = None

try:
    import markdown as md_lib
except ImportError:
    md_lib = None

try:
    from weasyprint import HTML
except ImportError:
    pass


XTEAM_ROOT = Path(__file__).resolve().parent.parent
REPORT_DIRS = [
    XTEAM_ROOT / "Email_harvester" / "reports",
    XTEAM_ROOT / "Web_Vulnerability_Scanner" / "vulnerability_reports",
    XTEAM_ROOT / "Phish_2FA" / "reports",
    XTEAM_ROOT / "reports",
]
MASTER_REPORT_PATH = XTEAM_ROOT / "reports" / "master_report.json"
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

SECTION_ORDER = ["OSINT", "Network Scan", "Vulnerabilities", "Phishing Campaign Results"]


def ensure_dirs():
    for d in REPORT_DIRS:
        d.mkdir(parents=True, exist_ok=True)
    (XTEAM_ROOT / "reports").mkdir(parents=True, exist_ok=True)


def scan_reports():
    files = []
    for report_dir in REPORT_DIRS:
        if not report_dir.exists():
            continue
        for ext in ("*.json", "*.csv", "*.txt"):
            files.extend(report_dir.rglob(ext))
    return sorted(set(files))


def categorize_file(path: Path):
    name = path.name.lower()
    parent = path.parent.name.lower()
    if "harvest" in name or "osint" in parent or "email" in parent:
        return "OSINT"
    if "nuclei" in name or "vulnerability" in parent or "vuln" in parent:
        return "Vulnerabilities"
    if "evilginx" in name or "phish" in parent:
        return "Phishing Campaign Results"
    if "post" in name or "exfil" in name:
        return "Post-Exploitation"
    if "scan" in name or "network" in parent:
        return "Network Scan"
    return "Uncategorized"


def parse_json_file(path: Path):
    records = []
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    # Only keep JSON objects (nuclei-style line-delimited reports)
                    if isinstance(obj, dict):
                        records.append(obj)
                except json.JSONDecodeError:
                    continue
    except Exception:
        pass
    return records


def parse_csv_file(path: Path):
    records = []
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(dict(row))
    except Exception:
        pass
    return records


def parse_txt_file(path: Path):
    text = ""
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            text = f.read()
    except Exception:
        pass
    return text


def extract_emails_from_text(text: str):
    return re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text)


def extract_ips_from_text(text: str):
    return re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", text)


def extract_urls_from_text(text: str):
    return re.findall(r"https?://[^\s,;\"]+", text)


def parse_file(path: Path):
    category = categorize_file(path)
    entry = {
        "file": str(path.relative_to(XTEAM_ROOT)),
        "category": category,
        "type": path.suffix.lower().lstrip("."),
        "modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
        "size": path.stat().st_size,
        "data": [],
        "summary": {},
    }

    if path.suffix.lower() == ".json":
        entry["data"] = parse_json_file(path)
        if entry["data"]:
            entry["summary"]["record_count"] = len(entry["data"])
            severities = []
            for record in entry["data"]:
                info = record.get("info", {}) if isinstance(record, dict) else {}
                sev = info.get("severity") if isinstance(info, dict) else None
                if sev:
                    severities.append(str(sev).lower())
            if severities:
                entry["summary"]["severity_counts"] = dict(Counter(severities))
    elif path.suffix.lower() == ".csv":
        entry["data"] = parse_csv_file(path)
        if entry["data"]:
            entry["summary"]["record_count"] = len(entry["data"])
            entry["summary"]["columns"] = list(entry["data"][0].keys()) if entry["data"] else []
    elif path.suffix.lower() == ".txt":
        text = parse_txt_file(path)
        entry["data"] = [text]
        entry["summary"]["char_count"] = len(text)
        entry["summary"]["line_count"] = text.count("\n")
        entry["summary"]["email_count"] = len(extract_emails_from_text(text))
        entry["summary"]["ip_count"] = len(extract_ips_from_text(text))
        entry["summary"]["url_count"] = len(extract_urls_from_text(text))
    return entry


def build_master_report():
    ensure_dirs()
    files = scan_reports()
    sections = defaultdict(list)
    total_files = 0
    total_records = 0
    total_emails = 0
    total_ips = 0
    total_urls = 0

    for path in files:
        entry = parse_file(path)
        sections[entry["category"]].append(entry)
        total_files += 1
        total_records += entry["summary"].get("record_count", 0)
        total_emails += entry["summary"].get("email_count", 0)
        total_ips += entry["summary"].get("ip_count", 0)
        total_urls += entry["summary"].get("url_count", 0)

    master = {
        "generated_at": datetime.now().isoformat(),
        "tool": "Xteam Report Generator",
        "summary": {
            "total_files": total_files,
            "total_records": total_records,
            "total_emails": total_emails,
            "total_ips": total_ips,
            "total_urls": total_urls,
            "sections": list(sections.keys()),
        },
        "sections": dict(sections),
    }

    with open(MASTER_REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(master, f, indent=2, default=str)

    return master


def build_charts_data(master):
    """Compute Chart.js datasets expected by the HTML template."""
    charts = {
        "severity_labels": [],
        "severity_values": [],
        "section_counts_labels": [],
        "section_counts_values": [],
        "email_counts_labels": [],
        "email_counts_values": [],
    }

    # Aggregate vulnerability severities across all entries
    sev_counter = Counter()
    for entries in master.get("sections", {}).values():
        for entry in entries:
            for sev, count in entry.get("summary", {}).get("severity_counts", {}).items():
                sev_counter[sev] += count
    if sev_counter:
        order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4, "unknown": 5}
        sorted_sevs = sorted(sev_counter.items(), key=lambda x: order.get(x[0], 99))
        charts["severity_labels"] = [name for name, _ in sorted_sevs]
        charts["severity_values"] = [count for _, count in sorted_sevs]

    # File counts per section
    for section in SECTION_ORDER:
        entries = master.get("sections", {}).get(section, [])
        if entries:
            charts["section_counts_labels"].append(section)
            charts["section_counts_values"].append(len(entries))

    # Emails per OSINT report file
    for entry in master.get("sections", {}).get("OSINT", []):
        charts["email_counts_labels"].append(entry.get("file", "unknown"))
        charts["email_counts_values"].append(entry.get("summary", {}).get("email_count", 0))

    return charts


def render_html(master, output_path):
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("report.html")
    charts_data = build_charts_data(master)
    html = template.render(report=master, charts_data=charts_data)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    return output_path


def render_pdf(master, output_path):
    if weasyprint is None:
        print("[!] weasyprint is not installed. Install it with: pip3 install weasyprint")
        print("[!] On Kali/Debian, you may also need: sudo apt install libpango-1.0-0 libharfbuzz0b libcairo2")
        return False
    html_path = output_path.with_suffix(".html")
    render_html(master, html_path)
    try:
        HTML(filename=str(html_path)).write_pdf(str(output_path))
        return True
    except Exception as e:
        print(f"[!] Failed to generate PDF: {e}")
        return False


def render_markdown(master, output_path):
    lines = []
    lines.append("# Xteam Master Report")
    lines.append(f"\n**Generated:** {master.get('generated_at', 'N/A')}")
    lines.append("\n## Summary\n")
    s = master.get("summary", {})
    lines.append(f"- Total Files: {s.get('total_files', 0)}")
    lines.append(f"- Total Records: {s.get('total_records', 0)}")
    lines.append(f"- Emails Found: {s.get('total_emails', 0)}")
    lines.append(f"- IPs Found: {s.get('total_ips', 0)}")
    lines.append(f"- URLs Found: {s.get('total_urls', 0)}")

    for section_name in SECTION_ORDER:
        entries = master.get("sections", {}).get(section_name, [])
        if not entries:
            continue
        lines.append(f"\n## {section_name}\n")
        for entry in entries:
            lines.append(f"### {entry.get('file', 'Unknown')}")
            lines.append(f"- **Type:** {entry.get('type', 'unknown')}")
            lines.append(f"- **Modified:** {entry.get('modified', 'N/A')}")
            summary = entry.get("summary", {})
            if summary:
                lines.append("- **Summary:**")
                for k, v in summary.items():
                    lines.append(f"  - {k}: {v}")
            lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return output_path


def interactive_menu(master):
    print("\n" + "=" * 60)
    print("Xteam Report Generator")
    print("=" * 60)
    print(f"Master report loaded: {MASTER_REPORT_PATH}")
    print(f"Total files scanned : {master.get('summary', {}).get('total_files', 0)}")
    print(f"Sections found      : {', '.join(master.get('summary', {}).get('sections', []))}")
    print("=" * 60)
    print("Select output format:")
    print("  [1] HTML (with Chart.js)")
    print("  [2] PDF")
    print("  [3] Markdown")
    print("  [4] All formats")
    print("  [5] Exit")
    print("=" * 60)

    choice = input("Enter choice [1-5]: ").strip()
    if choice not in ("1", "2", "3", "4"):
        print("[!] Exiting report generator.")
        return

    default_name = f"xteam_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    output_name = input(f"Enter output filename (without extension, default: {default_name}): ").strip()
    if not output_name:
        output_name = default_name

    output_base = XTEAM_ROOT / "reports" / output_name

    if choice in ("1", "4"):
        html_path = output_base.with_suffix(".html")
        render_html(master, html_path)
        print(f"[+] HTML report saved to: {html_path}")

    if choice in ("2", "4"):
        pdf_path = output_base.with_suffix(".pdf")
        success = render_pdf(master, pdf_path)
        if success:
            print(f"[+] PDF report saved to: {pdf_path}")
        else:
            print("[-] PDF generation failed or skipped.")

    if choice in ("3", "4"):
        md_path = output_base.with_suffix(".md")
        render_markdown(master, md_path)
        print(f"[+] Markdown report saved to: {md_path}")


def main():
    parser = argparse.ArgumentParser(description="Xteam Report Generator")
    parser.add_argument("--output", help="Output filename (without extension)", default=None)
    parser.add_argument("--format", choices=["html", "pdf", "markdown", "all"], default=None)
    args = parser.parse_args()

    print("[*] Scanning reports directories...")
    master = build_master_report()
    print(f"[+] Master report built. Total files: {master['summary']['total_files']}")

    if args.output and args.format:
        output_base = XTEAM_ROOT / "reports" / args.output
        fmt = args.format
        if fmt in ("html", "all"):
            render_html(master, output_base.with_suffix(".html"))
            print(f"[+] HTML report saved to: {output_base.with_suffix('.html')}")
        if fmt in ("pdf", "all"):
            success = render_pdf(master, output_base.with_suffix(".pdf"))
            if success:
                print(f"[+] PDF report saved to: {output_base.with_suffix('.pdf')}")
        if fmt in ("markdown", "all"):
            render_markdown(master, output_base.with_suffix(".md"))
            print(f"[+] Markdown report saved to: {output_base.with_suffix('.md')}")
    else:
        interactive_menu(master)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Interrupted.")
        sys.exit(0)
