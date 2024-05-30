# __init__.py
from homeassistant.core import HomeAssistant

DOMAIN = "egdczpowerdata"

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    return True
