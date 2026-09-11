from datetime import datetime

from nonebot_plugin_xianmei.config import GroupState
from nonebot_plugin_xianmei.trigger import decide, status_text

NOW = datetime(2026, 9, 11, 20, 30, 0)


def make_state(**kwargs) -> GroupState:
    return GroupState(owner_qq="888", **kwargs)


def test_owner_triggers():
    should, new = decide(make_state(), "888", NOW)
    assert should is True
    assert new.today_count == 1
    assert new.last_trigger_ts == NOW.timestamp()
    assert new.today_date == "2026-09-11"


def test_non_owner_ignored():
    should, _ = decide(make_state(), "777", NOW)
    assert should is False


def test_owner_not_set():
    should, _ = decide(GroupState(), "888", NOW)
    assert should is False


def test_disabled():
    should, _ = decide(make_state(enabled=False), "888", NOW)
    assert should is False


def test_cooldown_blocks():
    state = make_state(last_trigger_ts=NOW.timestamp() - 60, today_count=1, today_date="2026-09-11")
    should, _ = decide(state, "888", NOW)
    assert should is False


def test_cooldown_expired():
    state = make_state(last_trigger_ts=NOW.timestamp() - 31 * 60, today_count=1, today_date="2026-09-11")
    should, new = decide(state, "888", NOW)
    assert should is True
    assert new.today_count == 2


def test_daily_limit_blocks():
    state = make_state(today_count=5, today_date="2026-09-11")
    should, _ = decide(state, "888", NOW)
    assert should is False


def test_new_day_resets_count():
    state = make_state(today_count=5, today_date="2026-09-10")
    should, new = decide(state, "888", NOW)
    assert should is True
    assert new.today_count == 1
    assert new.today_date == "2026-09-11"


def test_limit_customized():
    state = make_state(daily_limit=2, today_count=2, today_date="2026-09-11")
    should, _ = decide(state, "888", NOW)
    assert should is False


def test_original_state_not_mutated():
    state = make_state()
    decide(state, "888", NOW)
    assert state.today_count == 0


def test_status_text():
    state = make_state(today_count=2, today_date="2026-09-11")
    text = status_text(state)
    assert "888" in text
    assert "5 条" in text
    assert "30 分钟" in text
    assert "2 条" in text
    assert "开启" in text
