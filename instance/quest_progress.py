import datetime
from dataclasses import dataclass
from enum import Enum

from utils.db import get_connection


class QuestStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class QuestEntry:
    quest_id: str
    status: QuestStatus
    started_at: str
    completed_at: str


class QuestProgress:
    def __init__(self):
        self._quests: dict[str, QuestEntry] = {}
        self.reload()

    def reload(self) -> None:
        self._quests.clear()
        with get_connection() as conn:
            for row in conn.execute(
                "SELECT quest_id, status, started_at, completed_at FROM quest_progress"
            ):
                entry = QuestEntry(
                    quest_id=row["quest_id"],
                    status=QuestStatus(row["status"]),
                    started_at=row["started_at"],
                    completed_at=row["completed_at"] or "",
                )
                self._quests[entry.quest_id] = entry

    def get_completed(self) -> set[str]:
        return {q.quest_id for q in self._quests.values() if q.status == QuestStatus.COMPLETED}

    def get_active(self) -> set[str]:
        return {q.quest_id for q in self._quests.values() if q.status == QuestStatus.ACTIVE}

    def get_status(self, quest_id: str) -> QuestStatus | None:
        entry = self._quests.get(quest_id)
        return entry.status if entry else None

    def start(self, quest_id: str) -> bool:
        if quest_id in self._quests:
            return False
        now = datetime.datetime.now().isoformat(timespec="seconds")
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO quest_progress (quest_id, status, started_at, completed_at) VALUES (?, ?, ?, ?)",
                (quest_id, QuestStatus.ACTIVE, now, ""),
            )
        self._quests[quest_id] = QuestEntry(quest_id=quest_id, status=QuestStatus.ACTIVE, started_at=now, completed_at="")
        return True

    def complete(self, quest_id: str) -> bool:
        entry = self._quests.get(quest_id)
        if not entry or entry.status != QuestStatus.ACTIVE:
            return False
        now = datetime.datetime.now().isoformat(timespec="seconds")
        entry.status = QuestStatus.COMPLETED
        entry.completed_at = now
        with get_connection() as conn:
            conn.execute(
                "UPDATE quest_progress SET status = ?, completed_at = ? WHERE quest_id = ?",
                (QuestStatus.COMPLETED, now, quest_id),
            )
        return True

    def fail(self, quest_id: str) -> bool:
        entry = self._quests.get(quest_id)
        if not entry or entry.status != QuestStatus.ACTIVE:
            return False
        entry.status = QuestStatus.FAILED
        with get_connection() as conn:
            conn.execute(
                "UPDATE quest_progress SET status = ? WHERE quest_id = ?",
                (QuestStatus.FAILED, quest_id),
            )
        return True

    def remove(self, quest_id: str) -> bool:
        entry = self._quests.get(quest_id)
        if not entry or entry.status != QuestStatus.ACTIVE:
            return False
        del self._quests[quest_id]
        with get_connection() as conn:
            conn.execute("DELETE FROM quest_progress WHERE quest_id = ?", (quest_id,))
        return True
