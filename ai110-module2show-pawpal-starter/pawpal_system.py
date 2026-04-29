from __future__ import annotations
from dataclasses import dataclass
from datetime import time, datetime, date, timedelta


PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


@dataclass
class TimeSlot:
    day: str
    start_time: time
    end_time: time

    def duration_hours(self) -> float:
        """Returns the length of this time slot in hours."""
        start = datetime.combine(datetime.today(), self.start_time)
        end = datetime.combine(datetime.today(), self.end_time)
        return (end - start).seconds / 3600


@dataclass
class Pet:
    name: str
    breed: str
    special_notes: str = ""
    tasks: list = None

    def __post_init__(self):
        """Initializes the tasks list to avoid shared mutable default."""
        if self.tasks is None:
            self.tasks = []

    def add_task(self, task) -> None:
        """Adds a task to this pet's task list."""
        self.tasks.append(task)

    def task_count(self) -> int:
        """Returns the number of tasks assigned to this pet."""
        return len(self.tasks)

    def edit_pet_info(self, field: str, value: str) -> None:
        """Updates a pet attribute by field name; raises ValueError if the field doesn't exist."""
        if hasattr(self, field):
            setattr(self, field, value)
        else:
            raise ValueError(f"Pet has no field '{field}'")

    def summary(self) -> str:
        """Returns a formatted one-line summary of the pet's name, breed, and notes."""
        notes = f" | Notes: {self.special_notes}" if self.special_notes else ""
        return f"{self.name} ({self.breed}){notes}"


@dataclass
class Task:
    id: str
    title: str
    duration: float
    priority: str
    assigned_pet: Pet
    completed: bool = False
    time: time = None
    frequency: str | None = None  # "daily", "weekly", or None for one-time tasks
    due_date: date | None = None

    def mark_complete(self) -> Task | None:
        """Marks this task complete. Returns a new Task for the next occurrence if recurring, else None."""
        self.completed = True
        if self.frequency is None or self.frequency.lower() not in ("daily", "weekly"):
            return None
        delta = timedelta(days=1) if self.frequency.lower() == "daily" else timedelta(weeks=1)
        return Task(
            id=f"{self.id}_next",
            title=self.title,
            duration=self.duration,
            priority=self.priority,
            assigned_pet=self.assigned_pet,
            time=self.time,
            frequency=self.frequency,
            due_date=date.today() + delta,
        )

    def edit_task(self, field: str, value) -> None:
        """Updates a task attribute by field name; raises ValueError if the field doesn't exist."""
        if hasattr(self, field):
            setattr(self, field, value)
        else:
            raise ValueError(f"Task has no field '{field}'")


class Owner:
    def __init__(self, name: str):
        self.name = name
        self.availability: list[TimeSlot] = []
        self.pets: list[Pet] = []
        self.tasks: list[Task] = []

    def add_availability(self, day: str, start_time: time, end_time: time) -> None:
        """Appends a new available time slot for the given day."""
        self.availability.append(TimeSlot(day, start_time, end_time))

    def edit_availability(self, day: str, start_time: time, end_time: time) -> None:
        """Updates the time window for an existing day; raises ValueError if the day isn't found."""
        for slot in self.availability:
            if slot.day == day:
                slot.start_time = start_time
                slot.end_time = end_time
                return
        raise ValueError(f"No availability found for '{day}'")

    def calculate_daily_free_time(self) -> dict[str, float]:
        """Returns total available hours per day as a dict keyed by day name."""
        free_time: dict[str, float] = {}
        for slot in self.availability:
            free_time[slot.day] = free_time.get(slot.day, 0) + slot.duration_hours()
        return free_time


