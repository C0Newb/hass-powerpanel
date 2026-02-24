"""Config flow for PowerPanel integration."""

from __future__ import annotations

import logging
import traceback

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import (
    CONF_IP_ADDRESS,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
)
from homeassistant.core import callback

from .const import CONFIG_SCHEMA_A, DEFAULT_SCAN_INTERVAL, DOMAIN, LOGGER
from .sensor import PowerPanelSnmpMonitor

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_IP_ADDRESS): str,
        vol.Required(CONF_USERNAME, description={"suggested_value": "hassio"}): str,
        vol.Required(
            CONF_PORT, default=161, description={"suggested_value": "161"}
        ): str,
    }
)


class ConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Linter."""

    def __init__(self) -> None:
        """Initialize."""
        self.data_schema = CONFIG_SCHEMA_A

    async def async_step_user(self, user_input=None) -> config_entries.ConfigFlowResult:
        """Handle a flow initialized by the user."""
        # if self._async_current_entries():
        #    return self.async_abort(reason="single_instance_allowed")

        if not user_input:
            return self._show_form()

        # password = user_input[CONF_PASSWORD]
        ipaddress = user_input[CONF_IP_ADDRESS]
        username = user_input[CONF_USERNAME]
        port = user_input[CONF_PORT]
        scanInterval = user_input[CONF_SCAN_INTERVAL]

        try:
            PowerPanelSnmpMonitor(ipaddress, port, username, scanInterval)
        except:  # noqa: E722
            e = traceback.format_exc()
            LOGGER.error("Unable to connect to snmp: %s", e)
            # if ex.errcode == 400:
            #    return self._show_form({"base": "invalid_credentials"})
            return self._show_form({"base": "connection_error"})

        return self.async_create_entry(
            title=user_input[CONF_IP_ADDRESS],
            data={
                CONF_USERNAME: username,
                CONF_IP_ADDRESS: ipaddress,
                CONF_PORT: port,
                CONF_SCAN_INTERVAL: scanInterval,
            },
        )

    @callback
    def _show_form(self, errors=None):
        """Show the form to the user."""
        return self.async_show_form(
            step_id="user",
            data_schema=self.data_schema,
            errors=errors or {},
        )

    async def async_step_import(self, import_config) -> config_entries.ConfigFlowResult:
        """Import a config entry from configuration.yaml."""
        # if self._async_current_entries():
        #    LOGGER.warning("Only one configuration of abode is allowed.")
        #    return self.async_abort(reason="single_instance_allowed")

        return await self.async_step_user(import_config)

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Linter."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Linter."""

    def __init__(self, config_entry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        self.options = dict(config_entry.options)

    async def async_step_init(self, user_input=None) -> config_entries.ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    ): int,
                }
            ),
        )

    async def _update_options(self):
        """Update config entry options."""
        return self.async_create_entry(title="", data=self.options)
