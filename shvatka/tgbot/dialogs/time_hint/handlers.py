from typing import Any

from adaptix import Retort
from aiogram import types
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, SubManager
from aiogram_dialog.widgets.kbd import Button
from dishka import AsyncContainer
from dishka.integrations.aiogram import CONTAINER_NAME

from shvatka.core.models.dto import hints
from shvatka.core.utils import exceptions
from shvatka.tgbot import states
from shvatka.tgbot.views.hint_factory.hint_parser import HintParser
from shvatka.tgbot.views.hint_sender import HintSender


async def select_time(c: CallbackQuery, widget: Any, manager: DialogManager, item_id: str):
    await set_time(int(item_id), manager)


async def process_edit_time_message(m: Message, dialog_: Any, manager: DialogManager) -> None:
    try:
        time_ = int(m.text)
    except ValueError:
        await m.answer("Некорректный формат времени. Пожалуйста введите время в формате ЧЧ:ММ")
        return
    retort: Retort = manager.middleware_data["retort"]
    hint = retort.load(manager.start_data["time_hint"], hints.TimeHint)
    if not hint.can_update_time():
        await m.reply(
            "Увы, отредактировать время данной подсказки не получится. "
            "Скорее всего это загадка уровня (Подсказка 0 мин.). "
            "Придётся переделать прямо тут текст (или медиа, или что там)"
        )
        return
    manager.dialog_data["time"] = time_
    await manager.switch_to(states.TimeHintEditSG.details)


async def process_time_message(m: Message, dialog_: Any, manager: DialogManager) -> None:
    try:
        time_ = int(m.text)
    except ValueError:
        await m.answer("Некорректный формат времени. Пожалуйста введите время в формате ЧЧ:ММ")
        return
    await set_time(time_, manager)


async def edit_single_hint(c: CallbackQuery, widget: Any, manager: DialogManager):
    assert isinstance(manager, SubManager)
    dishka: AsyncContainer = manager.middleware_data[CONTAINER_NAME]
    retort = await dishka.get(Retort)
    hint = retort.load(manager.dialog_data["hints"], list[hints.AnyHint])
    hint_sender = await dishka.get(HintSender)
    chat: types.Chat = manager.middleware_data["event_chat"]
    hint_index = manager.item_id
    await hint_sender.send_hint(hint[int(hint_index)], chat.id)


async def delete_single_hint(c: CallbackQuery, widget: Any, manager: DialogManager):
    assert isinstance(manager, SubManager)
    dishka: AsyncContainer = manager.middleware_data[CONTAINER_NAME]
    retort = await dishka.get(Retort)
    hints_ = retort.load(manager.dialog_data.get("hints"), list[hints.AnyHint])
    hint_index = manager.item_id
    hints_.pop(int(hint_index))
    manager.dialog_data["hints"] = retort.dump(hints, list[hints.AnyHint])


async def delete_whole_time_hint(c: CallbackQuery, widget: Any, manager: DialogManager):
    await manager.done({"edited_time_hint": {"__deleted__": "__deleted_true__"}})


async def save_edited_time_hint(c: CallbackQuery, widget: Any, manager: DialogManager):
    dishka: AsyncContainer = manager.middleware_data[CONTAINER_NAME]
    retort = await dishka.get(Retort)
    time_hint = retort.load(manager.start_data["time_hint"], hints.TimeHint)
    try:
        time_hint.update_time(manager.dialog_data["time"])
        time_hint.update_hint(retort.load(manager.dialog_data["hints"], list[hints.AnyHint]))
    except exceptions.LevelError as e:
        assert isinstance(c.message, Message)
        await c.message.reply(e.text)
        return
    await manager.done({"edited_time_hint": retort.dump(time_hint)})


async def set_time(time_minutes: int, manager: DialogManager):
    data = manager.dialog_data
    if not isinstance(data, dict):
        data = {}
    data["time"] = int(time_minutes)
    await manager.switch_to(states.TimeHintSG.hint)


async def process_hint(m: Message, dialog_: Any, manager: DialogManager) -> None:
    retort: Retort = manager.middleware_data["retort"]
    parser: HintParser = manager.middleware_data["hint_parser"]
    hint = await parser.parse(m, manager.middleware_data["player"])
    manager.dialog_data["hints"].append(retort.dump(hint))


async def on_finish(c: CallbackQuery, button: Button, manager: DialogManager):
    retort: Retort = manager.middleware_data["retort"]
    hints_ = retort.load(manager.dialog_data["hints"], list[hints.AnyHint])
    time_ = manager.dialog_data["time"]
    time_hint = hints.TimeHint(time=time_, hint=hints_)
    await manager.done({"time_hint": retort.dump(time_hint)})


async def hint_on_start(start_data: dict, manager: DialogManager):
    prev_time = int(manager.start_data.get("previous_time", 0))
    if prev_time == -1:
        manager.dialog_data["time"] = 0
        await manager.switch_to(states.TimeHintSG.hint)
    manager.dialog_data.setdefault("hints", [])


async def hint_edit_on_start(start_data: dict, manager: DialogManager):
    retort: Retort = manager.middleware_data["retort"]
    hint = retort.load(manager.start_data["time_hint"], hints.TimeHint)
    manager.dialog_data["hints"] = retort.dump(hint.hint, list[hints.AnyHint])
    manager.dialog_data["time"] = hint.time
