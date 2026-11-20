#!/usr/bin/env python3
"""Build stories.json: complete bedtime stories of 7-10 minutes, from LibriVox (public-domain recordings).

Each story is complete in one sitting (no chapters of longer books). The app picks one at random each
day, never one the child has already heard, and can pick from a theme ("a story about animals").

Rules:
  * Free in the EU as well as the USA: the author died before 1956, or the tale is anonymous/traditional.
    (Thornton Burgess, d. 1965, and Howard Garis, d. 1962, are left out for that reason.)
  * 7-10 minutes (400-630 seconds). Aesop's one-minute fables are grouped into 7-10 minute nights.
  * Gentle: titles about death, ghosts, witches, robbers and the like are left out, and so are known sad
    or frightening tales.
  * Each file is checked against the Internet Archive's file list, so every story can play.
  * The same tale in two collections is kept once.

Run:  python3 tools/build-stories.py   (writes stories.json next to index.html; caches API answers in
      ~/.cache/star-chart-stories so a second run is fast)
"""
import json
import pathlib
import re
import time
import urllib.parse
import urllib.request

API = "https://librivox.org/api/feed/"
OUT = pathlib.Path(__file__).resolve().parent.parent / "stories.json"
CACHE = pathlib.Path.home() / ".cache" / "star-chart-stories"
UA = {"User-Agent": "star-chart-story-list/1.0"}  # the LibriVox API refuses Python's default
MIN_SECS, MAX_SECS = 400, 630
EU_FREE_BEFORE = 1956

# (last name, first-name prefix, title filter, titles to leave out): every English LibriVox book by that author whose
# title matches. Gentler books come first: when two books tell the same tale, the first one's telling is kept
# (Perrault's Cinderella, not Grimm's).
AUTHORS = [
    ("Potter", "Beatrix", r".", r"caravan|pig robinson"), ("Gruelle", "Johnny", r".", None), ("Paine", "Albert", r"hollow tree|rabbit", None),
    ("Hopkins", "William", r"sandman", None), ("Blaisdell", "Mary", r".", None), ("Baum", "L", r"mother goose|wizard stories|twinkle|little|queer|sea fair", None),
    ("Perrault", "Charles", r".", None), ("Mabie", "Hamilton", r"fairy|folk|myth|young folks", r"volume ([2-9]|1[0-9])|myth"),
    ("Jacobs", "Joseph", r"fairy|tales", None), ("Ozaki", "Yei", r".", None), ("Bryce", "Catherine", r".", None),
    ("Skinner", "Ada", r".", None), ("Poulsson", "Emilie", r".", None), ("Chisholm", "Louey", r".", None),
    ("Lang", "Andrew", r"fairy book|fairy tales|animal story|story book", None), ("Tolstoy", "Leo", r"fable|for children|for little", None),
    ("Andersen", "Hans", r"fairy|tales|stories", r"short stories volume"), ("Grimm", "", r"fairy|household|tales|stories", None),
]
TITLES = [r"^Children's Short Works", r"^Bed-Time Stories", r"^Short Story Collection for Children"]
AESOP_IDS = [353, 360, 193, 194, 195, 196, 197, 198, 199, 356, 357, 359]

SCARY = re.compile(r"\b(death|dead|die[sd]?|dying|murder\w*|kill\w*|devil\w*|ghost\w*|grave\w*|corpse|blood\w*|robber\w*|thie(f|ves)|"
                   r"witch\w*|wicked|cruel|hang\w*|executioner|bluebeard|juniper|skeleton|haunted|demon\w*|hell|fear|terror|"
                   r"cannibal|ogre\w*|troll\w*|wolf and the seven|hansel|red shoes|match girl|little mermaid|tin soldier|"
                   r"fir tree|girl who trod|snow queen|shadow|sorrow|funeral|match.?seller|loki|angel\w*|rumple\w*|wolf and the (six|seven)|black (mingo|sambo|quasha|quibba)|bannerman|sweetheart roland|war\b|battle|soldier|sin\b|drunk\w*|"
                   r"goose.?girl|frog.?king|rumpel\w*|snow.?white|twelve brothers|seven ravens|fitcher|godfather|rapunzel|"
                   r"clever elsie|without hands|brother lustig|singing bone|almond tree|jew\w*|"
                   r"negro\w*|nigger\w*|dark(e)?y|savage\w*|injun\w*|chinaman|g[iy]ps(y|ies)|coolie\w*|mammy|pickaninn\w*|sambo|squaw)\b", re.I)
