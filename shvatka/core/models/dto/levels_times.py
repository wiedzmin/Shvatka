from dataclasses import dataclass
from datetime import datetime

from .game import Game
from .team import Team


@dataclass
class LevelTime:
    id: int
    game: Game
    team: Team
    level_number: int
    start_at: datetime

    def to_on_game(self, levels_count: int):
        is_finished = self.level_number > levels_count
        return LevelTimeOnGame(
            id=self.id,
            game=self.game,
            team=self.team,
            level_number=self.level_number,
            start_at=self.start_at,
            is_finished=is_finished,
        )

    def __repr__(self) -> str:
        return (
            f"<LevelTime team={self.team} level_number={self.level_number} "
            f"at={self.start_at.isoformat()}>"
        )


@dataclass
class LevelTimeOnGame(LevelTime):
    is_finished: bool

    def __repr__(self):
        return super().__repr__()


@dataclass
class GameStat:
    level_times: dict[Team, list[LevelTimeOnGame]]
