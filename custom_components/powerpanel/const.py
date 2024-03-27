"""Constants for the PowerPanel integration."""

import logging

import voluptuous as vol

from homeassistant.const import (
    CONF_IP_ADDRESS,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
)

LOGGER = logging.getLogger(__package__)
DEFAULT_NAME = "My UPS"
DOMAIN = "power_panel"
DEFAULT_SCAN_INTERVAL = 10

MANUFACTURE = "CyberPower"
MODEL = "PowerPanel"

CONFIG_SCHEMA_A = vol.Schema(
    {
        vol.Required(CONF_IP_ADDRESS, "IP Address"): str,
        vol.Required(CONF_PORT, "Port"): int,
        vol.Required(CONF_USERNAME, "Service name"): str,
        vol.Optional(CONF_SCAN_INTERVAL, "Scan interval", DEFAULT_SCAN_INTERVAL): int,
    }
)

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: CONFIG_SCHEMA_A},
    extra=vol.ALLOW_EXTRA,
)