# Andersen and the original Grimm tell many sad or harsh tales: only these gentle ones are kept from them
# (the Grimm retold for children in one-syllable words is kept whole).
GENTLE = {
    "Andersen": r"ugly duck|thumbelina|tiny|princess (and|on) the pea|real princess|emperor'?s new|nightingale|darning.?needle|flax|"
                r"little ida|swineherd|shepherdess|happy family|butterfly|snow.?man|buckwheat|top and (the )?ball|sweethearts|"
                r"pen and inkstand|money.?pig|ole.?luk|sandman|what the old man does|quite true|conceited apple|jumper|leaping|"
                r"drop of water|old street lamp|bell|elder.?tree mother|goloshes|galoshes",
    "Grimm": r"elves|shoemaker|porridge|star.?(money|talers|dollars)|bremen|golden goose|danc(ing|ed)|mother holle|frau holle|"
             r"old sultan|fox and (the )?cat|hare and (the )?hedgehog|straw|turnip|golden key|grandson|queen bee|three feathers|"
             r"wren|red (cap|riding)|bean|sausage|the sole|nail|clever hans|spindle|thrushbeard|sweet porridge|sleeping beauty|frog prince|"
             r"hans in luck|travelling musicians",
}
SKIP = re.compile(r"^(preface|introduction|dedication|foreword|contents|afterword|note|notes|chapter\b.*|[ivxlc]+\.?)$", re.I)

