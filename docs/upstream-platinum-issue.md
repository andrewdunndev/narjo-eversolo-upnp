# Upstream issue: Plutinosoft Platinum

Paste-ready issue for `plutinosoft/Platinum` on GitHub. The repo has been
quiet since 2021, so I am filing this primarily as a public record for
other control-point developers Googling the same symptom, not with an
expectation of a merge.

---

## Title

`MediaRenderer` `GetProtocolInfo` Sink list omits DSD MIMEs despite native DSD decode

## Body

The `MediaRenderer` shipped by Platinum-based products (in my case, an
Eversolo DMP-A6 Master Gen 2 running `UPnP/1.0 DLNADOC/1.50 Platinum/1.0.5.13`)
does not advertise any DSD MIME types in its `ConnectionManager:GetProtocolInfo`
Sink response, even though the device decodes DSD natively when handed
DSF bytes labelled correctly in DIDL-Lite.

This causes conformant control points that gate DSD passthrough on
`GetProtocolInfo` to silently fall back to lossy transcoding for DSD
sources, even when the renderer would handle native passthrough fine.

### Observed

`GetProtocolInfo` Sink response from this device contains 392 entries,
108 of which match `audio/*`. Audio sinks are exhaustively standard
PCM / FLAC / AAC / WMA / RealAudio / etc. There is no entry containing
`dsf`, `dsd`, `dff`, or any DoP-flavoured DLNA profile name.

Full sink list captured at:
[narjo-eversolo-upnp/docs/eversolo-getprotocolinfo.txt](../docs/eversolo-getprotocolinfo.txt)

### Expected

A renderer that decodes DSD natively should advertise the corresponding
MIMEs so conformant control points can detect the capability without
device-specific overrides. The DLNA spec never standardised a DSD MIME,
so most of the field uses one or more of:

- `audio/x-dsf`
- `audio/x-dsd`
- `audio/dsd`
- `audio/x-dff`
- `audio/dff`

### Reproduction

Against any Platinum-based MediaRenderer that supports DSD playback:

1. Send `M-SEARCH` for `urn:schemas-upnp-org:device:MediaRenderer:1`
2. Fetch the device descriptor from the SSDP `LOCATION` URL
3. SOAP `GetProtocolInfo` against `ConnectionManager:1`'s control URL
4. Search the returned `Sink` list for `dsf`, `dsd`, `dff`. Empty.
5. Independently, SOAP `SetAVTransportURI` with a DIDL-Lite `<res>`
   element containing `protocolInfo="http-get:*:audio/x-dsf:*"` and
   a URL to a DSF file, then `Play`.
6. The renderer fetches the URL, decodes natively, plays back at the
   source sample rate (DSD64, DSD128, DSD256 all confirmed against
   the Eversolo).

Reproduction scripts (Python stdlib only, no install) are at
[gitlab.com/dunn.dev/narjo-eversolo-upnp](https://gitlab.com/dunn.dev/narjo-eversolo-upnp).
The relevant files:

- `descriptor_fetch.py` -- pulls the descriptor.
- `avtransport_proof.py` -- drives `SetAVTransportURI` + `Play` and
  polls `GetTransportInfo` / `GetPositionInfo` until the renderer
  reports `PLAYING`. The repo's `proof_of_chain.log` shows successful
  end-to-end runs at DSD64 and DSD256 with native passthrough confirmed
  on the device's display and audibly on balanced XLR output.

### Impact

Real-world consequence on a closed-source iOS Subsonic client (Narjo,
build 84) talking to the Eversolo:

```
[Control] Renderer ConnectionManager:GetProtocolInfo
  device: DMP-A6(livingroom)
  sinkCount: 392
  supportsDSF: NO
  supportsFLAC: YES
  supportsWAV: YES
```

Subsequent cast attempts of DSF tracks force-transcode to MP3 320 kbps
because the parser concludes the renderer does not support DSD. The
renderer would have decoded the DSD natively, as the proof-of-chain
script independently demonstrates.

### Suggested fix

Either of:

1. Add common DSD MIMEs to the default Sink protocol-info template so
   Platinum-based renderers advertise capabilities consistent with
   what the underlying decoder accepts.
2. Document the API path SDK consumers can use to extend the Sink list
   at startup, so device firmware teams (e.g. Eversolo) can opt their
   product in without forking Platinum.

Option 1 is the right default because the existing renderers already
accept DSD bytes correctly when handed them; option 2 is a workaround
for the dormant-upstream case.

### Notes

I understand the repo has been quiet for a few years. Filing for the
public record so other control-point developers searching for this
symptom find a coherent description and a working repro, even if no
upstream fix lands.
