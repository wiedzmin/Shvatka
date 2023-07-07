from datetime import datetime, timedelta

import pytest
from dataclass_factory import Factory
from mockito import mock, when, ANY

from shvatka.core.interfaces.clients.file_storage import FileStorage
from shvatka.core.interfaces.scheduler import Scheduler
from shvatka.core.models import dto
from shvatka.core.models.enums import GameStatus
from shvatka.core.models.enums.played import Played
from shvatka.core.services.game import start_waivers
from shvatka.core.services.game_play import start_game, send_hint, check_key, get_available_hints
from shvatka.core.services.game_stat import get_typed_keys
from shvatka.core.services.organizers import get_orgs
from shvatka.core.services.player import join_team
from shvatka.core.services.waiver import add_vote, approve_waivers
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.core.utils.key_checker_lock import KeyCheckerFactory
from shvatka.core.views.game import (
    GameLogWriter,
    OrgNotifier,
    LevelUp,
    GameLogEvent,
    GameLogType,
)
from shvatka.infrastructure.db import models
from shvatka.infrastructure.db.dao.holder import HolderDao
from tests.mocks.aiogram_mocks import mock_coro
from tests.mocks.game_view import GameViewMock
from tests.utils.time_key import assert_time_key


@pytest.mark.asyncio
async def test_game_play(
    dao: HolderDao,
    locker: KeyCheckerFactory,
    check_dao: HolderDao,
    scheduler: Scheduler,
    author: dto.Player,
    harry: dto.Player,
    hermione: dto.Player,
    gryffindor: dto.Team,
    game: dto.FullGame,
):
    await start_waivers(game, author, dao.game)

    await join_team(hermione, gryffindor, harry, dao.team_player)
    await add_vote(game, gryffindor, harry, Played.yes, dao.waiver_vote_adder)
    await add_vote(game, gryffindor, hermione, Played.yes, dao.waiver_vote_adder)
    await approve_waivers(game, gryffindor, harry, dao.waiver_approver)

    dummy_view = GameViewMock()
    dummy_log = mock(GameLogWriter)
    when(dummy_log).log(GameLogEvent(GameLogType.GAME_STARTED, {"game": game.name})).thenReturn(
        mock_coro(None)
    )
    dummy_sched = mock(Scheduler)
    when(dummy_sched).plain_hint(
        level=game.levels[0], team=gryffindor, hint_number=1, run_at=ANY
    ).thenReturn(mock_coro(None))
    game.start_at = datetime.now(tz=tz_utc)
    await start_game(game, dao.game_starter, dummy_log, dummy_view, dummy_sched)
    dummy_view.assert_send_only_puzzle(gryffindor, game.levels[0])
    assert 1 == await check_dao.level_time.count()

    when(dummy_sched).plain_hint(game.levels[0], gryffindor, 2, ANY).thenReturn(mock_coro(None))
    await send_hint(
        level=game.levels[0],
        hint_number=1,
        team=gryffindor,
        dao=dao.level_time,
        view=dummy_view,
        scheduler=dummy_sched,
    )
    dummy_view.assert_send_only_hint(gryffindor, 1, game.levels[0])

    dummy_org_notifier = mock(OrgNotifier)
    orgs = await get_orgs(game, dao.organizer)
    key_kwargs = dict(
        player=harry,
        team=gryffindor,
        game=game,
        dao=dao.game_player,
        view=dummy_view,
        game_log=dummy_log,
        org_notifier=dummy_org_notifier,
        locker=locker,
        scheduler=scheduler,
    )
    await check_key(key="SHWRONG", **key_kwargs)
    keys = await get_typed_keys(game=game, player=author, dao=check_dao.typed_keys)

    assert [gryffindor] == list(keys.keys())
    assert 1 == len(keys[gryffindor])
    expected_key = dto.KeyTime(
        text="SHWRONG",
        is_correct=False,
        is_duplicate=False,
        at=datetime.now(tz=tz_utc),
        level_number=0,
        player=harry,
        team=gryffindor,
    )
    assert_time_key(expected_key, list(keys[gryffindor])[0])
    dummy_view.assert_wrong_key_only(expected_key)

    await check_key(key="SH123", **key_kwargs)
    expected_key = dto.KeyTime(
        text="SH123",
        is_correct=True,
        is_duplicate=False,
        at=datetime.now(tz=tz_utc),
        level_number=0,
        player=harry,
        team=gryffindor,
    )
    dummy_view.assert_correct_key_only(expected_key)

    await check_key(key="SH123", **key_kwargs)
    expected_key = dto.KeyTime(
        text="SH123",
        is_correct=True,
        is_duplicate=True,
        at=datetime.now(tz=tz_utc),
        level_number=0,
        player=harry,
        team=gryffindor,
    )
    dummy_view.assert_duplicate_key_only(expected_key)

    when(dummy_org_notifier).notify(
        LevelUp(team=gryffindor, new_level=game.levels[1], orgs_list=orgs)
    ).thenReturn(mock_coro(None))
    await check_key(key="SH321", **key_kwargs)
    expected_key = dto.KeyTime(
        text="SH321",
        is_correct=True,
        is_duplicate=False,
        at=datetime.now(tz=tz_utc),
        level_number=0,
        player=harry,
        team=gryffindor,
    )
    dummy_view.assert_correct_key_only(expected_key)
    dummy_view.assert_send_only_puzzle(gryffindor, game.levels[1])

    when(dummy_log).log(GameLogEvent(GameLogType.GAME_FINISHED, {"game": game.name})).thenReturn(
        mock_coro(None)
    )
    when(dummy_org_notifier).notify(
        LevelUp(team=gryffindor, new_level=game.levels[1], orgs_list=orgs)
    ).thenReturn(mock_coro(None))
    await check_key(key="SHOOT", **key_kwargs)
    expected_key = dto.KeyTime(
        text="SHOOT",
        is_correct=True,
        is_duplicate=False,
        at=datetime.now(tz=tz_utc),
        level_number=1,
        player=harry,
        team=gryffindor,
    )
    dummy_view.assert_correct_key_only(expected_key)
    dummy_view.assert_game_finished_only(gryffindor)
    dummy_view.assert_game_finished_all({gryffindor})

    keys = await get_typed_keys(game=game, player=author, dao=check_dao.typed_keys)

    assert [gryffindor] == list(keys.keys())
    assert 5 == len(keys[gryffindor])
    assert_time_key(
        dto.KeyTime(
            text="SHWRONG",
            is_correct=False,
            is_duplicate=False,
            at=datetime.now(tz=tz_utc),
            level_number=0,
            player=harry,
            team=gryffindor,
        ),
        list(keys[gryffindor])[0],
    )
    assert_time_key(
        dto.KeyTime(
            text="SH123",
            is_correct=True,
            is_duplicate=False,
            at=datetime.now(tz=tz_utc),
            level_number=0,
            player=harry,
            team=gryffindor,
        ),
        list(keys[gryffindor])[1],
    )
    assert_time_key(
        dto.KeyTime(
            text="SH123",
            is_correct=True,
            is_duplicate=True,
            at=datetime.now(tz=tz_utc),
            level_number=0,
            player=harry,
            team=gryffindor,
        ),
        list(keys[gryffindor])[2],
    )
    assert_time_key(
        dto.KeyTime(
            text="SH321",
            is_correct=True,
            is_duplicate=False,
            at=datetime.now(tz=tz_utc),
            level_number=0,
            player=harry,
            team=gryffindor,
        ),
        list(keys[gryffindor])[3],
    )
    assert_time_key(
        dto.KeyTime(
            text="SHOOT",
            is_correct=True,
            is_duplicate=False,
            at=datetime.now(tz=tz_utc),
            level_number=0,
            player=harry,
            team=gryffindor,
        ),
        list(keys[gryffindor])[4],
    )
    assert await dao.game_player.is_all_team_finished(game)
    assert GameStatus.finished == (await dao.game.get_by_id(game.id, author)).status
    dummy_view.assert_no_unchecked()


@pytest.mark.asyncio
async def test_get_current_hints(
    game: dto.FullGame,
    dao: HolderDao,
    dcf: Factory,
    locker: KeyCheckerFactory,
    file_storage: FileStorage,
    author: dto.Player,
    harry: dto.Player,
    hermione: dto.Player,
    gryffindor: dto.Team,
):
    await start_waivers(game, author, dao.game)

    await join_team(hermione, gryffindor, harry, dao.team_player)
    await add_vote(game, gryffindor, harry, Played.yes, dao.waiver_vote_adder)
    await add_vote(game, gryffindor, hermione, Played.yes, dao.waiver_vote_adder)
    await approve_waivers(game, gryffindor, harry, dao.waiver_approver)
    level_time = models.LevelTime(
        game_id=game.id,
        team_id=gryffindor.id,
        level_number=0,
        start_at=datetime.now(tz=tz_utc) - timedelta(minutes=1),
    )
    dao.level_time._save(level_time)
    await dao.commit()
    actual_hints = await get_available_hints(game, gryffindor, dao.game_player)
    assert len(actual_hints) == 2
