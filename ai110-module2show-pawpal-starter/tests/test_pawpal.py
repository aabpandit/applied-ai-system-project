import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import time, date, timedelta
from pawpal_system import Pet, Task, Scheduler


def test_mark_complete_changes_status():
    pet = Pet(name="Buddy", breed="Labrador")
    task = Task(id="t1", title="Morning walk", duration=1.0, priority="high", assigned_pet=pet)

    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Mochi", breed="Persian Cat")
    task = Task(id="t2", title="Vet medication", duration=0.5, priority="high", assigned_pet=pet)

    assert pet.task_count() == 0
    pet.add_task(task)
    assert pet.task_count() == 1


# --- Sorting Correctness ---

def test_sort_by_time_returns_chronological_order():
    pet = Pet(name="Buddy", breed="Labrador")
    t1 = Task(id="s1", title="Evening walk",  duration=1.0, priority="low",    assigned_pet=pet, time=time(18, 0))
    t2 = Task(id="s2", title="Morning walk",  duration=1.0, priority="high",   assigned_pet=pet, time=time(7, 0))
    t3 = Task(id="s3", title="Afternoon play", duration=0.5, priority="medium", assigned_pet=pet, time=time(13, 30))

    sorted_tasks = Scheduler.sort_by_time([t1, t2, t3])

    assert [t.time for t in sorted_tasks] == [time(7, 0), time(13, 30), time(18, 0)]


def test_sort_by_time_places_no_time_tasks_last():
    pet = Pet(name="Luna", breed="Siamese")
    timed   = Task(id="s4", title="Feeding",  duration=0.25, priority="high", assigned_pet=pet, time=time(8, 0))
    untimed = Task(id="s5", title="Grooming", duration=0.5,  priority="low",  assigned_pet=pet, time=None)

    sorted_tasks = Scheduler.sort_by_time([untimed, timed])

    assert sorted_tasks[0].id == "s4"
    assert sorted_tasks[1].id == "s5"


# --- Recurrence Logic ---

def test_daily_task_complete_creates_next_day_task():
    pet = Pet(name="Rex", breed="German Shepherd")
    task = Task(id="r1", title="Daily walk", duration=1.0, priority="high",
                assigned_pet=pet, frequency="daily")
    tasks = [task]

    next_task = Scheduler.mark_task_complete(task, tasks)

    assert task.completed is True
    assert next_task is not None
    assert next_task.due_date == date.today() + timedelta(days=1)
    assert next_task in tasks


def test_one_time_task_complete_returns_none():
    pet = Pet(name="Whiskers", breed="Maine Coon")
    task = Task(id="r2", title="Vet visit", duration=2.0, priority="high",
                assigned_pet=pet, frequency=None)
    tasks = [task]

    next_task = Scheduler.mark_task_complete(task, tasks)

    assert task.completed is True
    assert next_task is None
    assert len(tasks) == 1  # no new task appended


# --- Conflict Detection ---

def test_detect_conflicts_flags_duplicate_times():
    pet = Pet(name="Coco", breed="Poodle")
    t1 = Task(id="c1", title="Feeding",    duration=0.25, priority="high",   assigned_pet=pet, time=time(9, 0))
    t2 = Task(id="c2", title="Medication", duration=0.25, priority="medium", assigned_pet=pet, time=time(9, 0))

    warnings = Scheduler.detect_conflicts([t1, t2])

    assert len(warnings) == 1
    assert "09:00" in warnings[0]
    assert "Feeding" in warnings[0]
    assert "Medication" in warnings[0]


def test_detect_conflicts_no_warning_for_distinct_times():
    pet = Pet(name="Max", breed="Beagle")
    t1 = Task(id="c3", title="Morning run", duration=1.0, priority="high", assigned_pet=pet, time=time(7, 0))
    t2 = Task(id="c4", title="Evening run", duration=1.0, priority="low",  assigned_pet=pet, time=time(18, 0))

    warnings = Scheduler.detect_conflicts([t1, t2])

    assert warnings == []


def test_detect_conflicts_skips_tasks_without_time():
    pet = Pet(name="Daisy", breed="Corgi")
    t1 = Task(id="c5", title="Grooming", duration=1.0, priority="low", assigned_pet=pet, time=None)
    t2 = Task(id="c6", title="Brushing", duration=0.5, priority="low", assigned_pet=pet, time=None)

    warnings = Scheduler.detect_conflicts([t1, t2])

    assert warnings == []
