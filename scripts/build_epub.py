#!/usr/bin/env python3
"""Build a single EPUB 3 from the per-chapter Readme.md files in this repo.

Each top-level "NN. Title" directory becomes one chapter. Images referenced as
./images/foo.png are copied into the book. A unified TOC (chapters + their
top-level sections) is generated as both EPUB 3 nav and EPUB 2 NCX.

Requires: pip install markdown

Usage: python3 build_epub.py [-o output.epub]
"""

import argparse
import html
import re
import sys
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree

try:
    import markdown
except ImportError:
    sys.exit("Missing dependency. Run: pip install markdown")

ROOT = Path(__file__).resolve().parent
CHAPTER_DIR_RE = re.compile(r"^(\d{2})\.\s*(.+)$")
BOOK_TITLE = "System Design Interview - Notes"
BOOK_AUTHOR = "Victor Peinado"
BOOK_LANGUAGE = "en"

CSS = """\
html, body { margin: 0; padding: 0; }
body {
  font-family: Georgia, "Times New Roman", serif;
  line-height: 1.5;
  padding: 0 0.6em;
  widows: 2;
  orphans: 2;
}
h1, h2, h3, h4, h5, h6 {
  font-family: Helvetica, Arial, sans-serif;
  line-height: 1.25;
  page-break-after: avoid;
  break-after: avoid;
}
h1 {
  font-size: 1.7em;
  margin: 1em 0 0.8em;
  padding-bottom: 0.3em;
  border-bottom: 3px solid #444;
}
h2 { font-size: 1.3em; margin: 1.6em 0 0.5em; }
h3 { font-size: 1.1em; margin: 1.3em 0 0.4em; }
h4 { font-size: 1em; margin: 1.2em 0 0.3em; font-style: italic; }
p { margin: 0.6em 0; text-align: left; }
ul, ol { margin: 0.6em 0; padding-left: 1.4em; }
li { margin: 0.25em 0; }
a { color: #17418f; text-decoration: none; }
hr {
  border: 0;
  border-top: 1px solid #bbb;
  margin: 1.6em auto;
  width: 60%;
}
code, kbd, samp {
  font-family: "DejaVu Sans Mono", "Courier New", monospace;
  font-size: 0.85em;
  background: #f2f2f2;
  padding: 0.05em 0.25em;
  border-radius: 3px;
}
pre {
  font-family: "DejaVu Sans Mono", "Courier New", monospace;
  font-size: 0.8em;
  line-height: 1.35;
  background: #f5f5f5;
  border-left: 3px solid #ccc;
  padding: 0.6em 0.8em;
  margin: 0.8em 0;
  overflow-x: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
}
pre code { background: transparent; padding: 0; font-size: 1em; }
blockquote {
  margin: 0.8em 0 0.8em 1em;
  padding-left: 0.8em;
  border-left: 3px solid #ccc;
  font-style: italic;
}
table {
  border-collapse: collapse;
  margin: 1em auto;
  font-size: 0.85em;
  font-family: Helvetica, Arial, sans-serif;
}
th, td { border: 1px solid #bbb; padding: 0.35em 0.6em; text-align: left; }
th { background: #eee; }
/* Figures: images are laid out centred and never overflow the page. */
img {
  max-width: 100%;
  height: auto;
  display: block;
  margin: 0.4em auto;
}
div.figure, div[style] { margin: 1em 0 !important; text-align: center; }
/* Title page */
.titlepage { text-align: center; margin-top: 25%; }
.titlepage h1 { border: 0; font-size: 2.2em; margin-bottom: 0.2em; }
.titlepage .subtitle { font-size: 1.1em; color: #555; font-style: italic; }
.titlepage .author { margin-top: 2.5em; font-size: 1.1em; }
/* Table of contents */
nav#toc ol { list-style: none; padding-left: 0; margin: 0; }
nav#toc > ol > li { margin: 0.7em 0; font-weight: bold; }
nav#toc ol ol { padding-left: 1.2em; margin: 0.25em 0; }
nav#toc ol ol li { font-weight: normal; font-size: 0.9em; margin: 0.15em 0; }
"""

# Named entities that are legal in HTML but undefined in XHTML/XML.
ENTITY_FIX = {
    "&nbsp;": "&#160;",
    "&mdash;": "&#8212;",
    "&ndash;": "&#8211;",
    "&hellip;": "&#8230;",
    "&rarr;": "&#8594;",
    "&larr;": "&#8592;",
    "&times;": "&#215;",
    "&copy;": "&#169;",
    "&reg;": "&#174;",
    "&trade;": "&#8482;",
    "&deg;": "&#176;",
    "&mu;": "&#956;",
    "&bull;": "&#8226;",
    "&laquo;": "&#171;",
    "&raquo;": "&#187;",
    "&ldquo;": "&#8220;",
    "&rdquo;": "&#8221;",
    "&lsquo;": "&#8216;",
    "&rsquo;": "&#8217;",
}

