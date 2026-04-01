from datetime import time
from pawpal_system import Owner, Pet, Task, MakeSchedule

# --- Setup ---
owner = Owner("Alex")
owner.add_availability("Monday", time(7, 0), time(9, 0))   # 2h
owner.add_availability("Monday", time(17, 0), time(20, 0)) # 3h
owner.add_availability("Tuesday", time(8, 0), time(11, 0)) # 3h

# --- Pets ---
buddy = Pet(name="Buddy", breed="Labrador", special_notes="Allergic to wheat")
mochi = Pet(name="Mochi", breed="Persian Cat", special_notes="Indoor only")

owner.pets = [buddy, mochi]

# --- Tasks ---
owner.tasks = [
    Task(id="t1", title="Morning walk",       duration=1.0, priority="high",   assigned_pet=buddy),
    Task(id="t2", title="Vet medication",     duration=0.5, priority="high",   assigned_pet=mochi),
    Task(id="t3", title="Grooming session",   duration=2.0, priority="medium", assigned_pet=buddy),
    Task(id="t4", title="Playtime",           duration=1.5, priority="low",    assigned_pet=mochi),
]

# --- Generate Schedule ---
schedule = MakeSchedule()
schedule.make_plan(owner)

# --- Print Today's Schedule ---
print("=" * 40)
print("        TODAY'S SCHEDULE")
print("=" * 40)

if schedule.daily_plan:
    current_day = None
    for day, task in schedule.daily_plan:
        if day != current_day:
            current_day = day
            print(f"\n  {day.upper()}")
            print("  " + "-" * 20)
        print(f"  [ ] {task.title} ({task.duration}h) — {task.assigned_pet.name}  [{task.priority.upper()}]")
else:
    print("  No tasks could be scheduled.")

if schedule.incomplete_tasks:
    print("\n  COULD NOT SCHEDULE:")
    print("  " + "-" * 20)
    for task in schedule.incomplete_tasks:
        print(f"  [!] {task.title} ({task.duration}h) — {task.assigned_pet.name}  [{task.priority.upper()}]")

print("\n" + "=" * 40)
print("  REASONING")
print("=" * 40)
print(schedule.explain_reasoning())
print("=" * 40)
