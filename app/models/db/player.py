from sqlalchemy import Column, BigInteger, ForeignKey
from sqlalchemy.orm import relationship

from app.models.db.base import Base


class Player(Base):
    __tablename__ = "players"
    __mapper_args__ = {"eager_defaults": True}
    id = Column(BigInteger, primary_key=True)
    user_id = Column(ForeignKey("users.id"))
    user = relationship(
        "User",
        back_populates="player",
        foreign_keys=user_id,
        uselist=False,
    )

    my_games = relationship(
        "Game",
        back_populates="author",
        foreign_keys="Game.author_id",
    )
    my_levels = relationship(
        "Level",
        back_populates="author",
        foreign_keys="Level.author_id",
    )
    typed_keys = relationship(
        "KeyTime",
        back_populates="player",
        foreign_keys="KeyTime.player_id",
    )
    organizers = relationship(
        "Organizer",
        back_populates="player",
        foreign_keys="Organizer.player_id",
    )
    played_games = relationship(
        "Waiver",
        back_populates="player",
        foreign_keys="Waiver.player_id",
    )
    teams = relationship(
        "PlayerInTeam",
        back_populates="player",
        foreign_keys="PlayerInTeam.player_id",
    )
    captain_by_team = relationship(
        "Team",
        back_populates="captain",
        foreign_keys="Team.captain_id",
    )

    def __repr__(self):
        return (
            f"<Player "
            f"id={self.id} "
            f"user_id={self.user_id} "
            f">"
        )
