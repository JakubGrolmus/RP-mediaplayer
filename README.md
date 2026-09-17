# RPi media prehravac

Jednoducha aplikace pro Raspberry Pi 4 s Raspberry Pi OS Lite (bez desktopu),
ktera prehrava lokalni audio/video soubory (loop nebo playlist), umoznuje
vybrat video a audio vystup, a spousti se automaticky po kazdem bootu.
Prehravani bezi pres **mpv** primo pres DRM/KMS - X server ani desktop
prostredi neni potreba.

## Soubory

| Soubor              | Ucel                                                        |
|----------------------|--------------------------------------------------------------|
| `config.ini`          | Konfigurace - cesta k obsahu, loop/playlist, vystupy         |
| `mediaplayer.py`      | Hlavni skript - cte config, ridi mpv, hlida zmeny za behu    |
| `list-outputs.sh`     | Vypise dostupne HDMI a audio vystupy                          |
| `mediaplayer.service` | systemd jednotka pro autostart po bootu                       |
| `install.sh`          | Instalace vseho na Pi                                         |

## 1. Priprava Raspberry Pi OS Lite

Over v `/boot/firmware/config.txt` (na starsich verzich `/boot/config.txt`),
ze je zapnuty KMS video driver (na aktualnich obrazech je to vychozi):

```
dtoverlay=vc4-kms-v3d
```

Pokud tam neni, pridej radek a restartuj Pi.

## 2. Nahrani souboru na Pi

Zkopiruj cely tento adresar na Pi, napr. pres `scp`:

```bash
scp -r rpi-mediaplayer pi@<IP-adresa-Pi>:~/
```

## 3. Instalace

Na Pi:

```bash
cd ~/rpi-mediaplayer
chmod +x install.sh
./install.sh
```

Skript nainstaluje `mpv`, zkopiruje konfiguraci do `/etc/mediaplayer/config.ini`,
skripty do `/usr/local/bin/` a zaregistruje systemd sluzbu, ktera se
spousti automaticky po kazdem bootu.

## 4. Zjisteni dostupnych vystupu

```bash
list-outputs.sh
```

Ukaze, kolik HDMI konektoru Pi ma a jestli jsou pripojene, a jake
ALSA audio karty jsou v systemu (HDMI zvuk, 3.5mm jack, pripadne USB
zvukovka).

## 5. Uprava konfigurace

```bash
sudo nano /etc/mediaplayer/config.ini
```

Priklad:

```ini
[source]
path = /media/usb0/video.mp4
loop = true
shuffle = false

[video]
output = hdmi0

[audio]
output = jack
volume = 100
```

- `path` muze byt jeden soubor, nebo cela slozka (pak se prehraje
  playlist vsech podporovanych souboru serazenych podle nazvu).
- Zmena souboru se **projevi automaticky do ~3 vterin** - prehravani
  se restartuje s novymi parametry, neni potreba restartovat Pi ani
  sluzbu rucne.

## 6. Spusteni

```bash
sudo systemctl start mediaplayer.service
```

Od tehto chvile se sluzba bude spoustet automaticky pri kazdem bootu
a bezet s aktualni konfiguraci, dokud ji rucne nezmenis.

## Uzitecne prikazy

```bash
# stav sluzby
sudo systemctl status mediaplayer.service

# live log
journalctl -u mediaplayer.service -f

# rucni restart (napr. po zmene, ktera se z nejakeho duvodu neprojevila)
sudo systemctl restart mediaplayer.service

# zastaveni / vypnuti autostartu
sudo systemctl stop mediaplayer.service
sudo systemctl disable mediaplayer.service
```

## Pozn. k autu USB flash disku

Pokud obsah bydli na USB disku, over, ze se pripojuje automaticky
(napr. pres `/etc/fstab` s UUID a volbou `nofail`), aby byl dostupny
driv, nez se sluzba pokusi spustit prehravani po bootu.
