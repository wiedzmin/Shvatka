from typing import Protocol

from shvatka.core.interfaces.dal.base import Committer
from shvatka.core.models import dto


class ChatUpserter(Committer, Protocol):
    async def upsert_chat(self, chat: dto.Chat) -> dto.Chat:
        raise NotImplementedError


class ChatIdUpdater(Committer, Protocol):
    async def update_chat_id(self, chat: dto.Chat, new_id: int) -> None:
        raise NotImplementedError


class TeamChatChanger(Committer, Protocol):
    async def change_team_chat(self, chat: dto.Chat, team: dto.Team) -> None:
        raise NotImplementedError
