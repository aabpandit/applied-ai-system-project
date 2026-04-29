# PawPal+ with Health Chatbot

## Original Project: PawPal+

**PawPal+** is a Streamlit app designed to help busy pet owners stay on top of daily care routines. The original app lets an owner enter their available time windows, add pets, and create care tasks (walks, feeding, etc.) with a priority level and duration. A scheduling engine then fits those tasks into the owner's day, sorted by priority, and explains exactly why each task was placed where it was or why it couldn't be placed.

---

## What This Project Adds: RAG-Powered Health Chatbot

This extension adds a Retrieval-Augmented Generation (RAG) pipeline to the original PawPal+ scheduler. The new Health Chatbot lets a pet owner describe their pet's symptoms in plain language and receive personalised, urgency-aware veterinary guidance from a curated knowledge base of veterinary FAQs (human-made) and synthesized by Google Gemini.

**Why it matters:** Scheduling care tasks helps owners stay consistent, but pet ownership also involves unexpected health concerns. Having a chatbot that can answer pet health related questions directly inside the same app means owners get both planning and guidance without switching tools.
---

## Architecture Overview

The system has two distinct layers that share a single Streamlit frontend:

```
User (Streamlit UI — app.py)
        │
        ├── Scheduling layer (original project)
        │       pawpal_system.py
        │       Owner / Pet / Task / MakeSchedule / Scheduler
        │
        └── RAG chatbot layer
                build_index.py  ──►  data/embeddings.npy
                                      data/metadata.pkl
                retriever.py    ──►  cosine similarity lookup
                rag_chat.py     ──►  Gemini API (gemini-2.5-flash-lite)
```

1. **Index build** (`build_index.py`) — reads `data/rag_knowledge_base.json`, encodes every FAQ entry with sentence embeddings and saves `embeddings.npy` + `metadata.pkl` to disk. This step runs once, offline.

2. **Retrieval** (`retriever.py`) — loads the saved index once per process. At query time it encodes the user's symptom description with the same model and finds the closest FAQ entry using a dot-product cosine similarity.

3. **Generation** (`rag_chat.py`) — builds a structured prompt that includes the matched FAQ, the owner's raw text, and urgency-specific instructions. The prompt is sent to Gemini, which synthesizes a personalised ≤220-word response.

4. **Scheduling core** (`pawpal_system.py`) — five classes handle the original scheduling domain: `Owner` (availability + pets + tasks), `Pet` (breed, notes, task list), `Task` (duration, priority, recurrence), `MakeSchedule` (greedy priority-first scheduler with reasoning log), and `Scheduler` (static helpers: sort by time, filter, conflict detection, recurring task completion).

---

## Setup Instructions

### 1. Clone and create a virtual environment

```bash
git clone <repo-url>
cd ai110-module2show-pawpal-starter

python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows
.venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Add your Gemini API key

Create a `.env` file in the project root:

```
GEMINI_API_KEY=your-key-here
```

### 4. Build the vector index (one-time step)

```bash
python build_index.py
```

This reads `data/rag_knowledge_base.json` and writes `data/embeddings.npy` and `data/metadata.pkl`. You only need to re-run this if the knowledge base changes.

### 5. Launch the app

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`.

---

## Sample Interactions

Loom video link: https://www.loom.com/share/9f515a24c81d4041b2ec2b1d2861eb92 

### Example 1 — Scheduling: high-priority tasks fill the day first

**Input:** Owner "Jordan" has 4 hours free on Monday. Three tasks are added:
- Evening grooming — 1 h, low priority
- Morning walk — 0.5 h, high priority
- Medication — 0.25 h, high priority

**Output (Schedule table):**

| Day    | Task          | Pet   | Duration (h) | Priority   |
|--------|---------------|-------|-------------|------------|
| Monday | Morning walk  | Mochi | 0.5         | High       |
| Monday | Medication    | Mochi | 0.25        | High       |
| Monday | Evening groom | Mochi | 1.0         | Low        |

**Scheduling reasoning (expander):**
```
'Morning walk' (high) scheduled on Monday for Mochi — 0.5h used, 3.5h remaining.
'Medication' (high) scheduled on Monday for Mochi — 0.25h used, 3.25h remaining.
'Evening groom' (low) scheduled on Monday for Mochi — 1.0h used, 2.25h remaining.
```

---

### Example 2 — Health Chatbot: Minor concern

**Input:** "My dog has been scratching a lot and I noticed some flaking around his ears."

**Urgency banner:** `ROUTINE — Schedule a regular vet visit`

**PawPal+ Advice (Gemini response, excerpt):**
> It sounds like your dog may be dealing with a skin issue, possibly dry skin, allergies, or early signs of a yeast or bacterial skin infection around the ear area. For now, keep the area clean and dry, avoid letting him scratch excessively (an e-collar can help), and check for redness, discharge, or odour that could signal an infection. This information is drawn from the ASPCA Pet Care Library. *PawPal+ is not a substitute for professional veterinary advice.*

---

### Example 3 — Health Chatbot: Emergency

**Input:** "My cat collapsed and isn't responding to me. She's breathing very strangely."

**Urgency banner:** `EMERGENCY — Go to an emergency vet immediately`

**PawPal+ Advice (Gemini response, excerpt):**
> **Go to an emergency veterinary clinic right now.** Collapse combined with abnormal breathing is a critical emergency — do not wait to see if she improves. Keep her as still and calm as possible during transport. Do not offer food or water. This aligns with guidance from the VCA Animal Hospital emergency care resources. *PawPal+ is not a substitute for professional veterinary advice.*

---

## Design Decisions

**Why use RAG instead of a just a LLM?**
Pet health is a very real concern for owners.A large language model can hallucinate plausible-sounding but incorrect veterinary advice, so grounding every response in a database gives the model a concrete, source-attributed fact to work from. It reduces hallucination risk, and lets us cite the source in the response so owners know where the information came from.

**Why save the index to disk rather than re-embedding each request?**
Embedding 100+ FAQs with a transformer takes a few seconds. Doing that on every user request would make the UI feel slow. Saving the index once and loading it as a module-level singleton means retrieval happens in milliseconds after the first warm-up.

---