VOID_ELEMENTS = ("img", "br", "hr", "input", "meta", "link", "col", "area", "source")

def find_chapters():
    """Return [(number, dir_path, readme_path)] for the NN. <Title> directories."""
    chapters = []
    for entry in sorted(ROOT.iterdir()):
        if not entry.is_dir():
            continue
        match = CHAPTER_DIR_RE.match(entry.name)
        if not match:
            continue
        readme = next(
            (p for p in sorted(entry.iterdir()) if p.name.lower() == "readme.md"), None
        )
        if readme is None:
            print(f"  ! skipping {entry.name}: no Readme.md", file=sys.stderr)
            continue
        chapters.append((int(match.group(1)), entry, readme))
    return chapters


def close_void_tags(text):
    """Make void elements XHTML-self-closing: <img ...> -> <img ... />."""
    pattern = re.compile(
        r"<(%s)\b((?:[^<>\"']|\"[^\"]*\"|'[^']*')*?)\s*/?>" % "|".join(VOID_ELEMENTS),
        re.IGNORECASE,
    )
    return pattern.sub(lambda m: f"<{m.group(1)}{m.group(2).rstrip()} />", text)


def sanitize_entities(text):
    for name, numeric in ENTITY_FIX.items():
        text = text.replace(name, numeric)
    # Escape stray ampersands that are not already part of an entity reference.
    return re.sub(r"&(?!#\d+;|#x[0-9a-fA-F]+;|amp;|lt;|gt;|quot;|apos;)", "&amp;", text)


def rewrite_image_paths(text, chapter_id):
    """./images/foo.png (as authored) -> ../images/<chapter_id>/foo.png (in book)."""
    def repl(match):
        quote, path = match.group(2), match.group(3)
        name = Path(re.sub(r"^\./", "", path).replace("//", "/")).name
        return f"{match.group(1)}={quote}../images/{chapter_id}/{name}{quote}"

    return re.sub(r"\b(src|href)=(['\"])(\./images/[^'\"]+)\2", repl, text)


def convert_image_sizes(text):
    """Turn width="600" into a CSS width the reader can still shrink.

    The authored pixel width is the intended display size, so it is kept as an
    inline width; the stylesheet's img { max-width: 100% } then caps it on
    narrow screens. height attributes are dropped so nothing gets distorted.
    """
    def repl(match):
        tag = match.group(0)
        width = re.search(r"\bwidth=(['\"]?)(\d+)\1", tag)
        tag = re.sub(r"\s+(width|height)=(['\"])[^'\"]*\2", "", tag)
        tag = re.sub(r"\s+(width|height)=\d+", "", tag)
        if not width:
            return tag
        rule = f"width:{width.group(2)}px"
        style = re.search(r"\sstyle=(['\"])(.*?)\1", tag)
        if style:
            # Authored margins were manual indentation; the stylesheet centres.
            kept = [
                decl for decl in style.group(2).split(";")
                if decl.strip() and not decl.strip().lower().startswith("margin")
            ]
            merged = "; ".join([d.strip() for d in kept] + [rule])
            return tag[: style.start()] + f' style="{merged}"' + tag[style.end() :]
        return re.sub(r"\s*/?>$", f' style="{rule}" />', tag)

    return re.sub(r"<img\b[^<>]*?/?>", repl, text)


FENCE_RE = re.compile(r"^(?P<fence>```+|~~~+).*$", re.MULTILINE)
# A wrapper whose entire content is images: the sole purpose is indenting or
# centring the figure, which the stylesheet already does.
IMG_WRAPPER_RE = re.compile(
    r"<(div|p)\b[^>]*>((?:\s|<img\b[^<>]*?/?>)*?)</\1\s*>", re.IGNORECASE
)
ALIGN_RE = re.compile(r'\s+align=(["\'])(center|left|right|justify)\1', re.IGNORECASE)
# A lone HTML line (usually a figure) directly above "---" gets read as a setext
# heading underline; the rule is meant as a separator, so force a blank line.
# Only HTML lines are touched, to leave genuine setext headings alone.
SETEXT_TRAP_RE = re.compile(
    r"^([ \t]*<[^\n]*>[ \t]*)\n(-{3,}[ \t]*)$", re.MULTILINE
)


