#!/usr/bin/env python3
"""
Jednoduchy media prehravac pro Raspberry Pi 4 (Raspberry Pi OS Lite, bez
desktopu). Cte konfiguraci z /etc/mediaplayer/config.ini, spousti mpv
pres DRM/KMS (bez X serveru) a za behu hlida zmeny konfiguracniho
souboru - kdyz se soubor zmeni, prehravani se automaticky restartuje
s novymi parametry.
"""

import configparser
import glob
import os
import re
import signal
import subprocess
import time

CONFIG_PATH = "/etc/mediaplayer/config.ini"

MEDIA_EXTENSIONS = {
    ".mp4", ".mkv", ".avi", ".mov", ".m4v", ".webm",
    ".mp3", ".flac", ".wav", ".ogg", ".m4a",
}


def load_config(path=CONFIG_PATH):
    cfg = configparser.ConfigParser()
    if not cfg.read(path):
        raise FileNotFoundError(f"Konfiguracni soubor {path} nenalezen.")
    return cfg


def build_playlist(path):
    if os.path.isdir(path):
        files = [
            f for f in sorted(glob.glob(os.path.join(path, "*")))
            if os.path.splitext(f)[1].lower() in MEDIA_EXTENSIONS
        ]
        if not files:
            raise FileNotFoundError(f"Ve slozce {path} nejsou zadne podporovane soubory.")
        return files
    if os.path.isfile(path):
        return [path]
    raise FileNotFoundError(f"Zdroj {path} neexistuje.")


def find_drm_connector(preference):
    """
    preference: 'hdmi0' | 'hdmi1' | 'auto'
    Vraci nazev DRM konektoru (napr. 'HDMI-A-1') pro parametr mpv --drm-connector,
    nebo None pokud ma mpv vybrat vystup sam.
    """
    if preference == "auto":
        return None

    wanted_index = {"hdmi0": 0, "hdmi1": 1}.get(preference)
    if wanted_index is None:
        raise ValueError(f"Neznamy video vystup '{preference}' (pouzij hdmi0/hdmi1/auto).")

    connectors = sorted(
        c for c in glob.glob("/sys/class/drm/card*-HDMI-A-*")
        if re.search(r"HDMI-A-\d+$", c)
    )

    if wanted_index >= len(connectors):
        raise RuntimeError(
            f"Video vystup '{preference}' nebyl na tomto Pi nalezen "
            f"(nalezeno {len(connectors)} HDMI konektoru)."
        )

    return re.search(r"HDMI-A-\d+$", connectors[wanted_index]).group(0)


def find_alsa_device(preference):
    """
    preference: 'hdmi0' | 'hdmi1' | 'jack' | 'usb' | 'none'
    Vraci retezec pro mpv --audio-device.
    """
    if preference == "none":
        return "null"

    if not os.path.exists("/proc/asound/cards"):
        raise RuntimeError("ALSA neni dostupna (/proc/asound/cards chybi).")

    with open("/proc/asound/cards") as f:
        cards_raw = f.read()

    # format radku: " 0 [vc4hdmi0       ]: vc4-hdmi - vc4-hdmi-0"
    cards = re.findall(r"^\s*\d+\s+\[(\S+)\s*\]:\s*(.+)$", cards_raw, re.MULTILINE)

    keyword_map = {
        "hdmi0": ["hdmi0", "hdmi-0"],
        "hdmi1": ["hdmi1", "hdmi-1"],
        "jack": ["headphones", "headphone", "analog"],
        "usb": ["usb"],
    }
    keywords = keyword_map.get(preference)
    if keywords is None:
        raise ValueError(f"Neznamy audio vystup '{preference}'.")

    for short_name, long_name in cards:
        haystack = f"{short_name} {long_name}".lower()
        if any(k in haystack for k in keywords):
            return f"alsa/plughw:CARD={short_name},DEV=0"

    raise RuntimeError(
        f"Audio vystup '{preference}' nebyl nalezen. "
        f"Dostupne karty: {[c[0] for c in cards]}. "
        f"Spust 'list-outputs.sh' pro presny vypis."
    )


def build_mpv_command(cfg):
    source = cfg.get("source", "path")
    loop = cfg.getboolean("source", "loop", fallback=True)
    shuffle = cfg.getboolean("source", "shuffle", fallback=False)

    video_output = cfg.get("video", "output", fallback="auto")
    audio_output = cfg.get("audio", "output", fallback="hdmi0")
    volume = cfg.getint("audio", "volume", fallback=100)

    playlist = build_playlist(source)

    cmd = [
        "mpv",
        "--fullscreen",
        "--vo=gpu",
        "--gpu-context=drm",
        "--no-terminal",
        "--idle=no",
        "--really-quiet",
        f"--volume={volume}",
    ]

    connector = find_drm_connector(video_output)
    if connector:
        cmd.append(f"--drm-connector={connector}")

    cmd.append(f"--audio-device={find_alsa_device(audio_output)}")

    if loop:
        cmd.append("--loop-playlist=inf" if len(playlist) > 1 else "--loop-file=inf")

    if shuffle and len(playlist) > 1:
        cmd.append("--shuffle")

    cmd.extend(playlist)
    return cmd


def stop_process(proc):
    if proc is None:
        return
    proc.send_signal(signal.SIGTERM)
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


def main():
    mpv_process = None
    last_mtime = None

    while True:
        try:
            mtime = os.path.getmtime(CONFIG_PATH)
        except OSError:
            time.sleep(5)
            continue

        config_changed = mtime != last_mtime
        mpv_died = mpv_process is not None and mpv_process.poll() is not None

        if config_changed or mpv_died:
            if config_changed and mpv_process is not None:
                print("Konfigurace se zmenila, restartuji prehravani...", flush=True)
                stop_process(mpv_process)
            elif mpv_died:
                print("mpv skoncil, spoustim znovu...", flush=True)

            try:
                cfg = load_config()
                cmd = build_mpv_command(cfg)
                print("Spoustim:", " ".join(cmd), flush=True)
                mpv_process = subprocess.Popen(cmd)
            except Exception as exc:
                print(f"Chyba konfigurace: {exc}", flush=True)
                mpv_process = None

            last_mtime = mtime

        time.sleep(3)


if __name__ == "__main__":
    main()