class MakeSchedule:
    def __init__(self):
        self.daily_plan: list[tuple[str, Task]] = []  # (day, task)
        self.reasoning: str = ""
        self.incomplete_tasks: list[Task] = []

    def make_plan(self, owner: Owner) -> None:
        """Schedules owner's tasks by priority into available time slots, tracking any that don't fit."""
        self.daily_plan = []
        self.incomplete_tasks = []
        self.reasoning = ""

        free_time = owner.calculate_daily_free_time()
        remaining: dict[str, float] = dict(free_time)

        sorted_tasks = sorted(
            owner.tasks,
            key=lambda t: PRIORITY_ORDER.get(t.priority.lower(), 99)
        )

        log = []
        for task in sorted_tasks:
            scheduled = False
            for day, available in remaining.items():
                if task.duration <= available:
                    self.daily_plan.append((day, task))
                    remaining[day] -= task.duration
                    log.append(
                        f"'{task.title}' ({task.priority}) scheduled on {day} "
                        f"for {task.assigned_pet.name} — {task.duration}h used, "
                        f"{remaining[day]:.1f}h remaining."
                    )
                    scheduled = True
                    break
            if not scheduled:
                self.incomplete_tasks.append(task)
                log.append(
                    f"'{task.title}' ({task.priority}) could not be scheduled "
                    f"— not enough free time on any day."
                )

        self.reasoning = "\n".join(log)

    def explain_reasoning(self) -> str:
        """Returns the scheduling log, or a default message if no plan exists."""
        return self.reasoning if self.reasoning else "No plan has been generated yet."

    def edit_plan(self, task_id: str, new_time: time) -> None:
        """Reschedules a task to a new time by ID; raises ValueError if the task isn't in the plan."""
        for i, (day, task) in enumerate(self.daily_plan):
            if task.id == task_id:
                slot_str = new_time.strftime("%H:%M")
                self.daily_plan[i] = (day, task)
                self.reasoning += f"\n'{task.title}' manually rescheduled to {slot_str} on {day}."
                return
        raise ValueError(f"No scheduled task found with id '{task_id}'")


class Scheduler:
    @staticmethod
    def sort_by_time(tasks: list[Task]) -> list[Task]:
        """Returns a new list of tasks sorted by their time attribute; tasks without a time come last."""
        return sorted(tasks, key=lambda t: (t.time is None, t.time))

    @staticmethod
    def filter_tasks(
        tasks: list[Task],
        completed: bool | None = None,
        pet_name: str | None = None,
    ) -> list[Task]:
        """Returns tasks matching the given completion status and/or pet name (case-insensitive)."""
        result = tasks
        if completed is not None:
            result = [t for t in result if t.completed == completed]
        if pet_name is not None:
            result = [t for t in result if t.assigned_pet.name.lower() == pet_name.lower()]
        return result

    @staticmethod
    def mark_task_complete(task: Task, tasks: list[Task]) -> Task | None:
        """Marks a task complete and, if it recurs, appends the next occurrence to tasks.

        Returns the newly created Task, or None for one-time tasks.
        """
        next_task = task.mark_complete()
        if next_task is not None:
            tasks.append(next_task)
        return next_task

    @staticmethod
    def detect_conflicts(tasks: list[Task]) -> list[str]:
        """Returns a warning string for every pair of tasks that share the same time slot.

        Tasks without a time attribute are skipped. Does not raise; returns an empty list
        when no conflicts exist.
        """
        buckets: dict[time, list[Task]] = {}
        for task in tasks:
            if task.time is not None:
                buckets.setdefault(task.time, []).append(task)

        warnings: list[str] = []
        for slot_time, group in buckets.items():
            if len(group) < 2:
                continue
            time_str = slot_time.strftime("%H:%M")
            for i in range(len(group)):
                for j in range(i + 1, len(group)):
                    a, b = group[i], group[j]
                    pet_note = (
                        "same pet"
                        if a.assigned_pet.name == b.assigned_pet.name
                        else "different pets"
                    )
                    warnings.append(
                        f"WARNING [{time_str}]: '{a.title}' ({a.assigned_pet.name})"
                        f" conflicts with '{b.title}' ({b.assigned_pet.name}) — {pet_note}"
                    )
        return warnings
