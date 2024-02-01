import typing
from dataclasses import dataclass, field
from datetime import datetime
from typing import Sequence, Generic

from shvatka.core.models import dto
from shvatka.core.models.dto import scn
from shvatka.core.models.enums import GameStatus

T = typing.TypeVar("T")


@dataclass
class Page(Generic[T]):
    content: Sequence[T]


@dataclass
class Player:
    id: int
    can_be_author: bool

    @classmethod
    def from_core(cls, core: dto.Player):
        return cls(
            id=core.id,
            can_be_author=core.can_be_author,
        )


@dataclass
class Team:
    id: int
    name: str
    captain: Player | None
    description: str | None

    @classmethod
    def from_core(cls, core: dto.Team):
        return cls(
            id=core.id,
            name=core.name,
            captain=Player.from_core(core.captain) if core.captain else None,
            description=core.description,
        )


@dataclass
class Game:
    id: int
    author: Player
    name: str
    status: GameStatus
    start_at: datetime | None

    @classmethod
    def from_core(cls, core: dto.Game | None):
        if core is None:
            return None
        return cls(
            id=core.id,
            author=Player.from_core(core.author),
            name=core.name,
            status=core.status,
            start_at=core.start_at,
        )


@dataclass
class Level:
    db_id: int
    name_id: str
    author: Player
    scenario: scn.LevelScenario
    game_id: int | None = None
    number_in_game: int | None = None

    @classmethod
    def from_core(cls, core: dto.Level | None = None):
        if core is None:
            return None
        return cls(
            db_id=core.db_id,
            name_id=core.name_id,
            author=Player.from_core(core.author),
            scenario=core.scenario,
            game_id=core.game_id,
            number_in_game=core.number_in_game,
        )


@dataclass
class FullGame:
    id: int
    author: Player
    name: str
    status: GameStatus
    start_at: datetime | None
    levels: list[Level] = field(default_factory=list)

    @classmethod
    def from_core(cls, core: dto.FullGame | None = None):
        if core is None:
            return None
        return cls(
            id=core.id,
            author=Player.from_core(core.author),
            name=core.name,
            status=core.status,
            start_at=core.start_at,
            levels=[Level.from_core(level) for level in core.levels],
        )