def split_code_fences(text):
    """Yield (is_code, chunk) so transforms can skip fenced code blocks."""
    pos, in_code, fence = 0, False, None
    for m in FENCE_RE.finditer(text):
        marker = m.group("fence")
        if not in_code:
            yield False, text[pos : m.start()]
            pos, in_code, fence = m.start(), True, marker[0] * 3
        elif marker.startswith(fence) and not m.group(0)[len(marker) :].strip():
            yield True, text[pos : m.end()]
            pos, in_code, fence = m.end(), False, None
    yield in_code, text[pos:]


def preprocess_markdown(text):
    """Flatten presentational figure wrappers before markdown conversion.

    Sources wrap images in <div style="margin-left:3rem"> / <p align="center">.
    When those sit inside a list item, markdown emits <p><div>...</div></p>,
    which is invalid XHTML. Images are inline and valid anywhere, and the
    stylesheet handles centring, so the wrappers are dropped. Fenced code
    blocks are left untouched: chapter 18 quotes JSON containing a <div>.
    """
    out = []
    for is_code, chunk in split_code_fences(text):
        if not is_code:
            previous = None
            while previous != chunk:  # repeat to collapse nested wrappers
                previous = chunk
                chunk = IMG_WRAPPER_RE.sub(
                    lambda m: "\n" + " ".join(m.group(2).split()) + "\n", chunk
                )
            chunk = ALIGN_RE.sub("", chunk)
            chunk = SETEXT_TRAP_RE.sub(r"\1\n\n\2", chunk)
        out.append(chunk)
    return "".join(out)


def rewrite_chapter_links(text, chapter_by_number):
    """Point links at sibling chapter directories to that chapter's XHTML."""
    def repl(match):
        prefix, quote, target = match.groups()
        decoded = re.sub(r"%20", " ", target).strip("./")
        num = re.match(r"(?:\.\./)*(?:chapter)?\s*(\d{1,2})", decoded, re.IGNORECASE)
        if num and int(num.group(1)) in chapter_by_number:
            return f'{prefix}={quote}{chapter_by_number[int(num.group(1))]}.xhtml{quote}'
        return match.group(0)

    return re.sub(r"\b(href)=(['\"])(\.\./[^'\"]+)\2", repl, text)


def build_chapter(number, directory, readme):
    """Render one chapter's markdown to XHTML; return its metadata dict."""
    chapter_id = f"ch{number:02d}"
    md = markdown.Markdown(
        extensions=["extra", "sane_lists", "toc", "admonition"],
        extension_configs={"toc": {"toc_depth": "2-3"}},
    )
    body = md.convert(preprocess_markdown(readme.read_text(encoding="utf-8")))

    # The first <h1> is the chapter title; lift it out so the TOC can use it and
    # so we can give it a stable anchor for the NCX/nav entry.
    title_match = re.search(r"<h1[^>]*>(.*?)</h1>", body, re.DOTALL)
    if title_match:
        title = re.sub(r"<[^>]+>", "", title_match.group(1)).strip()
        title = html.unescape(title)
        body = body[: title_match.start()] + body[title_match.end() :]
    else:
        title = CHAPTER_DIR_RE.match(directory.name).group(2).strip()
        print(f"  ! {directory.name}: no H1 found, using directory name", file=sys.stderr)

    body = rewrite_image_paths(body, chapter_id)
    body = convert_image_sizes(body)
    body = close_void_tags(body)
    body = sanitize_entities(body)

    # Only images actually referenced get bundled; the repo holds a few strays.
    used_images = {
        Path(src).name
        for src in re.findall(r'<img\b[^>]*?\bsrc="([^"]+)"', body)
    }

    # Section entries for the unified TOC (top-level ## headings only).
    sections = [
        {"id": tok["id"], "title": html.unescape(re.sub(r"<[^>]+>", "", tok["name"]))}
        for tok in md.toc_tokens
        if tok["level"] == 2
    ]

    xhtml = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="{BOOK_LANGUAGE}" xml:lang="{BOOK_LANGUAGE}">
<head>
  <meta charset="utf-8" />
  <title>{html.escape(title)}</title>
  <link rel="stylesheet" type="text/css" href="../style.css" />
</head>
<body epub:type="bodymatter">
  <section epub:type="chapter" id="{chapter_id}">
    <h1 id="{chapter_id}-title">{html.escape(title)}</h1>
{body}
  </section>
