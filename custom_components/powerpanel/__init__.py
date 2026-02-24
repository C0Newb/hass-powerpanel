"""The PowerPanel integration."""

from __future__ import annotations

import json

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_IP_ADDRESS,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity import Entity

from .const import DOMAIN, LOGGER

# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.
PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup(hass: HomeAssistant, config: ConfigEntry) -> bool:
    """Set up a skeleton component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up PowerPanel from a config entry."""

    hass.data.setdefault(DOMAIN, {})
    LOGGER.info("setup_entry: " + json.dumps(dict(entry.data)))  # noqa: G003
    # Forward setup for all declared platforms
    await hass.async_create_background_task(
        hass.config_entries.async_forward_entry_setups(entry, PLATFORMS),
        f"{DOMAIN}::async_setup",
    )
    # await hass.async_add_job(
    #     hass.config_entries.async_forward_entry_setups(entry, "sensor")
    # )
    entry.add_update_listener(update_listener)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def update_listener(hass, entry):
    """Update listener?."""
    LOGGER.info("Update listener" + json.dumps(dict(entry.options)))
    hass.data[DOMAIN][entry.entry_id][
        "monitor"
    ].updateIntervalSeconds = entry.options.get(CONF_SCAN_INTERVAL)