THEMES = {  # key: [picture, name, title words]
    "animals": ["🐰", "Animals", r"rabbit|bunny|hare|cat|kitten|puss|dog|pupp|fox|bear|mouse|mice|pig|hen|chick|duck|goose|bird|owl|"
                r"frog|toad|squirrel|elephant|lion|tiger|monkey|wolf|sheep|lamb|cow|calf|horse|pony|donkey|goat|turtle|tortoise|crow|"
                r"fish|bee|ant|grasshopper|butterfly|camel|crocodile|deer|robin|sparrow|swan|parrot|kangaroo|beaver|animal|beast|"
                r"jackal|ox|cricket|ladybird|spider|snail|whale|seal|penguin|zebra|giraffe|hedgehog|badger|mole|otter"],
    "fairy": ["🧚", "Fairy tales & magic", r"fair(y|ies)|elf|elves|magic|wizard|dwarf|gnome|brownie|pixie|goblin|enchant|giant|dragon|"
              r"mermaid|wish|spell|fay|oz|sprite|unicorn"],
    "royal": ["👑", "Princes & princesses", r"prince|princess|king|queen|castle|palace|royal|emperor"],
    "toys": ["🧸", "Toys & dolls", r"raggedy|doll|toy|teddy|ball|kite|drum|tin|wooden|puppet|cecco|nursery"],
    "nature": ["🌳", "Farm & nature", r"farm|garden|tree|flower|wind|rain|snow|sea|river|forest|wood|meadow|field|apple|seed|"
               r"spring|summer|autumn|winter|sandman|hollow tree"],
    "night": ["🌙", "Moon & stars", r"moon|star|night|sleep|dream|sandman|bed|lullab|cradle|sun"],
    "fables": ["🦉", "Fables", r"aesop|fable"],
    "world": ["🌏", "Tales from far away", r"japan\w*|india\w*|china|chinese|russia\w*|norse|norw\w*|arab\w*|africa\w*|celtic|irish|"
              r"scot\w*|persia\w*|egypt\w*|eskimo"],
}
EMOJI = [  # first matching word in the story title (then the book title) gives its picture
    (r"rabbit|bunny|hare", "🐰"), (r"cat|kitten|puss", "🐱"), (r"dog|pupp\w*", "🐶"), (r"fox", "🦊"), (r"bear", "🐻"),
    (r"mouse|mice", "🐭"), (r"pig\w*", "🐷"), (r"hen|chick\w*|rooster|cock", "🐔"), (r"duck\w*", "🦆"), (r"goose|geese|swan", "🦢"),
    (r"owl", "🦉"), (r"frog|toad", "🐸"), (r"squirrel", "🐿️"), (r"elephant", "🐘"), (r"lion", "🦁"), (r"tiger", "🐯"),
    (r"monkey|ape", "🐒"), (r"wolf", "🐺"), (r"sheep|lamb", "🐑"), (r"cow|calf|ox", "🐮"), (r"horse|pony", "🐴"),
    (r"donkey", "🫏"), (r"goat", "🐐"), (r"turtle|tortoise", "🐢"), (r"crow|raven|bird\w*|robin|sparrow|wren", "🐦"),
    (r"fish\w*", "🐟"), (r"bees?", "🐝"), (r"ants?", "🐜"), (r"grasshopper|cricket", "🦗"), (r"butterfly", "🦋"),
    (r"camel", "🐫"), (r"crocodile", "🐊"), (r"deer|stag", "🦌"), (r"dragon", "🐉"), (r"mermaid", "🧜"), (r"giant", "🧌"),
    (r"fair(y|ies)|elf|elves|pixie|sprite", "🧚"), (r"wizard|magic|enchant\w*|spell", "🪄"), (r"princess|queen", "👸"),
    (r"prince|king|emperor", "🤴"), (r"castle|palace", "🏰"), (r"raggedy|doll|toy|teddy|cecco|puppet", "🧸"),
    (r"moon", "🌙"), (r"stars?", "⭐"), (r"sun", "☀️"), (r"snow|winter", "❄️"), (r"rain", "🌧️"), (r"sea|ship|boat", "⛵"),
    (r"trees?|forest|wood", "🌳"), (r"flowers?|rose|lily", "🌸"), (r"apples?", "🍎"), (r"cake|bread|pie|porridge", "🥧"),
    (r"sandman|sleep|dream|bed", "🌙"), (r"farm", "🚜"), (r"aesop|fables?", "🦉"), (r"japan\w*", "🗾"), (r"india\w*", "🪔"),
]

_last = [0.0]


def fetch(url, cache_key):
    path = CACHE / (re.sub(r"[^A-Za-z0-9_.-]+", "_", cache_key)[:150] + ".json")
    if path.exists():
        return json.loads(path.read_text())
    err = None
    for attempt in range(4):
        wait = 0.35 - (time.time() - _last[0])
        if wait > 0:
            time.sleep(wait)  # be gentle with a volunteer project's server
        _last[0] = time.time()
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                data = json.load(r)
            CACHE.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data))
            return data
        except urllib.error.HTTPError as e:
            if e.code == 404:  # LibriVox answers 404 when a search finds nothing
                return {}
            err = e
        except Exception as e:  # noqa: BLE001 - retry any network hiccup
            err = e
        time.sleep(2 + attempt * 3)
    raise SystemExit(f"no answer ({err}): {url}")


def lv(kind, cache_key, **params):
    return fetch(API + kind + "/?" + urllib.parse.urlencode({**params, "format": "json"}), kind + "_" + cache_key)


def sections(book_id):
    found = lv("audiobooks", f"id_{book_id}", id=book_id, extended=1).get("books") or [{}]
    return found[0].get("sections", [])


def archive_files(ident):
    """MP3 files the Internet Archive really has in an item, with each file's author (creator)."""
    meta = fetch("https://archive.org/metadata/" + urllib.parse.quote(ident), "ia_" + ident)
    return {f["name"]: (f.get("creator") or "") for f in meta.get("files", []) if f.get("name", "").endswith(".mp3")}


_author_dod = {}


