#!/usr/bin/env python3
"""Builds the site: wraps every page in src/ with the shared header and footer
and writes the result to docs/, which is the folder GitHub Pages serves.

    python3 build.py

No dependencies beyond Python 3. Images, CSS and PDFs live in docs/assets/ and
are not touched by the build.
"""
import html
import pathlib
import re
import struct

ROOT = pathlib.Path(__file__).parent
SRC = ROOT / "src"
OUT = ROOT / "docs"
SITE = "https://www.abhignay.com"  # used for canonical links and the sitemap

NAV = [
    ("index", "Projects"),
    ("documents", "Documents"),
    ("highlights", "Highlights"),
    ("archive", "Archive"),
    ("contact", "Contact"),
]

SOCIAL = [
    ("GitHub", "https://github.com/abhignay"),
    ("YouTube", "https://www.youtube.com/@abhignay"),
    ("X", "https://x.com/abhignayrk"),
    ("LinkedIn", "https://www.linkedin.com/in/abhigna-yerramreddikalva-97230231a/"),
    ("Flickr", "https://www.flickr.com/photos/202569144@N06/"),
]

# Flight computer outlines in millimetres, used by {{lineup}}.
BOARDS = [
    ("SNIX R2", 67, 97),
    ("SNIX R2B", 50, 86),
    ("SAFAC r1", 42, 78),
    ("TFAC r1 to r3", 45, 85),
]

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<script>
  // Pick the theme before the page draws, so it never flashes the wrong colours.
  (function () {{
    var saved = null;
    try {{ saved = localStorage.getItem("theme"); }} catch (e) {{}}
    var dark = saved ? saved === "dark" : window.matchMedia("(prefers-color-scheme: dark)").matches;
    if (dark) document.documentElement.setAttribute("data-theme", "dark");
  }})();
</script>
<title>{title}</title>
<meta name="description" content="{description}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:type" content="website">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{site}/assets/img/hopper-hero.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{canonical}">{robots}
<link rel="icon" href="{root}assets/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600&family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;1,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{root}assets/style.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site-header">
  <div class="wrap">
    <a class="site-name" href="{root}index.html">Abhigna Y</a>
    <nav aria-label="Main">
{nav}
      <button class="theme-toggle" type="button" aria-label="Switch to dark mode">
        <svg class="moon" viewBox="0 0 24 24" aria-hidden="true"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5Z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>
        <svg class="sun" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4" fill="none" stroke="currentColor" stroke-width="2"/><path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.9 4.9l1.8 1.8M17.3 17.3l1.8 1.8M4.9 19.1l1.8-1.8M17.3 6.7l1.8-1.8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
      </button>
    </nav>
  </div>
</header>
<main id="main">
{body}
</main>
<footer class="site-footer">
  <div class="wrap">
    <p>&copy; Abhigna Y</p>
    <ul>
{social}
    </ul>
  </div>
</footer>
<script>
  (function () {{
    var root = document.documentElement;
    var button = document.querySelector(".theme-toggle");
    function label() {{
      var dark = root.getAttribute("data-theme") === "dark";
      button.setAttribute("aria-label", dark ? "Switch to light mode" : "Switch to dark mode");
    }}
    label();
    button.addEventListener("click", function () {{
      var dark = root.getAttribute("data-theme") !== "dark";
      if (dark) root.setAttribute("data-theme", "dark"); else root.removeAttribute("data-theme");
      try {{ localStorage.setItem("theme", dark ? "dark" : "light"); }} catch (e) {{}}
      label();
    }});
  }})();
