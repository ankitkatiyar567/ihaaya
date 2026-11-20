#!/usr/bin/env python3
"""Build stories.json: one bedtime story a night, from LibriVox (public-domain recordings).

Only authors who died before 1956 are used, so the stories are free in the EU (life + 70)
as well as in the USA. Thornton Burgess (d. 1965) and Howard Garis (d. 1962) are left out
for that reason. Each night is one chapter or story; Aesop's one-minute fables are grouped
into nights of about six minutes. The order mixes the long run of Arthur Scott Bailey's
animal books with the other books, and starts with Peter Rabbit.

Run:  python3 tools/build-stories.py   (writes stories.json next to index.html)
"""
import json
import math
import pathlib
import re
import time
import urllib.parse
import urllib.request

API = "https://librivox.org/api/feed/audiobooks/"
OUT = pathlib.Path(__file__).resolve().parent.parent / "stories.json"
MIN_SECS, MAX_SECS = 60, 30 * 60      # leave out credits-only tracks and very long chapters
AESOP_NIGHT_SECS = 360                # group short fables into nights of about six minutes
FRONT_MATTER = re.compile(r"(preface|introduction|dedication|foreword|preface and dedication)( by .*)?", re.I)

# The other books, in the order they first appear (each stays in order inside itself).
# Each lists LibriVox recordings to try in turn: the first one still on the Internet Archive is used.
OTHERS = [
    ("potter", [15229]), ("gruelle", [1407, 1239, 9449]), ("hopkins", [18433]), ("williams", [433, 432]),
    ("kipling", [585, 1163, 1048]), ("paine", [12166]), ("gruelle", [2052, 15782]), ("potter", [385, 2990]),
    ("potter", [22227]), ("williams", [21700]), ("gruelle", [10711]), ("potter", [8406]), ("paine", [15140]),
    ("paine", [13368]), ("gruelle", [16330]), ("gruelle", [16348]), ("gruelle", [17842]), ("potter", [22560]),
]
AESOP = [353, 360, 193, 194, 195, 196, 197, 198, 199, 356, 357, 359]
EMOJI = [  # first keyword found in the book title wins
    ("Daddy Long", "🕷️"), ("Fox", "🦊"), ("Badger", "🦡"), ("Butterfly", "🦋"), ("Woodchuck", "🦫"), ("Beaver", "🦫"),
    ("Bumblebee", "🐝"), ("Cricket", "🦗"), ("Katydid", "🦗"), ("Bear", "🐻"), ("Mouse", "🐭"), ("Coon", "🦝"),
    ("Frog", "🐸"), ("Firefly", "✨"), ("Squirrel", "🐿️"), ("Chipmunk", "🐿️"), ("Weasel", "🦦"), ("Mink", "🦦"),
    ("Muskrat", "🐀"), ("Pig", "🐷"), ("Hen", "🐔"), ("Rabbit", "🐰"), ("Monkey", "🐒"), ("Cat", "🐱"), ("Ladybug", "🐞"),
    ("LadyBug", "🐞"), ("Cow", "🐮"), ("Deer", "🦌"), ("Dog", "🐶"), ("Pony", "🐴"), ("Lamb", "🐑"), ("Owl", "🦉"),
    ("Turtle", "🐢"), ("Turkey", "🦃"), ("Mole", "🐾"), ("Crow", "🐦"), ("Jay", "🐦"), ("Robin", "🐦"), ("Wren", "🐦"),
    ("Woodpecker", "🐦"), ("Bobolink", "🐦"), ("Raggedy", "🧸"), ("Fairies", "🧚"), ("Fairy Stories", "🧚"),
    ("Caravan", "🎪"), ("Sandman", "🌙"), ("Hollow Tree", "🌳"), ("Velveteen", "🐰"), ("Cecco", "🧸"),
    ("Just So", "🐘"), ("Camel", "🐫"), ("Pebble", "💎"), ("Beatrix Potter", "🐰"), ("Aesop", "🦊"),
]


def get(params):
    url = API + "?" + urllib.parse.urlencode({**params, "format": "json"})
    req = urllib.request.Request(url, headers={"User-Agent": "star-chart-story-list/1.0"})  # the API refuses Python's default
    err = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception as e:  # noqa: BLE001 - retry any network hiccup
            err = e
            time.sleep(2 + attempt * 3)
    raise SystemExit(f"LibriVox API did not answer ({err}): {url}")


_files = {}


def archive_files(base):
    """The MP3 files that really exist in an Internet Archive item (an empty set when the item is gone)."""
    ident = base.rstrip("/").rsplit("/", 1)[-1]
    if ident not in _files:
        req = urllib.request.Request("https://archive.org/metadata/" + urllib.parse.quote(ident), headers={"User-Agent": "star-chart-story-list/1.0"})
        names = set()
        for attempt in range(4):
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    names = {f["name"] for f in json.load(r).get("files", []) if f.get("name", "").endswith(".mp3")}
                break
            except Exception:  # noqa: BLE001 - retry any network hiccup
                time.sleep(2 + attempt * 3)
        _files[ident] = names
    return _files[ident]


def book(book_id):
    time.sleep(0.4)  # be gentle with a volunteer project's server
    return get({"id": book_id, "extended": 1})["books"][0]


def clean(title):
    t = re.sub(r"^\s*(chapter|story|part)?\s*[0-9ivxlc]+\s*[-–—:.)]\s*", "", title, flags=re.I).strip()
    return t or title.strip()


def norm(title):
    t = re.sub(r"\((version|dramatic)[^)]*\)", "", title, flags=re.I).lower()
    t = t.replace("longlegs", "long legs").replace("the tale of", "").replace("tale of", "")
    return re.sub(r"[^a-z]+", " ", t).strip()


