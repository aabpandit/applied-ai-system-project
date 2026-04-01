import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pawpal_system import Pet, Task


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
