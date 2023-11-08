"""DataUpdateCoordinator for the Kassalapp component."""
from __future__ import annotations

import datetime
import logging
from typing import TYPE_CHECKING, Any, Final

from kassalappy.models import ShoppingListItem

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

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
        self._shopping_list_id = shopping_list_id

    async def _async_update_data(self) -> list[dict[str, Any]]:
        """Fetch tasks from API endpoint."""
        return await self.api.get_shopping_list_items(self._shopping_list_id)
