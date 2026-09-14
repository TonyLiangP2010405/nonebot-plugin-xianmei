# nonebot-plugin-xianmei v2（私聊群控 + 出现播报）实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** superuser 可私聊机器人管理任意群配置（私聊命令第一个参数为群号）；群主出现触发献媚时先播报「检测到 XX 出现」「开始献媚」再发彩虹屁。

**Architecture:** commands.py 增加纯函数 `split_group_arg` 解析私聊的"群号+参数"，六个 handler 改为群聊取当前群、私聊取解析结果；`__init__.py` 的 flatter handler 在 decide() 为 True 时依次 send 两条播报再 finish 彩虹屁。播报用 sender.card → nickname → "桃神" 回退链取名。

**Tech Stack:** 同 v1（NoneBot2、pytest + nonebug、ruff）。基线 main@2562dfa，分支 feat/private-cmd-announce。

## Global Constraints

- 基线：v1 全部 38 个测试必须保持绿色（群聊用法与回复文案不变）
- 命令仍全部 `permission=SUPERUSER`；私聊可用，群号参数仅用于定位配置
- 播报三条消息顺序固定：「🔔 检测到 {name} 出现！」→「🫡 开始献媚！」→ 彩虹屁；name = sender.card or sender.nickname or "桃神"
- 播报不计入每日上限；decide() 为 False 时静默（不播报不发）
- 私聊缺群号/群号非法（非 ASCII 数字）→ 用法提示（逐字）：各命令 "用法：<命令> <群号> ...（私聊时必须带群号）"
- 现有成功回复文案逐字不变（如 "✅ 已绑定本群桃神：{qq}\n桃神出现时将自动献媚~"）
- ruff clean（`ruff check .`）；测试命令用 `.venv/bin/python -m pytest ...`
- nonebug 用法（本机实测）：`async with app.test_matcher(m) as ctx:` 内先 `ctx.receive_event(bot, event)` 再声明期望；Bot self_id="100001"；superuser=999，非 superuser=555
- spec：docs/superpowers/specs/2026-09-14-private-commands-and-announce-design.md

---

### Task 1: 私聊命令解析（split_group_arg + commands.py 改造）

**Files:**
- Modify: `nonebot_plugin_xianmei/commands.py`（全文重写为下述内容）
- Modify: `tests/test_commands.py`（追加单测与集成测试；`make_group_event` 增加 card/nickname 可选参数）
- Test: `tests/test_commands.py`

**Interfaces:**
- Consumes: `config.get_store()`、`trigger.status_text`、`quips.get_library`（v1 已存在）
- Produces:
  - `split_group_arg(plain: str) -> tuple[str | None, str]`（纯函数：私聊文本 → (群号, 剩余参数)；首 token 非 ASCII 数字或为空 → (None, "")）
  - `make_group_event(user_id: int, message: str, card: str = "五冠王桃神", nickname: str = "桃神")`（测试辅助，六个命令测试与 Task 2 的 flatter 测试共用）
  - `make_private_event(user_id: int, message: str)`（测试辅助）
  - 六个 handler 改为：群聊 → group_id=当前群、arg=全部参数；私聊 → `split_group_arg`，群号 None 时 finish 对应用法提示

- [ ] **Step 1: 修改 make_group_event 并追加 make_private_event（tests/test_commands.py 顶部辅助区）**

将现有 `make_group_event` 替换为：

```python
def make_group_event(user_id: int, message: str, card: str = "五冠王桃神", nickname: str = "桃神"):
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
            "nickname": nickname,
            "card": card,
            "sex": "unknown",
            "age": 0,
            "area": "",
            "level": "1",
            "role": "member",
            "title": "",
        },
    )


def make_private_event(user_id: int, message: str):
    from nonebot.adapters.onebot.v11 import Message, PrivateMessageEvent

    return PrivateMessageEvent(
        time=0,
        self_id=100001,
        post_type="message",
        message_type="private",
        sub_type="friend",
        message_id=1,
        user_id=user_id,
        message=Message(message),
        raw_message=message,
        font=0,
        sender={"user_id": user_id, "nickname": "n", "sex": "unknown", "age": 0},
    )
```

注意：`make_group_event` 的 import 原来在函数内只有 `GroupMessageEvent, Message`——保持函数内 import 风格不变（与 v1 一致）。

