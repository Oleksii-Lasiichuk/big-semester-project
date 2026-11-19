"""Export posts from a PUBLIC Telegram channel via its web preview (t.me/s/<channel>).

No login or API keys needed. Walks backwards with ?before=<id> until --since.
Output: JSONL, one post per line: channel, post_id, datetime (UTC ISO), text, views, url.

Usage:
    python scripts/tg_export.py kpszsu --since 2026-11-01 --out data/telegram/kpszsu.jsonl
"""
import argparse
import html
import json
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone

UA = "Mozilla/5.0 (research export; university course project)"
MSG_RE = re.compile(r'<div class="tgme_widget_message [^"]*"[^>]*data-post="([^"/]+)/(\d+)"(.*?)(?=<div class="tgme_widget_message_wrap|\Z)', re.S)
TEXT_RE = re.compile(r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>', re.S)
DT_RE = re.compile(r'<time datetime="([^"]+)"')
VIEWS_RE = re.compile(r'<span class="tgme_widget_message_views">([^<]+)</span>')


def clean(fragment: str) -> str:
    fragment = re.sub(r"<br\s*/?>", "\n", fragment)
    fragment = re.sub(r"<[^>]+>", "", fragment)
    return html.unescape(fragment).strip()


def parse_views(v):
    if not v:
        return None
    v = v.strip().upper()
    mult = 1000 if v.endswith("K") else 1_000_000 if v.endswith("M") else 1
    return int(float(v.rstrip("KM")) * mult)


def fetch(channel, before=None, retries=8):
    url = f"https://t.me/s/{channel}" + (f"?before={before}" if before else "")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:  # network blips, 429s
            wait = min(300, 5 * 2 ** attempt)
            print(f"{channel}: {e!r}, retry in {wait}s", file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError(f"giving up on {url}")


def parse(page):
    for ch, pid, body in MSG_RE.findall(page):
        dt = DT_RE.search(body)
        txt = TEXT_RE.search(body)
        views = VIEWS_RE.search(body)
        yield {
            "channel": ch,
            "post_id": int(pid),
            "datetime": dt.group(1) if dt else None,
            "text": clean(txt.group(1)) if txt else "",
            "views": parse_views(views.group(1) if views else None),
            "url": f"https://t.me/{ch}/{pid}",
        }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("channel")
    ap.add_argument("--since", required=True, help="YYYY-MM-DD (UTC)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--delay", type=float, default=1.5, help="seconds between requests (be polite)")
    ap.add_argument("--resume", action="store_true", help="append to --out, continuing from its oldest post")
    a = ap.parse_args()
    since = datetime.fromisoformat(a.since).replace(tzinfo=timezone.utc)

    seen, before, n = set(), None, 0
    if a.resume:
        try:
            with open(a.out, encoding="utf-8") as f:
                seen = {json.loads(l)["post_id"] for l in f if l.strip()}
            before = min(seen) if seen else None
            print(f"resuming {a.channel} before id {before} ({len(seen)} existing)", file=sys.stderr)
        except FileNotFoundError:
            pass
    with open(a.out, "a" if a.resume else "w", encoding="utf-8") as f:
        while True:
            posts = list(parse(fetch(a.channel, before)))
            if not posts:
                break
            oldest = min(p["post_id"] for p in posts)
            stop = False
            for p in posts:
                if p["post_id"] in seen:
                    continue
                seen.add(p["post_id"])
                if p["datetime"] and datetime.fromisoformat(p["datetime"]) < since:
                    stop = True
                    continue
                f.write(json.dumps(p, ensure_ascii=False) + "\n")
                n += 1
            print(f"{a.channel}: {n} posts, oldest id {oldest}", file=sys.stderr)
            if stop or oldest == before or oldest <= 1:
                break
            before = oldest
            time.sleep(a.delay)
    print(f"done: {n} posts -> {a.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
