# nonebot-plugin-xianmei 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 开发 NoneBot2 插件 nonebot-plugin-xianmei：群主（B站主播「小小桃纸哟」）在群里出现时自动随机发送一条谄媚彩虹屁。

**Architecture:** 纯本地插件，三个独立模块——`config.py`（每群 JSON 状态存储）、`trigger.py`（纯函数触发判定：群主匹配/冷却/日封顶/自然日重置）、`quips.py`（5000 条文案库加载与抽取）；`commands.py` 提供 superuser 管理命令；`__init__.py` 接线。文案由 `scripts/gen_quips.py` 用「模板×语料槽位」组合去重生成。

**Tech Stack:** Python ≥3.10、NoneBot2 ≥2.2.0、nonebot-adapter-onebot ≥2.4.0、PyYAML、pytest + pytest-asyncio(asyncio_mode=auto) + nonebug、ruff、hatchling。

## Global Constraints

- Python `>=3.10`；构建后端 hatchling；包名 `nonebot-plugin-xianmei`，模块名 `nonebot_plugin_xianmei`
- 依赖（逐字来自 spec/设计文档）：`nonebot2>=2.2.0`、`nonebot-adapter-onebot>=2.4.0`；dev 组 `nonebot2[fastapi]>=2.2.0`、`pytest>=7.0`、`pytest-asyncio>=0.21`、`nonebug>=0.3`、`ruff>=0.1.0`
- ruff line-length 120，select `["E","F","W","I","N","UP","B","C4","SIM"]`，ignore `["E501","B008"]`
- 所有命令仅限 superuser（`permission=SUPERUSER`），且仅群聊生效
- 文案库 ≥5000 条、无重复、每条 10~30 字符（含标点，按 `len()` 计）
- 零外部 API；默认参数：日封顶 5 条、冷却 30 分钟
- 数据文件：`Path.cwd()/data/xianmei/state.json`（不进 git）
- 命令前缀为 `/`（NoneBot `command_start`，由部署方配置，测试 conftest 中设为 `["/"]`）
- GitHub 用户名/作者：`TonyLiangP2010405`；License MIT
- nonebug 本版本（已实测）用法：`async with app.test_matcher(m) as ctx:` → 先 `ctx.receive_event(bot, event)`，再声明 `ctx.should_pass_rule/should_pass_permission/should_call_send/should_finished`，事件在 `async with` 退出时分发校验
- 所有 pytest 命令用 `.venv/bin/python -m pytest ...`（每个 shell 都是新会话，不能依赖 activate）

---

### Task 1: 项目脚手架与加载测试

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `nonebot_plugin_xianmei/__init__.py`
- Create: `tests/conftest.py`
- Create: `tests/test_load.py`

**Interfaces:**
- Consumes: 无
- Produces: 插件包 `nonebot_plugin_xianmei` 可被 NoneBot 加载；`__plugin_meta__.name == "桃子献媚"`；conftest 提供 `nonebot.init(command_start=["/"], superusers={"999"})` + `nonebot.load_plugin("nonebot_plugin_xianmei")` 的全局测试环境

- [ ] **Step 1: 创建 pyproject.toml**

```toml
[project]
name = "nonebot-plugin-xianmei"
version = "0.1.0"
description = "向本群群主（B站主播小小桃纸哟）自动献媚的娱乐插件：群主出现即随机发送一条彩虹屁"
readme = "README.md"
license = { text = "MIT" }
requires-python = ">=3.10"
authors = [
    { name = "TonyLiangP2010405", email = "" },
]
keywords = ["nonebot", "nonebot2", "plugin", "bilibili", "娱乐", "彩虹屁"]
classifiers = [
    "Development Status :: 4 - Beta",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
]
dependencies = [
    "nonebot2>=2.2.0",
    "nonebot-adapter-onebot>=2.4.0",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = [
    "nonebot2[fastapi]>=2.2.0",
    "pytest>=7.0",
    "pytest-asyncio>=0.21",
    "nonebug>=0.3",
    "ruff>=0.1.0",
]

[project.urls]
Homepage = "https://github.com/TonyLiangP2010405/nonebot-plugin-xianmei"
Repository = "https://github.com/TonyLiangP2010405/nonebot-plugin-xianmei"

[tool.nonebot]
plugins = ["nonebot_plugin_xianmei"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["nonebot_plugin_xianmei"]

[tool.ruff]
line-length = 120
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "C4", "SIM"]
ignore = ["E501", "B008"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

- [ ] **Step 2: 创建 .gitignore**

```
.venv/
__pycache__/
*.pyc
data/
dist/
.pytest_cache/
.ruff_cache/
.DS_Store
```

- [ ] **Step 3: 创建 nonebot_plugin_xianmei/__init__.py（仅元数据，handler 后续任务再加）**

```python
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
```

- [ ] **Step 4: 创建 tests/conftest.py**

```python
import nonebot

nonebot.init(command_start=["/"], superusers={"999"})
nonebot.load_plugin("nonebot_plugin_xianmei")
```

- [ ] **Step 5: 创建 tests/test_load.py**

```python
import nonebot


