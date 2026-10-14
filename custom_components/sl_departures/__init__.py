"""SL Departures integration."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    API_BASE,
    CONF_FORECAST,
    CONF_SITE_ID,
    CONF_TRANSPORT,
    DEFAULT_FORECAST,
    DOMAIN,
    SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["sensor"]


class SLCoordinator(DataUpdateCoordinator[list[dict[str, Any]]]):
    """Fetch departures for one site."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.data[CONF_SITE_ID]}",
            update_interval=SCAN_INTERVAL,
        )
        self.entry = entry

    async def _async_update_data(self) -> list[dict[str, Any]]:
        conf = {**self.entry.data, **self.entry.options}
        url = f"{API_BASE}/sites/{conf[CONF_SITE_ID]}/departures"
        params: dict[str, Any] = {"forecast": conf.get(CONF_FORECAST, DEFAULT_FORECAST)}
        session = async_get_clientsession(self.hass)
        modes = conf.get(CONF_TRANSPORT) or []
        try:
            if len(modes) == 1:
                params["transport"] = modes[0]
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                resp.raise_for_status()
                data = await resp.json()
        except (aiohttp.ClientError, TimeoutError) as err:
            raise UpdateFailed(f"Error fetching departures: {err}") from err

        departures = data.get("departures", [])
        if len(modes) > 1:
            departures = [
                d for d in departures if d.get("line", {}).get("transport_mode") in modes
            ]
        return departures


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = SLCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    entry.async_on_unload(entry.add_update_listener(_reload))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _reload(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if unloaded := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded
