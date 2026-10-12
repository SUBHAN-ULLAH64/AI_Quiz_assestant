"""Basic automated checks and a manual-review export for project evaluation."""
import json

def validate_quiz_json(raw_text: str):
    """Return (is_valid, message) for JSON syntax and basic quiz structure."""
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        return False, f"Invalid JSON: {exc}"
    if not isinstance(data, dict) or not isinstance(data.get("questions"), list):
        return False, "JSON must be an object with a questions array."
    required = {"question", "options", "correct_answer", "explanation", "difficulty", "source_chunk"}
    for i, question in enumerate(data["questions"], start=1):
        if not isinstance(question, dict) or not required.issubset(question):
            return False, f"Question {i} is missing required fields."
        if question["difficulty"] not in {"easy", "medium", "hard"}:
            return False, f"Question {i} has an invalid difficulty."
    return True, "JSON structure is valid."

def source_id_grounding_rate(questions, retrieved_chunk_ids):
    """Simple structural grounding check, not proof of factual correctness."""
    if not questions:
        return 0.0
    allowed = set(retrieved_chunk_ids)
    grounded = sum(1 for q in questions if q.get("source_chunk") in allowed)
    return grounded / len(questions)

def manual_review_template(questions):
    """Rows for a human reviewer to assess factual support and answer quality."""
    rows = []
    for q in questions:
        rows.append({
            "question": q.get("question", ""),
            "options": " | ".join(q.get("options", [])),
            "proposed_answer": q.get("correct_answer", ""),
            "explanation": q.get("explanation", ""),
            "source_chunk": q.get("source_chunk", ""),
            "grounded_in_source_yes_no": "",
            "answer_correct_yes_no": "",
            "clear_unambiguous_yes_no": "",
            "reviewer_notes": "",
        })
    return rows
