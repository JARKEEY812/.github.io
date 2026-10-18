#!/usr/bin/env python3
"""Static SEO checks for HTML files. Stdlib only. Exit 1 if any ERROR."""
import json
import sys
from html.parser import HTMLParser
from pathlib import Path

TITLE_MAX = 60   # ориентир: Google режет по пикселям (~600px)
DESC_MAX = 160   # ориентир, не правило


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.lang = None
        self.title = None
        self.meta = {}
        self.canonicals = []
        self.h1 = 0
        self.img_no_alt = []
        self.jsonld = []
        self._in = None
        self._buf = []

    def handle_starttag(self, tag, attrs):
        a = {k: (v or "") for k, v in attrs}
        if tag == "html":
            self.lang = a.get("lang")
        elif tag == "title":
            self._in, self._buf = "title", []
        elif tag == "meta" and a.get("name"):
            self.meta[a["name"].lower()] = a.get("content", "")
        elif tag == "link" and "canonical" in a.get("rel", "").lower().split():
            self.canonicals.append(a.get("href", ""))
        elif tag == "h1":
            self.h1 += 1
        elif tag == "img" and "alt" not in a:
            self.img_no_alt.append((self.getpos()[0], a.get("src", "?")))
        elif tag == "script" and a.get("type", "").lower() == "application/ld+json":
            self._in, self._buf = "jsonld", []
            self._jl_line = self.getpos()[0]

    def handle_endtag(self, tag):
        if self._in == "title" and tag == "title":
            self.title = "".join(self._buf).strip()
            self._in = None
        elif self._in == "jsonld" and tag == "script":
            self.jsonld.append((self._jl_line, "".join(self._buf)))
            self._in = None

    def handle_data(self, data):
        if self._in:
            self._buf.append(data)


def check(path):
    p = Page()
    p.feed(path.read_text(encoding="utf-8", errors="replace"))
    out = []
    E = lambda m: out.append(("ERROR", m))
    W = lambda m: out.append(("WARN", m))

    if not p.title:
        E("нет <title> или он пустой")
    elif len(p.title) > TITLE_MAX:
        W(f"title {len(p.title)} симв. (> ~{TITLE_MAX}, может обрезаться)")

    desc = p.meta.get("description")
    if not desc:
        W("нет meta description")
    elif len(desc) > DESC_MAX:
        W(f"description {len(desc)} симв. (> ~{DESC_MAX}, может обрезаться)")

    robots = (p.meta.get("robots", "") + "," + p.meta.get("googlebot", "")).lower()
    if "noindex" in robots:
        E("meta robots содержит noindex — страница не попадёт в индекс")

    if not p.lang:
        W("нет <html lang>")
    if "viewport" not in p.meta:
        W("нет meta viewport (мобильная версия)")

    if len(p.canonicals) > 1:
        E(f"несколько canonical: {p.canonicals}")
    elif p.canonicals and not p.canonicals[0].startswith(("http://", "https://")):
        W(f"canonical не абсолютный: {p.canonicals[0]}")

    if p.h1 == 0:
        W("нет <h1>")
    elif p.h1 > 1:
        W(f"{p.h1} тегов <h1> (допустимо, но проверь иерархию)")

    for line, src in p.img_no_alt:
        W(f"строка {line}: <img> без alt ({src})")

    for line, raw in p.jsonld:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            E(f"строка {line}: невалидный JSON-LD — {e.msg}")
            continue
        items = data if isinstance(data, list) else [data]
        for it in items:
            if isinstance(it, dict) and "@context" not in it and "@graph" not in it:
                W(f"строка {line}: JSON-LD без @context")
            if isinstance(it, dict) and "@type" not in it and "@graph" not in it:
                W(f"строка {line}: JSON-LD без @type")
    return out


def main(args):
    files = []
    for a in args or ["."]:
        p = Path(a)
        files += sorted(p.rglob("*.html")) if p.is_dir() else [p]
    files = [f for f in files if "node_modules" not in f.parts and ".git" not in f.parts]
    errors = 0
    for f in files:
        res = check(f)
        errors += sum(1 for lvl, _ in res if lvl == "ERROR")
        if res:
            print(f"## {f}")
            for lvl, msg in res:
                print(f"  {lvl}: {msg}")
    print(f"\nфайлов: {len(files)}, ERROR: {errors}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
