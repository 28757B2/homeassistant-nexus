"""
#### Packet Information (from https://github.com/merbanan/rtl_433/blob/master/src/devices/nexus.c) ###

    Nexus sensor protocol with ID, temperature and optional humidity
    also FreeTec (Pearl) NC-7345 sensors for FreeTec Weatherstation NC-7344,
    also infactory/FreeTec (Pearl) NX-3980 sensors for infactory/FreeTec NX-3974 station,
    also Solight TE82S sensors for Solight TE76/TE82/TE83/TE84 stations,
    also TFA 30.3209.02 temperature/humidity sensor.
    The sensor sends 36 bits 12 times,
    the packets are ppm modulated (distance coding) with a pulse of ~500 us
    followed by a short gap of ~1000 us for a 0 bit or a long ~2000 us gap for a
    1 bit, the sync gap is ~4000 us.
    The data is grouped in 9 nibbles:
        [id0] [id1] [flags] [temp0] [temp1] [temp2] [const] [humi0] [humi1]
    - The 8-bit id changes when the battery is changed in the sensor.
    - flags are 4 bits B 0 C C, where B is the battery status: 1=OK, 0=LOW
    - and CC is the channel: 0=CH1, 1=CH2, 2=CH3
    - temp is 12 bit signed scaled by 10
    - const is always 1111 (0x0F)
    - humidity is 8 bits
"""

import bitstring
import operator

from typing import List, Tuple

FREQUENCY = 434.0
SYNC_WORD = 0x00 # No sync word - use default carrier sense threshold to trigger RX
PACKET_LENGTH = 1024

"""
Pulse width is ~500us = 500 * 10^-6
2 * (1 / 500 * 10^-6) = 4000 (4kbps)
"""
BAUD_RATE = 4

def decode_rx_bytes(rx_bytes: bytes) -> List[str]:
    """Decode the received bytes to a sequence of Nexus packets (36-bit strings)"""

    # Convert the received bytes to a string of bits
    rx_bits = bitstring.BitArray(bytes=rx_bytes).bin

    packets = []

    bits = ""
    count = 0

    # Decode OOK by iterating over each bit
    for bit in rx_bits:
        # A sequence of 1's seperate each OOK-encoded bit
        if bit == "1":
            # 10 or more 0's indicates the start of a packet
            if count > 10:
                # Nexus data packets are 36-bits
                if len(bits) == 36:
                    packets.append(bits)
                bits = ""
            # 4 or more 0's is an OOK 1
            elif count > 4:
                bits += "1"
            # 1 or more 0's is an OOK 0
            elif count > 0: 
                bits += "0"
            count = 0
        else:
            # Count the number of zeros
            count += 1
    
    return packets

class Message:
    """Class representing a message received from a sensor"""

    def __init__(self, id: int, channel: int, temperature: int, humidity: int, is_battery_ok: bool):
        self.id = id
        self.channel = channel
        self.temperature = temperature
        self.humidity = humidity
        self.is_battery_ok = is_battery_ok

    @classmethod
    def from_packet(cls, packet: str) -> "Message":
        """Convert a string of bits to a message"""

        id, battery_ok, const0, channel, temperature, const1, humidity = bitstring.Bits(bin=packet).unpack("uint:8, bool:1, bool:1, uint:2, int:12, uint:4, uint:8")
           
        if channel not in [0,1,2] or const0 != 0 or const1 != 0xF or humidity > 100:
            raise ValueError

        return cls(id, channel + 1, temperature / 10, humidity, battery_ok)

    def __repr__(self) -> str:
        return f"Message(ID: {self.id} Battery: {'OK' if self.is_battery_ok else 'LOW'} Channel: {self.channel} Temperature: {self.temperature} °C Humidity: {self.humidity}% )"

    def __hash__(self) -> int:
        return hash((self.id, self.channel, self.temperature, self.humidity, self.is_battery_ok))

    def __eq__(self, other) -> bool:
        return (self.id, self.channel, self.temperature, self.humidity, self.is_battery_ok) == (other.id, other.channel, other.temperature, other.humidity, other.is_battery_ok)

def message_vote(messages: List[Message]) -> Message:
    """From a list of messages, return the most common (i.e. the most likely to be correct)"""

    # Get values for the number of each message 
    votes = {}
    for message in messages:
        if message in votes:
            votes[message] += 1
        else:
            votes[message] = 1

    # https://stackoverflow.com/questions/268272/getting-key-with-maximum-value-in-dictionary
    return max(votes.items(), key=operator.itemgetter(1))[0]