"""Pure filtering helpers (no Home Assistant imports)."""

from __future__ import annotations

from typing import Any


def site_global_id(site_id: int) -> str:
    """Journey planner stop id for a transport API site id."""
    return f"9091001{int(site_id):09d}"


def parse_journeys(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalise journey planner trips to flat dicts."""
    result = []
    for journey in data.get("journeys") or []:
        # Klass 98/99/100 = byte/gång, inte en riktig resa
        legs = [
            leg
            for leg in journey.get("legs") or []
            if ((leg.get("transportation") or {}).get("product") or {}).get("class", 0) < 98
        ]
        if not legs:
            continue
        first, last = legs[0], legs[-1]
        origin, dest = first.get("origin") or {}, last.get("destination") or {}
        transport = first.get("transportation") or {}
        seconds = journey.get("tripRtDuration") or journey.get("tripDuration") or 0
        result.append(
            {
                "line": transport.get("disassembledName") or transport.get("number"),
                "transport_mode": (transport.get("product") or {}).get("name"),
                "scheduled": origin.get("departureTimePlanned"),
                "expected": origin.get("departureTimeEstimated") or origin.get("departureTimePlanned"),
                "arrival": dest.get("arrivalTimeEstimated") or dest.get("arrivalTimePlanned"),
                "platform": (origin.get("properties") or {}).get("platformName"),
                "interchanges": int(journey.get("interchanges") or 0),
                "duration_minutes": round(seconds / 60),
                "legs": [
                    {
                        "line": (leg.get("transportation") or {}).get("disassembledName"),
                        "from": (leg.get("origin") or {}).get("name"),
                        "to": (leg.get("destination") or {}).get("name"),
                    }
                    for leg in legs
                ],
            }
        )
    return result


def filter_departures(
    departures: list[dict[str, Any]],
    modes: list[str] | None = None,
    destination: str | None = None,
) -> list[dict[str, Any]]:
    """Filter by transport modes and comma-separated, case-insensitive destination substrings."""
    if modes:
        departures = [
            d for d in departures if (d.get("line") or {}).get("transport_mode") in modes
        ]
    wanted = [w.strip().lower() for w in (destination or "").split(",") if w.strip()]
    if wanted:
        departures = [
            d
            for d in departures
            if any(w in (d.get("destination") or "").lower() for w in wanted)
        ]
    return departures
