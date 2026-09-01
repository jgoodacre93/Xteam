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
echo -e "$Green Created By \e[1;34m"
figlet X TEAM | lolcat
sleep 1.0
echo ""
echo -e " $Cyan       ||----------------------------$Red [Phishing Toolkit] $Blue ---------------------------||"
echo ""
echo -e " $Purple%=>$Yellow[1] zphisher - Traditional Phishing$White"
echo -e " $Purple%=>$Yellow[2] Evilginx2 - 2FA Bypass$White"
echo -e " $Purple%=>$Yellow[3] Cleanup Evilginx2 (kill session)$White"
echo -e " $Purple%=>$Yellow[4] Back to Main Menu$White"
echo ""
echo -ne "$Red[?] Select option [1-4]: $White"
read -r phish_choice

case "$phish_choice" in
    1)
        cd $HOME
        git clone https://github.com/htr-tech/zphisher.git
        cd zphisher
        bash zphisher.sh
        ;;
    2)
        cd "$HOME/Xteam/Phish_2FA"
        source evilginx_setup.sh
        setup_evilginx_phish
        ;;
    3)
        cd "$HOME/Xteam/Phish_2FA"
        source evilginx_setup.sh
        cleanup_evilginx
        ;;
    4)
        cd $HOME/Xteam
        bash Xteam.sh
        ;;
    *)
        echo -e "$Red[!] Invalid Input !!!$White"
        sleep 2
        bash start.sh
        ;;
esac
