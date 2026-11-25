"""Prepare the published snapshot for a Cloudflare Pages domain root."""

import json
import shutil
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "site"
OUTPUT = ROOT / "cloudflare-site"
TARGET = "https://portfolio-xh-2026.pages.dev"
TEXT_EXTENSIONS = {".html", ".mjs", ".js", ".css", ".xml", ".txt", ".json", ".svg"}


def build():
    if not (SOURCE / "index.html").is_file():
        raise RuntimeError("Missing site/index.html; export the portfolio first.")
    manifest = json.loads((ROOT / "docs" / "export-manifest.json").read_text(encoding="utf-8"))
    previous_target = manifest["target"].rstrip("/")
    previous_base = urlsplit(previous_target).path.rstrip("/") + "/"
    count = 0
    for source in sorted(SOURCE.rglob("*")):
        if not source.is_file():
            continue
        destination = OUTPUT / source.relative_to(SOURCE)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.suffix.lower() in TEXT_EXTENSIONS:
            text = source.read_text(encoding="utf-8").replace(previous_target, TARGET)
            if previous_base != "/":
                text = text.replace(previous_base, "/")
            destination.write_text(text, encoding="utf-8")
        else:
            shutil.copy2(source, destination)
        count += 1
    print(f"Cloudflare Pages: {count} files in {OUTPUT.name}/", flush=True)


if __name__ == "__main__":
    build()