def emoji(title):
    return next((e for k, e in EMOJI if k.lower() in title.lower()), "📖")


def tracks(b):
    out = []
    for s in sorted(b["sections"], key=lambda s: int(s["section_number"])):
        url, secs = s.get("listen_url") or "", int(s.get("playtime") or 0)
        if FRONT_MATTER.fullmatch(clean(s["title"]).strip(" .")):
            continue  # a preface or an introduction for grown-ups is not a bedtime story
        if url.endswith(".mp3"):
            out.append((clean(s["title"]), url, secs))
    return out


def base_and_files(trs):
    base = trs[0][1].rsplit("/", 1)[0] + "/"
    if all(u.startswith(base) for _, u, _ in trs):
        return base.replace("https://www.archive.org/", "https://archive.org/"), [u[len(base):] for _, u, _ in trs]
    return "", [u for _, u, _ in trs]


books, nights = [], []


def add_book(b, author, title=None, skip_titles=None):
    trs = [t for t in tracks(b) if MIN_SECS <= t[2] <= MAX_SECS]
    if trs:  # keep only files the Internet Archive still has
        have = archive_files(trs[0][1].rsplit("/", 1)[0] + "/")
        trs = [t for t in trs if t[1].rsplit("/", 1)[-1] in have]
    if skip_titles is not None:
        trs = [t for t in trs if norm(t[0]) not in skip_titles]
        skip_titles.update(norm(t[0]) for t in trs)
    if not trs:
        return []
    base, files = base_and_files(trs)
    title = title or re.sub(r"\s*\((version|dramatic)[^)]*\)", "", b["title"], flags=re.I)
    if title.startswith("Tale "):
        title = "The " + title
    books.append({"t": title, "a": author, "e": emoji(title), "b": base,
                  "s": [[t[0], f, t[2]] for t, f in zip(trs, files)]})
    i = len(books) - 1
    return [[i, j] for j in range(len(trs))]


def author_name(b, last):
    a = next(x for x in b["authors"] if x["last_name"] == last)
    return (a["first_name"] + " " + a["last_name"]).strip()


# 1. Arthur Scott Bailey: one recording per book (the one with most chapters), oldest first.
bailey = [b for b in get({"author": "Bailey", "limit": 300})["books"]
          if b["language"] == "English" and b["title"].lower().startswith("tale")
          and any(a["last_name"] == "Bailey" and a["first_name"].startswith("Arthur") and a["dod"] and int(a["dod"]) < 1956 for a in b["authors"])]
groups = {}
for b in bailey:
    groups.setdefault(norm(b["title"]), []).append(b)
bailey_units = []
for versions in sorted(groups.values(), key=lambda v: min(int(b["id"]) for b in v)):
    versions.sort(key=lambda b: (int(b["num_sections"]), "dramatic" not in b["title"].lower(), -int(b["id"])), reverse=True)
    for b in versions:  # the best recording that is still on the Internet Archive
        unit = add_book(book(b["id"]), "Arthur Scott Bailey")
        if unit:
            bailey_units.append(unit)
            break

# 2. The other books; Beatrix Potter's collections share stories, so each story is kept once.
seen_potter = set()
other_nights = []
for last, ids in OTHERS:
    for bid in ids:
        b = book(bid)
        a = next(x for x in b["authors"] if x["last_name"].lower() == last)
        if not a["dod"] or int(a["dod"]) >= 1956:
            raise SystemExit(f"{b['title']}: author died {a['dod']!r}, not free in the EU")
        got = add_book(b, author_name(b, a["last_name"]), skip_titles=seen_potter if last == "potter" else None)
        if got or last == "potter":  # Potter collections overlap: an empty one just repeats stories
            other_nights += got
            break

# 3. Aesop: group the fables into nights of about six minutes; one Aesop night after every four others.
fables = []
for bid in AESOP:
    b = book(bid)
    trs = [t for t in tracks(b) if t[2] > 0]
    if trs:
        have = archive_files(trs[0][1].rsplit("/", 1)[0] + "/")
        fables += [t for t in trs if t[1].rsplit("/", 1)[-1] in have]
base, files = base_and_files(fables)
books.append({"t": "Aesop's Fables", "a": "Aesop", "e": "🦊", "b": base, "s": [[t[0], f, t[2]] for t, f in zip(fables, files)]})
ai, aesop_nights, group, secs = len(books) - 1, [], [], 0
for j, t in enumerate(fables):
    group.append(j); secs += t[2]
    if secs >= AESOP_NIGHT_SECS:
        aesop_nights.append([ai, group]); group, secs = [], 0
if group:
    aesop_nights.append([ai, group])
mixed = []
while other_nights or aesop_nights:
    mixed += other_nights[:4]; other_nights = other_nights[4:]
    if aesop_nights:
        mixed.append(aesop_nights.pop(0))

# 4. The night order: a few of the other stories, then a whole Bailey book, and again.
per = math.ceil(len(mixed) / len(bailey_units))
for unit in bailey_units:
    nights += mixed[:per] + unit
    mixed = mixed[per:]
nights += mixed

OUT.write_text(json.dumps({
    "v": 1, "built": time.strftime("%Y-%m-%d"),
    "source": "LibriVox.org public-domain recordings, hosted by the Internet Archive",
    "books": books, "nights": nights,
}, ensure_ascii=False, separators=(",", ":")))
total = sum(books[n[0]]["s"][j][2] for n in nights for j in (n[1] if isinstance(n[1], list) else [n[1]]))
print(f"{len(books)} books, {len(nights)} nights, {total / 3600:.0f} hours, {OUT.stat().st_size // 1024} KB -> {OUT}")
