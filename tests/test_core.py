import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from adaptive import next_difficulty, weak_topics
from document_processor import split_into_chunks
from evaluation import validate_quiz_json, source_id_grounding_rate

def test_chunking_overlap_returns_chunks():
    text = ("Computer science studies computation and algorithms. " * 200)
    chunks = split_into_chunks(text, chunk_size=100, overlap=20)
    assert len(chunks) > 1
    assert all(isinstance(c, str) and c for c in chunks)

def test_adaptive_difficulty():
    assert next_difficulty("medium", 3, 0)[0] == "hard"
    assert next_difficulty("medium", 0, 2)[0] == "easy"
    assert next_difficulty("hard", 3, 0)[0] == "hard"
    assert next_difficulty("easy", 0, 2)[0] == "easy"

def test_validate_quiz_json():
    good = json.dumps({"questions": [{
        "question": "What is 2+2?", "options": ["4", "3", "2", "5"],
        "correct_answer": "4", "explanation": "Basic arithmetic.",
        "difficulty": "easy", "source_chunk": "abc"
    }]})
    assert validate_quiz_json(good)[0]
    assert not validate_quiz_json("{bad json")[0]

def test_grounding_rate():
    questions = [{"source_chunk": "a"}, {"source_chunk": "missing"}]
    assert source_id_grounding_rate(questions, ["a"]) == 0.5

def test_weak_topics():
    result = weak_topics([
        {"topic": "Networks", "total_attempts": 5, "correct_attempts": 2, "difficulty": "easy"},
        {"topic": "OOP", "total_attempts": 5, "correct_attempts": 4, "difficulty": "medium"},
        {"topic": "New", "total_attempts": 1, "correct_attempts": 0, "difficulty": "medium"},
    ])
    assert result[0]["topic"] == "Networks"
    assert len(result) == 2
