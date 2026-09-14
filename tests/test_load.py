import nonebot


def test_plugin_load():
    plugin = nonebot.get_plugin("nonebot_plugin_xianmei")
    assert plugin is not None
    assert plugin.metadata is not None
    assert plugin.metadata.name == "桃子献媚"