def creator_free(creator):
    """True when a story's author died before 1956 (LibriVox's author list), or the tale is anonymous/traditional."""
    c = re.sub(r"\s*\(.*?\)", "", creator or "").strip()
    if re.fullmatch(r"(anonymous|unknown|traditional|folk\w*|aesop|mother goose|.*folk ?tales?.*)", c, re.I):
        return True
    parts = c.replace(",", " ").split()
    if len(parts) < 2 or re.fullmatch(r"([A-Z]\.){1,3}", c.replace(" ", "")):
        return False  # no name or initials only: the author can't be checked
    last, first = parts[-1], parts[0]
    key = (last.lower(), first.lower())
    if key not in _author_dod:
        found = lv("authors", "last_" + last, last_name=last).get("authors", [])
        dods = [a.get("dod") for a in found if a.get("first_name", "").lower().startswith(first.lower()[:3])]
        _author_dod[key] = next((int(d) for d in dods if d and str(d).isdigit()), None)
    dod = _author_dod[key]
    return dod is not None and dod < EU_FREE_BEFORE


def clean(title):
    if title.isupper():
        title = title.title()
    t = re.sub(r"^\s*(\d+\s*[-–—:.)]?\s*)?((chapter|story|part|no\.?)\s*[0-9ivxlc]+\s*[-–—:.)]\s*)?", "", title, flags=re.I).strip()
    return re.sub(r"\s+", " ", t) or title.strip()


ALIASES = [  # one key for a tale told under different names
    (r"red.?(cap|riding)", "redridinghood"), (r"bremen|travell?ing musicians", "bremenmusicians"),
    (r"danc(ing|ed).*princess|danced to pieces", "dancingprincesses"), (r"tigg(y|ie).?winkle", "tiggywinkle"),
    (r"willow.?wren", "willowwren"), (r"three little pigs", "threelittlepigs"), (r"three bears", "threebears"),
]


def norm(title):
    """The same tale under small spelling differences ("Tiggy-Winkle", "Tiggywinkle") gives the same key."""
    for rx, key in ALIASES:
        if re.search(rx, title, re.I):
            return key
    t = re.sub(r"\((version|dramatic)[^)]*\)|\b(the|a|an|of|story|tale|mrs?|mr)\b", " ", title.lower())
    return re.sub(r"[^a-z]+", "", t)


def has(rx, text):
    return re.search(r"\b(" + rx + r")\b", text, re.I) is not None


def picture(title, book):
    for text in (title, book):
        for rx, e in EMOJI:
            if has(rx, text):
                return e
    return "📖"


books, stories, seen_titles, counts = [], [], set(), {}


def book_index(title, author, base):
    for i, b in enumerate(books):
        if b["t"] == title and b["b"] == base:
            return i
    books.append({"t": title, "a": author, "b": base})
    return len(books) - 1


def add_book(b, one_author, only=None):
    """Add the 7-10 minute, gentle, playable, not-yet-seen stories of one LibriVox book."""
    btitle = re.sub(r"\s*\((version|dramatic)[^)]*\)", "", b["title"], flags=re.I).strip()
    secs = sections(b["id"])
    urls = [s.get("listen_url") or "" for s in secs]
    ident = next((u.split("/download/")[1].split("/")[0] for u in urls if "/download/" in u), None)
    if not ident:
        return
    have = archive_files(ident)
    for s in sorted(secs, key=lambda s: int(s["section_number"])):
        url, length, title = s.get("listen_url") or "", int(s.get("playtime") or 0), clean(s["title"])
        fname = url.rsplit("/", 1)[-1]
        if not (MIN_SECS <= length <= MAX_SECS) or fname not in have or SKIP.match(title) or SCARY.search(title):
            continue
        if only and not re.search(only, title, re.I):
            continue
        if not one_author:
            if not creator_free(have[fname]):
                continue
            who = next((k for k in GENTLE if k.lower() in have[fname].lower()), None)
            if who and not re.search(GENTLE[who], title, re.I):
                continue  # an Andersen or Grimm tale inside a mixed collection: gentle ones only
        key = norm(title)
        if not key or key in seen_titles:
            continue
        seen_titles.add(key)
        base = url.rsplit("/", 1)[0].replace("://www.archive.org/", "://archive.org/").replace("http://", "https://") + "/"
        author = (b["authors"][0]["first_name"] + " " + b["authors"][0]["last_name"]) if one_author else (have[fname] or "Anonymous")
        th = [k for k, v in THEMES.items() if has(v[2], title)]
        th += [k for k in ("world", "fables", "toys", "nature", "night") if k not in th and has(THEMES[k][2], btitle)]
        if "fairy" not in th and has(r"fair(y|ies)|faery|household tales|folk|wonder|snowdrop|grimm|andersen", btitle):
            th.append("fairy")
        stories.append([book_index(btitle, author.strip(), base), title, fname, length, ",".join(th), picture(title, btitle)])
        counts[btitle] = counts.get(btitle, 0) + 1