def test_plugin_load():
    plugin = nonebot.get_plugin("nonebot_plugin_xianmei")
    assert plugin is not None
    assert plugin.metadata is not None
    assert plugin.metadata.name == "桃子献媚"
```

- [ ] **Step 6: 建虚拟环境并安装依赖**

```bash
cd /Users/liangpuyue/Desktop/develop/nonebot-plugin-xianmei
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

Expected: 安装成功，无报错（nonebot2、nonebug、ruff 等全部装上）。

- [ ] **Step 7: 跑测试确认通过**

Run: `.venv/bin/python -m pytest tests/test_load.py -v`
Expected: PASS（`test_plugin_load` 1 passed）

- [ ] **Step 8: 提交**

```bash
git add pyproject.toml .gitignore nonebot_plugin_xianmei/__init__.py tests/
git commit -m "feat: 项目脚手架与插件加载测试"
```

---

### Task 2: 配置存储 config.py

**Files:**
- Create: `nonebot_plugin_xianmei/config.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Consumes: 无
- Produces:
  - `GroupState`（dataclass）：字段 `owner_qq: str | None = None`、`daily_limit: int = 5`、`cooldown_minutes: int = 30`、`enabled: bool = True`、`last_trigger_ts: float = 0.0`、`today_count: int = 0`、`today_date: str = ""`
  - `Store(path: Path)`：`get(group_id: str) -> GroupState`（同步，缺省返回默认）、`put(group_id: str, state: GroupState) -> None`（同步，仅内存）、`async save() -> None`（`asyncio.to_thread` 落盘）
  - `get_store() -> Store`（单例，默认路径 `Path.cwd()/data/xianmei/state.json`，模块全局 `_store` 可被 monkeypatch）
  - JSON 文件格式：`{group_id字符串: GroupState字段dict}`，`ensure_ascii=False`，`indent=2`

- [ ] **Step 1: 写失败测试**

```python
from pathlib import Path

import pytest

from nonebot_plugin_xianmei.config import GroupState, Store


def test_default_state():
    state = GroupState()
    assert state.owner_qq is None
    assert state.daily_limit == 5
    assert state.cooldown_minutes == 30
    assert state.enabled is True
    assert state.last_trigger_ts == 0.0
    assert state.today_count == 0
    assert state.today_date == ""


def test_get_missing_group_returns_default(tmp_path: Path):
    store = Store(tmp_path / "state.json")
    assert store.get("12345") == GroupState()


async def test_put_and_get(tmp_path: Path):
    store = Store(tmp_path / "state.json")
    state = GroupState(owner_qq="888", daily_limit=9)
    store.put("12345", state)
    assert store.get("12345").owner_qq == "888"
    assert store.get("12345").daily_limit == 9
    assert store.get("99999") == GroupState()


async def test_save_and_reload(tmp_path: Path):
    path = tmp_path / "state.json"
    store = Store(path)
    store.put("12345", GroupState(owner_qq="888", today_count=3, today_date="2026-09-11"))
    await store.save()

    store2 = Store(path)
    state = store2.get("12345")
    assert state.owner_qq == "888"
    assert state.today_count == 3
    assert state.today_date == "2026-09-11"


async def test_save_creates_parent_dir(tmp_path: Path):
    path = tmp_path / "sub" / "dir" / "state.json"
    store = Store(path)
    store.put("1", GroupState(owner_qq="888"))
    await store.save()
    assert path.exists()


def test_corrupted_file_starts_empty(tmp_path: Path):
    path = tmp_path / "state.json"
    path.write_text("{not valid json", encoding="utf-8")
    store = Store(path)
    assert store.get("12345") == GroupState()
```

- [ ] **Step 2: 运行确认失败**

Run: `.venv/bin/python -m pytest tests/test_config.py -v`
Expected: 全部 FAIL/ERROR，`ModuleNotFoundError: No module named 'nonebot_plugin_xianmei.config'`

- [ ] **Step 3: 实现 config.py**

```python
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
        for group_id, data in raw.items():
            if isinstance(data, dict):
                self._states[group_id] = GroupState(**data)

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
```

- [ ] **Step 4: 运行确认通过**

Run: `.venv/bin/python -m pytest tests/test_config.py -v`
Expected: 6 passed

- [ ] **Step 5: 提交**

```bash
git add nonebot_plugin_xianmei/config.py tests/test_config.py
git commit -m "feat: 每群配置存储 GroupState/Store"
```

---

### Task 3: 触发判定 trigger.py

**Files:**
- Create: `nonebot_plugin_xianmei/trigger.py`
- Test: `tests/test_trigger.py`

**Interfaces:**
- Consumes: `config.GroupState`（Task 2）
- Produces: `decide(state: GroupState, sender_qq: str, now: datetime) -> tuple[bool, GroupState]` — 纯函数；返回 `(是否发送, 新状态)`。自然日切换时先把 `today_date` 更新为当天并清零 `today_count`；触发条件全部满足时 `today_count+1`、`last_trigger_ts=now.timestamp()`。调用方只在 `should=True` 时落盘。
- Produces（后续 Task 6/7 依赖）: `status_text(state: GroupState) -> str`，多行状态文案，格式见 Step 3 代码

- [ ] **Step 1: 写失败测试**

```python
from datetime import datetime

