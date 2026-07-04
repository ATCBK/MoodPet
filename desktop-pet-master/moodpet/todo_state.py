from dataclasses import dataclass, replace
from datetime import date
from typing import Iterable, List, Sequence


@dataclass(frozen=True)
class TodoItem:
    id: int
    title: str
    category: str
    due_time: str
    completed: bool = False
    starred: bool = False
    completed_at: str = ""


DEFAULT_TODOS = [
    TodoItem(1, "完成产品需求文档初稿", "工作", "10:00"),
    TodoItem(2, "回复重要邮件", "工作", "14:00"),
    TodoItem(3, "运动 30 分钟", "生活", "18:00"),
    TodoItem(4, "喝一杯水", "生活", "09:15", completed=True, starred=True, completed_at="09:15"),
]

CATEGORY_COLORS = {
    "工作": "#ffb45a",
    "生活": "#56a8ff",
    "学习": "#9c7cff",
    "健康": "#20b987",
}


def today_label(today: date | None = None) -> str:
    current = today or date.today()
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    return f"今天是 {current:%Y/%m/%d} {weekdays[current.weekday()]}"


def completion_text(items: Sequence[TodoItem]) -> str:
    total = len(items)
    done = sum(1 for item in items if item.completed)
    return f"已完成 {done}/{total}" if total else "已完成 0/0"


def completion_ratio(items: Sequence[TodoItem]) -> float:
    if not items:
        return 0.0
    return sum(1 for item in items if item.completed) / len(items)


def visible_todos(items: Iterable[TodoItem], tab: str = "today", sort_mode: str = "time") -> List[TodoItem]:
    if tab == "completed":
        filtered = [item for item in items if item.completed]
    else:
        filtered = list(items)

    if sort_mode == "category":
        return sorted(filtered, key=lambda item: (item.category, item.completed, item.due_time, item.id))
    if sort_mode == "starred":
        return sorted(filtered, key=lambda item: (not item.starred, item.completed, item.due_time, item.id))
    return sorted(filtered, key=lambda item: (item.completed, item.due_time, item.id))


def next_todo_id(items: Sequence[TodoItem]) -> int:
    return max((item.id for item in items), default=0) + 1


def add_todo(items: Sequence[TodoItem], title: str, category: str = "生活", due_time: str = "今天") -> List[TodoItem]:
    clean_title = title.strip()
    if not clean_title:
        return list(items)
    return list(items) + [TodoItem(next_todo_id(items), clean_title, category, due_time)]


def toggle_completed(items: Sequence[TodoItem], item_id: int, completed_at: str = "刚刚") -> List[TodoItem]:
    result = []
    for item in items:
        if item.id == item_id:
            done = not item.completed
            result.append(replace(item, completed=done, completed_at=completed_at if done else ""))
        else:
            result.append(item)
    return result


def toggle_starred(items: Sequence[TodoItem], item_id: int) -> List[TodoItem]:
    return [replace(item, starred=not item.starred) if item.id == item_id else item for item in items]


def fatigue_level(completed_count: int, total_count: int) -> int:
    if total_count <= 0:
        return 50
    unfinished = total_count - completed_count
    return max(15, min(90, 40 + unfinished * 12 - completed_count * 4))


def assistant_message(items: Sequence[TodoItem]) -> str:
    remaining = [item for item in items if not item.completed]
    if not remaining:
        return "今天任务都清空啦，给自己一点奖励吧！"
    if len(remaining) == 1:
        return "先完成最后一个小任务，会让你更有成就感！"
    return "先完成一个小任务，会让你更有成就感！"

