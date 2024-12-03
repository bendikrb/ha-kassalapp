from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from homeassistant.helpers.storage import Store
from homeassistant.config import ConfigType

import attr

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.components.todo import TodoItem

STORAGE_VERSION = 1
STORAGE_KEY = "kassalapp.storage"

LISTENER_STORAGE_KEY = "ha_kassalapp.config_listeners"

_LOGGER = logging.getLogger(__name__)


# noinspection PyArgumentList
@attr.s
class SortWeightsStoreData:
    weights = attr.ib(type=dict[str, int], factory=dict)

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    # noinspection PyTypeChecker
    def asdict(self):
        return attr.asdict(self)


@attr.s
class ConfigStoreData:
    sort_weights = attr.ib(type=dict[str:SortWeightsStoreData], factory=dict)

    @classmethod
    def from_dict(cls, data=None):
        if data is None:
            data = {}

        sort_weights = {
            k: SortWeightsStoreData.from_dict(v)
            for k, v in data.get("sort_weights", {}).items()
        }
        return cls(
            **(
                data
                | {
                    "sort_weights": sort_weights,
                }
            )
        )

    # noinspection PyTypeChecker
    def asdict(self):
        return attr.asdict(self)


class KassalappStore:
    def __init__(self, hass: HomeAssistant):
        self.store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self.listeners = []
        self.data: ConfigStoreData | None = None
        self.dirty = False

    async def save(self, force_save=False):
        if self.dirty or force_save:
            await self.store.async_save(attr.asdict(self.data))
            self.dirty = False

    async def load(self):
        stored = await self.store.async_load()
        if stored:
            self.data = ConfigStoreData.from_dict(stored)
        if self.data is None:
            self.data = ConfigStoreData()
            await self.save(True)
        self.dirty = False

    def load_weights(self, entity_id):
        return self.data.sort_weights.setdefault(
            entity_id, SortWeightsStoreData()
        ).weights

    def set_weights(self, weights, entity_id) -> None:
        self.data.sort_weights[entity_id].weights = weights
        self.dirty = True

    async def updated(self):
        self.dirty = True
        for listener in self.listeners:
            listener(attr.asdict(self.data))
        await self.save()

    def asdict(self):
        return self.data.asdict()

    def add_listener(self, callback):
        self.listeners.append(callback)

        def remove_listener():
            self.listeners.remove(callback)

        return remove_listener

    def sorted_items(self, items: list[TodoItem], entity_id):
        sort_weights = self.load_weights(entity_id)

        def sort_key(item: TodoItem):
            return sort_weights.get(item.uid, float("inf"))

        return sorted(items, key=sort_key)