from nonebot_plugin_xianmei.config import GroupState
from nonebot_plugin_xianmei.trigger import decide, status_text

NOW = datetime(2026, 9, 11, 20, 30, 0)


def make_state(**kwargs) -> GroupState:
    return GroupState(owner_qq="888", **kwargs)


def test_owner_triggers():
    should, new = decide(make_state(), "888", NOW)
    assert should is True
    assert new.today_count == 1
    assert new.last_trigger_ts == NOW.timestamp()
    assert new.today_date == "2026-09-11"


def test_non_owner_ignored():
    should, _ = decide(make_state(), "777", NOW)
    assert should is False


def test_owner_not_set():
    should, _ = decide(GroupState(), "888", NOW)
    assert should is False


def test_disabled():
    should, _ = decide(make_state(enabled=False), "888", NOW)
    assert should is False


def test_cooldown_blocks():
    state = make_state(last_trigger_ts=NOW.timestamp() - 60, today_count=1, today_date="2026-09-11")
    should, _ = decide(state, "888", NOW)
    assert should is False


def test_cooldown_expired():
    state = make_state(last_trigger_ts=NOW.timestamp() - 31 * 60, today_count=1, today_date="2026-09-11")
    should, new = decide(state, "888", NOW)
    assert should is True
    assert new.today_count == 2


def test_daily_limit_blocks():
    state = make_state(today_count=5, today_date="2026-09-11")
    should, _ = decide(state, "888", NOW)
    assert should is False


def test_new_day_resets_count():
    state = make_state(today_count=5, today_date="2026-09-10")
    should, new = decide(state, "888", NOW)
    assert should is True
    assert new.today_count == 1
    assert new.today_date == "2026-09-11"


def test_limit_customized():
    state = make_state(daily_limit=2, today_count=2, today_date="2026-09-11")
    should, _ = decide(state, "888", NOW)
    assert should is False


def test_original_state_not_mutated():
    state = make_state()
    decide(state, "888", NOW)
    assert state.today_count == 0


def test_status_text():
    state = make_state(today_count=2, today_date="2026-09-11")
    text = status_text(state)
    assert "888" in text
    assert "5 条" in text
    assert "30 分钟" in text
    assert "2 条" in text
    assert "开启" in text
```

- [ ] **Step 2: 运行确认失败**

Run: `.venv/bin/python -m pytest tests/test_trigger.py -v`
Expected: FAIL，`ModuleNotFoundError: No module named 'nonebot_plugin_xianmei.trigger'`

- [ ] **Step 3: 实现 trigger.py**

```python
from dataclasses import replace
from datetime import datetime

from .config import GroupState


def decide(state: GroupState, sender_qq: str, now: datetime) -> tuple[bool, GroupState]:
    new = replace(state)
    today = now.date().isoformat()
    if new.today_date != today:
        new.today_date = today
        new.today_count = 0

    if not new.enabled or new.owner_qq is None:
        return False, new
    if new.owner_qq != sender_qq:
        return False, new
    if new.today_count >= new.daily_limit:
        return False, new
    if now.timestamp() - new.last_trigger_ts < new.cooldown_minutes * 60:
        return False, new

    new.today_count += 1
    new.last_trigger_ts = now.timestamp()
    return True, new


def status_text(state: GroupState) -> str:
    owner = state.owner_qq if state.owner_qq is not None else "未设置"
    switch = "开启" if state.enabled else "关闭"
    return (
        "📊 本群献媚状态\n"
        f"桃神QQ：{owner}\n"
        f"每日上限：{state.daily_limit} 条\n"
        f"冷却时间：{state.cooldown_minutes} 分钟\n"
        f"今日已献媚：{state.today_count} 条\n"
        f"状态：{switch}"
    )
