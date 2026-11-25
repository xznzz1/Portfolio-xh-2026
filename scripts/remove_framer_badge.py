"""Remove the floating Framer badge from the standalone portfolio snapshot."""

import re
from html.parser import HTMLParser
from pathlib import Path

BADGE_ID = "__framer-badge-container"
BADGE_MOUNT = re.compile(
    r'\(function\(\)\{[\w$]+&&[\w$]+\(\(\)=>\{[\w$]+\(document\.getElementById\(`__framer-badge-container`\),.*?\}\)\}\)\(\)',
    re.S,
)


class BadgeParser(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=False)
        self.offsets = [0]
        for line in text.splitlines(keepends=True):
            self.offsets.append(self.offsets[-1] + len(line))
        self.depth = 0
        self.start = None
        self.ranges = []

    def position(self):
        line, column = self.getpos()
        return self.offsets[line - 1] + column

    def handle_starttag(self, tag, attrs):
        if tag != "div":
            return
        if self.depth:
            self.depth += 1
        elif dict(attrs).get("id") == BADGE_ID:
            self.start = self.position()
            self.depth = 1

    def handle_endtag(self, tag):
        if tag == "div" and self.depth:
            self.depth -= 1
            if self.depth == 0:
                self.ranges.append((self.start, self.position() + len("</div>")))


def remove_from_html(text):
    if not re.search(r'<div\b[^>]*\bid=["\']__framer-badge-container["\']', text):
        return text
    parser = BadgeParser(text)
    parser.feed(text)
    if parser.depth or not parser.ranges:
        raise RuntimeError("Could not locate the complete Framer badge container.")
    for start, end in reversed(parser.ranges):
        text = text[:start] + text[end:]
    return text


def remove_from_javascript(text):
    result, count = BADGE_MOUNT.subn("", text)
    if BADGE_ID in text and "document.getElementById(`" + BADGE_ID + "`)" in result:
        raise RuntimeError("Framer badge initialization changed; review the published script.")
    return result


def main():
    root = Path(__file__).resolve().parents[1]
    count = 0
    for file in (root / "site").rglob("*"):
        if file.suffix not in (".html", ".mjs", ".js"):
            continue
        text = file.read_text(encoding="utf-8")
        result = remove_from_html(text) if file.suffix == ".html" else remove_from_javascript(text)
        if result != text:
            file.write_text(result, encoding="utf-8")
            count += 1
    print(f"Removed Framer badge from {count} files", flush=True)
    from build_cloudflare import build
    build()


if __name__ == "__main__":
    main()
