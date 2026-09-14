from datetime import datetime
from pathlib import Path

import pytest
from nonebug import App

from tests.test_commands import make_group_event


@pytest.fixture
def store(tmp_path: Path, monkeypatch):
    from nonebot_plugin_xianmei import config

    s = config.Store(tmp_path / "state.json")
    monkeypatch.setattr(config, "_store", s)
    return s


@pytest.fixture(autouse=True)
def library(monkeypatch):
    from nonebot_plugin_xianmei import quips

    monkeypatch.setattr(quips, "_library", quips.QuipLibrary(["固定彩虹屁"]))


async def test_owner_speaking_gets_flattered(app: App, store):
    from nonebot.adapters.onebot.v11 import Bot

    from nonebot_plugin_xianmei import flatter
    from nonebot_plugin_xianmei.config import GroupState

    store.put("12345", GroupState(owner_qq="888"))
    async with app.test_matcher(flatter) as ctx:
        bot = ctx.create_bot(base=Bot, self_id="100001")
        event = make_group_event(888, "大家晚上好")
        ctx.receive_event(bot, event)
        ctx.should_pass_rule(flatter)
        ctx.should_pass_permission(flatter)
        ctx.should_call_send(event, "🔔 检测到 五冠王桃神 出现！", result=True)
        ctx.should_call_send(event, "🫡 开始献媚！", result=True)
        ctx.should_call_send(event, "固定彩虹屁", result=True)
        ctx.should_finished(flatter)
    state = store.get("12345")
    assert state.today_count == 1
    assert state.last_trigger_ts > 0


async def test_cooldown_blocks_second_message(app: App, store):
    from nonebot.adapters.onebot.v11 import Bot

    from nonebot_plugin_xianmei import flatter
    from nonebot_plugin_xianmei.config import GroupState

    store.put("12345", GroupState(owner_qq="888"))
    async with app.test_matcher(flatter) as ctx:
        bot = ctx.create_bot(base=Bot, self_id="100001")
        event1 = make_group_event(888, "第一句")
        ctx.receive_event(bot, event1)
        ctx.should_call_send(event1, "🔔 检测到 五冠王桃神 出现！", result=True)
        ctx.should_call_send(event1, "🫡 开始献媚！", result=True)
        ctx.should_call_send(event1, "固定彩虹屁", result=True)
        ctx.should_finished(flatter)
        event2 = make_group_event(888, "第二句")
        ctx.receive_event(bot, event2)


async def test_non_owner_ignored(app: App, store):
    from nonebot.adapters.onebot.v11 import Bot

    from nonebot_plugin_xianmei import flatter
    from nonebot_plugin_xianmei.config import GroupState

    store.put("12345", GroupState(owner_qq="888"))
    async with app.test_matcher(flatter) as ctx:
        bot = ctx.create_bot(base=Bot, self_id="100001")
        event = make_group_event(777, "我是路人")
        ctx.receive_event(bot, event)
    assert store.get("12345").today_count == 0


async def test_disabled_group_ignored(app: App, store):
    from nonebot.adapters.onebot.v11 import Bot

    from nonebot_plugin_xianmei import flatter
    from nonebot_plugin_xianmei.config import GroupState

    store.put("12345", GroupState(owner_qq="888", enabled=False))
    async with app.test_matcher(flatter) as ctx:
        bot = ctx.create_bot(base=Bot, self_id="100001")
        event = make_group_event(888, "大家晚上好")
        ctx.receive_event(bot, event)
    assert store.get("12345").today_count == 0


async def test_daily_cap_blocks(app: App, store):
    from nonebot.adapters.onebot.v11 import Bot

    from nonebot_plugin_xianmei import flatter
    from nonebot_plugin_xianmei.config import GroupState

    today = datetime.now().date().isoformat()
    store.put("12345", GroupState(owner_qq="888", today_count=5, today_date=today))
    async with app.test_matcher(flatter) as ctx:
        bot = ctx.create_bot(base=Bot, self_id="100001")
        event = make_group_event(888, "大家晚上好")
        ctx.receive_event(bot, event)
    assert store.get("12345").today_count == 5


async def test_announce_name_fallback(app: App, store):
    from nonebot.adapters.onebot.v11 import Bot

    from nonebot_plugin_xianmei import flatter
    from nonebot_plugin_xianmei.config import GroupState

    store.put("12345", GroupState(owner_qq="888"))
    async with app.test_matcher(flatter) as ctx:
        bot = ctx.create_bot(base=Bot, self_id="100001")
        event = make_group_event(888, "大家晚上好", card="", nickname="")
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "🔔 检测到 桃神 出现！", result=True)
        ctx.should_call_send(event, "🫡 开始献媚！", result=True)
        ctx.should_call_send(event, "固定彩虹屁", result=True)
        ctx.should_finished(flatter)


async def test_announce_name_from_nickname(app: App, store):
    from nonebot.adapters.onebot.v11 import Bot

    from nonebot_plugin_xianmei import flatter
    from nonebot_plugin_xianmei.config import GroupState

    store.put("12345", GroupState(owner_qq="888"))
    async with app.test_matcher(flatter) as ctx:
        bot = ctx.create_bot(base=Bot, self_id="100001")
        event = make_group_event(888, "大家晚上好", card="", nickname="小桃桃")
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "🔔 检测到 小桃桃 出现！", result=True)
        ctx.should_call_send(event, "🫡 开始献媚！", result=True)
        ctx.should_call_send(event, "固定彩虹屁", result=True)
        ctx.should_finished(flatter)
