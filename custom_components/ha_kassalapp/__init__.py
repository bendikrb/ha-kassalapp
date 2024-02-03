"""The Kassalapp integration."""
from __future__ import annotations

import datetime
import logging
from typing import TYPE_CHECKING

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.const import CONF_TOKEN, Platform
from homeassistant.core import SupportsResponse
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from kassalappy import Kassalapp

from .const import DATA_API, DATA_STORE, DOMAIN, SERVICE_PRODUCT_SEARCH
from .store import KassalappStore

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import (
        HomeAssistant,
        ServiceCall,
        ServiceResponse,
    )

SERVICE_PRODUCT_SEARCH_SCHEMA = vol.Schema({
    vol.Optional("search"): cv.string,
    vol.Optional("brand"): cv.string,
    vol.Optional("vendor"): cv.string,
    vol.Optional("excl_allergens"): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional("incl_allergens"): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional("exclude_without_ean"): cv.boolean,
    vol.Optional("price_max"): cv.positive_float,
    vol.Optional("price_min"): cv.positive_float,
    vol.Optional("size"): vol.All(vol.Coerce(int), vol.Range(min=1, max=50)),
    vol.Optional("sort"): cv.string,
    vol.Optional("unique"): cv.boolean,
})

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = datetime.timedelta(minutes=1)

PLATFORMS: list[Platform] = [Platform.TODO]

TIMEOUT = 10


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Kassalapp from a config entry."""

    async def product_search_service(call: ServiceCall) -> ServiceResponse:
        """Search kassalapp for product."""
        client: Kassalapp = hass.data[DOMAIN][entry.entry_id][DATA_API]
        results = await client.product_search(**call.data)
        return {
            "results": [p.model_dump(mode="json") for p in results],
        }

    hass.data.setdefault(DOMAIN, {})
    token = entry.data[CONF_TOKEN]
    api = Kassalapp(token, timeout=TIMEOUT, websession=async_get_clientsession(hass))

    data_store = KassalappStore(hass)
    await data_store.load()

    hass.data[DOMAIN][entry.entry_id] = {
        DATA_API: api,
        DATA_STORE: data_store,
    }
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    hass.services.async_register(
        DOMAIN,
        SERVICE_PRODUCT_SEARCH,
        product_search_service,
        schema=SERVICE_PRODUCT_SEARCH_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
