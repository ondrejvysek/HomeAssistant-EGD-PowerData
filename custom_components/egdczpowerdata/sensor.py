from homeassistant.helpers.entity import Entity
from homeassistant.core import HomeAssistant
import logging
from datetime import datetime, timedelta
import aiohttp
import asyncio
from dateutil import tz
from collections import defaultdict

DOMAIN = "egdczpowerdata"

from homeassistant.const import (
    EVENT_HOMEASSISTANT_STARTED,
    EVENT_HOMEASSISTANT_STOP,
)

BASE_URL = "https://data.distribuce24.cz"
TOKEN_URL = "https://idm.distribuce24.cz/oauth/token"
DATA_URL = BASE_URL + "/rest/spotreby"

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    client_id = config.get("client_id")
    client_secret = config.get("client_secret")
    ean = config.get("ean")
    days = config.get("days")
    sensor_icc1 = EGDPowerDataSensor(hass, client_id, client_secret, ean, days, "ICC1", "mdi:transmission-tower-export")
    sensor_isc1 = EGDPowerDataSensor(hass, client_id, client_secret, ean, days, "ISC1", "mdi:transmission-tower-import")

    async_add_entities([sensor_icc1, sensor_isc1])

    async def handle_event(event):
        _LOGGER.info(f"---Event received for {sensor_icc1.name} and {sensor_isc1.name}: {event.data}---")
        token = await sensor_icc1._get_access_token()
        if token:
            await sensor_icc1._update_state(token)
            await sensor_isc1._update_state(token)
            sensor_icc1._attributes["last_updated"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            sensor_isc1._attributes["last_updated"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            sensor_icc1.async_write_ha_state()
            sensor_isc1.async_write_ha_state()
        else:
            _LOGGER.error("Failed to retrieve access token")

    hass.bus.async_listen(EVENT_HOMEASSISTANT_STARTED, handle_event)
    hass.bus.async_listen("run_egd", handle_event)

class EGDPowerDataSensor(Entity):
    def __init__(self, hass, client_id, client_secret, ean, days, profile, icon):
        _LOGGER.info(f"---Init EGDPowerDataSensor for {ean} and profile {profile}---")
        self._state = None
        self._attributes = {}
        self.hass = hass
        self.client_id = client_id
        self.client_secret = client_secret
        self.ean = ean
        self.days = days
        self.profile = profile
        self._icon = icon
        self._unique_id = f"egd_{ean}_{profile}"
        self.entity_id = f"sensor.egd_{ean}_{profile}"
        self._attributes["ean"] = ean  # Expose EAN as an attribute

    @property
    def name(self):
        return f"EGD {self.ean} {self.profile}"

    @property
    def state(self):
        return self._state

    @property
    def unique_id(self):
        return self._unique_id
    
    @property
    def icon(self):
        return self._icon    
    
    @property
    def extra_state_attributes(self):
        return self._attributes


    async def _get_access_token(self):
        async with aiohttp.ClientSession() as session:
            data = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'scope': 'namerena_data_openapi'
            }
            _LOGGER.info(f"---Getting access token at {TOKEN_URL} with {data} ---")
            async with session.post(TOKEN_URL, data=data) as response:
                if response.status < 400:
                    token_data = await response.json()
                    return token_data.get('access_token')
                else:
                    _LOGGER.error("Error retrieving access token")
                    return None

    async def _update_state(self, token):
        local_tz = await asyncio.to_thread(tz.gettz, 'Europe/Prague')
        local_stime = await asyncio.to_thread(lambda: (datetime.now() - timedelta(days=self.days)).replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=local_tz))
        local_etime = await asyncio.to_thread(lambda: (datetime.now() - timedelta(days=1)).replace(hour=23, minute=45, second=0, microsecond=0, tzinfo=local_tz))

        utc_stime = local_stime.astimezone(tz.tzutc())
        utc_etime = local_etime.astimezone(tz.tzutc())

        headers = {
            "Authorization": f"Bearer {token}"
        }
        params = {
            'ean': self.ean,
            'profile': self.profile,
            'from': utc_stime.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
            'to': utc_etime.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
            'pageSize': 3000
        }
        _LOGGER.info(f"---Getting data at {DATA_URL} with params {params} ---")
        async with aiohttp.ClientSession() as session:
            async with session.get(DATA_URL, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    _LOGGER.info(f"---Response JSON: {data} ---")
                    if 'error' in data and data['error'] == 'No results':
                        _LOGGER.info(f"---No results found for {self.name}, setting state to 0---")
                        self._state = 0
                    else:
                        _LOGGER.info(f"---Response JSON: {data} ---")
                        total_value = sum(float(item['value']) for item in data[0]['data'])/4
                        self._state = total_value
                        _LOGGER.info(f"---Total value: {total_value} ---")
                    self._attributes = {
                        'stime': utc_stime.strftime('%Y-%m-%d %H:%M:%S %Z%z'),
                        'etime': utc_etime.strftime('%Y-%m-%d %H:%M:%S %Z%z'),
                        'local_stime': local_stime.strftime('%Y-%m-%d %H:%M:%S %Z%z'),
                        'local_etime': local_etime.strftime('%Y-%m-%d %H:%M:%S %Z%z'),
                        'json': f"{data}"
                    }
                else:
                    _LOGGER.error(f"Error retrieving data: {response.status}")
                    self._state = "Error"
