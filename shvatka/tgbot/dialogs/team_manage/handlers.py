import typing
from typing import Any

from aiogram import Bot
from aiogram.types import Message, CallbackQuery
from aiogram.utils.text_decorations import html_decoration as hd
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button

from shvatka.core.models import dto
from shvatka.core.models import enums
from shvatka.core.services.player import (
    get_my_team,
    get_full_team_player,
    flip_permission,
    get_team_player_by_player,
    get_player_by_id,
    leave,
    change_role,
    change_emoji,
    get_player_by_user_id,
    join_team,
)
from shvatka.core.services.team import (
    rename_team,
    change_team_desc,
)
from shvatka.core.utils import exceptions
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot import keyboards as kb
from shvatka.tgbot import states
from shvatka.tgbot.utils.data import MiddlewareData
from shvatka.tgbot.views.utils import total_remove_msg


async def rename_team_handler(
    m: Message, widget: Any, dialog_manager: DialogManager, new_name: str
):
    dao: HolderDao = dialog_manager.middleware_data["dao"]
    player: dto.Player = dialog_manager.middleware_data["player"]
    team = await get_my_team(player=player, dao=dao.team_player)
    team_player = await get_full_team_player(player=player, team=team, dao=dao.team_player)
    await rename_team(team=team, captain=team_player, new_name=new_name, dao=dao.team)


async def change_desc_team_handler(
    m: Message, widget: Any, dialog_manager: DialogManager, new_desc: str
):
    dao: HolderDao = dialog_manager.middleware_data["dao"]
    player: dto.Player = dialog_manager.middleware_data["player"]
    team = await get_my_team(player=player, dao=dao.team_player)
    team_player = await get_full_team_player(player=player, team=team, dao=dao.team_player)
    await change_team_desc(team=team, captain=team_player, new_desc=new_desc, dao=dao.team)


async def select_player(c: CallbackQuery, widget: Any, manager: DialogManager, player_id: str):
    data = manager.dialog_data
    data["selected_player_id"] = int(player_id)
    await manager.switch_to(states.CaptainsBridgeSG.player)


async def change_permission_handler(c: CallbackQuery, button: Button, manager: DialogManager):
    await c.answer()
    dao: HolderDao = manager.middleware_data["dao"]
    captain: dto.Player = manager.middleware_data["player"]
    team = await get_my_team(captain, dao.team_player)
    captain_team_player = await get_full_team_player(captain, team, dao.team_player)
    player_id = manager.dialog_data["selected_player_id"]
    player = await get_player_by_id(player_id, dao.player)
    team_player = await get_team_player_by_player(player, dao.team_player)
    assert button.widget_id
    permission = enums.TeamPlayerPermission[button.widget_id]
    await flip_permission(captain_team_player, team_player, permission, dao.team_player)


async def start_merge(c: CallbackQuery, button: Button, manager: DialogManager):
    data = typing.cast(MiddlewareData, manager.middleware_data)
    dao = data["dao"]
    captain = data["player"]
    assert captain
    team = await get_my_team(captain, dao.team_player)
    assert team
    await manager.start(states.MergeTeamsSG.main, data={"team_id": team.id})


async def remove_player_handler(c: CallbackQuery, button: Button, manager: DialogManager):
    await c.answer()
    dao: HolderDao = manager.middleware_data["dao"]
    captain: dto.Player = manager.middleware_data["player"]
    player_id = manager.dialog_data["selected_player_id"]
    player = await get_player_by_id(player_id, dao.player)
    await leave(player=player, remover=captain, dao=dao.team_leaver)
    bot: Bot = manager.middleware_data["bot"]
    team = await get_my_team(captain, dao.team_player)
    assert team
    await bot.send_message(
        chat_id=team.get_chat_id(),
        text=f"Игрок {hd.quote(player.name_mention)} был исключён из команды.",
    )
    await manager.switch_to(state=states.CaptainsBridgeSG.players)


async def change_role_handler(m: Message, widget: Any, manager: DialogManager, role: str):
    dao: HolderDao = manager.middleware_data["dao"]
    captain: dto.Player = manager.middleware_data["player"]
    player_id = manager.dialog_data["selected_player_id"]
    player = await get_player_by_id(player_id, dao.player)
    team = await get_my_team(captain, dao.team_player)
    await change_role(player, team, captain, role, dao.team_player)
    await manager.switch_to(states.CaptainsBridgeSG.player)


async def change_emoji_handler(m: Message, widget: Any, manager: DialogManager, emoji: str):
    dao: HolderDao = manager.middleware_data["dao"]
    captain: dto.Player = manager.middleware_data["player"]
    player_id = manager.dialog_data["selected_player_id"]
    player = await get_player_by_id(player_id, dao.player)
    team = await get_my_team(captain, dao.team_player)
    await change_emoji(player, team, captain, emoji, dao.team_player)
    await manager.switch_to(states.CaptainsBridgeSG.player)


async def send_user_request(c: CallbackQuery, widget: Any, manager: DialogManager):
    assert isinstance(c.message, Message)
    msg = await c.message.answer(
        "Чтобы добавить игрока <b><u>нажми кнопку в самом низу</u></b>",
        reply_markup=kb.get_user_request_kb(),
    )
    manager.dialog_data["user_request_message"] = msg.message_id


async def gotten_user_request(m: Message, widget: Any, manager: DialogManager):
    assert m.user_shared
    target_id = m.user_shared.user_id
    dao: HolderDao = manager.middleware_data["dao"]
    captain: dto.Player = manager.middleware_data["player"]
    team = await get_my_team(captain, dao.team_player)
    assert team
    player = await get_player_by_user_id(target_id, dao.player)
    bot: Bot = manager.middleware_data["bot"]
    chat: dto.Chat = manager.middleware_data["chat"]
    try:
        await join_team(player, team, captain, dao.team_player)
    except exceptions.PlayerAlreadyInTeam as e:
        return await bot.send_message(
            chat_id=captain.get_chat_id(),
            text=f"‼️Игрок {hd.quote(player.name_mention)} уже находится в команде "
            f"({hd.quote(e.team.name)}).\n",  # type: ignore
        )
    except exceptions.PlayerRestoredInTeam:
        await bot.send_message(
            chat_id=captain.get_chat_id(),
            text="Игрок возвращён в команду, я сделаю вид что и не покидал",
        )
    else:
        await bot.send_message(
            chat_id=captain.get_chat_id(),
            text=f"В команду {hd.bold(team.name)} добавлен игрок {hd.bold(player.name_mention)}",
        )
    await total_remove_msg(
        bot, chat_id=chat.tg_id, msg_id=manager.dialog_data.pop("user_request_message")
    )
    await manager.switch_to(states.CaptainsBridgeSG.players)


async def remove_user_request(c: CallbackQuery, widget: Any, manager: DialogManager):
    bot: Bot = manager.middleware_data["bot"]
    chat: dto.Chat = manager.middleware_data["chat"]
    await total_remove_msg(
        bot, chat_id=chat.tg_id, msg_id=manager.dialog_data.pop("user_request_message")
    )
