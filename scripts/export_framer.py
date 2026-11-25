"""Archive the published portfolio as a static GitHub Pages website."""

import argparse
import concurrent.futures
import hashlib
import html
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
CACHE = ROOT / ".cache" / "framer-source"
ASSET_HOSTS = {"framerusercontent.com", "fonts.gstatic.com", "app.framerstatic.com"}
ABSOLUTE = re.compile(r'https?://[^\s\"\'<>`\\)]+')
RELATIVE = re.compile(r'(?:\bfrom\s*|\bimport\s*(?:\(\s*)?)[\"\'`]((?:\./|\.\./)[^\"\'`\s]+)[\"\'`]')
CSS_URL = re.compile(r'url\(\s*[\"\']?([^\s\"\')]+)')
CMS_URL = re.compile(r'new URL\(`([^`]+)`,`(https://framerusercontent\.com/modules/[^`]+)`\)\.href\.replace\(`/modules/`,`/cms/`\)')


def cms_reference(match):
    return urllib.parse.urljoin(match.group(2), match.group(1)).replace('/modules/', '/cms/')


def fetch(url):
    cache_path = None
    if urllib.parse.urlsplit(url).hostname in ASSET_HOSTS:
        cache_path = CACHE / "downloads" / asset_path(url)
        if cache_path.exists() and cache_path.with_suffix(cache_path.suffix + ".type").exists():
            return cache_path.read_bytes(), cache_path.with_suffix(cache_path.suffix + ".type").read_text()
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 PortfolioArchive/1.0"})
            with urllib.request.urlopen(request, timeout=60) as response:
                data, content_type = response.read(), response.headers.get("Content-Type", "")
                if cache_path:
                    cache_path.parent.mkdir(parents=True, exist_ok=True)
                    cache_path.write_bytes(data)
                    cache_path.with_suffix(cache_path.suffix + ".type").write_text(content_type)
                return data, content_type
        except (OSError, urllib.error.URLError) as error:
            if attempt == 2:
                raise RuntimeError(f"Download failed for {url}: {error}") from error
            time.sleep(attempt + 1)


def clean_url(url):
    return html.unescape(url).replace("\\u0026", "&").split("#", 1)[0]


def asset_path(url):
    parsed = urllib.parse.urlsplit(url)
    relative = Path("_assets") / parsed.netloc / urllib.parse.unquote(parsed.path.lstrip("/"))
    if parsed.query:
        digest = hashlib.sha256(parsed.query.encode()).hexdigest()[:12]
        relative = relative.with_name(relative.stem + "-" + digest + relative.suffix)
    destination = (SITE / relative).resolve()
    if SITE.resolve() not in destination.parents:
        raise ValueError("Asset path escapes website directory")
    return relative.as_posix()


