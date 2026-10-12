"""LLM calls and output validation using the Groq API."""
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from prompts import build_quiz_prompt, build_grading_prompt, build_explanation_prompt

# Load .env from this project folder regardless of the terminal's working directory.
load_dotenv(Path(__file__).resolve().parent / ".env", override=False)


def get_client():
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key or api_key == "put_your_api_key_here":
        raise RuntimeError(
            "GROQ_API_KEY is missing. Open the .env file beside app.py and add your Groq API key. "
            "Use the variable name GROQ_API_KEY exactly."
        )
    return OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
        timeout=60.0,
        max_retries=2,
    )


def get_model():
    return os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip() or "llama-3.3-70b-versatile"


def _chat_json(prompt: str) -> dict:
    client = get_client()
    response = client.chat.completions.create(
        model=get_model(),
        messages=[
            {"role": "system", "content": "Return valid JSON only. Follow the requested schema."},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    content = response.choices[0].message.content or "{}"
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError("The model did not return valid JSON. Please try again.") from exc
    if not isinstance(data, dict):
        raise ValueError("The model returned an unexpected response format.")
    return data


def generate_quiz(topic, difficulty, question_type, question_count, retrieved_chunks):
    context = "\n\n".join(
        f"CHUNK_ID: {c['id']}\nSOURCE: {c['source_file']} — {c['source_location']}\nTEXT:\n{c['text']}"
        for c in retrieved_chunks
    )
    prompt = build_quiz_prompt(topic, difficulty, question_type, question_count, context)
    data = _chat_json(prompt)
    if not isinstance(data, dict) or not isinstance(data.get("questions"), list):
        raise ValueError("Invalid response: expected a JSON object with a questions array.")

    allowed_ids = {c["id"] for c in retrieved_chunks}
    validated = []
    for q in data["questions"]:
        required = {"question", "options", "correct_answer", "explanation", "difficulty", "source_chunk"}
        if not isinstance(q, dict) or not required.issubset(q):
            continue
        if q["source_chunk"] not in allowed_ids:
            continue
        if q["difficulty"] not in {"easy", "medium", "hard"}:
            continue
        if not isinstance(q["question"], str) or not q["question"].strip():
            continue
        if not isinstance(q["options"], list) or not isinstance(q["correct_answer"], str):
            continue
        if question_type == "mcq":
            if len(q["options"]) != 4 or q["correct_answer"] not in q["options"]:
                continue
        elif question_type == "true_false":
            if q["options"] != ["True", "False"] or q["correct_answer"] not in q["options"]:
                continue
        elif question_type == "short_answer":
            if q["options"] != []:
                continue
        else:
            continue
        q["question_type"] = question_type
        validated.append(q)

    if not validated:
        message = data.get("message") or "No valid questions were returned. Try a broader topic or upload relevant notes."
        raise ValueError(message)
    return validated


def grade_short_answer(question, correct_answer, student_answer, source_chunk):
    prompt = build_grading_prompt(question, correct_answer, student_answer, source_chunk)
    data = _chat_json(prompt)
    return {
        "is_correct": bool(data.get("is_correct", False)),
        "feedback": str(data.get("feedback", "Answer reviewed."))[:1000],
    }


def explain_wrong_answer(question, correct_answer, student_answer, source_chunk, source_reference):
    prompt = build_explanation_prompt(
        question, correct_answer, student_answer, source_chunk, source_reference
    )
    response = get_client().chat.completions.create(
        model=get_model(),
        messages=[
            {"role": "system", "content": "Be accurate, simple, and grounded in the provided source."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content or "Please review the cited course material."
