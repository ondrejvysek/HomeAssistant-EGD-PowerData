import logging
import requests
import datetime
from datetime import timedelta
import voluptuous as vol
from dateutil import tz
from collections import defaultdict
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorDeviceClass
from homeassistant.const import UnitOfEnergy
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle
from homeassistant.helpers.entity_component import async_update_entity
from homeassistant.core import HomeAssistant
from urllib.parse import quote
from .const import DOMAIN, CONF_CLIENT_ID, CONF_CLIENT_SECRET, TOKEN_URL, DATA_URL

_LOGGER = logging.getLogger(__name__)

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=15)

CONF_DAYS = "days"
CONF_EAN = "ean"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_CLIENT_ID): cv.string,
    vol.Required(CONF_CLIENT_SECRET): cv.string,
    vol.Required(CONF_EAN): cv.string,
    vol.Optional(CONF_DAYS, default=1): cv.positive_int,
})

def setup_platform(hass, config, add_entities, discovery_info=None):
    client_id = config[CONF_CLIENT_ID]
    client_secret = config[CONF_CLIENT_SECRET]
    ean = config[CONF_EAN]
    days = config[CONF_DAYS]

    status_sensor = EGDPowerDataStatusSensor(hass, client_id, client_secret, ean, days)
    consumption_sensor = EGDPowerDataConsumptionSensor(hass, client_id, client_secret, ean, days)
    production_sensor = EGDPowerDataProductionSensor(hass, client_id, client_secret, ean, days)
    
    add_entities([status_sensor, consumption_sensor, production_sensor], True)

class EGDPowerDataSensor(Entity):
    def __init__(self, hass, client_id, client_secret, ean, days, profile):
        self.hass = hass
        self.client_id = client_id
        self.client_secret = client_secret
        self.ean = ean
        self.days = days
        self.profile = profile
        self._state = None
        self._attributes = {}
        self._session = requests.Session()
        self._unique_id = f"egdpowerdata_{ean}_{days}_{profile.lower()}"
        self.entity_id = f"sensor.egdpowerdata_{ean}_{days}_{profile.lower()}"
        _LOGGER.debug("Initialized EGDPowerDataSensor with EAN: %s, Profile: %s", self.ean, self.profile)
        self.update()

    @property
    def name(self):
        return f"EGD Power Data Sensor {self.ean} {self.days} {self.profile}"

    @property
    def state(self):
        return self._state

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def extra_state_attributes(self):
        return self._attributes

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self, no_throttle=False):
        if not self.ean:
            _LOGGER.warning("EAN is not set. Skipping update.")
            return

        _LOGGER.debug("Updating EGD Power Data Sensor for EAN: %s, Profile: %s", self.ean, self.profile)
        try:
            token = self._get_access_token()
            self._get_data(token)
        except Exception as e:
            _LOGGER.error("Error updating sensor: %s", e)

    def _get_access_token(self):
        _LOGGER.debug("Retrieving access token")
        try:
            response = self._session.post(
                TOKEN_URL,
                data={
                    'grant_type': 'client_credentials',
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'scope': 'namerena_data_openapi'
                }
            )
            response.raise_for_status()
            token = response.json().get('access_token')
            _LOGGER.debug("Access token retrieved: %s", token)
            return token
        except requests.exceptions.RequestException as e:
            _LOGGER.error("Error retrieving access token: %s", e)
            raise

    def _get_data(self, token):
        _LOGGER.debug("Retrieving data with token: %s", token)

        # Define the CEST timezone
        local_tz = tz.gettz('Europe/Prague')

        # Define the start time as the previous number of days at 00:00:00
        local_stime = (datetime.datetime.now() - timedelta(days=self.days)).replace(hour=0, minute=0, second=0, microsecond=0)
        # Define the end time as yesterday at 23:45:00
        local_etime = (datetime.datetime.now() - timedelta(days=1)).replace(hour=23, minute=45, second=0, microsecond=0)

        # Assign the CEST timezone to the local time
        local_stime = local_stime.replace(tzinfo=local_tz)
        local_etime = local_etime.replace(tzinfo=local_tz)

        # Convert local time to UTC
        utc_stime = local_stime.astimezone(tz.tzutc())
        utc_etime = local_etime.astimezone(tz.tzutc())

        headers = {
            'Authorization': f'Bearer {token}'
        }
        params = {
            'ean': self.ean,
            'profile': self.profile,
            'from': utc_stime.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
            'to': utc_etime.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
            'pageSize': 3000
        }

        try:
            _LOGGER.debug("Headers: %s", params)
            _LOGGER.debug("Data url: %s", DATA_URL)
            response = self._session.get(DATA_URL, headers=headers, params=params)
            _LOGGER.debug("Response status code: %s", response.status_code)
            _LOGGER.debug("Response content: %s", response.content)
            response.raise_for_status()
            data = response.json()
            _LOGGER.debug("Data retrieved: %s", data)
            total_value = sum(float(item['value']) for item in data[0]['data'])
            self._state = total_value
            self._attributes = {
                'stime': utc_stime.strftime('%Y-%m-%d %H:%M:%S %Z%z'),
                'etime': utc_etime.strftime('%Y-%m-%d %H:%M:%S %Z%z'),
                'local_stime': local_stime.strftime('%Y-%m-%d %H:%M:%S %Z%z'),
                'local_etime': local_etime.strftime('%Y-%m-%d %H:%M:%S %Z%z')
            }
            _LOGGER.debug("Total value: %s", total_value)
        except requests.exceptions.RequestException as e:
            _LOGGER.error("Error retrieving data: %s", e)
            raise