</body>
</html>
"""
    return {
        "number": number,
        "id": chapter_id,
        "title": title,
        "href": f"text/{chapter_id}.xhtml",
        "xhtml": xhtml,
        "sections": sections,
        "images_dir": directory / "images",
        "used_images": used_images,
    }


def build_titlepage():
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="{BOOK_LANGUAGE}" xml:lang="{BOOK_LANGUAGE}">
<head>
  <meta charset="utf-8" />
  <title>{html.escape(BOOK_TITLE)}</title>
  <link rel="stylesheet" type="text/css" href="../style.css" />
</head>
<body epub:type="frontmatter">
  <section epub:type="titlepage" class="titlepage">
    <h1>System Design Interview</h1>
    <p class="subtitle">Notes on An Insider's Guide, Volumes 1 &amp; 2</p>
    <p class="author">{html.escape(BOOK_AUTHOR)}</p>
  </section>
</body>
</html>
"""


def build_nav(chapters):
    """EPUB 3 navigation document: the unified, two-level table of contents."""
    items = []
    for ch in chapters:
        subitems = "".join(
            f'\n          <li><a href="{ch["href"]}#{s["id"]}">{html.escape(s["title"])}</a></li>'
            for s in ch["sections"]
        )
        nested = f"\n        <ol>{subitems}\n        </ol>\n      " if subitems else ""
        items.append(
            f'      <li>\n        <a href="{ch["href"]}">'
            f'{html.escape(ch["title"])}</a>{nested}</li>'
        )
    entries = "\n".join(items)
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="{BOOK_LANGUAGE}" xml:lang="{BOOK_LANGUAGE}">
<head>
  <meta charset="utf-8" />
  <title>Table of Contents</title>
  <link rel="stylesheet" type="text/css" href="style.css" />
</head>
<body>
  <nav epub:type="toc" id="toc" role="doc-toc">
    <h1>Table of Contents</h1>
    <ol>
{entries}
    </ol>
  </nav>
  <nav epub:type="landmarks" id="landmarks" hidden="hidden">
    <ol>
      <li><a epub:type="titlepage" href="text/titlepage.xhtml">Title Page</a></li>
      <li><a epub:type="toc" href="nav.xhtml">Table of Contents</a></li>
      <li><a epub:type="bodymatter" href="{chapters[0]["href"]}">Start of Content</a></li>
    </ol>
  </nav>
</body>
</html>
"""


def build_ncx(chapters, book_uid):
    """EPUB 2 NCX, kept for readers that ignore the EPUB 3 nav document."""
    points, order = [], 1
    for ch in chapters:
        subpoints = []
        for s in ch["sections"]:
            order += 1
            # Section slugs repeat across chapters ("step-1-..."), so the NCX id
            # is namespaced by chapter to stay document-unique.
            subpoints.append(
                f'      <navPoint id="nav-{ch["id"]}-{s["id"]}" playOrder="{order}">\n'
                f'        <navLabel><text>{html.escape(s["title"])}</text></navLabel>\n'
                f'        <content src="{ch["href"]}#{s["id"]}" />\n'
                f"      </navPoint>"
            )
        nested = ("\n" + "\n".join(subpoints)) if subpoints else ""
        points.append(
            f'    <navPoint id="nav-{ch["id"]}" playOrder="{order - len(subpoints)}">\n'
            f'      <navLabel><text>{html.escape(ch["title"])}</text></navLabel>\n'
            f'      <content src="{ch["href"]}" />{nested}\n'
            f"    </navPoint>"
        )
        order += 1
    body = "\n".join(points)
    return f"""<?xml version="1.0" encoding="utf-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head>
    <meta name="dtb:uid" content="urn:uuid:{book_uid}" />
    <meta name="dtb:depth" content="2" />
    <meta name="dtb:totalPageCount" content="0" />
    <meta name="dtb:maxPageNumber" content="0" />
  </head>
  <docTitle><text>{html.escape(BOOK_TITLE)}</text></docTitle>
  <docAuthor><text>{html.escape(BOOK_AUTHOR)}</text></docAuthor>
  <navMap>
{body}
  </navMap>
