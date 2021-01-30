import logging
import voluptuous as vol

from cc1101.config import RXConfig, Modulation
from cc1101 import CC1101

from datetime import timedelta

from homeassistant.core import HomeAssistant, Config
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.event import track_time_interval
from homeassistant.helpers.dispatcher import dispatcher_send

from .const import DOMAIN, DATA_NEXUS, SIGNAL_UPDATE_NEXUS
from .common import FREQUENCY, BAUD_RATE, SYNC_WORD, PACKET_LENGTH, Message, decode_rx_bytes, message_vote

SCAN_INTERVAL = timedelta(seconds=1)
_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required("device"): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA
)

def setup(hass: HomeAssistant, config: Config) -> bool:
    conf = config[DOMAIN]    

    # Configure the CC1101 for RX
    rx_config = RXConfig(FREQUENCY, Modulation.OOK, BAUD_RATE, SYNC_WORD, PACKET_LENGTH)
    radio = CC1101(conf.get("device"), rx_config)

    # Create a data entry for the sensor messages
    hass.data[DATA_NEXUS] = {}

    def update(event_time) -> None:

        # Get any received bytes from the CC1101 driver
        for rx_bytes in radio.receive():

            # Try to decode as Nexus messages
            messages = []
            for packet in decode_rx_bytes(rx_bytes):                
                try:
                    messages.append(Message.from_packet(packet))
                except ValueError:
                    pass
            
            # If any messages were decoded, vote on the most likely accurate message
            if len(messages) > 0:
                message = message_vote(messages)

                # Pass the winner to the sensors and send the signal to indicate a message is waiting
                hass.data[DATA_NEXUS][message.channel] = message
                dispatcher_send(hass, SIGNAL_UPDATE_NEXUS)

    # Call the update function every SCAN_INTERVAL
    track_time_interval(hass, update, SCAN_INTERVAL)
    return True