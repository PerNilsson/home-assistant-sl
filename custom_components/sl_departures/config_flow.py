"""Config flow for SL Departures."""

from __future__ import annotations

from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    API_BASE,
    CONF_DESTINATION,
    CONF_FORECAST,
    CONF_JOURNEY_TO,
    CONF_MAX_DEPARTURES,
    CONF_SEARCH,
    CONF_SITE_ID,
    CONF_SITE_NAME,
    CONF_TRANSPORT,
    DEFAULT_FORECAST,
    DEFAULT_MAX_DEPARTURES,
    DOMAIN,
    TRANSPORT_MODES,
)


def _transport_selector() -> SelectSelector:
    return SelectSelector(
        SelectSelectorConfig(
            options=TRANSPORT_MODES,
            multiple=True,
            mode=SelectSelectorMode.DROPDOWN,
            translation_key="transport",
        )
    )


def _number(min_: int, max_: int) -> NumberSelector:
    return NumberSelector(NumberSelectorConfig(min=min_, max=max_, step=1, mode="box"))


def _settings_schema(defaults: dict[str, Any]) -> dict:
    return {
        vol.Optional(CONF_TRANSPORT, default=defaults.get(CONF_TRANSPORT, [])): _transport_selector(),
        vol.Optional(CONF_DESTINATION, default=defaults.get(CONF_DESTINATION, "")): str,
        vol.Optional(CONF_JOURNEY_TO, default=defaults.get(CONF_JOURNEY_TO, "")): str,
        vol.Optional(
            CONF_MAX_DEPARTURES, default=defaults.get(CONF_MAX_DEPARTURES, DEFAULT_MAX_DEPARTURES)
        ): _number(1, 30),
        vol.Optional(
            CONF_FORECAST, default=defaults.get(CONF_FORECAST, DEFAULT_FORECAST)
        ): _number(10, 1200),
    }


def _unique_id(site_id: int, journey_to: str) -> str:
    return f"{site_id}:{journey_to.strip().lower()}"


def _title(name: str, journey_to: str) -> str:
    journey_to = journey_to.strip()
    return f"{name} → {journey_to}" if journey_to else name


def _site_selector(sites: list[dict[str, Any]]) -> SelectSelector:
    options = [SelectOptionDict(value=str(s["id"]), label=s["name"]) for s in sites]
    return SelectSelector(SelectSelectorConfig(options=options, mode=SelectSelectorMode.DROPDOWN))


async def _search_sites(hass: HomeAssistant, query: str) -> list[dict[str, Any]]:
    """Return up to 50 sites whose name or alias contains the query."""
    query = query.strip().lower()
    session = async_get_clientsession(hass)
    async with session.get(f"{API_BASE}/sites", params={"expand": "false"}) as resp:
        resp.raise_for_status()
        sites = await resp.json()
    return [
        s
        for s in sites
        if query in s.get("name", "").lower()
        or any(query in a.lower() for a in (s.get("alias") or []))
    ][:50]


class SLConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._sites: list[dict[str, Any]] = []

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return SLOptionsFlow()

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                self._sites = await _search_sites(self.hass, user_input[CONF_SEARCH])
            except (aiohttp.ClientError, TimeoutError):
                errors["base"] = "cannot_connect"
            else:
                if self._sites:
                    return await self.async_step_select()
                errors["base"] = "no_results"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_SEARCH): str}),
            errors=errors,
        )

    async def async_step_select(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            site_id = int(user_input[CONF_SITE_ID])
            name = next(s["name"] for s in self._sites if s["id"] == site_id)
            journey_to = user_input.get(CONF_JOURNEY_TO, "")
            await self.async_set_unique_id(_unique_id(site_id, journey_to))
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=_title(name, journey_to),
                data={
                    CONF_SITE_ID: site_id,
                    CONF_SITE_NAME: name,
                    CONF_TRANSPORT: user_input.get(CONF_TRANSPORT, []),
                    CONF_DESTINATION: user_input.get(CONF_DESTINATION, ""),
                    CONF_JOURNEY_TO: journey_to,
                    CONF_MAX_DEPARTURES: int(user_input[CONF_MAX_DEPARTURES]),
                    CONF_FORECAST: int(user_input[CONF_FORECAST]),
                },
            )

        schema = {
            vol.Required(CONF_SITE_ID): _site_selector(self._sites),
            **_settings_schema({}),
        }
        return self.async_show_form(step_id="select", data_schema=vol.Schema(schema))


class SLOptionsFlow(OptionsFlow):
    """Change stop (optional) and filters."""

    def __init__(self) -> None:
        self._sites: list[dict[str, Any]] = []

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            query = user_input.get(CONF_SEARCH, "").strip()
            if not query:
                # Tomt sökfält = behåll nuvarande hållplats
                return await self.async_step_filters()
            try:
                self._sites = await _search_sites(self.hass, query)
            except (aiohttp.ClientError, TimeoutError):
                errors["base"] = "cannot_connect"
            else:
                if self._sites:
                    return await self.async_step_select()
                errors["base"] = "no_results"

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({vol.Optional(CONF_SEARCH, default=""): str}),
            description_placeholders={"current": self.config_entry.data[CONF_SITE_NAME]},
            errors=errors,
        )

    async def async_step_select(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            site_id = int(user_input[CONF_SITE_ID])
            name = next(s["name"] for s in self._sites if s["id"] == site_id)
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data={**self.config_entry.data, CONF_SITE_ID: site_id, CONF_SITE_NAME: name},
            )
            return await self.async_step_filters()

        return self.async_show_form(
            step_id="select",
            data_schema=vol.Schema({vol.Required(CONF_SITE_ID): _site_selector(self._sites)}),
            errors=errors,
        )

    async def async_step_filters(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        current = {**self.config_entry.data, **self.config_entry.options}
        if user_input is not None:
            user_input[CONF_MAX_DEPARTURES] = int(user_input[CONF_MAX_DEPARTURES])
            user_input[CONF_FORECAST] = int(user_input[CONF_FORECAST])
            site_id = self.config_entry.data[CONF_SITE_ID]
            journey_to = user_input.get(CONF_JOURNEY_TO, "")
            uid = _unique_id(site_id, journey_to)
            if any(
                e.entry_id != self.config_entry.entry_id and e.unique_id == uid
                for e in self.hass.config_entries.async_entries(DOMAIN)
            ):
                errors["base"] = "already_configured"
                current = {**current, **user_input}
            else:
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    title=_title(self.config_entry.data[CONF_SITE_NAME], journey_to),
                    unique_id=uid,
                )
                return self.async_create_entry(data=user_input)

        return self.async_show_form(
            step_id="filters", data_schema=vol.Schema(_settings_schema(current)), errors=errors
        )