</script>
</body>
</html>
"""


def image_size(path):
    """(width, height) of a PNG, JPEG, GIF or WebP file as displayed, or None."""
    try:
        with open(path, "rb") as f:
            data = f.read(65536)
            if data[:8] == b"\x89PNG\r\n\x1a\n":
                return (int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big"))
            if data[:6] in (b"GIF87a", b"GIF89a"):
                return (int.from_bytes(data[6:8], "little"), int.from_bytes(data[8:10], "little"))
            if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
                if data[12:16] == b"VP8X":
                    return (int.from_bytes(data[24:27], "little") + 1, int.from_bytes(data[27:30], "little") + 1)
                if data[12:16] == b"VP8 ":
                    return (int.from_bytes(data[26:28], "little") & 0x3FFF, int.from_bytes(data[28:30], "little") & 0x3FFF)
                if data[12:16] == b"VP8L":
                    b = int.from_bytes(data[21:25], "little")
                    return ((b & 0x3FFF) + 1, ((b >> 14) & 0x3FFF) + 1)
            if data[:2] == b"\xff\xd8":
                f.seek(2)
                while True:
                    marker = f.read(2)
                    if len(marker) < 2 or marker[0] != 0xFF:
                        return None
                    length = int.from_bytes(f.read(2), "big")
                    if marker[1] in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                        seg = f.read(5)
                        h, w = int.from_bytes(seg[1:3], "big"), int.from_bytes(seg[3:5], "big")
                        if orientation(path) in (5, 6, 7, 8):
                            w, h = h, w
                        return (w, h)
                    f.seek(length - 2, 1)
    except (OSError, ZeroDivisionError):
        return None
    return None


def orientation(path):
    """EXIF orientation of a JPEG (1 if none). Phone photos are often stored sideways."""
    with open(path, "rb") as f:
        data = f.read(65536)
    i = data.find(b"Exif\x00\x00")
    if i < 0:
        return 1
    t = data[i + 6:]
    big = t[:2] == b"MM"
    get = lambda o, n: int.from_bytes(t[o:o + n], "big" if big else "little")
    try:
        ifd = get(4, 4)
        for k in range(get(ifd, 2)):
            e = ifd + 2 + 12 * k
            if get(e, 2) == 0x0112:
                return get(e + 8, 2)
    except Exception:
        pass
    return 1


def mp4_ratio(path):
    """Display width / height of the first video track in an MP4, from its tkhd box."""
    try:
        data = pathlib.Path(path).read_bytes()
    except OSError:
        return None
    def boxes(start, end):
        i = start
        while i + 8 <= end:
            size, kind = struct.unpack(">I4s", data[i:i + 8]); hdr = 8
            if size == 1:
                size = struct.unpack(">Q", data[i + 8:i + 16])[0]; hdr = 16
            elif size == 0:
                size = end - i
            if size < hdr:
                return
            yield kind, i + hdr, i + size
            i += size
    def find(start, end):
        for kind, s, e in boxes(start, end):
            if kind in (b"moov", b"trak"):
                r = find(s, e)
                if r:
                    return r
            elif kind == b"tkhd":
                off = s + (88 if data[s] == 1 else 76)
                w, h = (v / 65536 for v in struct.unpack(">II", data[off:off + 8]))
                if w and h:
                    a, b = struct.unpack(">ii", data[off - 36:off - 28])
                    if a == 0 and b != 0:  # rotated 90 degrees
                        w, h = h, w
                    return w / h
        return None
    try:
        return find(0, len(data))
    except struct.error:
        return None


def figure(match, root=""):
    parts = [p.strip() for p in match.group(1).split("|")]
    name, alt = parts[0], parts[1]
    caption = parts[2] if len(parts) > 2 else ""
    cap = f"<figcaption>{caption}</figcaption>" if caption else ""
    size = image_size(OUT / "assets" / "img" / name)
    shape = f' style="--r: {size[0] / size[1]:.3f}; --w: {size[0]}px"' if size and size[1] else ""
    return (
        f'<figure data-file="assets/img/{name}"{shape}>'
        f'<img src="{root}assets/img/{name}" alt="{html.escape(alt)}" loading="lazy" '
        f"onerror=\"this.parentNode.classList.add('missing')\">{cap}</figure>"
    )


def video(match, root=""):
    parts = [p.strip() for p in match.group(1).split("|")]
    name = parts[0]
    caption = parts[1] if len(parts) > 1 else ""
    cap = f"<figcaption>{caption}</figcaption>" if caption else ""
    return (
        f'<figure class="video" data-file="assets/video/{name}" style="--r: {mp4_ratio(OUT / "assets" / "video" / name) or 16 / 9:.3f}">'
        f'<video controls preload="metadata" src="{root}assets/video/{name}" '
        f"onerror=\"this.parentNode.classList.add('missing')\"></video>{cap}</figure>"
    )


def lineup(_match):
    scale, gap, pad_top, label_h, pad_side = 2, 44, 30, 54, 30
    tallest = max(h for _, _, h in BOARDS) * scale
    width = sum(w * scale for _, w, _ in BOARDS) + gap * (len(BOARDS) - 1) + 2 * pad_side
    height = pad_top + tallest + label_h
    out = [
        f'<svg class="lineup" viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="Outlines of the four flight computer board sizes, drawn to the same scale">'
    ]
    x = pad_side
    for name, w, h in BOARDS:
        bw, bh = w * scale, h * scale
        y = pad_top + tallest - bh
        cx = x + bw / 2
        out.append(f'<rect class="board" x="{x + 1}" y="{y}" width="{bw - 2}" height="{bh}" rx="5"/>')
        for hx, hy in ((x + 11, y + 10), (x + bw - 11, y + 10), (x + 11, y + bh - 10), (x + bw - 11, y + bh - 10)):
            out.append(f'<circle class="hole" cx="{hx}" cy="{hy}" r="3.5"/>')
        out.append(f'<text class="dim" x="{cx}" y="{y - 9}" text-anchor="middle">{w} &#215; {h} mm</text>')
        out.append(f'<text class="name" x="{cx}" y="{pad_top + tallest + 30}" text-anchor="middle">{name}</text>')
        x += bw + gap
    out.append("</svg>")
    return "\n".join(out)


def build():
    social = "\n".join(f'      <li><a href="{url}">{name}</a></li>' for name, url in SOCIAL)
    urls = []
    for src in sorted(SRC.rglob("*.html")):
        rel = src.relative_to(SRC)
        root = "../" * (len(rel.parts) - 1)  # pages in src/post/ sit one folder down
        text = src.read_text(encoding="utf-8").replace("\r\n", "\n")
        if "\n---\n" not in text:
            raise SystemExit(
                f"src/{rel.as_posix()}: the top of this file needs the title:, description: "
                "and nav: lines, then a line with just --- before the page content."
            )
        head, body = text.split("\n---\n", 1)
        meta = dict(line.split(": ", 1) for line in head.strip().splitlines())
        body = re.sub(r"\{\{img (.+?)\}\}", lambda m: figure(m, root), body)
        body = re.sub(r"\{\{video (.+?)\}\}", lambda m: video(m, root), body)
        body = re.sub(r"\{\{lineup\}\}", lineup, body)
        nav = "\n".join(
            '      <a href="{0}{1}.html"{2}>{3}</a>'.format(
                root, slug, ' aria-current="page"' if meta.get("nav") == slug else "", label
            )
            for slug, label in NAV
        )
        # Address without ".html", matching the old site: /watchpi, /post/june-july-2025, /
        path = rel.with_suffix("").as_posix()
        path = "" if path == "index" else path[: -len("index")] if path.endswith("/index") else path
        canonical = f"{SITE}/{path}"
        hidden = rel.name == "404.html"
        if not hidden:
            urls.append(canonical)
        page = PAGE.format(
            title=html.escape(meta["title"]),
            description=html.escape(meta["description"]),
            nav=nav,
            body=body.strip(),
            social=social,
            root=root,
            canonical=canonical,
            site=SITE,
            robots='\n<meta name="robots" content="noindex">' if hidden else "",
        )
        dest = OUT / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(page, encoding="utf-8")
        print("built", rel)
    sitemap = "".join(f"  <url><loc>{u}</loc></url>\n" for u in urls)
    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + sitemap + "</urlset>\n", encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8")
    print("built sitemap.xml and robots.txt")


if __name__ == "__main__":
    build()
