"""Sensor for SL Departures."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from . import SLCoordinator
from .const import (
    CONF_JOURNEY_TO,
    CONF_MAX_DEPARTURES,
    DEFAULT_MAX_DEPARTURES,
    DOMAIN,
)


def _parse(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = dt_util.parse_datetime(value)
    if parsed and parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt_util.DEFAULT_TIME_ZONE)
    return parsed


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = [SLNextDepartureSensor(coordinator, entry)]
    conf = {**entry.data, **entry.options}
    if (conf.get(CONF_JOURNEY_TO) or "").strip():
        entities += [SLInterchangesSensor(coordinator, entry), SLTravelTimeSensor(coordinator, entry)]
    async_add_entities(entities)


class SLNextDepartureSensor(CoordinatorEntity[SLCoordinator], SensorEntity):
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:bus-clock"
    _attr_has_entity_name = True
    _attr_name = "Next departure"

    def __init__(self, coordinator: SLCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_next_departure"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="SL",
            entry_type=DeviceEntryType.SERVICE,
        )

    def _departures(self) -> list[dict[str, Any]]:
        conf = {**self._entry.data, **self._entry.options}
        limit = conf.get(CONF_MAX_DEPARTURES, DEFAULT_MAX_DEPARTURES)
        return (self.coordinator.data or [])[:limit]

    @property
    def native_value(self) -> datetime | None:
        deps = self._departures()
        return _parse(deps[0].get("expected") or deps[0].get("scheduled")) if deps else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        items = []
        for d in self._departures():
            if "interchanges" in d:
                items.append(d)
                continue
            line = d.get("line", {})
            items.append(
                {
                    "line": line.get("designation"),
                    "transport_mode": line.get("transport_mode"),
                    "destination": d.get("destination"),
                    "display": d.get("display"),
                    "scheduled": d.get("scheduled"),
                    "expected": d.get("expected"),
                    "state": d.get("state"),
                    "platform": (d.get("stop_point") or {}).get("designation"),
                    "deviations": [x.get("message") for x in d.get("deviations", [])],
                }
            )
        return {"departures": items}


class _SLJourneySensor(CoordinatorEntity[SLCoordinator], SensorEntity):
    _attr_has_entity_name = True
    _key = ""

    def __init__(self, coordinator: SLCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_{self._key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="SL",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self) -> int | None:
        data = self.coordinator.data or []
        return data[0].get(self._key) if data else None


class SLInterchangesSensor(_SLJourneySensor):
    _key = "interchanges"
    _attr_name = "Interchanges"
    _attr_icon = "mdi:swap-horizontal"
    _attr_state_class = SensorStateClass.MEASUREMENT


class SLTravelTimeSensor(_SLJourneySensor):
    _key = "duration_minutes"
    _attr_name = "Travel time"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_state_class = SensorStateClass.MEASUREMENT
