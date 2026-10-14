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
    CONF_DESTINATION,
    CONF_FORECAST,
    CONF_JOURNEY_TO,
    CONF_MAX_DEPARTURES,
    CONF_SITE_ID,
    CONF_TRANSPORT,
    DEFAULT_FORECAST,
    DEFAULT_MAX_DEPARTURES,
    DOMAIN,
    JOURNEY_API_BASE,
    SCAN_INTERVAL,
)
from .filters import filter_departures, parse_journeys, site_global_id

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
        self._dest_ids: dict[str, str] = {}

    async def _resolve_stop(self, name: str) -> str:
        if name not in self._dest_ids:
            session = async_get_clientsession(self.hass)
            params = {"name_sf": name, "type_sf": "any", "any_obj_filter_sf": 2}
            async with session.get(
                f"{JOURNEY_API_BASE}/stop-finder",
                params=params,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
            stops = [loc for loc in data.get("locations", []) if loc.get("type") == "stop"]
            if not stops:
                raise UpdateFailed(f"Journey destination not found: {name}")
            best = next((s for s in stops if s.get("isBest")), stops[0])
            self._dest_ids[name] = best["id"]
        return self._dest_ids[name]

    async def _async_update_journeys(self, conf: dict[str, Any]) -> list[dict[str, Any]]:
        try:
            dest_id = await self._resolve_stop(conf[CONF_JOURNEY_TO].strip())
            params = {
                "type_origin": "any",
                "name_origin": site_global_id(conf[CONF_SITE_ID]),
                "type_destination": "any",
                "name_destination": dest_id,
                "calc_number_of_trips": 3,  # API avvisar > 3
            }
            session = async_get_clientsession(self.hass)
            async with session.get(
                f"{JOURNEY_API_BASE}/trips",
                params=params,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
        except (aiohttp.ClientError, TimeoutError) as err:
            raise UpdateFailed(f"Error fetching journeys: {err}") from err
        return parse_journeys(data)

    async def _async_update_data(self) -> list[dict[str, Any]]:
        conf = {**self.entry.data, **self.entry.options}
        if (conf.get(CONF_JOURNEY_TO) or "").strip():
            return await self._async_update_journeys(conf)
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

        return filter_departures(
            data.get("departures", []), modes, conf.get(CONF_DESTINATION)
        )


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
