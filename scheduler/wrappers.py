from contextlib import asynccontextmanager
from typing import AsyncContextManager

from db.dao.holder import HolderDao
from scheduler.context import ScheduledContextHolder, ScheduledContext
from shvatka.services.game_play import prepare_game, start_game
from tgbot.views.game import GameBotLog, BotView


@asynccontextmanager
async def prepare_context() -> AsyncContextManager[ScheduledContext]:
    async with ScheduledContextHolder.poll() as session:
        dao = HolderDao(session=session, redis=ScheduledContextHolder.redis)
        yield ScheduledContext(
            dao=dao,
            bot=ScheduledContextHolder.bot,
            scheduler=ScheduledContextHolder.scheduler,
            game_log_chat=ScheduledContextHolder.game_log_chat,
        )


async def prepare_game_wrapper(game_id: int, author_id: int):
    async with prepare_context as context:
        author = await context.dao.player.get_by_id(author_id)
        game = await context.dao.game.get_by_id(game_id, author)
        await prepare_game(game, context.dao.game_preparer, BotView(context.bot))


async def start_game_wrapper(game_id: int, author_id: int):
    async with prepare_context as context:
        context: ScheduledContext
        author = await context.dao.player.get_by_id(author_id)
        game = await context.dao.game.get_by_id(game_id, author)
        await start_game(
            game=game,
            dao=context.dao.game_starter,
            game_log=GameBotLog(bot=context.bot, log_chat_id=context.game_log_chat),
            view=BotView(bot=context.bot),
            scheduler=context.scheduler,
        )
