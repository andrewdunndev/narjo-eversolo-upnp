# Eversolo DMP-A6 — UPnP Device Descriptor Summary

Parsed from `eversolo_descriptor.xml` (the raw response to GET on the SSDP
LOCATION URL). Annotations inline.

```
[descriptor] GET http://<EVERSOLO_IP>:1054/description.xml
[descriptor] wrote eversolo_descriptor.xml (2367 bytes)
[descriptor] specVersion: 1.1
[descriptor] root attribs: {'configId': '9435121'}
[descriptor] root tag: root

DEVICE
  deviceType: urn:schemas-upnp-org:device:MediaRenderer:1
  friendlyName: DMP-A6
  manufacturer: EVERSOLO
  manufacturerURL: http://www.eversolo.com
  modelDescription: Plutinosoft AV Media Renderer Device
  modelName: AV Renderer Device
  modelURL: http://www.plutinosoft.com/platinum
  UDN: uuid:800a805eef11-dmr
  presentationURL: /
  X_DLNADOC: DMR-1.50
  icons:
    image/png 64x64 http://<EVERSOLO_IP>:1054/images/icon-64x64.png
  services:
    - type:    urn:schemas-upnp-org:service:AVTransport:1
      id:      urn:upnp-org:serviceId:AVTransport
      SCPD:    http://<EVERSOLO_IP>:1054/AVTransport/800a805eef11-dmr/scpd.xml
      control: http://<EVERSOLO_IP>:1054/AVTransport/800a805eef11-dmr/control.xml
      event:   http://<EVERSOLO_IP>:1054/AVTransport/800a805eef11-dmr/event.xml
    - type:    urn:schemas-upnp-org:service:ConnectionManager:1
      id:      urn:upnp-org:serviceId:ConnectionManager
      SCPD:    http://<EVERSOLO_IP>:1054/ConnectionManager/800a805eef11-dmr/scpd.xml
      control: http://<EVERSOLO_IP>:1054/ConnectionManager/800a805eef11-dmr/control.xml
      event:   http://<EVERSOLO_IP>:1054/ConnectionManager/800a805eef11-dmr/event.xml
    - type:    urn:schemas-upnp-org:service:RenderingControl:1
      id:      urn:upnp-org:serviceId:RenderingControl
      SCPD:    http://<EVERSOLO_IP>:1054/RenderingControl/800a805eef11-dmr/scpd.xml
      control: http://<EVERSOLO_IP>:1054/RenderingControl/800a805eef11-dmr/control.xml
      event:   http://<EVERSOLO_IP>:1054/RenderingControl/800a805eef11-dmr/event.xml
```
