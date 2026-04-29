import streamlit as st
from pawpal_system import Owner, Pet, Task, MakeSchedule, Scheduler
from rag_chat import ask as triage_ask

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
    avail_day = st.selectbox(
        "Day",
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    )
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
    duration = st.number_input(
        "Duration (hours)", min_value=0.25, max_value=8.0, value=0.5, step=0.25
    )
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

assigned_pet_name = st.selectbox(
    "Assign to pet", pet_options if pet_options else ["— add a pet first —"]
)

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

# ── Task list with filtering and sorting ─────────────────────────────────────
if owner and owner.tasks:
    st.markdown("**Current tasks**")

    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        filter_pet = st.selectbox(
            "Filter by pet",
            ["All pets"] + [p.name for p in owner.pets],
            key="filter_pet",
        )
    with filter_col2:
        filter_status = st.selectbox(
            "Filter by status", ["All", "Pending", "Completed"], key="filter_status"
        )

    filtered = owner.tasks
    if filter_pet != "All pets":
        filtered = Scheduler.filter_tasks(filtered, pet_name=filter_pet)
    if filter_status == "Pending":
        filtered = Scheduler.filter_tasks(filtered, completed=False)
    elif filter_status == "Completed":
        filtered = Scheduler.filter_tasks(filtered, completed=True)

    sorted_tasks = Scheduler.sort_by_time(filtered)

    PRIORITY_LABEL = {"high": "🔴 High", "medium": "🟡 Medium", "low": "🟢 Low"}

    if sorted_tasks:
        st.table(
            [
                {
                    "Title": t.title,
                    "Pet": t.assigned_pet.name,
                    "Duration (h)": t.duration,
                    "Priority": PRIORITY_LABEL.get(t.priority.lower(), t.priority),
                    "Time": t.time.strftime("%H:%M") if t.time else "—",
                    "Status": "✅ Done" if t.completed else "⏳ Pending",
                }
                for t in sorted_tasks
            ]
        )
    else:
        st.info("No tasks match the current filters.")

    # Inline conflict check — runs whenever tasks have assigned times
    conflicts = Scheduler.detect_conflicts(owner.tasks)
    if conflicts:
        st.markdown("**⚠️ Time Conflicts Detected**")
        for warning in conflicts:
            # Strip the raw "WARNING [HH:MM]:" prefix and reframe for a pet owner
            clean = warning.replace("WARNING ", "")
            if "same pet" in clean:
                st.warning(
                    f"**Same-pet conflict** — {clean}\n\n"
                    "Your pet cannot be in two places at once. "
                    "Reschedule or adjust the duration of one of these tasks."
                )
            else:
                st.warning(
                    f"**Overlapping tasks** — {clean}\n\n"
                    "You are double-booked at this time. "
                    "You can only attend one pet at a time — please adjust the schedule."
                )

st.divider()

# ── Generate Schedule ────────────────────────────────────────────────────────
st.subheader("Build Schedule")

if st.button("Generate schedule"):
    if owner is None or not owner.tasks:
        st.warning("Add an owner, a pet, and at least one task first.")
    else:
        st.session_state.scheduler.make_plan(owner)
        plan = st.session_state.scheduler.daily_plan
        incomplete = st.session_state.scheduler.incomplete_tasks

        # Conflict check on the scheduled tasks
        scheduled_tasks = [task for _, task in plan]
        conflicts = Scheduler.detect_conflicts(scheduled_tasks)
        if conflicts:
            st.markdown("### ⚠️ Schedule Conflicts")
            for warning in conflicts:
                clean = warning.replace("WARNING ", "")
                same = "same pet" in clean
                tip = (
                    "Your pet cannot do two things at once — adjust one task's time or duration."
                    if same
                    else "You can only be with one pet at a time — stagger these tasks."
                )
                st.warning(f"**{'Same-pet conflict' if same else 'Overlapping tasks'}:** {clean}\n\n💡 {tip}")

        if plan:
            st.success(f"Schedule generated — {len(plan)} task(s) placed across your availability.")
            PRIORITY_LABEL = {"high": "🔴 High", "medium": "🟡 Medium", "low": "🟢 Low"}
            st.table(
                [
                    {
                        "Day": day,
                        "Task": t.title,
                        "Pet": t.assigned_pet.name,
                        "Duration (h)": t.duration,
                        "Priority": PRIORITY_LABEL.get(t.priority.lower(), t.priority),
                    }
                    for day, t in plan
                ]
            )

        if incomplete:
            st.markdown("**Tasks that could not be scheduled:**")
            for task in incomplete:
                st.warning(
                    f"**{task.title}** for {task.assigned_pet.name} — "
                    f"needs {task.duration}h but no free slot is available. "
                    "Try adding more availability or shortening this task."
                )

        with st.expander("Scheduling reasoning"):
            st.text(st.session_state.scheduler.explain_reasoning())

st.divider()

# ── Symptom Triage (RAG + Gemini) ────────────────────────────────────────────
st.subheader("Symptom Triage")
st.caption("Describe your pet's symptoms and get personalised guidance drawn from trusted veterinary sources.")

URGENCY_CONFIG = {
    "emergency": {"icon": "🚨", "color": "error",   "label": "EMERGENCY — Go to an emergency vet immediately"},
    "urgent":    {"icon": "⚠️",  "color": "warning", "label": "URGENT — See a vet within 24 hours"},
    "monitor":   {"icon": "👀", "color": "warning", "label": "MONITOR — Watch at home; escalate if it worsens"},
    "routine":   {"icon": "📅", "color": "info",    "label": "ROUTINE — Schedule a regular vet visit"},
}

with st.form("triage_form"):
    symptom_query = st.text_area(
        "Describe your pet's symptoms",
        placeholder="e.g. My dog vomited twice this morning and seems really tired...",
        height=100,
    )
    species_filter = st.selectbox("Pet species (optional)", ["Any", "Dog", "Cat"])
    submitted = st.form_submit_button("Get Advice")

if submitted:
    if not symptom_query.strip():
        st.warning("Please describe the symptoms before submitting.")
    else:
        species_arg = None if species_filter == "Any" else species_filter.lower()
        with st.spinner("Finding the best match and generating a response…"):
            try:
                result = triage_ask(symptom_query, species=species_arg)
                match = result["match"]
                cfg = URGENCY_CONFIG.get(result["urgency"], URGENCY_CONFIG["routine"])

                # ── urgency banner ───────────────────────────────────────────
                banner = f"{cfg['icon']} **{cfg['label']}**"
                if cfg["color"] == "error":
                    st.error(banner)
                elif cfg["color"] == "warning":
                    st.warning(banner)
                else:
                    st.info(banner)

                # ── Gemini synthesised response ──────────────────────────────
                st.markdown("**PawPal+ Advice**")
                st.write(result["response"])

                # ── matched FAQ entry ────────────────────────────────────────
                if match:
                    with st.expander(
                        f"📚 Matched FAQ — similarity {match['score']:.0%} "
                        f"| {match['category']} | {', '.join(match['species'])}"
                    ):
                        st.markdown(f"**Q:** {match['question']}")
                        st.markdown(f"**A:** {match['answer']}")
                        st.markdown(
                            f"**Source:** [{match['source']}]({match['source_url']})"
                        )

                # ── prompt inspector (dev aid) ───────────────────────────────
                with st.expander("🔧 Prompt sent to Gemini"):
                    st.code(result["prompt"], language="markdown")

            except EnvironmentError as exc:
                st.error(str(exc))
            except Exception as exc:
                st.error(f"Something went wrong: {exc}")
