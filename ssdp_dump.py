#!/usr/bin/env python3
"""SSDP M-SEARCH multicast dump.

Sends ssdp:discover for ssdp:all plus MediaRenderer / AVTransport, captures
every response, prints headers grouped by USN. The output is the comparison
point: what does the LAN actually advertise to a UPnP control point?

stdlib only. Pipe stdout to a file to share with the Narjo dev:

    python3 ssdp_dump.py | tee ssdp_dump.txt
"""

import socket
import sys
import time
from collections import defaultdict

MCAST_GRP = "239.255.255.250"
MCAST_PORT = 1900
LISTEN_SECS = 8
MX = 3

SEARCH_TARGETS = [
    "ssdp:all",
    "upnp:rootdevice",
    "urn:schemas-upnp-org:device:MediaRenderer:1",
    "urn:schemas-upnp-org:service:AVTransport:1",
]


def msearch_payload(st: str) -> bytes:
    return (
        f"M-SEARCH * HTTP/1.1\r\n"
        f"HOST: {MCAST_GRP}:{MCAST_PORT}\r\n"
        f'MAN: "ssdp:discover"\r\n'
        f"MX: {MX}\r\n"
        f"ST: {st}\r\n"
        f"\r\n"
    ).encode("ascii")


def parse_response(data: bytes) -> dict:
    text = data.decode("utf-8", errors="replace")
    headers: dict[str, str] = {}
    for line in text.split("\r\n")[1:]:
        if ":" in line:
            k, _, v = line.partition(":")
            headers[k.strip().upper()] = v.strip()
    return headers


def main() -> int:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", 0))
    sock.settimeout(0.5)

    print(f"[ssdp] M-SEARCH -> {MCAST_GRP}:{MCAST_PORT}, MX={MX}")
    for st in SEARCH_TARGETS:
        sock.sendto(msearch_payload(st), (MCAST_GRP, MCAST_PORT))
        print(f"[ssdp]   sent ST: {st}")

    print(f"[ssdp] listening {LISTEN_SECS}s ...")

    by_usn: dict[str, list[dict]] = defaultdict(list)
    raw_count = 0
    deadline = time.time() + LISTEN_SECS

    while time.time() < deadline:
        try:
            data, addr = sock.recvfrom(8192)
        except socket.timeout:
            continue
        raw_count += 1
        h = parse_response(data)
        h["_FROM"] = f"{addr[0]}:{addr[1]}"
        usn = h.get("USN", f"<no-usn from {addr[0]}>")
        key = (h.get("ST", ""), h.get("LOCATION", ""))
        if not any((e.get("ST", ""), e.get("LOCATION", "")) == key for e in by_usn[usn]):
            by_usn[usn].append(h)

    sock.close()

    locations = sorted({e.get("LOCATION", "") for entries in by_usn.values() for e in entries} - {""})

    print(f"\n[ssdp] {raw_count} raw response(s), {len(by_usn)} unique USN(s), {len(locations)} unique LOCATION(s)")

    print("\n" + "=" * 78)
    print("LOCATIONS (feed each into descriptor_fetch.py)")
    print("=" * 78)
    for loc in locations:
        print(f"  {loc}")

    print("\n" + "=" * 78)
    print("DEVICES (grouped by USN)")
    print("=" * 78)

    skip = {"ST", "LOCATION", "SERVER", "USN", "CACHE-CONTROL", "EXT", "DATE", "HOST", "_FROM"}
    for usn, entries in sorted(by_usn.items()):
        print(f"\n--- {usn} ---")
        for h in entries:
            print(f"  FROM:     {h.get('_FROM', '')}")
            print(f"  ST:       {h.get('ST', '')}")
            print(f"  LOCATION: {h.get('LOCATION', '')}")
            print(f"  SERVER:   {h.get('SERVER', '')}")
            extra = {k: v for k, v in h.items() if k not in skip}
            for k, v in sorted(extra.items()):
                print(f"  {k}: {v}")
            print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
