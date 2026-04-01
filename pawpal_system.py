from dataclasses import dataclass


@dataclass
class TimeSlot:
    day: str
    start_time: str
    end_time: str


@dataclass
class Pet:
    name: str
    breed: str
    special_notes: str = ""

    def edit_pet_info(self, field: str, value: str) -> None:
        pass

    def summary(self) -> str:
        pass


@dataclass
class Task:
    title: str
    duration: float
    priority: str
    assigned_pet: str

    def edit_task(self, field: str, value) -> None:
        pass


class Owner:
    def __init__(self, name: str):
        self.name = name
        self.availability: list[TimeSlot] = []

    def add_availability(self, day: str, start_time: str, end_time: str) -> None:
        pass

    def edit_availability(self, day: str, start_time: str, end_time: str) -> None:
        pass

    def calculate_daily_free_time(self) -> float:
        pass


class MakeSchedule:
    def __init__(self):
        self.daily_plan: list[Task] = []
        self.reasoning: str = ""
        self.incomplete_tasks: list[Task] = []

    def make_plan(self, owner: Owner, pets: list[Pet], tasks: list[Task]) -> None:
        pass

    def explain_reasoning(self) -> str:
        pass

    def edit_plan(self, task_id: str, new_time: str) -> None:
        pass
