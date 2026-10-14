"""Config flow for SL Departures."""

from __future__ import annotations

from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
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
        vol.Optional(
            CONF_MAX_DEPARTURES, default=defaults.get(CONF_MAX_DEPARTURES, DEFAULT_MAX_DEPARTURES)
        ): _number(1, 30),
        vol.Optional(
            CONF_FORECAST, default=defaults.get(CONF_FORECAST, DEFAULT_FORECAST)
        ): _number(10, 1200),
    }


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
            query = user_input[CONF_SEARCH].strip().lower()
            try:
                session = async_get_clientsession(self.hass)
                async with session.get(f"{API_BASE}/sites", params={"expand": "false"}) as resp:
                    resp.raise_for_status()
                    sites = await resp.json()
            except (aiohttp.ClientError, TimeoutError):
                errors["base"] = "cannot_connect"
            else:
                self._sites = [
                    s
                    for s in sites
                    if query in s.get("name", "").lower() or query in (s.get("alias") or [""])[0].lower()
                ][:50]
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
            await self.async_set_unique_id(str(site_id))
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=name,
                data={
                    CONF_SITE_ID: site_id,
                    CONF_SITE_NAME: name,
                    CONF_TRANSPORT: user_input.get(CONF_TRANSPORT, []),
                    CONF_DESTINATION: user_input.get(CONF_DESTINATION, ""),
                    CONF_MAX_DEPARTURES: int(user_input[CONF_MAX_DEPARTURES]),
                    CONF_FORECAST: int(user_input[CONF_FORECAST]),
                },
            )

        options = [SelectOptionDict(value=str(s["id"]), label=s["name"]) for s in self._sites]
        schema = {
            vol.Required(CONF_SITE_ID): SelectSelector(
                SelectSelectorConfig(options=options, mode=SelectSelectorMode.DROPDOWN)
            ),
            **_settings_schema({}),
        }
        return self.async_show_form(step_id="select", data_schema=vol.Schema(schema))


class SLOptionsFlow(OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            user_input[CONF_MAX_DEPARTURES] = int(user_input[CONF_MAX_DEPARTURES])
            user_input[CONF_FORECAST] = int(user_input[CONF_FORECAST])
            return self.async_create_entry(data=user_input)

        current = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(
            step_id="init", data_schema=vol.Schema(_settings_schema(current))
        )
