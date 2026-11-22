#!/usr/bin/env python3
"""Build stories-fi.json: Finnish bedtime stories for Ihaaya.

Only real people reading (Ankit, 2026-11-22: no robotic voices). The only free Finnish
children's recordings are LibriVox's "Satuja ja tarinoita I" (H. C. Andersen, public domain),
so the list holds its gentle tales. The rest of that book is not for bedtime at five:
Tulukset and Iso Niilo ja Pikku Niilo (killing), Matkatoveri (a dead man, a troll),
Pieni merenneito, Satakauno and Vakaa tinasotamies (sad endings), Paha poika (a love tale),
Onnettaren kalossit (65 minutes).

Same format as stories.json (tools/build-stories.py), so the app plays both the same way.
Every file is checked against archive.org/metadata, and the length comes from there.

Usage: python3 tools/build-stories-fi.py
"""
import json, os, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.expanduser("~/.cache/star-chart-stories/fi")
UA = {"User-Agent": "star-chart-story-list/1.0"}

ITEM = "satujajatarinoitai_2507_librivox"
BOOK = {"t": "Satuja ja tarinoita I", "a": "H. C. Andersen", "b": f"https://archive.org/download/{ITEM}/"}
STORIES = [  # file, title, themes, emoji
    ("satujajatarinoitai_03_andersen_64kb.mp3", "Todellinen prinsessa", "royal,fairy", "👑"),
    ("satujajatarinoitai_09_andersen_64kb.mp3", "Keisarin uudet vaatteet", "royal", "🤴"),
    ("satujajatarinoitai_04_andersen_64kb.mp3", "Pikku Iidan kukkaset", "nature,fairy", "🌷"),
    ("satujajatarinoitai_05_andersen_64kb.mp3", "Peukalo-Liisa", "fairy,animals", "🌸"),
]
THEMES_FI = {
    "animals": ["🐰", "Eläimet"], "fairy": ["🧚", "Sadut ja taikuus"], "royal": ["👑", "Prinssit ja prinsessat"],
    "toys": ["🧸", "Lelut ja nuket"], "nature": ["🌳", "Luonto ja vuodenajat"], "night": ["🌙", "Kuu ja tähdet"],
    "fables": ["🦉", "Opettavaiset tarinat"], "world": ["🌏", "Kaukaiset maat"],
}


def metadata():
    os.makedirs(CACHE, exist_ok=True)
    local = os.path.join(CACHE, ITEM + ".json")
    if not os.path.exists(local):
        req = urllib.request.Request(f"https://archive.org/metadata/{ITEM}", headers=UA)
        data = urllib.request.urlopen(req, timeout=60).read()
        with open(local, "wb") as f:
            f.write(data)
    return json.load(open(local, encoding="utf-8"))


def seconds(length):
    """archive.org gives '17:16', '01:04:53' or plain seconds."""
    if ":" not in str(length):
        return round(float(length))
    total = 0
    for part in str(length).split(":"):
        total = total * 60 + float(part)
    return round(total)


def build():
    files = {f["name"]: f for f in metadata().get("files", [])}
    if not files:
        sys.exit(f"archive.org has no files for {ITEM}")
    stories = []
    for name, title, themes, emoji in STORIES:
        f = files.get(name)
        if not f or "length" not in f:
            sys.exit(f"missing on archive.org: {name}")
        stories.append([0, title, name, seconds(f["length"]), themes, emoji])
    out = {"v": 2, "lang": "fi", "themes": THEMES_FI, "books": [BOOK], "stories": stories}
    path = os.path.join(ROOT, "stories-fi.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print(f"stories-fi.json: {len(stories)} stories,", ", ".join(f"{s[1]} {s[3] // 60}:{s[3] % 60:02d}" for s in stories))


if __name__ == "__main__":
    build()
