from pathlib import Path

from nonebot_plugin_xianmei.config import GroupState, Store


def test_default_state():
    state = GroupState()
    assert state.owner_qq is None
    assert state.daily_limit == 5
    assert state.cooldown_minutes == 30
    assert state.enabled is True
    assert state.last_trigger_ts == 0.0
    assert state.today_count == 0
    assert state.today_date == ""


def test_get_missing_group_returns_default(tmp_path: Path):
    store = Store(tmp_path / "state.json")
    assert store.get("12345") == GroupState()


async def test_put_and_get(tmp_path: Path):
    store = Store(tmp_path / "state.json")
    state = GroupState(owner_qq="888", daily_limit=9)
    store.put("12345", state)
    assert store.get("12345").owner_qq == "888"
    assert store.get("12345").daily_limit == 9
    assert store.get("99999") == GroupState()


async def test_save_and_reload(tmp_path: Path):
    path = tmp_path / "state.json"
    store = Store(path)
    store.put("12345", GroupState(owner_qq="888", today_count=3, today_date="2026-09-11"))
    await store.save()

    store2 = Store(path)
    state = store2.get("12345")
    assert state.owner_qq == "888"
    assert state.today_count == 3
    assert state.today_date == "2026-09-11"


async def test_save_creates_parent_dir(tmp_path: Path):
    path = tmp_path / "sub" / "dir" / "state.json"
    store = Store(path)
    store.put("1", GroupState(owner_qq="888"))
    await store.save()
    assert path.exists()


def test_corrupted_file_starts_empty(tmp_path: Path):
    path = tmp_path / "state.json"
    path.write_text("{not valid json", encoding="utf-8")
    store = Store(path)
    assert store.get("12345") == GroupState()
