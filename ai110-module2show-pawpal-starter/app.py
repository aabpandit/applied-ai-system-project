import streamlit as st
from pawpal_system import Owner, Pet, Task, MakeSchedule

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ── Session-state bootstrap ──────────────────────────────────────────────────
if "owner" not in st.session_state:
    st.session_state.owner = None
if "scheduler" not in st.session_state:
    st.session_state.scheduler = MakeSchedule()
if "task_counter" not in st.session_state:
    st.session_state.task_counter = 0

# ── Owner setup ──────────────────────────────────────────────────────────────
st.subheader("Owner")
owner_name = st.text_input("Owner name", value="Jordan")

col_day, col_start, col_end = st.columns(3)
with col_day:
    avail_day = st.selectbox("Day", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
with col_start:
    start_hour = st.number_input("Start hour (0–23)", min_value=0, max_value=23, value=8)
with col_end:
    end_hour = st.number_input("End hour (0–23)", min_value=1, max_value=24, value=12)

if st.button("Set owner & availability"):
    from datetime import time
    st.session_state.owner = Owner(owner_name)
    st.session_state.owner.add_availability(avail_day, time(start_hour), time(end_hour))
    st.success(f"Owner '{owner_name}' created with {end_hour - start_hour}h free on {avail_day}.")

st.divider()

# ── Add a Pet ────────────────────────────────────────────────────────────────
st.subheader("Add a Pet")
pet_name = st.text_input("Pet name", value="Mochi")
pet_breed = st.text_input("Breed", value="Shiba Inu")
pet_notes = st.text_input("Special notes (optional)", value="")

if st.button("Add pet"):
    if st.session_state.owner is None:
        st.warning("Create an owner first.")
    else:
        pet = Pet(name=pet_name, breed=pet_breed, special_notes=pet_notes)
        st.session_state.owner.pets.append(pet)
        st.success(f"Added pet: {pet.summary()}")

if st.session_state.owner and st.session_state.owner.pets:
    st.write("Pets:", [p.summary() for p in st.session_state.owner.pets])

st.divider()

# ── Schedule a Task ──────────────────────────────────────────────────────────
st.subheader("Schedule a Task")

owner = st.session_state.owner
pet_options = [p.name for p in owner.pets] if owner else []

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (hours)", min_value=0.25, max_value=8.0, value=0.5, step=0.25)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

assigned_pet_name = st.selectbox("Assign to pet", pet_options if pet_options else ["— add a pet first —"])

if st.button("Add task"):
    if owner is None:
        st.warning("Create an owner first.")
    elif not owner.pets:
        st.warning("Add a pet before scheduling tasks.")
    else:
        pet_obj = next(p for p in owner.pets if p.name == assigned_pet_name)
        st.session_state.task_counter += 1
        task = Task(
            id=f"task-{st.session_state.task_counter}",
            title=task_title,
            duration=duration,
            priority=priority,
            assigned_pet=pet_obj,
        )
        pet_obj.add_task(task)
        owner.tasks.append(task)
        st.success(f"Task '{task.title}' ({priority}, {duration}h) added for {pet_obj.name}.")

if owner and owner.tasks:
    st.write("Current tasks:")
    st.table([
        {"Title": t.title, "Pet": t.assigned_pet.name, "Duration (h)": t.duration, "Priority": t.priority}
        for t in owner.tasks
    ])

st.divider()

# ── Generate Schedule ────────────────────────────────────────────────────────
st.subheader("Build Schedule")

if st.button("Generate schedule"):
    if owner is None or not owner.tasks:
        st.warning("Add an owner, a pet, and at least one task first.")
    else:
        st.session_state.scheduler.make_plan(owner)
        plan = st.session_state.scheduler.daily_plan
        if plan:
            st.success("Schedule generated!")
            st.table([
                {"Day": day, "Task": t.title, "Pet": t.assigned_pet.name,
                 "Duration (h)": t.duration, "Priority": t.priority}
                for day, t in plan
            ])
        incomplete = st.session_state.scheduler.incomplete_tasks
        if incomplete:
            st.warning("Could not schedule: " + ", ".join(t.title for t in incomplete))

        with st.expander("Scheduling reasoning"):
            st.text(st.session_state.scheduler.explain_reasoning())
