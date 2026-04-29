from dataclasses import dataclass
from datetime import time, datetime


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

    def mark_complete(self) -> None:
        """Marks this task as completed."""
        self.completed = True

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
