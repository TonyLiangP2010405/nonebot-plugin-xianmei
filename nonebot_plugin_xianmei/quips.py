import random
from pathlib import Path

import yaml

RESOURCE_PATH = Path(__file__).parent / "resources" / "quips.yaml"


class QuipLibrary:
    def __init__(self, quips: list[str]):
        self._quips = list(quips)

    @classmethod
    def from_yaml(cls, path: Path) -> "QuipLibrary":
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return cls(data["quips"])

    def pick(self, rng: random.Random | None = None) -> str:
        chooser = rng if rng is not None else random
        return chooser.choice(self._quips)

    def __len__(self) -> int:
        return len(self._quips)


_library: QuipLibrary | None = None


def get_library() -> QuipLibrary:
    global _library
    if _library is None:
        _library = QuipLibrary.from_yaml(RESOURCE_PATH)
    return _library
