"""LLM calls and output validation using the Groq API."""
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from prompts import (
    build_quiz_prompt, build_grading_prompt, build_explanation_prompt,
    build_learning_material_prompt, build_learning_material_reduction_prompt,
)

# Load .env from this project folder regardless of the terminal's working directory.
load_dotenv(Path(__file__).resolve().parent / ".env", override=False)


def _config_value(name: str, default: str = "") -> str:
    """Read configuration from environment/.env, then Streamlit secrets."""
    value = os.getenv(name, "").strip()
    if value:
        return value
    try:
        import streamlit as st
        value = str(st.secrets.get(name, default) or default).strip()
    except Exception:
        value = default
    return value


def get_client():
    api_key = _config_value("GROQ_API_KEY")
    if not api_key or api_key == "put_your_api_key_here":
        raise RuntimeError(
            "GROQ_API_KEY is missing. Add it to the .env file beside app.py "
            "or to Streamlit Cloud Secrets using the exact name GROQ_API_KEY."
        )
    return OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
        timeout=60.0,
        max_retries=2,
    )


def get_model():
    return _config_value("GROQ_MODEL", "openai/gpt-oss-120b") or "openai/gpt-oss-120b"


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


def _validate_learning_material(data: dict, allowed_references: set[str]) -> dict:
    summary = data.get("summary")
    points = data.get("key_points")
    if not isinstance(summary, str) or not summary.strip():
        raise ValueError("The AI returned an empty summary. Please try again.")
    if not isinstance(points, list):
        raise ValueError("The AI returned an invalid key-points format. Please try again.")

    validated_points = []
    for item in points:
        if not isinstance(item, dict):
            continue
        point = item.get("point")
        reference = item.get("source_reference")
        if (isinstance(point, str) and point.strip() and
                isinstance(reference, str) and reference in allowed_references):
            validated_points.append({
                "point": point.strip(),
                "source_reference": reference,
            })
    return {"summary": summary.strip(), "key_points": validated_points}


def generate_learning_material(topic: str, chunks: list[dict]) -> dict:
    """Generate a source-grounded summary and cited key points from course chunks.

    Large documents are summarized in small batches, then combined to reduce
    the risk of exceeding the model context window.
    """
    if not topic.strip():
        raise ValueError("Enter a topic or document title.")
    if not chunks:
        raise ValueError("No course material was found. Upload and process notes first.")

    references = sorted({
        f"{item.get('source_file', 'Unknown file')} — {item.get('source_location', 'Unknown location')}"
        for item in chunks
    })
    allowed_references = set(references)
    reference_text = "\n".join(f"- {reference}" for reference in references)

    batch_size = 8
    batch_results = []
    for start in range(0, len(chunks), batch_size):
        batch = chunks[start:start + batch_size]
        context_parts = []
        for item in batch:
            reference = f"{item.get('source_file', 'Unknown file')} — {item.get('source_location', 'Unknown location')}"
            context_parts.append(
                f"SOURCE: {reference}\nCHUNK_ID: {item.get('id', 'not available')}\n"
                f"TEXT:\n{item.get('text', '')}"
            )
        batch_references = sorted({
            f"{item.get('source_file', 'Unknown file')} — {item.get('source_location', 'Unknown location')}"
            for item in batch
        })
        batch_reference_text = "\n".join(f"- {reference}" for reference in batch_references)
        prompt = build_learning_material_prompt(
            topic, "\n\n---\n\n".join(context_parts), batch_reference_text
        )
        batch_data = _chat_json(prompt)
        batch_results.append(_validate_learning_material(batch_data, set(batch_references)))

    if len(batch_results) == 1:
        return batch_results[0]

    intermediate = "\n\n".join(
        f"BATCH {index}:\nSUMMARY: {item['summary']}\nKEY POINTS: " +
        "; ".join(f"{point['point']} [{point['source_reference']}]" for point in item['key_points'])
        for index, item in enumerate(batch_results, start=1)
    )
    final_prompt = build_learning_material_reduction_prompt(topic, intermediate, reference_text)
    final_data = _chat_json(final_prompt)
    return _validate_learning_material(final_data, allowed_references)
