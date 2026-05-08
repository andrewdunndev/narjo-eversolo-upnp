#!/usr/bin/env python3
"""Scan Navidrome (Subsonic API) for hi-res tracks.

Pages through search3 with an empty query and ranks tracks by sampling
rate / bit depth. Useful for picking targets for the AVTransport
passthrough test.

stdlib only. Auth params come from env to keep them out of argv:

    NAVI_BASE=https://navi.example \\
    NAVI_AUTH='u=<USER>&t=<TOKEN>&s=<SALT>' \\
    python3 find_hires.py
"""

import json
import os
import sys
import urllib.request
import urllib.parse

PAGE = 500
MAX_PAGES = 60


def call(base: str, auth: str, endpoint: str, params: dict) -> dict:
    qs = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items())
    url = f"{base}/rest/{endpoint}?{auth}&v=1.16.1&c=narjo-debug&f=json&{qs}"
    with urllib.request.urlopen(url, timeout=20) as r:
        return json.loads(r.read())


def is_hires(song: dict) -> bool:
    sr = song.get("samplingRate") or 0
    bd = song.get("bitDepth") or 0
    if bd == 1:
        return True
    if sr >= 96000:
        return True
    return False


def rank(song: dict) -> tuple:
    return (song.get("samplingRate") or 0, song.get("bitDepth") or 0, song.get("bitRate") or 0)


def main() -> int:
    base = os.environ["NAVI_BASE"].rstrip("/")
    auth = os.environ["NAVI_AUTH"]

    seen_ids: set[str] = set()
    hires: list[dict] = []
    total_seen = 0

    for page in range(MAX_PAGES):
        offset = page * PAGE
        resp = call(base, auth, "search3", {"query": '""', "songCount": PAGE, "songOffset": offset, "albumCount": 0, "artistCount": 0})
        songs = resp.get("subsonic-response", {}).get("searchResult3", {}).get("song", [])
        if not songs:
            print(f"[scan] page {page}: 0 songs, stopping")
            break
        new = 0
        for s in songs:
            sid = s.get("id")
            if sid in seen_ids:
                continue
            seen_ids.add(sid)
            new += 1
            total_seen += 1
            if is_hires(s):
                hires.append(s)
        print(f"[scan] page {page} offset={offset}: {len(songs)} returned, {new} new, {len(hires)} hires so far")
        if new == 0:
            break

    print(f"\n[scan] scanned {total_seen} unique songs, found {len(hires)} hi-res")

    hires.sort(key=rank, reverse=True)

    print("\n" + "=" * 78)
    print(f"TOP HI-RES TRACKS")
    print("=" * 78)
    for s in hires[:40]:
        sr = s.get("samplingRate") or 0
        bd = s.get("bitDepth") or 0
        br = s.get("bitRate") or 0
        sfx = s.get("suffix") or "?"
        ct = s.get("contentType") or "?"
        kind = "DSD" if bd == 1 else f"{bd}-bit PCM" if bd else "PCM"
        print(f"  {sr:>10}Hz {kind:>12} {br:>5}kbps {sfx:>6} {ct:>16}  id={s.get('id')}")
        print(f"             {s.get('artist','?')} - {s.get('title','?')} ({s.get('album','?')})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