def references(text, source_url):
    candidates = [m.group(0) for m in ABSOLUTE.finditer(text)]
    javascript = urllib.parse.urlsplit(source_url).path.endswith((".mjs", ".js"))
    if javascript:
        candidates += [m.group(1) for m in RELATIVE.finditer(text)]
        candidates += [cms_reference(m) for m in CMS_URL.finditer(text)]
    else:
        candidates += [m.group(1) for m in CSS_URL.finditer(text)]
    for candidate in candidates:
        if "${" in candidate or candidate.startswith(("data:", "#")):
            continue
        url = clean_url(urllib.parse.urljoin(source_url, candidate))
        parsed = urllib.parse.urlsplit(url)
        suffix = Path(parsed.path).suffix.lower()
        if parsed.hostname in ASSET_HOSTS and suffix in {".mjs", ".js", ".css", ".woff2", ".woff", ".ttf", ".otf", ".jpg", ".jpeg", ".png", ".webp", ".avif", ".gif", ".svg", ".mp4", ".webm", ".json", ".ico", ".pdf", ".framercms"}:
            yield candidate, url


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="https://successful-sandwich-977344.framer.app")
    parser.add_argument("--target", default="https://xznzz1.github.io/Portfolio-xh-2026/")
    args = parser.parse_args()
    source = args.source.rstrip("/")
    target = args.target.rstrip("/")
    base = urllib.parse.urlsplit(target).path + "/"
    CACHE.mkdir(parents=True, exist_ok=True)
    SITE.mkdir(parents=True, exist_ok=True)
    sitemap_data, _ = fetch(source + "/sitemap.xml")
    sitemap = ET.fromstring(sitemap_data)
    urls = [element.text for element in sitemap.iter() if element.tag.endswith("}loc")]
    pages = {}
    pending = set()
    for url in urls:
        data, _ = fetch(url)
        text = data.decode("utf-8")
        pages[url] = text
        route = urllib.parse.urlsplit(url).path.strip("/")
        cached = CACHE / route / "index.html"
        cached.parent.mkdir(parents=True, exist_ok=True)
        cached.write_text(text, encoding="utf-8")
        pending.update(url for _, url in references(text, url))
    print(f"Read {len(pages)} pages; found {len(pending)} initial assets", flush=True)

    assets = {}
    while pending:
        batch = sorted(pending - assets.keys())
        if not batch:
            break
        pending = set()
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
            futures = {pool.submit(fetch, url): url for url in batch}
            for future in concurrent.futures.as_completed(futures):
                url = futures[future]
                data, content_type = future.result()
                is_text = any(value in content_type for value in ("javascript", "text/", "json", "svg")) and not url.endswith('.framercms')
                text = data.decode("utf-8") if is_text else None
                assets[url] = {"data": data, "text": text, "content_type": content_type}
                if text:
                    pending.update(ref for _, ref in references(text, url) if ref not in assets)
        print(f"Downloaded {len(assets)} assets; {len(pending - assets.keys())} new dependencies", flush=True)

    def rewrite(text, url):
        # Use absolute project paths so nested CMS pages resolve every asset.
        text = CMS_URL.sub(lambda m: 'new URL(' + json.dumps(base + asset_path(cms_reference(m))) + ',import.meta.url).href', text)
        replacements = {original: base + asset_path(ref) for original, ref in references(text, url) if ref in assets}
        for original in sorted(replacements, key=len, reverse=True):
            text = text.replace(original, replacements[original])
        if urllib.parse.urlsplit(url).path.endswith((".mjs", ".js")):
            text = text.replace('path:`/`', 'path:`' + base + '`')
            text = text.replace('path:`/work/', 'path:`' + base + 'work/')
            # The editor overlay operates on Framer hosting, outside the static site.
            text = re.sub(r'EditorBar:s===void 0\?void 0:\(\(\)=>\{.*?\}\)\(\),adaptLayoutToTextDirection', 'EditorBar:void 0,adaptLayoutToTextDirection', text, flags=re.S)
        return text.replace(source, target)

    for url, record in assets.items():
        destination = SITE / asset_path(url)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if record["text"] is None:
            destination.write_bytes(record["data"])
        else:
            destination.write_text(rewrite(record["text"], url), encoding="utf-8")

    for url, text in pages.items():
        # Analytics and the editing service are bound to the source Framer site.
        text = re.sub(r'<script\b[^>]*src=[\"\']https://events\.framer\.com/[^>]*>.*?</script>', '', text, flags=re.S)
        text = rewrite(text, url)

        def href(match):
            original = html.unescape(match.group(2))
            if original.startswith(base):
                return match.group(0)
            resolved = urllib.parse.urljoin(url, original)
            parsed = urllib.parse.urlsplit(resolved)
            if parsed.hostname != urllib.parse.urlsplit(source).hostname:
                return match.group(0)
            route = parsed.path.strip("/")
            dest = base + (route + "/" if route else "")
            if parsed.query:
                dest += "?" + parsed.query
            if parsed.fragment:
                dest += "#" + parsed.fragment
            return match.group(1) + html.escape(dest, quote=True) + match.group(3)

        text = re.sub(r'(\bhref\s*=\s*[\"\'])([^\"\']+)([\"\'])', href, text)
        route = urllib.parse.urlsplit(url).path.strip("/")
        destination = SITE / route / "index.html"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(text, encoding="utf-8")

    (SITE / ".nojekyll").touch()
    (SITE / "sitemap.xml").write_text(sitemap_data.decode("utf-8").replace(source, target), encoding="utf-8")
    (SITE / "robots.txt").write_text("User-agent: *\nAllow: /\nSitemap: " + target + "/sitemap.xml\n", encoding="utf-8")
    manifest = {"source": source, "target": target + "/", "pages": urls, "asset_count": len(assets), "downloaded_bytes": sum(len(r["data"]) for r in assets.values()), "assets": {url: asset_path(url) for url in sorted(assets)}}
    (ROOT / "docs" / "export-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: manifest[key] for key in ("asset_count", "downloaded_bytes")}), flush=True)
    from build_cloudflare import build
    build()


if __name__ == "__main__":
    main()
