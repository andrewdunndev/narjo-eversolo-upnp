#!/usr/bin/env python3
"""Fetch and summarize a UPnP device descriptor.

GETs the LOCATION URL from SSDP and dumps:
  - raw XML (eversolo_descriptor.xml)
  - parsed summary to stdout

stdlib only. Usage:

    python3 descriptor_fetch.py http://192.0.2.10:1054/description.xml
"""

import sys
import urllib.request
import xml.etree.ElementTree as ET
from urllib.parse import urljoin

NS = {"d": "urn:schemas-upnp-org:device-1-0"}


def strip_ns(tag: str) -> str:
    return tag.split("}", 1)[1] if "}" in tag else tag


def fetch(url: str, timeout: float = 5.0) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "narjo-eversolo-upnp/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def text(elem, path: str) -> str:
    found = elem.find(path, NS)
    return (found.text or "").strip() if found is not None and found.text else ""


def summarize_device(dev, base_url: str, depth: int = 0) -> list[str]:
    indent = "  " * depth
    lines = []

    fields = [
        ("deviceType", text(dev, "d:deviceType")),
        ("friendlyName", text(dev, "d:friendlyName")),
        ("manufacturer", text(dev, "d:manufacturer")),
        ("manufacturerURL", text(dev, "d:manufacturerURL")),
        ("modelDescription", text(dev, "d:modelDescription")),
        ("modelName", text(dev, "d:modelName")),
        ("modelNumber", text(dev, "d:modelNumber")),
        ("modelURL", text(dev, "d:modelURL")),
        ("serialNumber", text(dev, "d:serialNumber")),
        ("UDN", text(dev, "d:UDN")),
        ("UPC", text(dev, "d:UPC")),
        ("presentationURL", text(dev, "d:presentationURL")),
    ]
    lines.append(f"{indent}DEVICE")
    for k, v in fields:
        if v:
            lines.append(f"{indent}  {k}: {v}")

    dlna_caps = dev.find("{urn:schemas-dlna-org:device-1-0}X_DLNADOC")
    if dlna_caps is not None and dlna_caps.text:
        lines.append(f"{indent}  X_DLNADOC: {dlna_caps.text.strip()}")

    icons = dev.find("d:iconList", NS)
    if icons is not None:
        lines.append(f"{indent}  icons:")
        for icon in icons.findall("d:icon", NS):
            mime = text(icon, "d:mimetype")
            w = text(icon, "d:width")
            h = text(icon, "d:height")
            url = text(icon, "d:url")
            lines.append(f"{indent}    {mime} {w}x{h} {urljoin(base_url, url)}")

    services = dev.find("d:serviceList", NS)
    if services is not None:
        lines.append(f"{indent}  services:")
        for svc in services.findall("d:service", NS):
            stype = text(svc, "d:serviceType")
            sid = text(svc, "d:serviceId")
            scpd = text(svc, "d:SCPDURL")
            ctrl = text(svc, "d:controlURL")
            evt = text(svc, "d:eventSubURL")
            lines.append(f"{indent}    - type:    {stype}")
            lines.append(f"{indent}      id:      {sid}")
            lines.append(f"{indent}      SCPD:    {urljoin(base_url, scpd)}")
            lines.append(f"{indent}      control: {urljoin(base_url, ctrl)}")
            lines.append(f"{indent}      event:   {urljoin(base_url, evt)}")

    embedded = dev.find("d:deviceList", NS)
    if embedded is not None:
        lines.append(f"{indent}  embedded devices:")
        for sub in embedded.findall("d:device", NS):
            lines.extend(summarize_device(sub, base_url, depth + 2))

    return lines


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {argv[0]} <LOCATION_URL>", file=sys.stderr)
        return 2

    url = argv[1]
    print(f"[descriptor] GET {url}")
    raw = fetch(url)

    out_xml = "eversolo_descriptor.xml"
    with open(out_xml, "wb") as f:
        f.write(raw)
    print(f"[descriptor] wrote {out_xml} ({len(raw)} bytes)")

    root = ET.fromstring(raw)
    spec_ver = root.find("d:specVersion", NS)
    if spec_ver is not None:
        major = text(spec_ver, "d:major")
        minor = text(spec_ver, "d:minor")
        print(f"[descriptor] specVersion: {major}.{minor}")

    url_base = text(root, "d:URLBase")
    if url_base:
        print(f"[descriptor] URLBase: {url_base}")
        base = url_base
    else:
        base = url

    print(f"[descriptor] root attribs: {dict(root.attrib)}")
    print(f"[descriptor] root tag: {strip_ns(root.tag)}")
    print()

    dev = root.find("d:device", NS)
    if dev is None:
        print("[descriptor] no <device> element found", file=sys.stderr)
        return 1

    for line in summarize_device(dev, base):
        print(line)

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
