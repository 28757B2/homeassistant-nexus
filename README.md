# Nexus 433MHz Home Assistant Integration

This project contains a Home Assistant integration for 433MHz wireless temperature and humidity sensors based on the Nexus protocol.

Receiving of the sensor's wireless signals is via a CC1101 radio connected via SPI, using the [CC1101 Linux Driver](https://github.com/28757B2/cc1101-driver) and [Python interface](https://github.com/28757B2/cc1101-python).

The Nexus protocol implementation is based on the [rtl_443](https://github.com/merbanan/rtl_433/blob/master/src/devices/nexus.c) decoder.

# Devices

The integration has been tested using the Bresser 7000020 sensors. According to the rtl_443 decoder, the following devices should also be supported:

* FreeTec (Pearl) NC-7345 
* infactory/FreeTec (Pearl) NX-3980
* Solight TE82S
* TFA 30.3209.02

# Sample Configuration

```yaml
nexus:
  device: /dev/cc1101.0.0

sensor:
  - platform: nexus
    sensors:
    - name: Garage
      channel: 1
    - name: Inside
      channel: 2
    - name: Outside
      channel: 3
```