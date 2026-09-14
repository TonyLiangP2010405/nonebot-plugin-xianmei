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