- [ ] **Step 2: 写失败单测（追加到 tests/test_commands.py 纯函数测试区）**

```python
from nonebot_plugin_xianmei.commands import parse_bounded_int, parse_qq, split_group_arg
```

```python
def test_split_group_arg_normal():
    assert split_group_arg("123456 6867955") == ("123456", "6867955")


def test_split_group_arg_no_arg():
    assert split_group_arg("123456") == ("123456", "")


def test_split_group_arg_invalid():
    assert split_group_arg("abc 123") == (None, "")
    assert split_group_arg("") == (None, "")
    assert split_group_arg("１２３４５６ 888") == (None, "")
```

- [ ] **Step 3: 运行确认失败**

Run: `.venv/bin/python -m pytest tests/test_commands.py -v`
Expected: 3 个新测试 FAIL（`ImportError: cannot import name 'split_group_arg'`）

- [ ] **Step 4: 重写 nonebot_plugin_xianmei/commands.py（完整内容）**

```python
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
        if group_id is None:
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
```

注意：v1 的"该命令仅限群聊使用~"分支整体移除（命令现在群聊/私聊均可用）；`group_id` 为 None 的分支里 `finish` 会终止，因此后续代码的 `group_id` 类型实际为 str。

- [ ] **Step 5: 运行单测确认通过，并全量回归**

Run: `.venv/bin/python -m pytest tests/test_commands.py -v`
Expected: 12 passed（9 旧 + 3 新）

Run: `.venv/bin/python -m pytest tests/ -q`
Expected: 41 passed

- [ ] **Step 6: 追加私聊集成测试（tests/test_commands.py 末尾）**

```python
async def test_set_owner_private_superuser(app: App, store):
    from nonebot.adapters.onebot.v11 import Bot

    from nonebot_plugin_xianmei.commands import matcher_set_owner

    async with app.test_matcher(matcher_set_owner) as ctx:
        bot = ctx.create_bot(base=Bot, self_id="100001")
        event = make_private_event(999, "/献媚设置群主 123456 6867955")
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher_set_owner)
        ctx.should_call_send(event, "✅ 已绑定本群桃神：6867955\n桃神出现时将自动献媚~", result=True)
        ctx.should_finished(matcher_set_owner)
    assert store.get("123456").owner_qq == "6867955"


async def test_set_owner_private_non_superuser(app: App, store):
    from nonebot.adapters.onebot.v11 import Bot

    from nonebot_plugin_xianmei.commands import matcher_set_owner

    async with app.test_matcher(matcher_set_owner) as ctx:
        bot = ctx.create_bot(base=Bot, self_id="100001")
        event = make_private_event(555, "/献媚设置群主 123456 6867955")
        ctx.receive_event(bot, event)
        ctx.should_not_pass_permission(matcher_set_owner)
    assert store.get("123456").owner_qq is None


async def test_toggle_private_invalid_group(app: App, store):
    from nonebot.adapters.onebot.v11 import Bot

    from nonebot_plugin_xianmei.commands import matcher_toggle

    async with app.test_matcher(matcher_toggle) as ctx:
        bot = ctx.create_bot(base=Bot, self_id="100001")
        event = make_private_event(999, "/献媚开关 abc")
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher_toggle)
        ctx.should_call_send(event, "用法：献媚开关 <群号>（私聊时必须带群号）", result=True)
        ctx.should_finished(matcher_toggle)
```

- [ ] **Step 7: 运行确认通过**

Run: `.venv/bin/python -m pytest tests/test_commands.py -v`
Expected: 15 passed

Run: `.venv/bin/python -m pytest tests/ -q && .venv/bin/ruff check .`
Expected: 44 passed；ruff All checks passed!

- [ ] **Step 8: 提交**

```bash
git add nonebot_plugin_xianmei/commands.py tests/test_commands.py
git commit -m "feat: 私聊带群号参数控制任意群配置"
```

---

### Task 2: 出现播报（__init__.py 三连播报 + flatter 测试更新 + README）

**Files:**
- Modify: `nonebot_plugin_xianmei/__init__.py:28-38`（handler 体）
- Modify: `tests/test_flatter.py`（更新两个既有测试 + 新增回退测试）
- Modify: `README.md`（功能与用法说明）

