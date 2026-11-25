"""Adapt Framer collection reads to ordinary static file hosting."""

import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

START = "async function C(e,t){let n=Ge(t),r=[],i=0;"
END = "}function w(e,t)"
MARKER = "__portfolioCmsFileCache"
REPLACEMENT = r'''var __portfolioCmsFileCache=new Map;
async function C(e,t){
    let url=new URL(e);
    url.searchParams.delete("range");
    let key=url.href;
    let pending=__portfolioCmsFileCache.get(key);
    if(!pending){
        pending=V(url).then(async response=>{
            if(response.status!==200)throw Error(`Request failed: ${response.status} ${response.statusText}`);
            return new Uint8Array(await response.arrayBuffer());
        });
        __portfolioCmsFileCache.set(key,pending);
        pending.catch(()=>{
            if(__portfolioCmsFileCache.get(key)===pending)__portfolioCmsFileCache.delete(key);
        });
    }
    let bytes=await pending;
    return t.map(range=>{
        if(range.from<0||range.to<range.from||range.to>bytes.length)throw Error("Collection range is outside the static data file");
        return bytes.subarray(range.from,range.to);
    });
}'''

LOCAL_VALUES = r'''
var __portfolioCmsLocalAssets=__IMAGE_MAP__;
function __portfolioCmsLocalValue(value){
    if(typeof value==="string")return __portfolioCmsLocalAssets[value.split(/[?#]/,1)[0]]||value;
    if(Array.isArray(value))return value.map(__portfolioCmsLocalValue);
    if(value&&typeof value==="object")for(let key of Object.keys(value))value[key]=__portfolioCmsLocalValue(value[key]);
    return value;
}
'''


def local_image_map(asset_paths, base):
    selected = {}
    for url, path in asset_paths.items():
        parsed = urlsplit(url)
        if parsed.hostname != "framerusercontent.com" or not parsed.path.startswith("/images/"):
            continue
        scale = parse_qs(parsed.query).get("scale-down-to", [None])[0]
        score = (scale == "2048", scale is None, int(scale or 0))
        key = parsed.scheme + "://" + parsed.netloc + parsed.path
        if key not in selected or score > selected[key][0]:
            selected[key] = (score, base + path)
    return {key: value[1] for key, value in sorted(selected.items())}


def adapt_javascript(text, asset_paths=None, base=None):
    gallery_exit = 'function I(e){a!==void 0&&(document.referrer&&new URL(document.referrer).origin===a.location.origin&&a.history.length>1?a.history.back():a.location.href=e)}'
    gallery_navigation = 'function I(e){if(a===void 0)return;let __portfolioBackLink=Array.from(document.querySelectorAll("a[href]")).find(link=>/Back to work/i.test(link.textContent));if(__portfolioBackLink){__portfolioBackLink.click();return}document.referrer&&new URL(document.referrer).origin===a.location.origin&&a.history.length>1?a.history.back():a.location.href=e}'
    text = text.replace(gallery_exit, gallery_navigation)
    if "__portfolioCmsLocalAssets" in text:
        return text
    start = text.find(START)
    if start < 0:
        start = text.find("var " + MARKER + "=new Map;")
        if start < 0:
            return text
        end = text.find("function w(e,t)", start)
    else:
        end = text.find(END, start)
        if end >= 0:
            end += 1
    if end < 0:
        raise RuntimeError("The Framer collection reader changed; review the static hosting adapter.")
    if asset_paths is None:
        root = Path(__file__).resolve().parents[1]
        manifest = json.loads((root / "docs" / "export-manifest.json").read_text(encoding="utf-8"))
        asset_paths = manifest["assets"]
        base = urlsplit(manifest["target"]).path.rstrip("/") + "/"
    images = json.dumps(local_image_map(asset_paths, base), separators=(",", ":"))
    text = text[:start] + REPLACEMENT + LOCAL_VALUES.replace("__IMAGE_MAP__", images) + text[end:]
    old = "t[n]=D.read(e)}return t}"
    if old not in text:
        raise RuntimeError("The Framer collection value decoder changed; review image localization.")
    return text.replace(old, "t[n]=__portfolioCmsLocalValue(D.read(e))}return t}", 1)


def main():
    root = Path(__file__).resolve().parents[1]
    count = 0
    for file in (root / "site" / "_assets").rglob("*.mjs"):
        text = file.read_text(encoding="utf-8")
        result = adapt_javascript(text)
        if result != text:
            file.write_text(result, encoding="utf-8")
            count += 1
    print(f"Adapted {count} collection reader modules", flush=True)
    from build_cloudflare import build
    build()


if __name__ == "__main__":
    main()
