import re

from nonebot import on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message, MessageEvent
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER

from .config import get_store
from .quips import get_library
from .trigger import status_text


def parse_qq(text: str) -> str | None:
    return text if re.fullmatch(r"[0-9]{5,11}", text) else None


def parse_bounded_int(text: str, lo: int, hi: int) -> int | None:
    try:
        n = int(text)
    except ValueError:
        return None
    return n if lo <= n <= hi else None


def split_group_arg(plain: str) -> tuple[str | None, str]:
    parts = plain.split(maxsplit=1)
    if not parts or not re.fullmatch(r"[0-9]+", parts[0]):
        return None, ""
    return parts[0], parts[1] if len(parts) > 1 else ""


matcher_set_owner = on_command("献媚设置群主", permission=SUPERUSER, block=True)
matcher_set_limit = on_command("献媚设置上限", permission=SUPERUSER, block=True)
matcher_set_cooldown = on_command("献媚设置冷却", permission=SUPERUSER, block=True)
matcher_toggle = on_command("献媚开关", permission=SUPERUSER, block=True)
matcher_status = on_command("献媚状态", permission=SUPERUSER, block=True)
matcher_preview = on_command("献媚预览", permission=SUPERUSER, block=True)


@matcher_set_owner.handle()
async def _set_owner(event: MessageEvent, args: Message = CommandArg()):
    plain = args.extract_plain_text().strip()
    if isinstance(event, GroupMessageEvent):
        group_id, arg = str(event.group_id), plain
    else:
        group_id, arg = split_group_arg(plain)
        if group_id is None or not arg:
            await matcher_set_owner.finish("用法：献媚设置群主 <群号> <QQ号>（私聊时必须带群号）")
    qq = parse_qq(arg)
    if qq is None:
        await matcher_set_owner.finish("用法：献媚设置群主 <QQ号>（5~11 位数字）")
    store = get_store()
    state = store.get(group_id)
    state.owner_qq = qq
    store.put(group_id, state)
    await store.save()
    await matcher_set_owner.finish(f"✅ 已绑定本群桃神：{qq}\n桃神出现时将自动献媚~")


@matcher_set_limit.handle()
async def _set_limit(event: MessageEvent, args: Message = CommandArg()):
    plain = args.extract_plain_text().strip()
    if isinstance(event, GroupMessageEvent):
        group_id, arg = str(event.group_id), plain
    else:
        group_id, arg = split_group_arg(plain)
        if group_id is None:
            await matcher_set_limit.finish("用法：献媚设置上限 <群号> <条数>（私聊时必须带群号）")
    n = parse_bounded_int(arg, 1, 100)
    if n is None:
        await matcher_set_limit.finish("用法：献媚设置上限 <正整数>（1~100）")
    store = get_store()
    state = store.get(group_id)
    state.daily_limit = n
    store.put(group_id, state)
    await store.save()
    await matcher_set_limit.finish(f"✅ 每日献媚上限已设为 {n} 条")


@matcher_set_cooldown.handle()
async def _set_cooldown(event: MessageEvent, args: Message = CommandArg()):
    plain = args.extract_plain_text().strip()
    if isinstance(event, GroupMessageEvent):
        group_id, arg = str(event.group_id), plain
    else:
        group_id, arg = split_group_arg(plain)
        if group_id is None:
            await matcher_set_cooldown.finish("用法：献媚设置冷却 <群号> <分钟>（私聊时必须带群号）")
    n = parse_bounded_int(arg, 1, 1440)
    if n is None:
        await matcher_set_cooldown.finish("用法：献媚设置冷却 <分钟>（1~1440）")
    store = get_store()
    state = store.get(group_id)
    state.cooldown_minutes = n
    store.put(group_id, state)
    await store.save()
    await matcher_set_cooldown.finish(f"✅ 冷却时间已设为 {n} 分钟")


@matcher_toggle.handle()
async def _toggle(event: MessageEvent, args: Message = CommandArg()):
    plain = args.extract_plain_text().strip()
    if isinstance(event, GroupMessageEvent):
        group_id, _ = str(event.group_id), plain
    else:
        group_id, _ = split_group_arg(plain)
        if group_id is None:
            await matcher_toggle.finish("用法：献媚开关 <群号>（私聊时必须带群号）")
    store = get_store()
    state = store.get(group_id)
    state.enabled = not state.enabled
    store.put(group_id, state)
    await store.save()
    if state.enabled:
        await matcher_toggle.finish("✅ 献媚功能已开启，桃神出现我就开舔")
    await matcher_toggle.finish("⏸️ 献媚功能已关闭，桃神出现我也装死")


@matcher_status.handle()
async def _status(event: MessageEvent, args: Message = CommandArg()):
    plain = args.extract_plain_text().strip()
    if isinstance(event, GroupMessageEvent):
        group_id, _ = str(event.group_id), plain
    else:
        group_id, _ = split_group_arg(plain)
        if group_id is None:
            await matcher_status.finish("用法：献媚状态 <群号>（私聊时必须带群号）")
    state = get_store().get(group_id)
    await matcher_status.finish(status_text(state))


@matcher_preview.handle()
async def _preview(event: MessageEvent, args: Message = CommandArg()):
    plain = args.extract_plain_text().strip()
    if isinstance(event, GroupMessageEvent):
        group_id, _ = str(event.group_id), plain
    else:
        group_id, _ = split_group_arg(plain)
        if group_id is None:
            await matcher_preview.finish("用法：献媚预览 <群号>（私聊时必须带群号）")
    await matcher_preview.finish(f"🔮 献媚预览：{get_library().pick()}")
