"""A todo platform for Kassalapp."""
from __future__ import annotations

import asyncio
import dataclasses
from typing import TYPE_CHECKING, cast

from homeassistant.components.todo import (
    TodoItem,
    TodoItemStatus,
    TodoListEntity,
    TodoListEntityFeature,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import KassalappCoordinator

if TYPE_CHECKING:
    from kassalappy import Kassalapp

    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

TODO_STATUS_MAP = {
    False: TodoItemStatus.NEEDS_ACTION,
    True: TodoItemStatus.COMPLETED,
}
TODO_STATUS_MAP_INV = {v: k for k, v in TODO_STATUS_MAP.items()}


def _convert_todo_item(item: TodoItem) -> dict[str, str]:
    """Convert TodoItem dataclass items to dictionary of attributes for the Kassalapp API."""
    result: dict[str, str] = {}
    if item.summary is not None:
        result["text"] = item.summary
    if item.status is not None:
        result["checked"] = TODO_STATUS_MAP_INV[item.status]
    return result


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Kassalapp to-do platform config entry."""
    api: Kassalapp = hass.data[DOMAIN][entry.entry_id]
    shopping_lists = await api.get_shopping_lists()
    async_add_entities(
        (
            KassalappTodoListEntity(
                KassalappCoordinator(hass, api, shopping_list["id"]),
                entry.entry_id,
                shopping_list["id"],
                shopping_list["title"],
            )
            for shopping_list in shopping_lists
        ),
        update_before_add=True,
    )


@dataclasses.dataclass
class KassalappProduct:
    """A product description from kassalapp."""

    id: int
    name: str
    image: str


@dataclasses.dataclass
class KassalappTodoItem(TodoItem):
    """An extended version of To-do item."""

    product: KassalappProduct | None = None


class KassalappTodoListEntity(CoordinatorEntity[KassalappCoordinator], TodoListEntity):
    """A Kassalapp TodoListEntity."""

    _attr_supported_features = (
        TodoListEntityFeature.CREATE_TODO_ITEM
        | TodoListEntityFeature.UPDATE_TODO_ITEM
        | TodoListEntityFeature.DELETE_TODO_ITEM
    )

    def __init__(
        self,
        coordinator: KassalappCoordinator,
        config_entry_id: str,
        shopping_list_id: int,
        shopping_list_title: str,
    ) -> None:
        """Initialize KassalappTodoListEntity."""
        super().__init__(coordinator=coordinator)
        self._shopping_list_id = shopping_list_id
        self._attr_unique_id = f"{config_entry_id}-{shopping_list_id}"
        self._attr_title = shopping_list_title

    @property
    def todo_items(self) -> list[KassalappTodoItem] | None:
        """Get the current set of To-do items."""
        if self.coordinator.data is None:
            return None
        return [
            KassalappTodoItem(
                summary=item["text"],
                uid=item["id"],
                status=TODO_STATUS_MAP.get(
                    item.get("checked"), TodoItemStatus.NEEDS_ACTION  # type: ignore[arg-type]
                ),
                product=item.get("product"),
            )
            for item in self.coordinator.data
        ]

    async def async_create_todo_item(self, item: TodoItem) -> None:
        """Add an item to the To-do list."""
        list_item = {
            "text": item.summary,
        }
        products: list[dict[str, any]] = await self.coordinator.api.product_search(
            search=list_item["text"],
            unique=True,
            size=1,
            sort="date_asc",
        )
        if products:
            product = products.pop()
            list_item["product_id"] = product["id"]

        await self.coordinator.api.add_shopping_list_item(
            list_id=self._shopping_list_id,
            **list_item,
        )
        await self.coordinator.async_refresh()

    async def async_update_todo_item(self, item: TodoItem) -> None:
        """Update a To-do item."""
        item_id: int = cast(int, item.uid)
        await self.coordinator.api.update_shopping_list_item(
            self._shopping_list_id,
            item_id,
            **_convert_todo_item(item),
        )
        await self.coordinator.async_refresh()

    async def async_delete_todo_items(self, uids: list[str]) -> None:
        """Delete a To-do item."""
        await asyncio.gather(
            *[self.coordinator.api.delete_shopping_list_item(
                list_id=self._shopping_list_id,
                item_id=cast(int, uid),
            ) for uid in uids]
        )
        await self.coordinator.async_refresh()
