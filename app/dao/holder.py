from sqlalchemy.ext.asyncio import AsyncSession

from app.dao import (
    ChatDao, UserDao, FileInfoDao, GameDao, LevelDao,
    LevelTimeDao, KeyTimeDao, OrganizerDao, PlayerDao,
    PlayerInTeamDao, TeamDao, WaiverDao,
)


class HolderDao:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user = UserDao(self.session)
        self.chat = ChatDao(self.session)
        self.file_info = FileInfoDao(self.session)
        self.game = GameDao(self.session)
        self.level = LevelDao(self.session)
        self.level_time = LevelTimeDao(self.session)
        self.key_time = KeyTimeDao(self.session)
        self.organizer = OrganizerDao(self.session)
        self.player = PlayerDao(self.session)
        self.player_in_team = PlayerInTeamDao(self.session)
        self.team = TeamDao(self.session)
        self.waiver = WaiverDao(self.session)

    async def commit(self):
        await self.session.commit()
