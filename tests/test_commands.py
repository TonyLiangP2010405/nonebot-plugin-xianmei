from pathlib import Path

import pytest
from nonebug import App

from nonebot_plugin_xianmei.commands import parse_bounded_int, parse_qq


def test_parse_qq_valid():
    assert parse_qq("6867955") == "6867955"


def test_parse_qq_rejects_junk():
    assert parse_qq("abc") is None
    assert parse_qq("1234") is None
    assert parse_qq("123456789012") is None
    assert parse_qq("") is None


def test_parse_bounded_int():
    assert parse_bounded_int("5", 1, 100) == 5
    assert parse_bounded_int("0", 1, 100) is None
    assert parse_bounded_int("101", 1, 100) is None
    assert parse_bounded_int("x", 1, 100) is None


def make_group_event(user_id: int, message: str):
    from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message

    return GroupMessageEvent(
        time=0,
        self_id=100001,
        post_type="message",
        message_type="group",
        sub_type="normal",
        message_id=1,
        user_id=user_id,
        group_id=12345,
        message=Message(message),
        raw_message=message,
        font=0,
        sender={
            "user_id": user_id,
            "nickname": "n",
            "card": "",
            "sex": "unknown",
            "age": 0,
            "area": "",
            "level": "1",
            "role": "member",
            "title": "",
        },
    )


@pytest.fixture
def store(tmp_path: Path, monkeypatch):
    from nonebot_plugin_xianmei import config

    s = config.Store(tmp_path / "state.json")
    monkeypatch.setattr(config, "_store", s)
    return s


@pytest.fixture
def library(monkeypatch):
    from nonebot_plugin_xianmei import quips

    monkeypatch.setattr(quips, "_library", quips.QuipLibrary(["固定彩虹屁"]))


async def test_set_owner_superuser(app: App, store):
    from nonebot.adapters.onebot.v11 import Bot

    from nonebot_plugin_xianmei.commands import matcher_set_owner

    async with app.test_matcher(matcher_set_owner) as ctx:
        bot = ctx.create_bot(base=Bot, self_id="100001")
        event = make_group_event(999, "/献媚设置群主 6867955")
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher_set_owner)
        ctx.should_call_send(event, "✅ 已绑定本群桃神：6867955\n桃神出现时将自动献媚~", result=True)
        ctx.should_finished(matcher_set_owner)
    assert store.get("12345").owner_qq == "6867955"


async def test_set_owner_non_superuser_rejected(app: App, store):
    from nonebot.adapters.onebot.v11 import Bot

    from nonebot_plugin_xianmei.commands import matcher_set_owner

    async with app.test_matcher(matcher_set_owner) as ctx:
        bot = ctx.create_bot(base=Bot, self_id="100001")
        event = make_group_event(555, "/献媚设置群主 6867955")
        ctx.receive_event(bot, event)
        ctx.should_not_pass_permission(matcher_set_owner)
    assert store.get("12345").owner_qq is None


async def test_set_owner_invalid_arg(app: App, store):
    from nonebot.adapters.onebot.v11 import Bot

    from nonebot_plugin_xianmei.commands import matcher_set_owner

    async with app.test_matcher(matcher_set_owner) as ctx:
        bot = ctx.create_bot(base=Bot, self_id="100001")
        event = make_group_event(999, "/献媚设置群主 abc")
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher_set_owner)
        ctx.should_call_send(event, "用法：献媚设置群主 <QQ号>（5~11 位数字）", result=True)
        ctx.should_finished(matcher_set_owner)


async def test_status(app: App, store):
    from nonebot.adapters.onebot.v11 import Bot

    from nonebot_plugin_xianmei.commands import matcher_status
    from nonebot_plugin_xianmei.config import GroupState

    store.put("12345", GroupState(owner_qq="6867955", today_count=2, today_date="2026-09-11"))
    async with app.test_matcher(matcher_status) as ctx:
        bot = ctx.create_bot(base=Bot, self_id="100001")
        event = make_group_event(999, "/献媚状态")
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher_status)
        ctx.should_call_send(
            event,
            "📊 本群献媚状态\n"
            "桃神QQ：6867955\n"
            "每日上限：5 条\n"
            "冷却时间：30 分钟\n"
            "今日已献媚：2 条\n"
            "状态：开启",
            result=True,
        )
        ctx.should_finished(matcher_status)


async def test_preview(app: App, library):
    from nonebot.adapters.onebot.v11 import Bot

    from nonebot_plugin_xianmei.commands import matcher_preview

    async with app.test_matcher(matcher_preview) as ctx:
        bot = ctx.create_bot(base=Bot, self_id="100001")
        event = make_group_event(999, "/献媚预览")
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher_preview)
        ctx.should_call_send(event, "🔮 献媚预览：固定彩虹屁", result=True)
        ctx.should_finished(matcher_preview)
