import logging

from aiogram import Dispatcher
from aiogram.dispatcher.filters import Command, ContentTypesFilter
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove, ContentType
from aiogram.utils.markdown import html_decoration as hd

from app.dao.holder import HolderDao
from app.models import dto
from app.services.chat import update_chat_id
from app.views.commands import CANCEL_COMMAND, CHAT_ID_COMMAND

logger = logging.getLogger(__name__)


async def chat_id(message: Message):
    text = (
        f"id этого чата: {hd.pre(message.chat.id)}\n"
        f"Ваш id: {hd.pre(message.from_user.id)}"
    )
    if message.reply_to_message:
        text += (
            f"\nid {hd.bold(message.reply_to_message.from_user.full_name)}: "
            f"{hd.pre(message.reply_to_message.from_user.id)}"
        )
    await message.reply(text, disable_notification=True)


async def cancel_state(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    logger.info('Cancelling state %s', current_state)
    # Cancel state and inform user about it
    await state.clear()
    # And remove keyboard (just in case)
    await message.reply('Диалог прекращён, данные удалены', reply_markup=ReplyKeyboardRemove())


async def chat_migrate(message: Message, chat: dto.Chat, dao: HolderDao):
    new_id = message.migrate_to_chat_id
    await update_chat_id(chat, new_id, dao.chat)
    logger.info("Migrate chat from %s to %s", message.chat.id, new_id)


def setup(dp: Dispatcher):
    dp.message.register(
        chat_id, Command(commands=["idchat", CHAT_ID_COMMAND.command], commands_prefix="/!")
    )
    dp.message.register(cancel_state, Command(commands=CANCEL_COMMAND.command))
    dp.message.register(
        chat_migrate, ContentTypesFilter(content_types=ContentType.MIGRATE_TO_CHAT_ID)
    )
