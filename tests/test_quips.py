from pathlib import Path
from random import Random

import pytest

from nonebot_plugin_xianmei.quips import QuipLibrary


@pytest.fixture
def quips_file(tmp_path: Path) -> Path:
    path = tmp_path / "quips.yaml"
    path.write_text("quips:\n  - 桃神永远伟大\n  - 群主大人说的都对\n", encoding="utf-8")
    return path


def test_from_yaml(quips_file: Path):
    lib = QuipLibrary.from_yaml(quips_file)
    assert len(lib) == 2


def test_pick_returns_member(quips_file: Path):
    lib = QuipLibrary.from_yaml(quips_file)
    rng = Random(42)
    for _ in range(20):
        assert lib.pick(rng) in {"桃神永远伟大", "群主大人说的都对"}


def test_pick_empty_library_raises():
    lib = QuipLibrary([])
    with pytest.raises(IndexError):
        lib.pick(Random(1))
