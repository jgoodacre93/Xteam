#!/bin/bash
clear
echo -e "$Yellow                            processing please wait..>"
sleep 2.0
clear
echo -e "$Yellow                            processing please wait...>"
sleep 2.0
clear
echo -e "$Yellow                            processing please wait....>"
sleep 2.0
clear
echo -e "$Yellow                            processing please wait.....>"
sleep 2.0
clear
echo -e "$Yellow                            processing please wait......>"
sleep 2.0
clear

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
python3 ai_assistant.py
