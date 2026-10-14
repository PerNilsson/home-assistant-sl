"""Constants for SL Departures."""

from datetime import timedelta

DOMAIN = "sl_departures"

API_BASE = "https://transport.integration.sl.se/v1"

CONF_SITE_ID = "site_id"
CONF_SITE_NAME = "site_name"
CONF_SEARCH = "search"
CONF_TRANSPORT = "transport"
CONF_MAX_DEPARTURES = "max_departures"
CONF_FORECAST = "forecast"

TRANSPORT_MODES = ["BUS", "METRO", "TRAIN", "TRAM", "SHIP"]

DEFAULT_MAX_DEPARTURES = 10
DEFAULT_FORECAST = 60
SCAN_INTERVAL = timedelta(minutes=1)
