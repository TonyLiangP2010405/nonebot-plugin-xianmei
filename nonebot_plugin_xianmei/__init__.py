from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="桃子献媚",
    description="向本群群主（B站主播小小桃纸哟）自动献媚的娱乐插件",
    usage=(
        "群主在群里出现时自动发送一条彩虹屁；\n"
        "superuser 命令：/献媚设置群主 /献媚设置上限 /献媚设置冷却 /献媚开关 /献媚状态 /献媚预览"
    ),
    type="application",
    homepage="https://github.com/TonyLiangP2010405/nonebot-plugin-xianmei",
    supported_adapters={"~onebot.v11"},
)

from datetime import datetime

from nonebot import on_message
from nonebot.adapters.onebot.v11 import GroupMessageEvent

from . import commands as _commands  # noqa: F401  # 注册命令 matcher
from .config import get_store
from .quips import get_library
from .trigger import decide

flatter = on_message(priority=100, block=False)


@flatter.handle()
async def _(event: GroupMessageEvent):
    store = get_store()
    group_id = str(event.group_id)
    state = store.get(group_id)
    should, new_state = decide(state, str(event.user_id), datetime.now())
    if not should:
        return
    store.put(group_id, new_state)
    await store.save()
    name = event.sender.card or event.sender.nickname or "桃神"
    await flatter.send(f"🔔 检测到 {name} 出现！")
    await flatter.send("🫡 开始献媚！")
    await flatter.finish(get_library().pick())
