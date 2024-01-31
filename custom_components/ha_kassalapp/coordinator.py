"""DataUpdateCoordinator for the Kassalapp component."""
from __future__ import annotations

import datetime
import logging
from typing import TYPE_CHECKING, Final

from kassalappy.models import ShoppingListItem, ShoppingList

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

if TYPE_CHECKING:
    from kassalappy import Kassalapp

    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL: Final = datetime.timedelta(minutes=30)


class KassalappCoordinator(DataUpdateCoordinator[list[ShoppingListItem]]):
    """Coordinator for updating task data from Kassalapp."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: Kassalapp,
        shopping_list_id: int,
    ) -> None:
        """Initialize the Kassalapp coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"Kassalapp {shopping_list_id}",
            update_interval=UPDATE_INTERVAL,
        )
        self.api = api
        self._shopping_lists: list[ShoppingList] | None = None
        self._shopping_list_id = shopping_list_id

    async def _async_update_data(self) -> list[ShoppingListItem]:
        """Fetch tasks from API endpoint."""
        try:
            return await self.api.get_shopping_list_items(self._shopping_list_id)
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    async def async_get_shopping_lists(self) -> list[ShoppingList]:
        """Return todoist projects fetched at most once."""
        if self._shopping_lists is None:
            self._shopping_lists = await self.api.get_shopping_lists()
        return self._shopping_lists
