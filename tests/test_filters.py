"""Tests for filters.py; loaded by path so Home Assistant is not required."""

import importlib.util
from pathlib import Path

_path = Path(__file__).parent.parent / "custom_components" / "sl_departures" / "filters.py"
_spec = importlib.util.spec_from_file_location("sl_filters", _path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
filter_departures = _mod.filter_departures


def dep(destination, mode="BUS"):
    return {"destination": destination, "line": {"transport_mode": mode}}


DEPS = [
    dep("Cityterminalen"),
    dep("Gustavsberg Lugnet"),
    dep("Slussen", "METRO"),
    {"destination": None, "line": None},
]


def names(result):
    return [d["destination"] for d in result]


def test_no_filters_returns_all():
    assert filter_departures(DEPS) == DEPS
    assert filter_departures(DEPS, [], "") == DEPS


def test_destination_case_insensitive_substring():
    assert names(filter_departures(DEPS, None, "city")) == ["Cityterminalen"]


def test_destination_comma_separated_with_spaces():
    result = filter_departures(DEPS, None, " cityterminalen , slussen ,")
    assert names(result) == ["Cityterminalen", "Slussen"]


def test_destination_without_match_is_empty():
    assert filter_departures(DEPS, None, "Odenplan") == []


def test_single_mode():
    assert names(filter_departures(DEPS, ["METRO"])) == ["Slussen"]


def test_multiple_modes():
    result = filter_departures(DEPS, ["BUS", "METRO"])
    assert len(result) == 3


def test_modes_and_destination_combined():
    assert filter_departures(DEPS, ["BUS"], "slussen") == []


def test_site_global_id():
    assert _mod.site_global_id(4174) == "9091001000004174"


def test_parse_journeys_skips_footpaths_and_counts_changes():
    bus = lambda n, o, d: {
        "transportation": {"disassembledName": n, "product": {"class": 5, "name": "Buss"}},
        "origin": {"name": o, "departureTimePlanned": "2026-10-14T14:28:48Z"},
        "destination": {"name": d, "arrivalTimeEstimated": "2026-10-14T14:55:42Z"},
    }
    walk = {"transportation": {"product": {"class": 100}}}
    data = {
        "journeys": [
            {
                "tripDuration": 1872,
                "tripRtDuration": 1536,
                "interchanges": 1,
                "legs": [bus("418", "A", "B"), walk, bus("444", "B", "Slussen")],
            }
        ]
    }
    (j,) = _mod.parse_journeys(data)
    assert j["interchanges"] == 1
    assert j["duration_minutes"] == 26
    assert j["line"] == "418"
    assert j["arrival"] == "2026-10-14T14:55:42Z"
    assert len(j["legs"]) == 2
    assert j["destination"] == "Slussen"
    assert j["interchange_stops"] == ["B"]
