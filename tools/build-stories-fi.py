#!/usr/bin/env python3
"""Build stories-fi.json: Finnish bedtime stories for Ihaaya.

Only real people reading (Ankit, 2026-11-22: no robotic voices), only stories for children
(Ankit, 2026-11-22: "only for kids, no adult type stories").

1. LibriVox "Satuja ja tarinoita I" (H. C. Andersen, public domain): its gentle tales.
   The rest of that book is not for bedtime at five: Tulukset and Iso Niilo ja Pikku Niilo (killing),
   Matkatoveri (a dead man, a troll), Pieni merenneito, Satakauno and Vakaa tinasotamies (sad endings),
   Paha poika (a love tale), Onnettaren kalossit (65 minutes).
2. Four free Finnish children's podcasts read by real people. The app streams each episode from the
   podcast's own public feed, the way a podcast app does, and names the show; no audio is copied here.
   Picked by hand with the same gentle rule as the English list (tools/build-stories.py): no ghosts,
   witches, trolls or ogres, no wolf eating anyone, no sad endings, no copy of the same tale twice.
   Left out on purpose:
   - Hippo-satuja: Hipot ja ullakon kummitus (ghost stories).
   - Kauneimmat lastensadut: Hannu ja Kerttu (witch), Lumikki (poisoned), Pieni merenneito and
     Pieni tulitikkutyttö (sad), Sammakkoprinssi, Saapasjalkakissa (ogre), Todellinen prinsessa (already
     in the Andersen book).
   - Iltasatu lapselle: Seitsemän pientä kiliä and Pieni Punahilkka (the wolf eats them), Kolme pukkia
     (troll), Ruma ankanpoikanen and Kultakutri (Kauneimmat has them).
   - Satuhetki: readings of other people's books still under copyright (Muumi, Melukylä, Kettu ja tonttu,
     Maukka ja Väykkä, Kirsi Kunnas, Kani joka tahtoi nukahtaa, Urpo ja Turpo), Saiturin joulu (ghosts),
     Siirin jouluyllätys (source unknown), and the 26-90 minute ones.
   Not used: Aava-kirjat (says it is made with AI), Iltasatumaailma (likely AI), Lasten sadut (Podplay only),
   Sveriges Radio Taikalipas (waiting for Sveriges Radio's permission).

Same format as stories.json, so the app plays both the same way: a podcast's "b" is empty and the file
is the full episode address. Every file is checked: LibriVox against archive.org/metadata, podcast
episodes with a 2-byte request; lengths come from archive.org or the feed.

Usage: python3 tools/build-stories-fi.py
"""
import json, os, sys, urllib.request
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.expanduser("~/.cache/star-chart-stories/fi")
UA = {"User-Agent": "star-chart-story-list/1.0"}
IT = "{http://www.itunes.com/dtds/podcast-1.0.dtd}"

ITEM = "satujajatarinoitai_2507_librivox"
BOOK = {"t": "Satuja ja tarinoita I", "a": "H. C. Andersen", "b": f"https://archive.org/download/{ITEM}/"}
STORIES = [  # file, title, themes, emoji
    ("satujajatarinoitai_03_andersen_64kb.mp3", "Todellinen prinsessa", "royal,fairy", "👑"),
    ("satujajatarinoitai_09_andersen_64kb.mp3", "Keisarin uudet vaatteet", "royal", "🤴"),
    ("satujajatarinoitai_04_andersen_64kb.mp3", "Pikku Iidan kukkaset", "nature,fairy", "🌷"),
    ("satujajatarinoitai_05_andersen_64kb.mp3", "Peukalo-Liisa", "fairy,animals", "🌸"),
]

# Podcasts: show name and credit (shown under the story title), feed, and the picked episodes:
# (episode title exactly as in the feed, themes, picture[, shorter title for the app]).
PODCASTS = [
    {"t": "Hippo-satuja lapsille", "a": "OP Pohjola", "feed": "https://feeds.transistor.fm/hippo-satuja-lapsille", "pick": [
        ("Hippojen kevätretki", "animals,nature", "🏕️"),
        ("Hippojen takkaillan savukaaos", "animals", "🎁"),
        ("Hipot sähkökatkoksen armoilla", "animals,night", "🕯️"),
        ("Hipot ja tiukka tietovisa", "animals", "🧠"),
        ("Hipot puutarhureina – hyötykasveja vai ötökkäparatiisi?", "animals,nature", "🥕", "Hipot puutarhureina"),
        ("Hipot ja kesäyön meteoriparvi", "animals,night", "🌠"),
        ("Teatterin taikaa", "animals", "🎭"),
        ("Harvinainen postimerkki", "animals", "📮"),
        ("Hannan superletut", "animals", "🥞"),
        ("Ajetaanko tandemilla?", "animals", "🚲"),
        ("Vauhdikas eväsretki", "animals,nature", "🛶"),
        ("Kokkikerhossa kuohuu", "animals", "🍪"),
        ("Leijan myrskylento", "animals,nature", "🪁"),
        ("Lumilinnan kaatuvat muurit", "animals,nature", "❄️"),
        ("Hiirulaisten hurja marjaretki", "animals,nature", "🍓"),
    ]},
    {"t": "Kauneimmat lastensadut", "a": "HÖÖD", "feed": "https://anchor.fm/s/4eb9e5a8/podcast/rss", "pick": [
        ("Ruma ankanpoikanen", "animals,fairy", "🦢"),
        ("Kultakutri ja kolme karhua", "animals,fairy", "🐻"),
        ("Korppi ja Kettu", "animals,fables", "🦊"),
    ]},
    {"t": "Iltasatu lapselle", "a": "Miiro Juuso", "feed": "https://anchor.fm/s/45eac6b8/podcast/rss", "pick": [
        ("Kukko käy kuninkaissa", "animals,royal", "🐓"),
        ("Ketun kalansaalis", "animals,fables", "🐟"),
        ("Jänis ja siili", "animals,fables", "🦔"),
        ("Laiska-Jaakko", "fables", "😴"),
        ("Kolme toivomusta", "fairy,fables", "✨"),
        ("Kolme pientä porsasta", "animals,fables", "🐷"),
        ("Jänis ja kilpikonna", "animals,fables", "🐢"),
        ("Tipu Tip", "animals", "🐥"),
        ("Kettu ja Kirjava Kana", "animals,fables", "🐔"),
        ("Piparkakkupoika", "fairy", "🍪"),
        ("Maalaishiiri ja Kaupunkilaishiiri", "animals,fables", "🐭"),
        ("Mestariräätäli", "fairy", "🧵"),
    ]},
    {"t": "Satuhetki", "a": "Satuja Jätkäsaaresta", "feed": "https://anchor.fm/s/11bbd15c/podcast/rss", "pick": [
        ("Pähkinänsärkijä ja jouluyön taika", "toys,fairy", "🎄"),
        ("Peurasaaren vuodenajat – Tarina ystävyydestä ja selviytymisestä", "animals,nature", "🦌", "Peurasaaren vuodenajat"),
        ("Hiirisisarukset ja Salaperäinen Syyskoulu", "animals", "🍂"),
        ("Hiirisisarukset vappupiknikillä", "animals", "🎈"),
        ("Hiirisisarukset metsässä", "animals,nature", "🌲"),
        ("Hiirisisarukset eväsretkellä", "animals,nature", "🧺"),
        ("Hiirisisarukset jalkapallo-ottelussa", "animals", "⚽"),
        ("Hiirisisarukset kaupungissa", "animals", "🏙️"),
        ("Masa Mainio rakentaa auton", "toys", "🚗"),
    ]},
]
MIN_SECS, MAX_SECS = 100, 1600  # podcast episodes: about 2 to 25 minutes

