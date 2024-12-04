"""A todo platform for Kassal.app."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from homeassistant.components.todo import (
    TodoItem,
    TodoItemStatus,
    TodoListEntity,
    TodoListEntityFeature,
)
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_API, DATA_STORE, DOMAIN
from .coordinator import KassalappCoordinator

if TYPE_CHECKING:
    from kassalappy import Kassalapp

    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .store import KassalappStore


def _convert_todo_item(item: TodoItem) -> dict[str, any]:
    """Convert TodoItem dataclass items to dictionary of attributes for the Kassalapp API."""
    result: dict[str, any] = {}
    if item.summary is not None:
        result["text"] = item.summary
    if item.status is not None:
        result["checked"] = item.status == TodoItemStatus.COMPLETED
    return result


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Kassalapp to-do platform config entry."""
    api: Kassalapp = hass.data[DOMAIN][entry.entry_id][DATA_API]
    data_store: KassalappStore = hass.data[DOMAIN][entry.entry_id][DATA_STORE]
    shopping_lists = await api.get_shopping_lists()
    async_add_entities(
        (
            KassalappTodoListEntity(
                KassalappCoordinator(hass, api, shopping_list.id),
                data_store,
                entry.entry_id,
                shopping_list.id,
                shopping_list.title,
            )
            for shopping_list in shopping_lists
        ),
        update_before_add=True,
    )


@dataclass
class KassalappProduct:
    """A product description from kassalapp."""

    id: int
    name: str
    image: str


@dataclass
class KassalappTodoItem(TodoItem):
    """An extended version of To-do item."""

    product: KassalappProduct | None = None


class KassalappTodoListEntity(CoordinatorEntity[KassalappCoordinator], TodoListEntity):
    """A Kassalapp TodoListEntity."""

    _attr_supported_features = (
        TodoListEntityFeature.CREATE_TODO_ITEM
        | TodoListEntityFeature.UPDATE_TODO_ITEM
        | TodoListEntityFeature.DELETE_TODO_ITEM
        | TodoListEntityFeature.MOVE_TODO_ITEM
    )

    def __init__(
        self,
        coordinator: KassalappCoordinator,
        store: KassalappStore,
        config_entry_id: str,
        shopping_list_id: int,
        shopping_list_title: str,
    ) -> None:
        """Initialize KassalappTodoListEntity."""
        super().__init__(coordinator=coordinator)
        self._shopping_list_id = shopping_list_id
        self._attr_unique_id = f"{config_entry_id}-{shopping_list_id}"
        self._attr_title = shopping_list_title
        self._data_store = store

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.coordinator.data is None:
            self._attr_todo_items = None
        else:
            items = []
            for item in self.coordinator.data:
                if item.checked:
                    status = TodoItemStatus.COMPLETED
                else:
                    status = TodoItemStatus.NEEDS_ACTION
                items.append(
                    TodoItem(
                        summary=item.text,
                        uid=str(item.id),
                        status=status,
                    )
                )
            self._attr_todo_items = self._data_store.sorted_items(items, self.entity_id)

        super()._handle_coordinator_update()

    async def async_create_todo_item(self, item: TodoItem) -> None:
        """Add an item to the To-do list."""
        list_item = {
            "text": item.summary,
        }

        await self.coordinator.api.add_shopping_list_item(
            list_id=self._shopping_list_id,
            **list_item,
        )
        await self.coordinator.async_refresh()

    async def async_update_todo_item(self, item: TodoItem) -> None:
        """Update a To-do item."""
        item_id = cast(int, item.uid)
        await self.coordinator.api.update_shopping_list_item(
            self._shopping_list_id,
            item_id,
            **_convert_todo_item(item),
        )
        await self.coordinator.async_refresh()

    async def async_delete_todo_items(self, uids: list[str]) -> None:
        """Delete a To-do item."""
        await asyncio.gather(
            *[
                self.coordinator.api.delete_shopping_list_item(
                    list_id=self._shopping_list_id,
                    item_id=cast(int, uid),
                )
                for uid in uids
            ]
        )
        await self.coordinator.async_refresh()

    async def async_move_todo_item(
        self, uid: str, previous_uid: str | None = None
    ) -> None:
        """Move an item in the To-do list."""
        if uid == previous_uid:
            return

        sort_weights = {
            item.uid: index for index, item in enumerate(self._attr_todo_items)
        }

        # Ensure this item has the lowest weight
        if previous_uid is None:
            min_weight = min(sort_weights.values(), default=0)
            sort_weights[uid] = min_weight - 1

        # Move the item after the item with previous_uid
        elif previous_uid in sort_weights:
            target_weight = sort_weights[previous_uid]
            for item_uid, weight in sort_weights.items():
                if weight > target_weight:
                    sort_weights[item_uid] += 1
            sort_weights[uid] = target_weight + 1
        else:
            msg = f"Item '{previous_uid}' not found in todo list {self.entity_id}"
            raise HomeAssistantError(msg)

        # Normalize weights to avoid overflow
        for index, (item_uid, _) in enumerate(
            sorted(sort_weights.items(), key=lambda x: x[1])
        ):
            sort_weights[item_uid] = index

        # Store the updated sort weights and hierarchy
        self._data_store.set_weights(sort_weights, self.entity_id)
        await self._async_save()
        await self.async_update_ha_state(force_refresh=True)

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass update state from existing coordinator data."""
        await super().async_added_to_hass()
        self._handle_coordinator_update()

    async def _async_save(self) -> None:
        """Persist local data to disk."""
        await self._data_store.save()
