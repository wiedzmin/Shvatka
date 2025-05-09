from adaptix import Retort
from aiogram_dialog import DialogManager

import shvatka.core.models.dto.action.keys
from shvatka.core.models.dto import hints


async def get_level_id(dialog_manager: DialogManager, **_):
    return {
        "level_id": dialog_manager.dialog_data.get("level_id", None)
        or dialog_manager.start_data["level_id"]
    }


async def get_keys(dialog_manager: DialogManager, **_):
    return {
        "keys": dialog_manager.dialog_data.get("keys", dialog_manager.start_data.get("keys", [])),
    }


async def get_bonus_keys(dialog_manager: DialogManager, **_):
    retort: Retort = dialog_manager.middleware_data["retort"]
    keys_raw = dialog_manager.dialog_data.get(
        "bonus_keys", dialog_manager.start_data.get("bonus_keys", [])
    )
    return {
        "bonus_keys": retort.load(keys_raw, list[shvatka.core.models.dto.action.keys.BonusKey]),
    }


async def get_level_data(dialog_manager: DialogManager, **_):
    dialog_data = dialog_manager.dialog_data
    retort: Retort = dialog_manager.middleware_data["retort"]
    hints_ = retort.load(dialog_data.get("time_hints", []), list[hints.TimeHint])
    return {
        "level_id": dialog_data["level_id"],
        "keys": dialog_data.get("keys", []),
        "bonus_keys": dialog_data.get("bonus_keys", []),
        "time_hints": hints_,
    }


async def get_time_hints(dialog_manager: DialogManager, **_):
    dialog_data = dialog_manager.dialog_data
    retort: Retort = dialog_manager.middleware_data["retort"]
    hints_ = retort.load(dialog_data.get("time_hints", []), list[hints.TimeHint])
    return {
        "level_id": dialog_manager.start_data["level_id"],
        "time_hints": hints_,
    }