THEMES_FI = {
    "animals": ["🐰", "Eläimet"], "fairy": ["🧚", "Sadut ja taikuus"], "royal": ["👑", "Prinssit ja prinsessat"],
    "toys": ["🧸", "Lelut ja nuket"], "nature": ["🌳", "Luonto ja vuodenajat"], "night": ["🌙", "Kuu ja tähdet"],
    "fables": ["🦉", "Opettavaiset tarinat"], "world": ["🌏", "Kaukaiset maat"],
}


def fetch(url, timeout=60, headers=None):
    req = urllib.request.Request(url, headers={**UA, **(headers or {})})
    return urllib.request.urlopen(req, timeout=timeout)


def metadata():
    os.makedirs(CACHE, exist_ok=True)
    local = os.path.join(CACHE, ITEM + ".json")
    if not os.path.exists(local):
        data = fetch(f"https://archive.org/metadata/{ITEM}").read()
        with open(local, "wb") as f:
            f.write(data)
    return json.load(open(local, encoding="utf-8"))


def seconds(length):
    """archive.org and feeds give '17:16', '01:04:53' or plain seconds."""
    if ":" not in str(length):
        return round(float(length))
    total = 0
    for part in str(length).split(":"):
        total = total * 60 + float(part)
    return round(total)


def plays(url):
    """The episode answers a 2-byte request with audio (some hosts redirect first)."""
    with fetch(url, timeout=30, headers={"Range": "bytes=0-1"}) as r:
        return r.status in (200, 206) and r.headers.get("Content-Type", "").startswith("audio/")


def librivox():
    files = {f["name"]: f for f in metadata().get("files", [])}
    if not files:
        sys.exit(f"archive.org has no files for {ITEM}")
    out = []
    for name, title, themes, emoji in STORIES:
        f = files.get(name)
        if not f or "length" not in f:
            sys.exit(f"missing on archive.org: {name}")
        out.append([0, title, name, seconds(f["length"]), themes, emoji])
    return out


def podcast(book, show):
    """The picked episodes of one show, straight from its public feed."""
    channel = ET.fromstring(fetch(show["feed"]).read()).find("channel")
    items = {(i.findtext("title") or "").strip(): i for i in channel.findall("item")}
    out = []
    for pick in show["pick"]:
        title, themes, emoji = pick[:3]
        item = items.get(title)
        enc = item.find("enclosure") if item is not None else None
        if enc is None or not enc.get("url"):
            sys.exit(f"{show['t']}: no episode '{title}' in the feed any more")
        url, secs = enc.get("url"), seconds(item.findtext(IT + "duration") or 0)
        if not MIN_SECS <= secs <= MAX_SECS:
            sys.exit(f"{show['t']}: '{title}' is {secs} s long, outside {MIN_SECS}-{MAX_SECS} s")
        if not plays(url):
            sys.exit(f"{show['t']}: '{title}' does not play: {url}")
        out.append([book, pick[3] if len(pick) > 3 else title, url, secs, themes, emoji])
    return out


def build():
    books, stories = [BOOK], librivox()
    for show in PODCASTS:
        books.append({"t": show["t"], "a": show["a"], "b": ""})
        stories += podcast(len(books) - 1, show)
    out = {"v": 2, "lang": "fi", "themes": THEMES_FI, "books": books, "stories": stories}
    path = os.path.join(ROOT, "stories-fi.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    per = {b["t"]: sum(1 for s in stories if s[0] == i) for i, b in enumerate(books)}
    print(f"stories-fi.json: {len(stories)} stories ({', '.join(f'{t} {n}' for t, n in per.items())}), "
          f"{sum(s[3] for s in stories) // 60} minutes in all")


if __name__ == "__main__":
    build()
