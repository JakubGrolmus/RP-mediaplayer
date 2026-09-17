#!/bin/bash
# Vypise dostupne video (HDMI) a audio vystupy na tomto Raspberry Pi.
# Pouziti: ./list-outputs.sh

echo "=== Video vystupy (DRM konektory) ==="
found=0
for f in /sys/class/drm/card*-HDMI-A-*/status; do
    [ -e "$f" ] || continue
    found=1
    conn=$(basename "$(dirname "$f")" | sed -E 's/^card[0-9]+-//')
    status=$(cat "$f")
    echo "  $conn  ->  $status"
done
if [ "$found" -eq 0 ]; then
    echo "  Zadne HDMI konektory nenalezeny (zkontroluj, ze je zapnuty KMS driver)."
fi

echo
echo "Poznamka: hdmi0 v config.ini = prvni konektor ve vypisu vyse,"
echo "          hdmi1 = druhy konektor. 'connected' = ma pripojeny kabel."

echo
echo "=== Audio vystupy (ALSA karty) ==="
if [ -f /proc/asound/cards ]; then
    cat /proc/asound/cards
else
    echo "  ALSA neni dostupna."
fi