```

- [ ] **Step 4: 运行确认通过**

Run: `.venv/bin/python -m pytest tests/test_trigger.py -v`
Expected: 11 passed

- [ ] **Step 5: 提交**

```bash
git add nonebot_plugin_xianmei/trigger.py tests/test_trigger.py
git commit -m "feat: 触发判定 decide 与状态文案 status_text"
```

---

### Task 4: 文案库 quips.py

**Files:**
- Create: `nonebot_plugin_xianmei/quips.py`
- Test: `tests/test_quips.py`

**Interfaces:**
- Consumes: 无
- Produces:
  - `QuipLibrary(quips: list[str])`：`from_yaml(path: Path) -> QuipLibrary`（读 `{"quips": [...]}`）、`pick(rng: random.Random | None = None) -> str`、`__len__`
  - `RESOURCE_PATH = Path(__file__).parent / "resources" / "quips.yaml"`
  - `get_library() -> QuipLibrary`（单例，模块全局 `_library` 可被 monkeypatch）

- [ ] **Step 1: 写失败测试**

```python
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
```

- [ ] **Step 2: 运行确认失败**

Run: `.venv/bin/python -m pytest tests/test_quips.py -v`
Expected: FAIL，`ModuleNotFoundError: No module named 'nonebot_plugin_xianmei.quips'`

- [ ] **Step 3: 实现 quips.py**

```python
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
```

- [ ] **Step 4: 运行确认通过**

Run: `.venv/bin/python -m pytest tests/test_quips.py -v`
Expected: 3 passed

- [ ] **Step 5: 提交**

```bash
git add nonebot_plugin_xianmei/quips.py tests/test_quips.py
git commit -m "feat: 文案库 QuipLibrary"
```

---

### Task 5: 5000 条文案生成器与文案库文件

**Files:**
- Create: `scripts/gen_quips.py`
- Create: `nonebot_plugin_xianmei/resources/quips.yaml`（生成产物，需提交）
- Test: `tests/test_quips_data.py`

**Interfaces:**
- Consumes: 无
- Produces: `nonebot_plugin_xianmei/resources/quips.yaml`，格式 `{"quips": [str, ...]}`，≥5000 条、无重复、每条 10~30 字符

- [ ] **Step 1: 写失败测试（验收文案库文件）**

```python
from pathlib import Path

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
```

- [ ] **Step 2: 运行确认失败**

Run: `.venv/bin/python -m pytest tests/test_quips_data.py -v`
Expected: FAIL，`AssertionError: 缺少 resources/quips.yaml`

- [ ] **Step 3: 创建 scripts/gen_quips.py（完整内容如下，直接写入）**

```python
"""献媚文案生成器：模板×语料槽位组合去重，生成 resources/quips.yaml。

用法: .venv/bin/python scripts/gen_quips.py
"""

import random
from pathlib import Path

import yaml

TITLES = ["桃神", "群主大人", "五冠王", "头部主播", "桃子", "小桃桃", "桃桃殿下", "我们桃子"]

DEEDS = [
    "出货了",
    "出大货了",
    "帮舰长抽卡抽到三点多",
    "把原神全图锄了一遍",
    "用一厘米的距离极限上岛",
    "在老演员堆里坚持到底",
    "理性消费没买资格",
    "把星露谷的菜地种满了",
    "重建了绝美家园",
    "解锁图鉴像个无情的机器",
    "钓鱼钓到手软",
    "带徒弟们堵门抽卡",
    "一个十连双金",
    "剧情一刀不跳全看完了",
    "一口气推完了至冬主线",
    "把星布谷地玩成了五冠王",
    "直播到困才下播",
    "拒绝了道德绑架",
    "音乐会员过期也坚持开播",
    "给徒弟们准备了礼物",
    "用全身的艺术细胞设计了迷宫",
    "把海岛生活安排得明明白白",
    "锄大地顺带清了全支线",
    "一边说穷一边出货",
    "把问卷都填完了",
    "求求求求关注求到我心坎里",
    "不动声色地赢了",
    "把图鉴解锁成了艺术",
    "让老演员都自愧不如",
    "更新了超长实况视频",
]

RHETORICS = [
    "这谁顶得住啊",
    "我直接跪了",
    "我先磕为敬",
    "这就是实力吗",
    "太有实力了",
    "跪了跪了",
    "属实顶流",
    "这波在大气层",
    "含金量拉满了",
    "天花板级别",
    "群文件都为你让路",
    "群规都得给你面子",
    "我辈楷模",
    "泪目了家人们",
    "谁懂啊这也太强了",
    "直接封神",
    "不愧是你",
    "学到了学到了",
    "我宣布今天群庆",
    "建议写进群公告",
    "这就是群主的含金量",
    "请受徒儿一拜",
    "给大佬递茶",
    "太强了太强了",
    "我心服口服",
]

THREE_SLOT_TEMPLATES = [
    "{t}又{d}，{r}！",
    "{t}今天{d}，{r}！",
    "{t}刚刚{d}，{r}！",
    "报告大家，{t}{d}，{r}！",
    "都闪开，{t}{d}，{r}！",
    "快看，{t}{d}，{r}！",
    "家人们，{t}{d}，{r}！",
    "我哭死，{t}{d}，{r}！",
    "{t}果然{d}，{r}！",
    "{t}又双叒{d}，{r}！",
    "全体起立！{t}{d}，{r}！",
    "{t}主打一个{d}，{r}！",
    "听说{t}{d}，{r}！",
    "{t}下播前还{d}，{r}！",
    "又是被{t}折服的一天，{d}，{r}！",
    "{t}深夜{d}，{r}！",
    "{t}一边{d}一边求关注，{r}！",
    "问就是{t}{d}，{r}！",
    "{t}还是太全面了，{d}，{r}！",
    "谁都别拦我，{t}{d}，{r}！",
    "恭迎{t}，{d}，{r}！",
    "群里沸腾了，{t}{d}，{r}！",
]

