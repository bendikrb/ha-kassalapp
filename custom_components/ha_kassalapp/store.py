from __future__ import annotations

from dataclasses import dataclass, field
import logging
from typing import TYPE_CHECKING

from kassalappy.models import BaseModel

from homeassistant.helpers.storage import Store

if TYPE_CHECKING:
    from homeassistant.components.todo import TodoItem
    from homeassistant.core import HomeAssistant

STORAGE_VERSION = 1
STORAGE_KEY = "kassalapp.storage"

LISTENER_STORAGE_KEY = "ha_kassalapp.config_listeners"

_LOGGER = logging.getLogger(__name__)


@dataclass
class SortWeightsStoreData(BaseModel):
    weights: dict[str, int] = field(default_factory=dict)


@dataclass
class ConfigStoreData(BaseModel):
    sort_weights: dict[str, SortWeightsStoreData] = field(default_factory=dict)


class KassalappStore:
    def __init__(self, hass: HomeAssistant):
        self.store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self.listeners = []
        self.data: ConfigStoreData | None = None
        self.dirty = False

    async def save(self, *, force_save: bool = False):
        if self.dirty or force_save:
            await self.store.async_save(self.data.to_dict())
            self.dirty = False

    async def load(self):
        stored = await self.store.async_load()
        if stored:
            self.data = ConfigStoreData.from_dict(stored)
        if self.data is None:
            self.data = ConfigStoreData()
            await self.save(force_save=True)
        self.dirty = False

    def load_weights(self, entity_id: str):
        return self.data.sort_weights.setdefault(
            entity_id, SortWeightsStoreData()
        ).weights

    def set_weights(self, weights: dict[str, int], entity_id: str) -> None:
        self.data.sort_weights[entity_id].weights = weights
        self.dirty = True

    async def updated(self):
        self.dirty = True
        for listener in self.listeners:
            listener(self.data.to_dict())
        await self.save()

    def add_listener(self, callback: callable):
        self.listeners.append(callback)

        def remove_listener():
            self.listeners.remove(callback)

        return remove_listener

    def sorted_items(self, items: list[TodoItem], entity_id: str):
        sort_weights = self.load_weights(entity_id)

        def sort_key(item: TodoItem):
            return sort_weights.get(item.uid, float("inf"))

        return sorted(items, key=sort_key)
