import asyncio
import json
from dataclasses import asdict, dataclass
from pathlib import Path

DATA_DIR = Path.cwd() / "data" / "xianmei"
DEFAULT_STATE_PATH = DATA_DIR / "state.json"


@dataclass
class GroupState:
    owner_qq: str | None = None
    daily_limit: int = 5
    cooldown_minutes: int = 30
    enabled: bool = True
    last_trigger_ts: float = 0.0
    today_count: int = 0
    today_date: str = ""


class Store:
    def __init__(self, path: Path):
        self.path = path
        self._states: dict[str, GroupState] = {}
        self._load()

    def get(self, group_id: str) -> GroupState:
        return self._states.get(group_id, GroupState())

    def put(self, group_id: str, state: GroupState) -> None:
        self._states[group_id] = state

    async def save(self) -> None:
        await asyncio.to_thread(self._save)

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return
        if not isinstance(raw, dict):
            return
        for group_id, data in raw.items():
            if isinstance(data, dict):
                try:
                    self._states[group_id] = GroupState(**data)
                except TypeError:
                    continue

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {gid: asdict(state) for gid, state in self._states.items()}
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


_store: Store | None = None


def get_store() -> Store:
    global _store
    if _store is None:
        _store = Store(DEFAULT_STATE_PATH)
    return _store
