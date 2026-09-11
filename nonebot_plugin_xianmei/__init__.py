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