TWO_SLOT_TEMPLATES = [
    "{t}又{d}！",
    "{t}今天{d}！",
    "{t}刚刚{d}！",
    "{t}又双叒{d}！",
    "{t}，{r}！",
    "又是被{t}折服的一天，{r}！",
    "{t}一出场，{r}！",
    "只要{t}在群里，{r}！",
    "向{t}学习，{r}！",
    "{t}带带我，{r}！",
    "为{t}打call，{r}！",
    "{t}贴贴，{r}！",
    "什么？{d}？{r}！",
    "都听说了吗，{d}，{r}！",
    "{d}，{r}！",
]

HANDWRITTEN = [
    "桃神一开口，群里的空气都变甜了",
    "群主大人亲临，本群蓬荜生辉",
    "五冠王的含金量，懂的人自然懂",
    "头部主播来群里视察了，大家列队",
    "桃神几点开播，我提前半小时堵门",
    "别人追星我追桃神，赢麻了",
    "桃神出货的那一刻，我在屏幕前哭出声",
    "理性消费的桃神最美丽，是我榜样",
    "抽到三点多的女人，什么大风浪没见过",
    "老演员再多，也挡不住桃神的脚步",
    "桃神说不要花钱买资格，我记小本本上了",
    "本群唯一指定信仰：桃神",
    "桃神的迷宫设计，艺术细胞拉满",
    "能把问卷都填完的主播，值得托付",
    "桃神的海岛，是我向往的退休生活",
    "音乐会员会过期，对桃神的爱不会",
    "桃神不更新的日子，我反复看实况",
    "能把星露谷种满的人，一定也能种进我心里",
    "桃神的一厘米，是我跨不过去的坎",
    "今天也是被桃神治愈的一天",
    "群主大人说话，我连标点符号都同意",
    "桃神说东我不西，桃神说一我不二",
    "向桃神学习，争做理性消费好群友",
    "桃神的新视频我看了十遍，不够看",
    "桃神永远伟大，出货见证神话",
    "群里可以没有我，不能没有桃神",
    "桃神一发言，我瞬间不困了",
    "这就是头部主播的排面吗，爱了",
    "桃神打原神的样子，像在巡视自家菜园",
    "萌新桃桃最可爱，老玩家心都化了",
    "我给桃神递茶，茶都是甜的",
    "桃神的故事会，比春晚好看",
    "建议把桃神语录印成群公告",
    "桃神的每个实况，都是我的下饭神器",
    "桃神不开播的日子，度日如年",
    "本群公告第一条：桃神说的都对",
]

TARGET_SIZE = 5200
MIN_LEN = 10
MAX_LEN = 30
SEED = 20260911


def build_pool() -> set[str]:
    pool: set[str] = set(HANDWRITTEN)
    for tpl in THREE_SLOT_TEMPLATES:
        for t in TITLES:
            for d in DEEDS:
                for r in RHETORICS:
                    pool.add(tpl.format(t=t, d=d, r=r))
    for tpl in TWO_SLOT_TEMPLATES:
        for t in TITLES:
            for d in DEEDS:
                if "{d}" in tpl:
                    pool.add(tpl.format(t=t, d=d))
            for r in RHETORICS:
                if "{r}" in tpl:
                    pool.add(tpl.format(t=t, r=r))
    return pool


