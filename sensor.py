import logging

import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.const import DEVICE_CLASS_TEMPERATURE, DEVICE_CLASS_HUMIDITY, DEVICE_CLASS_BATTERY, PERCENTAGE, TEMP_CELSIUS, STATE_UNKNOWN
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DATA_NEXUS, SIGNAL_UPDATE_NEXUS

from typing import Dict

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required("sensors"): vol.All([
        vol.Schema({
            vol.Required("name"): cv.string,
            vol.Required("channel"): vol.All(vol.Coerce(int)),
        })
    ])
})

def setup_platform(hass, config, add_devices, discovery_info=None):
    sensors = config.get("sensors")        
    add_devices([Nexus(sensor, DEVICE_CLASS_TEMPERATURE) for sensor in sensors])
    add_devices([Nexus(sensor, DEVICE_CLASS_HUMIDITY) for sensor in sensors])

class Nexus(Entity):

    def __init__(self, sensor, device_class):
        self._name = sensor["name"]
        self._channel = sensor["channel"]
        self._device_class = device_class
        self._state = STATE_UNKNOWN
        self._battery_low = False

    @property
    def name(self) -> str:
        if self._device_class == DEVICE_CLASS_TEMPERATURE:
            return f"{self._name} Temperature"
        else:
            return f"{self._name} Humidity"

    @property
    def state(self) -> str:
        return self._state

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def device_class(self) -> str:
        return self._device_class

    async def async_added_to_hass(self) -> None:
        async_dispatcher_connect(self.hass, SIGNAL_UPDATE_NEXUS, self._update_callback)

    @property
    def unit_of_measurement(self) -> str:
        if self._device_class == DEVICE_CLASS_TEMPERATURE:
            return "C"
        else:
            return "%"

    @property
    def device_state_attributes(self) -> Dict[str, bool]:
        return {
            "battery_low": self._battery_low,
        }

    @callback
    def _update_callback(self) -> None:
        """Call update method."""
        self.async_schedule_update_ha_state(True)

    def update(self) -> None:
        if self._channel in self.hass.data[DATA_NEXUS]:
            message = self.hass.data[DATA_NEXUS][self._channel]

            if self._device_class == DEVICE_CLASS_TEMPERATURE:
                self._state = message.temperature
            else:
                self._state = message.humidity

            self._battery_low = not message.is_battery_ok



