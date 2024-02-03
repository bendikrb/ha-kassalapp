"""Config flow for Kassalapp integration."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import (
    CONF_TOKEN,
)
from kassalappy import Kassalapp
from kassalappy.exceptions import AuthorizationError, FatalHttpException

from .const import DOMAIN, SETTINGS_URL

if TYPE_CHECKING:
    from homeassistant.data_entry_flow import FlowResult

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_TOKEN): str,
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Kassalapp."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        errors: dict[str, str] = {}
        if user_input is not None:
            api = Kassalapp(user_input[CONF_TOKEN])
            try:
                await api.healthy()
            except AuthorizationError:
                errors["base"] = "invalid_api_key"
            except FatalHttpException as err:
                errors["base"] = "cannot_connect"
                _LOGGER.exception("Cannot connect: %s", err)
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title="Kassalapp", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
            description_placeholders={"settings_url": SETTINGS_URL},
        )