def main() -> None:
    pool = build_pool()
    valid = [s for s in pool if MIN_LEN <= len(s) <= MAX_LEN]
    rng = random.Random(SEED)
    rng.shuffle(valid)

    handwritten = [s for s in HANDWRITTEN if MIN_LEN <= len(s) <= MAX_LEN]
    chosen = handwritten + valid[: max(0, TARGET_SIZE - len(handwritten))]
    chosen = sorted(set(chosen))

    out_path = Path(__file__).parent.parent / "nonebot_plugin_xianmei" / "resources" / "quips.yaml"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        yaml.dump({"quips": chosen}, ensure_ascii=False, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    print(f"候选池 {len(pool)} 条，长度合规 {len(valid)} 条，已写入 {len(chosen)} 条 -> {out_path}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 运行生成器**

Run: `.venv/bin/python scripts/gen_quips.py`
Expected: 输出类似 `候选池 8xxxx 条，长度合规 xxxxx 条，已写入 5200 条 -> .../quips.yaml`

- [ ] **Step 5: 抽查文案质量**

Run: `.venv/bin/shuf -n 30 nonebot_plugin_xianmei/resources/quips.yaml`（若无 shuf 则用 `.venv/bin/python -c "import random,yaml; q=yaml.safe_load(open('nonebot_plugin_xianmei/resources/quips.yaml'))['quips']; print('\n'.join(random.sample(q, 30)))"`）
Expected: 随机 30 条均为通顺的中文彩虹屁，无占位符残留、无语法破碎。若有个别劣质组合，从生成器语料/模板中移除对应条目后重新生成（不要手改 YAML，改源再生成）。

- [ ] **Step 6: 运行验收测试确认通过**

Run: `.venv/bin/python -m pytest tests/test_quips_data.py -v`
Expected: PASS

- [ ] **Step 7: 提交**

```bash
git add scripts/gen_quips.py nonebot_plugin_xianmei/resources/quips.yaml tests/test_quips_data.py
git commit -m "feat: 5200 条献媚文案库与生成器"
```

---

### Task 6: superuser 命令 commands.py

**Files:**
- Create: `nonebot_plugin_xianmei/commands.py`
- Test: `tests/test_commands.py`

**Interfaces:**
- Consumes: `config.get_store()`（Task 2）、`trigger.status_text()`（Task 3）、`quips.get_library()`（Task 4）
- Produces（Task 7 的 `__init__.py` 需要 import 本模块以注册命令）:
  - matcher 变量：`matcher_set_owner`、`matcher_set_limit`、`matcher_set_cooldown`、`matcher_toggle`、`matcher_status`、`matcher_preview`，均为 `on_command(..., permission=SUPERUSER, block=True)`，仅响应群消息
  - 纯函数（供单测）：`parse_qq(text: str) -> str | None`（5~11 位数字）、`parse_bounded_int(text: str, lo: int, hi: int) -> int | None`
  - 回复文案（测试断言用，逐字一致）：
    - 设群主成功：`"✅ 已绑定本群桃神：{qq}\n桃神出现时将自动献媚~"`；失败：`"用法：献媚设置群主 <QQ号>（5~11 位数字）"`
    - 设上限成功：`"✅ 每日献媚上限已设为 {n} 条"`；失败：`"用法：献媚设置上限 <正整数>（1~100）"`
    - 设冷却成功：`"✅ 冷却时间已设为 {n} 分钟"`；失败：`"用法：献媚设置冷却 <分钟>（1~1440）"`
    - 开关：`"✅ 献媚功能已开启，桃神出现我就开舔"` / `"⏸️ 献媚功能已关闭，桃神出现我也装死"`
    - 状态：`trigger.status_text(state)`
    - 预览：`"🔮 献媚预览：{quip}"`
    - 私聊/非群消息：`"该命令仅限群聊使用~"`

- [ ] **Step 1: 写失败测试（纯函数部分）**

```python
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
```

- [ ] **Step 2: 运行确认失败**

Run: `.venv/bin/python -m pytest tests/test_commands.py -v`
Expected: FAIL，`ModuleNotFoundError: No module named 'nonebot_plugin_xianmei.commands'`

- [ ] **Step 3: 实现 commands.py**

```python
from nonebot import on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent, MessageEvent
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER

from .config import get_store
from .quips import get_library
from .trigger import status_text


def parse_qq(text: str) -> str | None:
    return text if text.isdigit() and 5 <= len(text) <= 11 else None


def parse_bounded_int(text: str, lo: int, hi: int) -> int | None:
    try:
        n = int(text)
    except ValueError:
        return None
    return n if lo <= n <= hi else None


def _not_group():
    from nonebot import Matcher

    async def _reject(event: MessageEvent):
        if not isinstance(event, GroupMessageEvent):
            await Matcher.current().finish("该命令仅限群聊使用~")

    return _reject


matcher_set_owner = on_command("献媚设置群主", permission=SUPERUSER, block=True)
matcher_set_limit = on_command("献媚设置上限", permission=SUPERUSER, block=True)
matcher_set_cooldown = on_command("献媚设置冷却", permission=SUPERUSER, block=True)
matcher_toggle = on_command("献媚开关", permission=SUPERUSER, block=True)
matcher_status = on_command("献媚状态", permission=SUPERUSER, block=True)
matcher_preview = on_command("献媚预览", permission=SUPERUSER, block=True)


@matcher_set_owner.handle()
async def _set_owner(event: MessageEvent, args: Message = CommandArg()):
    if not isinstance(event, GroupMessageEvent):
        await matcher_set_owner.finish("该命令仅限群聊使用~")
    qq = parse_qq(args.extract_plain_text().strip())
    if qq is None:
        await matcher_set_owner.finish("用法：献媚设置群主 <QQ号>（5~11 位数字）")
    store = get_store()
    state = store.get(str(event.group_id))
    state.owner_qq = qq
    store.put(str(event.group_id), state)
    await store.save()
    await matcher_set_owner.finish(f"✅ 已绑定本群桃神：{qq}\n桃神出现时将自动献媚~")


@matcher_set_limit.handle()
async def _set_limit(event: MessageEvent, args: Message = CommandArg()):
    if not isinstance(event, GroupMessageEvent):
        await matcher_set_limit.finish("该命令仅限群聊使用~")
    n = parse_bounded_int(args.extract_plain_text().strip(), 1, 100)
    if n is None:
        await matcher_set_limit.finish("用法：献媚设置上限 <正整数>（1~100）")
    store = get_store()
    state = store.get(str(event.group_id))
    state.daily_limit = n
    store.put(str(event.group_id), state)
    await store.save()
    await matcher_set_limit.finish(f"✅ 每日献媚上限已设为 {n} 条")


@matcher_set_cooldown.handle()
async def _set_cooldown(event: MessageEvent, args: Message = CommandArg()):
    if not isinstance(event, GroupMessageEvent):
        await matcher_set_cooldown.finish("该命令仅限群聊使用~")
    n = parse_bounded_int(args.extract_plain_text().strip(), 1, 1440)
    if n is None:
        await matcher_set_cooldown.finish("用法：献媚设置冷却 <分钟>（1~1440）")
    store = get_store()
    state = store.get(str(event.group_id))
    state.cooldown_minutes = n
    store.put(str(event.group_id), state)
    await store.save()
    await matcher_set_cooldown.finish(f"✅ 冷却时间已设为 {n} 分钟")


@matcher_toggle.handle()
async def _toggle(event: MessageEvent):
    if not isinstance(event, GroupMessageEvent):
        await matcher_toggle.finish("该命令仅限群聊使用~")
    store = get_store()
    state = store.get(str(event.group_id))
    state.enabled = not state.enabled
    store.put(str(event.group_id), state)
    await store.save()
    if state.enabled:
        await matcher_toggle.finish("✅ 献媚功能已开启，桃神出现我就开舔")
    await matcher_toggle.finish("⏸️ 献媚功能已关闭，桃神出现我也装死")


@matcher_status.handle()
async def _status(event: MessageEvent):
    if not isinstance(event, GroupMessageEvent):
        await matcher_status.finish("该命令仅限群聊使用~")
    state = get_store().get(str(event.group_id))
    await matcher_status.finish(status_text(state))


@matcher_preview.handle()
async def _preview(event: MessageEvent):
    if not isinstance(event, GroupMessageEvent):
        await matcher_preview.finish("该命令仅限群聊使用~")
    await matcher_preview.finish(f"🔮 献媚预览：{get_library().pick()}")
```

注意：顶部需要 `from nonebot.adapters.onebot.v11 import Message` 用于 `CommandArg` 类型标注（与 GroupMessageEvent、MessageEvent 同行 import）。删除未使用的 `_not_group` 辅助函数（上面的最终代码不含它）。

- [ ] **Step 4: 运行纯函数测试确认通过**

Run: `.venv/bin/python -m pytest tests/test_commands.py -v`
Expected: 5 passed

- [ ] **Step 5: 写 nonebug 集成测试，追加到 tests/test_commands.py**

```python
from pathlib import Path

import pytest
from nonebug import App


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
```

然后逐条追加以下用例到 tests/test_commands.py：

```python
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


async def test_preview(app: App):
    from nonebot.adapters.onebot.v11 import Bot

    from nonebot_plugin_xianmei.commands import matcher_preview

    async with app.test_matcher(matcher_preview) as ctx:
        bot = ctx.create_bot(base=Bot, self_id="100001")
        event = make_group_event(999, "/献媚预览")
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher_preview)
        ctx.should_call_send(event, "🔮 献媚预览：固定彩虹屁", result=True)
        ctx.should_finished(matcher_preview)
```

- [ ] **Step 6: 运行全部命令测试确认通过**

Run: `.venv/bin/python -m pytest tests/test_commands.py -v`
Expected: 10 passed

若 `should_call_send` 对多行字符串断言失败，确认实际发送串与期望串逐字一致（尤其换行符）。

- [ ] **Step 7: 提交**

```bash
git add nonebot_plugin_xianmei/commands.py tests/test_commands.py
git commit -m "feat: superuser 管理命令与 nonebug 测试"
```

---

### Task 7: 插件入口接线 __init__.py 与献媚集成测试

**Files:**
- Modify: `nonebot_plugin_xianmei/__init__.py`（追加 handler；保留 Task 1 的 `__plugin_meta__`）
- Test: `tests/test_flatter.py`

**Interfaces:**
- Consumes: `config.get_store()`（Task 2）、`trigger.decide()`（Task 3）、`quips.get_library()`（Task 4）、`commands` 模块（Task 6，import 以注册命令）
- Produces: 模块级 matcher `flatter = on_message(priority=100, block=False)`，供测试 `from nonebot_plugin_xianmei import flatter`

- [ ] **Step 1: 写失败测试**

```python
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

    store.put("12345", GroupState(owner_qq="888", today_count=5, today_date="2026-09-11"))
    async with app.test_matcher(flatter) as ctx:
        bot = ctx.create_bot(base=Bot, self_id="100001")
        event = make_group_event(888, "大家晚上好")
        ctx.receive_event(bot, event)
    assert store.get("12345").today_count == 5
```

注意：跨测试文件 import（`from tests.test_commands import make_group_event`）需要 tests 为包——创建空文件 `tests/__init__.py`。conftest.py 里 `nonebot.load_plugin` 保持不变。

- [ ] **Step 2: 运行确认失败**

Run: `.venv/bin/python -m pytest tests/test_flatter.py -v`
Expected: FAIL，`ImportError: cannot import name 'flatter' from 'nonebot_plugin_xianmei'`

- [ ] **Step 3: 修改 __init__.py（在 `__plugin_meta__` 之后追加）**

```python
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
    await flatter.finish(get_library().pick())
```

- [ ] **Step 4: 运行确认通过**

Run: `.venv/bin/python -m pytest tests/test_flatter.py -v`
Expected: 5 passed

- [ ] **Step 5: 全量回归**

Run: `.venv/bin/python -m pytest tests/ -v`
Expected: 全部 passed（加载 1 + 配置 6 + 触发 11 + 文案库 3 + 数据 1 + 命令 10 + 集成 5 = 37）

- [ ] **Step 6: 提交**

```bash
git add nonebot_plugin_xianmei/__init__.py tests/test_flatter.py tests/__init__.py
git commit -m "feat: 献媚消息处理器与端到端集成测试"
```

---

### Task 8: README、LICENSE 与最终验证

**Files:**
- Create: `README.md`
- Create: `LICENSE`
- Modify: 无

**Interfaces:**
- Consumes: 全部前述任务产物
- Produces: 可发布的插件仓库（`pip install -e .` 可装、NoneBot 可加载、测试全绿、ruff 干净）

- [ ] **Step 1: 写 README.md**

````markdown
# nonebot-plugin-xianmei

向本群群主自动献媚的娱乐插件——为本群桃神（B站主播「[小小桃纸哟](https://space.bilibili.com/6867955)」）量身定制的彩虹屁机器人。群主在群里出现时，自动随机发送一条谄媚文案（内置 5200 条，玩主播本人梗）。

## 功能

- 群主（桃神）在群里出现时，自动随机发送一条献媚彩虹屁
- 冷却时间（默认 30 分钟）与每日封顶（默认 5 条）防刷屏
- 全部管理命令仅限 superuser
- 多群独立配置

## 安装

```bash
pip install nonebot-plugin-xianmei
```

并在 NoneBot 配置中加载插件（`pyproject.toml` 的 `[tool.nonebot]` 或 bot 的 `load_plugin`）。

## 使用方法

| 指令 | 权限 | 范围 | 说明 |
|---|---|---|---|
| `/献媚设置群主 <QQ号>` | superuser | 群聊 | 绑定本群群主（桃神）QQ |
| `/献媚设置上限 <N>` | superuser | 群聊 | 设置每日献媚条数上限（1~100） |
| `/献媚设置冷却 <分钟>` | superuser | 群聊 | 设置触发冷却时间（1~1440 分钟） |
| `/献媚开关` | superuser | 群聊 | 开关本群献媚功能 |
| `/献媚状态` | superuser | 群聊 | 查看本群配置与今日已发数量 |
| `/献媚预览` | superuser | 群聊 | 随机预览一条献媚文案 |

> 命令需要 NoneBot 配置 `command_start=["/"]`（默认即为 `/`）。

数据存储于运行目录 `data/xianmei/state.json`（每群独立，自动生成）。

## 文案风格

每条 10~30 字，梗来自桃神直播间：五冠王、头部主播、出货/老演员、堵门抽卡、抽到三点多、星露谷、理性消费「不买资格」等。文案由 `scripts/gen_quips.py` 生成，可改语料后重新生成。

## 示例

```
桃神：大家晚上好
机器人：桃神一出场，群规都得给你面子！
```

## 许可证

MIT
````

- [ ] **Step 2: 写 LICENSE（MIT，作者 TonyLiangP2010405，年份 2026）**

```text
MIT License

Copyright (c) 2026 TonyLiangP2010405

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 3: 最终验证四连**

Run: `.venv/bin/python -m compileall nonebot_plugin_xianmei`
Expected: 全部编译成功

Run: `.venv/bin/python -c "import nonebot_plugin_xianmei; print('import ok')"`
Expected: 输出 `import ok`

Run: `.venv/bin/ruff check .`
Expected: 无告警（`All checks passed!`）

Run: `.venv/bin/python -m pytest tests/ -q`
Expected: 全部 passed

- [ ] **Step 4: 提交**

```bash
git add README.md LICENSE
git commit -m "docs: README 与 MIT LICENSE"
```

---

## Self-Review 记录

- **Spec 覆盖**：触发机制（Task 3+7）、superuser 命令六件套（Task 6）、5000 条文案与验收（Task 5）、每群 JSON 存储（Task 2）、冷却/日封顶/自然日重置（Task 3）、测试要求（各任务 TDD + Task 7 集成）、README/LICENSE（Task 8）——spec 每节均有对应任务。
- **占位符扫描**：无 TBD/TODO；所有代码步骤含完整代码；语料（30 事迹/25 修辞/8 称呼/37 模板/36 手写）全部写实。
- **类型一致性**：`GroupState` 字段、`decide(state, sender_qq, now) -> tuple[bool, GroupState]`、`Store.get/put/save`、`QuipLibrary.from_yaml/pick`、`get_store/get_library`、matcher 变量名 `flatter`/`matcher_set_owner` 等在各任务间逐字一致；测试断言文案与 commands.py 回复逐字一致。