**Interfaces:**
- Consumes: Task 1 的 `make_group_event(card=..., nickname=...)` 参数
- Produces: 触发时三条消息序列：`f"🔔 检测到 {name} 出现！"`、`"🫡 开始献媚！"`、彩虹屁；`name = event.sender.card or event.sender.nickname or "桃神"`

- [ ] **Step 1: 先更新既有测试为新期望（RED：旧期望单条发送会失败）**

tests/test_flatter.py 中 `test_owner_speaking_gets_flattered` 的期望段改为：

```python
        ctx.should_call_send(event, "🔔 检测到 五冠王桃神 出现！", result=True)
        ctx.should_call_send(event, "🫡 开始献媚！", result=True)
        ctx.should_call_send(event, "固定彩虹屁", result=True)
        ctx.should_finished(flatter)
```

（`make_group_event` 默认 card="五冠王桃神"，所以名字断言用它。）

`test_cooldown_blocks_second_message` 中 event1 的期望段改为：

```python
        ctx.should_call_send(event1, "🔔 检测到 五冠王桃神 出现！", result=True)
        ctx.should_call_send(event1, "🫡 开始献媚！", result=True)
        ctx.should_call_send(event1, "固定彩虹屁", result=True)
        ctx.should_finished(flatter)
```

- [ ] **Step 2: 追加回退名单测（tests/test_flatter.py 末尾）**

```python
async def test_announce_name_fallback(app: App, store):
    from nonebot.adapters.onebot.v11 import Bot

    from nonebot_plugin_xianmei import flatter
    from nonebot_plugin_xianmei.config import GroupState

    store.put("12345", GroupState(owner_qq="888"))
    async with app.test_matcher(flatter) as ctx:
        bot = ctx.create_bot(base=Bot, self_id="100001")
        event = make_group_event(888, "大家晚上好", card="", nickname="")
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "🔔 检测到 桃神 出现！", result=True)
        ctx.should_call_send(event, "🫡 开始献媚！", result=True)
        ctx.should_call_send(event, "固定彩虹屁", result=True)
        ctx.should_finished(flatter)
```

注意顶部 import 改为 `from tests.test_commands import make_group_event`（v1 已是；保持）。

- [ ] **Step 3: 运行确认失败**

Run: `.venv/bin/python -m pytest tests/test_flatter.py -v`
Expected: 3 个测试 FAIL（handler 仍只发送彩虹屁一条，前两条 should_call_send 不匹配）

- [ ] **Step 4: 修改 __init__.py handler 体**

`flatter` handler 改为：

```python
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
```

- [ ] **Step 5: 运行确认通过 + 全量回归**

Run: `.venv/bin/python -m pytest tests/test_flatter.py -v`
Expected: 6 passed

Run: `.venv/bin/python -m pytest tests/ -q && .venv/bin/ruff check .`
Expected: 45 passed；ruff All checks passed!

- [ ] **Step 6: 更新 README.md**

功能列表首条改为：

```markdown
- 群主（桃神）在群里出现时，先播报「🔔 检测到 XX 出现！」「🫡 开始献媚！」，再自动随机发送一条献媚彩虹屁
```

使用方法表格下方补充段落（保留原有 command_start 提示）：

```markdown
> 群聊中发送时作用于当前群；**私聊发送时第一个参数必须是群号**，如 `/献媚设置群主 123456 6867955`、`/献媚状态 123456`。
```

- [ ] **Step 7: 最终验证与提交**

Run: `.venv/bin/python -m compileall nonebot_plugin_xianmei` —— 全部编译成功
Run: `.venv/bin/python -m pytest tests/ -q` —— 45 passed
Run: `.venv/bin/ruff check .` —— All checks passed!

```bash
git add nonebot_plugin_xianmei/__init__.py tests/test_flatter.py README.md
git commit -m "feat: 群主出现三连播报（检测到出现/开始献媚/彩虹屁）"
```

---

## Self-Review 记录

- **Spec 覆盖**：§2 私聊命令（Task 1：split_group_arg + 六 handler + 用法提示 + 权限保留）、§3 播报（Task 2：三连 + 回退链 + False 静默）、§5 文档（Task 2 Step 6）——全覆盖。
- **占位符扫描**：无 TBD/TODO；所有代码步骤含完整代码。
- **类型一致性**：`split_group_arg` 签名、`make_group_event` 新参数、三条消息文案在任务内逐字一致；既有回复文案未动（v1 测试不受影响）。