def free_author(b, last, first):
    a = next((x for x in b["authors"] if x.get("last_name") == last and x.get("first_name", "").startswith(first)), None)
    return a is not None and str(a.get("dod") or "").isdigit() and int(a["dod"]) < EU_FREE_BEFORE


# 1. Books by one author who died before 1956.
for last, first, title_rx, leave_out in AUTHORS:
    found = [b for b in lv("audiobooks", "author_" + last, author=last, limit=500).get("books", [])
             if b.get("language") == "English" and re.search(title_rx, b["title"], re.I) and free_author(b, last, first)
             and not (leave_out and re.search(leave_out, b["title"], re.I))]
    for b in sorted(found, key=lambda b: ("dramatic" in b["title"].lower(), int(b["id"]))):
        add_book(b, True, None if "one-syllable" in b["title"].lower() else GENTLE.get(last))

# 2. Mixed collections: each story's author is checked on its own.
for pattern in TITLES:
    for b in sorted(lv("audiobooks", "title_" + pattern, title=pattern, limit=500).get("books", []), key=lambda b: int(b["id"])):
        if b.get("language") == "English":
            add_book(b, False)

# 3. Aesop: one-minute fables grouped into 7-10 minute nights.
group = []
for bid in AESOP_IDS:
    secs = sections(bid)
    ident = secs[0]["listen_url"].split("/download/")[1].split("/")[0]
    have = archive_files(ident)
    base = secs[0]["listen_url"].rsplit("/", 1)[0].replace("://www.archive.org/", "://archive.org/") + "/"
    for s in sorted(secs, key=lambda s: int(s["section_number"])):
        f = s["listen_url"].rsplit("/", 1)[-1]
        if f not in have or int(s.get("playtime") or 0) <= 0 or SCARY.search(s["title"]) or SKIP.match(clean(s["title"])):
            continue
        group.append((clean(s["title"]), f, int(s["playtime"]), base))
        if sum(g[2] for g in group) >= 450:
            bi = book_index("Aesop's Fables", "Aesop", base)
            stories.append([bi, group[0][0] + " and " + str(len(group) - 1) + " more fables",
                            [[g[1], g[2]] for g in group], sum(g[2] for g in group), "fables,animals", "🦉"])
            group = []

OUT.write_text(json.dumps({"v": 2, "built": time.strftime("%Y-%m-%d"),
                           "source": "LibriVox.org public-domain recordings, hosted by the Internet Archive",
                           "themes": {k: [v[0], v[1]] for k, v in THEMES.items()}, "books": books, "stories": stories},
                          ensure_ascii=False, separators=(",", ":")))
print(f"{len(stories)} stories from {len(books)} books, {OUT.stat().st_size // 1024} KB -> {OUT}")
print("by theme:", {k: sum(k in s[4].split(",") for s in stories) for k in THEMES}, "| no theme:", sum(not s[4] for s in stories))
for t, n in sorted(counts.items(), key=lambda x: -x[1])[:45]:
    print(f"  {n:>4}  {t}")