class EGDPowerDataConsumptionSensor(EGDPowerDataSensor):
    def __init__(self, hass, client_id, client_secret, ean, days):
        super().__init__(hass, client_id, client_secret, ean, days, 'ICC1')

    @property
    def unit_of_measurement(self):
        return UnitOfEnergy.KILO_WATT_HOUR

    @property
    def device_class(self):
        return SensorDeviceClass.ENERGY

class EGDPowerDataProductionSensor(EGDPowerDataSensor):
    def __init__(self, hass, client_id, client_secret, ean, days):
        super().__init__(hass, client_id, client_secret, ean, days, 'ISC1')

    @property
    def unit_of_measurement(self):
        return UnitOfEnergy.KILO_WATT_HOUR

    @property
    def device_class(self):
        return SensorDeviceClass.ENERGY

class EGDPowerDataStatusSensor(Entity):
    def __init__(self, hass, client_id, client_secret, ean, days):
        self.hass = hass
        self.client_id = client_id
        self.client_secret = client_secret
        self.ean = ean
        self.days = days
        self._state = None
        self._attributes = {}
        self._session = requests.Session()
        self._unique_id = f"egdpowerdata_status_{ean}_{days}"
        self.entity_id = f"sensor.egdpowerdata_status_{ean}_{days}"
        _LOGGER.debug("Initialized EGDPowerDataStatusSensor with EAN: %s", self.ean)
        self.update()

    @property
    def name(self):
        return f"EGD Power Data Status Sensor {self.ean} {self.days}"

    @property
    def state(self):
        return self._state

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def extra_state_attributes(self):
        return self._attributes

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self, no_throttle=False):
        _LOGGER.debug("Updating EGD Power Data Status Sensor for EAN: %s", self.ean)
        try:
            self.hass.add_job(self._update_related_sensors())
            self._state = "updated"
        except Exception as e:
            _LOGGER.error("Error updating status sensor: %s", e)

    async def _update_related_sensors(self):
        _LOGGER.debug("Updating related sensors for EAN: %s", self.ean)
        for entity_id in [
            f"sensor.egdpowerdata_{self.ean}_{self.days}_icc1",
            f"sensor.egdpowerdata_{self.ean}_{self.days}_isc1"
        ]:
            await async_update_entity(self.hass, entity_id)