</ncx>
"""


MEDIA_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
    ".webp": "image/webp",
}


def build_opf(chapters, images, book_uid):
    manifest = [
        '    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav" />',
        '    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml" />',
        '    <item id="css" href="style.css" media-type="text/css" />',
        '    <item id="titlepage" href="text/titlepage.xhtml" media-type="application/xhtml+xml" />',
    ]
    spine = [
        '    <itemref idref="titlepage" />',
        '    <itemref idref="nav" />',
    ]
    for ch in chapters:
        manifest.append(
            f'    <item id="{ch["id"]}" href="{ch["href"]}" media-type="application/xhtml+xml" />'
        )
        spine.append(f'    <itemref idref="{ch["id"]}" />')
    for idx, (href, _src) in enumerate(images):
        media = MEDIA_TYPES.get(Path(href).suffix.lower(), "image/png")
        manifest.append(f'    <item id="img{idx}" href="{href}" media-type="{media}" />')

    modified = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="book-id" xml:lang="{BOOK_LANGUAGE}">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="book-id">urn:uuid:{book_uid}</dc:identifier>
    <dc:title>{html.escape(BOOK_TITLE)}</dc:title>
    <dc:creator id="creator">{html.escape(BOOK_AUTHOR)}</dc:creator>
    <dc:language>{BOOK_LANGUAGE}</dc:language>
    <dc:date>{modified}</dc:date>
    <dc:description>Notes on System Design Interview - An Insider's Guide (Vol 1 and 2) by Alex Xu.</dc:description>
    <dc:subject>System Design</dc:subject>
    <dc:subject>Software Architecture</dc:subject>
    <meta property="dcterms:modified">{modified}</meta>
  </metadata>
  <manifest>
{chr(10).join(manifest)}
  </manifest>
  <spine toc="ncx">
{chr(10).join(spine)}
  </spine>
</package>
"""


CONTAINER_XML = """<?xml version="1.0" encoding="utf-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml" />
  </rootfiles>
</container>
"""


def validate_xml(name, text):
    try:
        ElementTree.fromstring(re.sub(r"<!DOCTYPE[^>]*>", "", text))
        return True
    except ElementTree.ParseError as exc:
        print(f"  ! {name}: not well-formed XML: {exc}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-o", "--output", default=str(ROOT / "system-design-notes.epub"),
        help="output .epub path (default: system-design-notes.epub)",
    )
    args = parser.parse_args()

    found = find_chapters()
    if not found:
        sys.exit("No 'NN. Title' chapter directories found.")
    print(f"Found {len(found)} chapters.")

    book_uid = str(uuid.uuid5(uuid.NAMESPACE_URL, "https://github.com/system-design-notes"))
    chapters, images, ok = [], [], True

    for number, directory, readme in found:
        ch = build_chapter(number, directory, readme)
        ok &= validate_xml(ch["href"], ch["xhtml"])
        chapters.append(ch)
        if ch["images_dir"].is_dir():
            for name in sorted(ch["used_images"]):
                img = ch["images_dir"] / name
                if img.is_file():
                    images.append((f"images/{ch['id']}/{name}", img))
                else:
                    print(f"  ! {ch['id']}: missing image {name}", file=sys.stderr)
                    ok = False
        print(
            f"  {ch['id']}  {ch['title']}  "
            f"({len(ch['sections'])} sections, {len(ch['used_images'])} images)"
        )

    # Cross-chapter links can only be resolved once every chapter is known.
    chapter_by_number = {ch["number"]: ch["id"] for ch in chapters}
    for ch in chapters:
        ch["xhtml"] = rewrite_chapter_links(ch["xhtml"], chapter_by_number)

    titlepage = build_titlepage()
    nav = build_nav(chapters)
    ncx = build_ncx(chapters, book_uid)
    opf = build_opf(chapters, images, book_uid)
    for name, doc in [
        ("titlepage.xhtml", titlepage), ("nav.xhtml", nav),
        ("toc.ncx", ncx), ("content.opf", opf),
    ]:
        ok &= validate_xml(name, doc)
    if not ok:
        sys.exit("Aborting: generated XML is not well-formed (see errors above).")

    out = Path(args.output)
    if out.exists():
        out.unlink()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        # The mimetype entry must come first and be stored uncompressed.
        zf.writestr(
            zipfile.ZipInfo("mimetype"), "application/epub+zip",
            compress_type=zipfile.ZIP_STORED,
        )
        zf.writestr("META-INF/container.xml", CONTAINER_XML)
        zf.writestr("OEBPS/content.opf", opf)
        zf.writestr("OEBPS/nav.xhtml", nav)
        zf.writestr("OEBPS/toc.ncx", ncx)
        zf.writestr("OEBPS/style.css", CSS)
        zf.writestr("OEBPS/text/titlepage.xhtml", titlepage)
        for ch in chapters:
            zf.writestr(f"OEBPS/{ch['href']}", ch["xhtml"])
        for href, src in images:
            zf.write(src, f"OEBPS/{href}")

    size_mb = out.stat().st_size / 1024 / 1024
    print(
        f"\nWrote {out} ({size_mb:.1f} MB): "
        f"{len(chapters)} chapters, {len(images)} images, "
        f"{sum(len(c['sections']) for c in chapters)} TOC sub-entries."
    )


if __name__ == "__main__":
    main()
