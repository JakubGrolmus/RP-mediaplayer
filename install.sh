#!/bin/bash
set -e

echo "== Instalace zavislosti (mpv, alsa-utils) =="
sudo apt-get update
sudo apt-get install -y mpv alsa-utils

echo "== Vytvarim slozky =="
sudo mkdir -p /etc/mediaplayer

if [ ! -f /etc/mediaplayer/config.ini ]; then
    echo "== Kopiruji vychozi konfiguraci =="
    sudo cp config.ini /etc/mediaplayer/config.ini
else
    echo "== Konfigurace uz existuje, necham puvodni =="
fi

echo "== Instaluji skripty =="
sudo cp mediaplayer.py /usr/local/bin/mediaplayer.py
sudo chmod +x /usr/local/bin/mediaplayer.py
sudo cp list-outputs.sh /usr/local/bin/list-outputs.sh
sudo chmod +x /usr/local/bin/list-outputs.sh

echo "== Instaluji systemd sluzbu =="
sudo cp mediaplayer.service /etc/systemd/system/mediaplayer.service
sudo systemctl daemon-reload
sudo systemctl enable mediaplayer.service

echo
echo "Hotovo."
echo
echo "Pred prvnim spustenim:"
echo "  1) uprav /etc/mediaplayer/config.ini (cesta k souboru, vystupy...)"
echo "  2) over, ze je uzivatel 'pi' ve spravnych skupinach:"
echo "       groups pi"
echo "       sudo usermod -aG video,render,audio pi"
echo "  3) over dostupne vystupy prikazem:"
echo "       list-outputs.sh"
echo
echo "Sluzbu spustis:"
echo "  sudo systemctl start mediaplayer.service"
echo "Log sledujes:"
echo "  journalctl -u mediaplayer.service -f"
