from typing import Protocol

from shvatka.core.interfaces.dal.organizer import OrgByPlayerGetter
from shvatka.core.models import dto


class GameKeyGetter(Protocol):
    async def get_typed_keys_grouped(self, game: dto.Game) -> dict[dto.Team, list[dto.KeyTime]]:
        raise NotImplementedError


class TypedKeyGetter(GameKeyGetter, OrgByPlayerGetter, Protocol):
    pass


class TeamKeysMerger(Protocol):
    async def replace_team_keys(self, primary: dto.Team, secondary: dto.Team):
        raise NotImplementedError


class PlayerKeysMerger(Protocol):
    async def replace_player_keys(self, primary: dto.Player, secondary: dto.Player):
        raise NotImplementedError
