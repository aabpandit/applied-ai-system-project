from __future__ import annotations

import os
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv

from retriever import retrieve, retrieve_for_species

load_dotenv(Path(__file__).parent / ".env")

# gemini-2.0-flash has no free-tier quota (limit: 0).
# gemini-1.5-flash is free up to 15 RPM / 1,500 req/day.
GEMINI_MODEL = "gemini-2.5-flash-lite"

_URGENCY_INSTRUCTION: dict[str, str] = {
    "emergency": (
        "THIS IS A MEDICAL EMERGENCY. Lead your response with a clear, "
        "prominent call to action: go to an emergency vet RIGHT NOW. "
        "Do not bury this warning."
    ),
    "urgent": (
        "This situation is urgent. Advise the owner to call or visit a vet "
        "within the next 24 hours and explain why waiting is risky."
    ),
    "monitor": (
        "This can be managed at home for now. Provide specific home-care steps "
        "and clear criteria for when to escalate to a vet."
    ),
    "routine": (
        "This is a routine concern. Give practical, reassuring advice and "
        "recommend scheduling a regular vet visit."
    ),
}


def _build_prompt(user_query: str, match: dict) -> str:
    urgency_instruction = _URGENCY_INSTRUCTION.get(match["urgency"], "")
    species_str = " and ".join(match.get("species", ["pet"]))

    return (
        f"You are PawPal+, a knowledgeable and compassionate pet care assistant. "
        f"A pet owner has described a concern about their {species_str}. "
        f"Use the Closest Matching FAQ below as your primary source of truth, "
        f"then personalise the answer to their specific situation.\n\n"
        f"## Closest Matching FAQ\n"
        f"Question : {match['question']}\n"
        f"Answer   : {match['answer']}\n"
        f"Urgency  : {match['urgency'].upper()}\n"
        f"Source   : {match['source']}\n\n"
        f"## What the Owner Said\n"
        f"\"{user_query}\"\n\n"
        f"## Response Instructions\n"
        f"- Urgency handling: {urgency_instruction}\n"
        f"- Address the owner's description directly; do not just repeat the FAQ verbatim.\n"
        f"- Use plain, empathetic language -- the owner may be worried.\n"
        f"- If the urgency is 'emergency', your first sentence must be the emergency action.\n"
        f"- Cite the source (\"{match['source']}\") naturally within or at the end of your response.\n"
        f"- Close with exactly one sentence: a disclaimer that PawPal+ is not a substitute "
        f"for professional veterinary advice.\n"
        f"- Keep the total response under 220 words.\n"
    )


def ask(
    user_query: str,
    species: str | None = None,
    top_k: int = 1,
) -> dict:
    """Retrieve the best FAQ match and return a Gemini-synthesised response.

    Parameters
    ----------
    user_query  Free-text symptom description from the pet owner.
    species     'dog' or 'cat' to restrict retrieval; None searches all entries.
    top_k       Number of FAQ candidates to retrieve.

    Returns
    -------
    dict with keys: response, match, urgency, prompt
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GEMINI_API_KEY not set. Add it to your .env file:\n"
            "  GEMINI_API_KEY=your-key-here"
        )

    if species:
        results = retrieve_for_species(user_query, species=species, top_k=top_k)
        if not results:
            results = retrieve(user_query, top_k=top_k)
    else:
        results = retrieve(user_query, top_k=top_k)

    if not results:
        return {
            "response": (
                "I could not find a relevant FAQ entry for your description. "
                "Please consult your veterinarian directly."
            ),
            "match": None,
            "urgency": "routine",
            "prompt": "",
        }

    match = results[0]
    prompt = _build_prompt(user_query, match)

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(GEMINI_MODEL)
    gemini_response = model.generate_content(prompt)

    return {
        "response": gemini_response.text,
        "match": match,
        "urgency": match["urgency"],
        "prompt": prompt,
    }


if __name__ == "__main__":
    import sys

    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "my cat has not eaten for a day"
    print(f"\nQuery: {query!r}\n{'=' * 60}")

    result = ask(query)
    match = result["match"]

    print(f"\nURGENCY: {result['urgency'].upper()}")
    if match:
        print(f"Matched FAQ (score={match['score']:.3f}): {match['question']}")
    print(f"\n--- Gemini Response ---\n{result['response']}")