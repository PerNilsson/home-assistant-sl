"""Pure filtering helpers (no Home Assistant imports)."""

from __future__ import annotations

from typing import Any


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
