from datetime import time, date
from pawpal_system import Owner, Pet, Task, MakeSchedule, Scheduler

# --- Setup ---
owner = Owner("Alex")
owner.add_availability("Monday", time(7, 0), time(9, 0))   # 2h
owner.add_availability("Monday", time(17, 0), time(20, 0)) # 3h
owner.add_availability("Tuesday", time(8, 0), time(11, 0)) # 3h

# --- Pets ---
buddy = Pet(name="Buddy", breed="Labrador", special_notes="Allergic to wheat")
mochi = Pet(name="Mochi", breed="Persian Cat", special_notes="Indoor only")

owner.pets = [buddy, mochi]

# --- Tasks (added out of order by time) ---
owner.tasks = [
    Task(id="t4", title="Playtime",         duration=1.5, priority="low",    assigned_pet=mochi, time=time(15, 0)),
    Task(id="t2", title="Vet medication",   duration=0.5, priority="high",   assigned_pet=mochi, time=time(9, 30), frequency="weekly",  due_date=date.today()),
    Task(id="t3", title="Grooming session", duration=2.0, priority="medium", assigned_pet=buddy, time=time(11, 0)),
    Task(id="t1", title="Morning walk",     duration=1.0, priority="high",   assigned_pet=buddy, time=time(7, 0),  frequency="daily",   due_date=date.today()),
    # Deliberately conflicting tasks
    Task(id="t5", title="Nail trim",        duration=0.5, priority="medium", assigned_pet=buddy, time=time(9, 30)),  # different-pet conflict with t2
    Task(id="t6", title="Morning stretch",  duration=0.5, priority="low",    assigned_pet=buddy, time=time(7, 0)),   # same-pet conflict with t1
]

# --- Conflict Detection ---
print("=" * 40)
print("  CONFLICT DETECTION")
print("=" * 40)
conflicts = Scheduler.detect_conflicts(owner.tasks)
if conflicts:
    for warning in conflicts:
        print(f"  {warning}")
else:
    print("  No conflicts found.")
print()

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

# --- Recurring task demo ---
print("\n" + "=" * 40)
print("  RECURRING TASK COMPLETION")
print("=" * 40)

def _task_row(t: Task) -> str:
    freq = f"[{t.frequency}]" if t.frequency else "[one-time]"
    due  = f"due {t.due_date}" if t.due_date else ""
    status = "[x]" if t.completed else "[ ]"
    return f"  {status} {t.title} {freq} {due}".rstrip()

print(f"\n  Tasks before completion ({len(owner.tasks)} total):")
for t in owner.tasks:
    print(_task_row(t))

# Complete both recurring tasks through Scheduler so next occurrences are auto-added
morning_walk   = next(t for t in owner.tasks if t.id == "t1")
vet_medication = next(t for t in owner.tasks if t.id == "t2")

next_walk = Scheduler.mark_task_complete(morning_walk,   owner.tasks)
next_vet  = Scheduler.mark_task_complete(vet_medication, owner.tasks)

print(f"\n  Tasks after completion ({len(owner.tasks)} total):")
for t in owner.tasks:
    print(_task_row(t))

print("\n  Newly created occurrences:")
for new_task in (next_walk, next_vet):
    if new_task:
        print(f"    -> {new_task.title} | due {new_task.due_date} [{new_task.frequency}]")

# --- Sort by time ---
print("\n" + "=" * 40)
print("  SORTED BY TIME")
print("=" * 40)
sorted_tasks = Scheduler.sort_by_time(owner.tasks)
for task in sorted_tasks:
    time_str = task.time.strftime("%H:%M") if task.time else "no time"
    status = "[x]" if task.completed else "[ ]"
    print(f"  {status} {time_str}  {task.title} — {task.assigned_pet.name}")

# --- Filter: incomplete tasks only ---
print("\n" + "=" * 40)
print("  FILTER: INCOMPLETE TASKS")
print("=" * 40)
incomplete = Scheduler.filter_tasks(owner.tasks, completed=False)
for task in incomplete:
    print(f"  [ ] {task.title} — {task.assigned_pet.name}")

# --- Filter: tasks for Buddy ---
print("\n" + "=" * 40)
print("  FILTER: BUDDY'S TASKS")
print("=" * 40)
buddy_tasks = Scheduler.filter_tasks(owner.tasks, pet_name="Buddy")
for task in buddy_tasks:
    status = "[x]" if task.completed else "[ ]"
    print(f"  {status} {task.title} [{task.priority.upper()}]")

print("=" * 40)
