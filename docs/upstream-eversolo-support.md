# Eversolo support ticket

Paste-ready ticket text for the Eversolo support form (or email,
whichever they currently route through). Customer-tone, specific
firmware request, evidence linked.

---

## Subject

DMP-A6 Master Gen 2: UPnP `GetProtocolInfo` does not advertise DSD MIME types, even though the device decodes DSD natively

## Body

Hi Eversolo team,

I am a DMP-A6 Master Gen 2 owner using the device on a UPnP/DLNA setup
with a self-hosted music server. The renderer is excellent: it accepts
direct SOAP control, fetches over HTTPS, and plays DSF files at native
sample rate up through DSD256 with the input format shown correctly on
the front display. I have confirmed this end-to-end with a small Python
control-point script.

There is one UPnP advertisement issue I would like to flag for a future
firmware drop.

### What I see

When a control point asks the device's
`ConnectionManager:GetProtocolInfo`, the returned `Sink` list contains
392 entries. 108 of them are audio MIMEs covering PCM / FLAC / WAV /
AAC / WMA / Ogg / RealAudio / etc. None of the entries reference DSD
in any common MIME form: no `audio/x-dsf`, `audio/x-dsd`, `audio/dsd`,
`audio/x-dff`, `audio/dff`, and no DLNA profile name covering DSD.

So a control point that uses `GetProtocolInfo` to detect DSD capability
sees a "no" from this device, even though the device decodes DSD
natively if it is handed DSF bytes labelled correctly in DIDL-Lite.

### Why this matters in practice

A closed-source iOS Subsonic client I use (Narjo) recently shipped
`GetProtocolInfo` introspection. It correctly classifies the DMP-A6 as
`supportsFLAC: YES`, `supportsWAV: YES`, `supportsDSF: NO`. When I
cast a DSF track from this client, it now force-transcodes to MP3 320
kbps because the renderer "does not support" DSF per the advertisement.
The DAC is fully capable; the advertisement is the only thing in the
way.

This is not specific to Narjo. Any UPnP control point that gates DSD
passthrough on `GetProtocolInfo` (which is what the spec says they
should do) will fall back to lossy for DSF sources against the
DMP-A6.

### Evidence

The full `GetProtocolInfo` Sink dump and a working end-to-end DSD256
native-passthrough log are both in a small public repo I built while
debugging this with the Narjo developer:

[gitlab.com/dunn.dev/narjo-eversolo-upnp](https://gitlab.com/dunn.dev/narjo-eversolo-upnp)

Specifically:

- `eversolo_descriptor.xml` -- the device descriptor.
- `proof_of_chain.log` -- transcript of three SOAP runs (Opus, DSD64,
  DSD256) all reaching `PLAYING` with native passthrough confirmed
  on the device's display and audibly on the balanced XLR output.

### What I am asking for

At Platinum SDK initialization in your firmware, extend the
`ConnectionManager` protocol-info `Sink` list to advertise the DSD
MIME types the device already accepts. Common forms in the field are:

- `http-get:*:audio/x-dsf:*`
- `http-get:*:audio/x-dsd:*`
- `http-get:*:audio/dsd:*`
- `http-get:*:audio/x-dff:*`
- `http-get:*:audio/dff:*`

This is a small additive change. Plutinosoft Platinum's upstream repo
has been dormant since 2021, so the fix is unlikely to come from
there. The firmware-side override does not require forking the SDK;
Platinum exposes API for extending the Sink list at runtime.

If a future firmware build advertises the DSD MIMEs, every conformant
UPnP control point gets accurate capability detection for the DMP-A6,
and bit-perfect DSD playback through generic UPnP control points
becomes possible without device-specific override hacks.

Happy to run additional tests if useful, or to share the diagnostic
script with whoever picks this up internally.

Thanks for the great hardware and for the responsive firmware updates,

Andrew Dunn
