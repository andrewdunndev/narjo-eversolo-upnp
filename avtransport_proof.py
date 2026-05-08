#!/usr/bin/env python3
"""AVTransport proof-of-chain.

Drives a UPnP MediaRenderer end-to-end: SetAVTransportURI -> Play -> poll
GetPositionInfo / GetTransportInfo. Confirms the renderer side is sound,
independent of any iOS client.

stdlib only. The stream and cover-art URLs are passed in fully-formed (with
Subsonic auth params already attached), so this script doesn't need to know
anything about Navidrome auth.

Usage:

    python3 avtransport_proof.py \\
        --control-url 'http://192.0.2.10:1054/AVTransport/<UDN>/control.xml' \\
        --stream-url  'http://navi.example/rest/stream?id=<ID>&u=<U>&t=<T>&s=<S>&v=1.16.1&c=narjo-debug&format=raw' \\
        --art-url     'http://navi.example/rest/getCoverArt?id=<ID>&u=<U>&t=<T>&s=<S>&v=1.16.1&c=narjo-debug' \\
        --title 'Song Title' --artist 'Artist' --album 'Album' \\
        --mime audio/flac
"""

import argparse
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape as xml_escape

AVT_NS = "urn:schemas-upnp-org:service:AVTransport:1"


def didl_lite(stream_url: str, art_url: str, title: str, artist: str, album: str, mime: str) -> str:
    return (
        '<DIDL-Lite xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" '
        'xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/">'
        '<item id="narjo-debug-1" parentID="0" restricted="1">'
        f"<dc:title>{xml_escape(title)}</dc:title>"
        f"<dc:creator>{xml_escape(artist)}</dc:creator>"
        f"<upnp:album>{xml_escape(album)}</upnp:album>"
        f"<upnp:albumArtURI>{xml_escape(art_url)}</upnp:albumArtURI>"
        "<upnp:class>object.item.audioItem.musicTrack</upnp:class>"
        f'<res protocolInfo="http-get:*:{xml_escape(mime)}:*">{xml_escape(stream_url)}</res>'
        "</item>"
        "</DIDL-Lite>"
    )


def soap_envelope(action: str, args_xml: str) -> bytes:
    body = (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" '
        's:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">'
        "<s:Body>"
        f'<u:{action} xmlns:u="{AVT_NS}">'
        f"{args_xml}"
        f"</u:{action}>"
        "</s:Body>"
        "</s:Envelope>"
    )
    return body.encode("utf-8")


def soap_call(control_url: str, action: str, args_xml: str, timeout: float = 10.0) -> tuple[int, bytes]:
    body = soap_envelope(action, args_xml)
    req = urllib.request.Request(
        control_url,
        data=body,
        method="POST",
        headers={
            "Content-Type": 'text/xml; charset="utf-8"',
            "SOAPAction": f'"{AVT_NS}#{action}"',
            "User-Agent": "narjo-eversolo-upnp/0.1",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def parse_response(action: str, body: bytes) -> dict:
    """Pull text fields out of the <u:<action>Response> element."""
    try:
        root = ET.fromstring(body)
    except ET.ParseError as e:
        return {"_parse_error": str(e), "_raw": body.decode("utf-8", "replace")}
    out: dict[str, str] = {}
    for elem in root.iter():
        tag = elem.tag.split("}", 1)[1] if "}" in elem.tag else elem.tag
        if tag.endswith("Response") or tag in {"Body", "Envelope", "Fault"}:
            continue
        if elem.text and elem.text.strip():
            out[tag] = elem.text.strip()
    return out


def log_call(label: str, action: str, status: int, body: bytes, parsed: dict) -> None:
    print(f"\n--- {label}: {action} -> HTTP {status} ---")
    if "_parse_error" in parsed:
        print(f"  PARSE ERROR: {parsed['_parse_error']}")
        print(f"  RAW: {parsed.get('_raw', '')[:500]}")
        return
    if not parsed:
        print(f"  (no fields in response, raw {len(body)} bytes)")
        return
    for k, v in parsed.items():
        if len(v) > 200:
            v = v[:200] + " ...[truncated]"
        print(f"  {k}: {v}")


def main() -> int:
    p = argparse.ArgumentParser(description="UPnP AVTransport proof-of-chain")
    p.add_argument("--control-url", required=True)
    p.add_argument("--stream-url", required=True)
    p.add_argument("--art-url", required=True)
    p.add_argument("--title", default="Narjo Debug Track")
    p.add_argument("--artist", default="Test Artist")
    p.add_argument("--album", default="Test Album")
    p.add_argument("--mime", default="audio/flac")
    p.add_argument("--poll-secs", type=int, default=15)
    p.add_argument("--poll-interval", type=float, default=2.0)
    args = p.parse_args()

    print(f"[avt] control: {args.control_url}")
    print(f"[avt] stream:  {args.stream_url}")
    print(f"[avt] art:     {args.art_url}")
    print(f"[avt] track:   {args.artist} - {args.title} ({args.album}) [{args.mime}]")

    metadata = didl_lite(args.stream_url, args.art_url, args.title, args.artist, args.album, args.mime)
    set_args = (
        "<InstanceID>0</InstanceID>"
        f"<CurrentURI>{xml_escape(args.stream_url)}</CurrentURI>"
        f"<CurrentURIMetaData>{xml_escape(metadata)}</CurrentURIMetaData>"
    )
    status, body = soap_call(args.control_url, "SetAVTransportURI", set_args)
    parsed = parse_response("SetAVTransportURI", body)
    log_call("step 1", "SetAVTransportURI", status, body, parsed)
    if status >= 400:
        print(f"[avt] SetAVTransportURI failed (HTTP {status}); aborting.")
        return 1

    play_args = "<InstanceID>0</InstanceID><Speed>1</Speed>"
    status, body = soap_call(args.control_url, "Play", play_args)
    parsed = parse_response("Play", body)
    log_call("step 2", "Play", status, body, parsed)
    if status >= 400:
        print(f"[avt] Play failed (HTTP {status}); aborting.")
        return 1

    print(f"\n[avt] polling for {args.poll_secs}s every {args.poll_interval}s ...")
    deadline = time.time() + args.poll_secs
    tick = 0
    while time.time() < deadline:
        tick += 1
        status, body = soap_call(args.control_url, "GetTransportInfo", "<InstanceID>0</InstanceID>")
        info = parse_response("GetTransportInfo", body)
        log_call(f"poll {tick} transport", "GetTransportInfo", status, body, info)

        status, body = soap_call(args.control_url, "GetPositionInfo", "<InstanceID>0</InstanceID>")
        pos = parse_response("GetPositionInfo", body)
        log_call(f"poll {tick} position", "GetPositionInfo", status, body, pos)

        time.sleep(args.poll_interval)

    print("\n[avt] done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
