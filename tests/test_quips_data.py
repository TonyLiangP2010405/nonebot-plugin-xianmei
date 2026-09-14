from nonebot_plugin_xianmei.quips import RESOURCE_PATH, QuipLibrary


def test_shipped_quips_satisfy_spec():
    assert RESOURCE_PATH.exists(), "缺少 resources/quips.yaml，请先运行 scripts/gen_quips.py"
    lib = QuipLibrary.from_yaml(RESOURCE_PATH)
    quips = lib._quips
    assert len(quips) >= 5000, f"只有 {len(quips)} 条"
    assert len(set(quips)) == len(quips), "存在重复文案"
    for q in quips:
        assert 10 <= len(q) <= 30, f"长度不合规（{len(q)}）：{q}"
        assert "{" not in q and "}" not in q, f"含未填充占位符：{q}"
