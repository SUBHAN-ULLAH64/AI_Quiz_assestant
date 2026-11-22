import importlib.util
import sys
import types
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# These tests mock all network calls; provide a tiny SDK placeholder when the
# optional runtime dependency has not been installed in the test environment.
if importlib.util.find_spec("openai") is None:
    openai_stub = types.ModuleType("openai")
    openai_stub.OpenAI = object
    sys.modules["openai"] = openai_stub

from prompts import build_learning_material_prompt, build_learning_material_reduction_prompt
from llm_service import _validate_learning_material


def test_learning_prompt_includes_topic_and_source_context():
    prompt = build_learning_material_prompt(
        "OSI Model", "The OSI model has seven layers.", "- Networks.pdf — Page 2"
    )
    assert "OSI Model" in prompt
    assert "seven layers" in prompt
    assert "Networks.pdf — Page 2" in prompt


def test_learning_material_validation_keeps_only_cited_key_points():
    result = _validate_learning_material(
        {
            "summary": "The OSI model has seven layers.",
            "key_points": [
                {"point": "It has seven layers.", "source_reference": "Networks.pdf — Page 2"},
                {"point": "Unsupported citation.", "source_reference": "Other.pdf — Page 9"},
            ],
        },
        {"Networks.pdf — Page 2"},
    )
    assert result["summary"].startswith("The OSI model")
    assert len(result["key_points"]) == 1
    assert result["key_points"][0]["source_reference"] == "Networks.pdf — Page 2"


def test_reduction_prompt_includes_intermediate_notes():
    prompt = build_learning_material_reduction_prompt(
        "Networks", "Batch 1: Seven layers", "- Networks.pdf — Page 2"
    )
    assert "Batch 1: Seven layers" in prompt
    assert "Networks.pdf — Page 2" in prompt


def test_generate_learning_material_batches_large_documents(monkeypatch):
    import llm_service

    calls = []
    def fake_chat_json(prompt):
        calls.append(prompt)
        if "INTERMEDIATE NOTES" in prompt:
            return {
                "summary": "Combined summary from all document sections.",
                "key_points": [
                    {"point": "A supported key point.", "source_reference": "Notes.pdf — Page 1"}
                ],
            }
        return {
            "summary": "Summary for this batch.",
            "key_points": [
                {"point": "A supported key point.", "source_reference": "Notes.pdf — Page 1"}
            ],
        }

    monkeypatch.setattr(llm_service, "_chat_json", fake_chat_json)
    chunks = [
        {"id": str(index), "text": f"Course text {index}",
         "source_file": "Notes.pdf", "source_location": "Page 1"}
        for index in range(9)
    ]
    result = llm_service.generate_learning_material("Entire document", chunks)
    assert result["summary"] == "Combined summary from all document sections."
    assert len(calls) == 3  # two source batches and one final reduction
