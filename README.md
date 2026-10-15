# AI Quiz Master

A university prototype that creates quizzes from course materials using retrieval-augmented generation (RAG), adapts difficulty, explains incorrect answers, stores history, and exports reports.

## Features

- Upload PDF, DOCX, and PPTX course files.
- Extract text and split it into token chunks (default 500 tokens, 80-token overlap).
- Generate local embeddings and persist them in Chroma.
- Search course chunks by meaning.
- Generate MCQ, true/false, and short-answer quizzes using an LLM API.
- Validate JSON structure and require a source chunk ID from retrieval.
- Explain incorrect answers with a course source reference.
- Store users, quizzes, attempts, scores, and per-topic adaptive stats in SQLite.
- Dashboard with accuracy over time, accuracy per topic, and weak areas.
- Export quiz CSV, results CSV, and a PDF results report.
- Basic tests and an evaluation checklist.

## Requirements

- Windows 10/11, macOS, or Linux
- Python 3.11 recommended
- Internet access for package/model downloads and LLM API calls
- An GROQ_API_KEY key for Grok to generate/grade quizzes

## First use

1. Open **Course material** and upload a text-based PDF, DOCX, or PPTX.
2. Click **Process and store files**. The first run can take longer because the local embedding model may need to download.
3. Try semantic search to check retrieval.
4. Open **Take a quiz**, enter a topic found in your notes, select question type and difficulty, then generate.
5. Submit answers to see explanations and source references.
6. Use the Dashboard and Export tabs.

## API key and cost

Document parsing, local Chroma storage, and semantic retrieval do not need an LLM API key. Quiz generation and LLM-based short-answer grading/explanations do. API calls may incur provider charges. Review your provider's pricing and usage limits before using it.

`GROQ_API_KEY` defaults to `GROQ_API_KEY`, and the app uses the official GROQ_API_KEY endpoint `GROQ_API_KEY`. Check your xAI console for model access and current pricing/credits before use. Creating an API key does not guarantee free API usage.

## Run tests

```powershell
pytest -q
```

## Data locations

- `data/chroma/`: local vector database
- `data/quiz_master.sqlite3`: users, quizzes, attempts, and topic statistics

These are local files and are ignored by `.gitignore`.

## Important limitations

- Scanned PDFs and images inside slides are not OCR-processed.
- Slide notes and complex embedded objects are not extracted.
- Retrieval and source-ID validation reduce unsupported questions but cannot guarantee truth. Manually review generated questions.
- Short-answer grading and explanations can make additional API calls.
- The username selector is a demo identity feature, not secure login or multi-user access control.
- This app is intended as an educational prototype, not a production learning platform.
- If a document is re-uploaded with changed content, old chunks are not automatically removed. Clear `data/chroma/` only while the app is stopped if you want to reset the vector database (this deletes stored vector data).

## Evaluation plan

Review about 50 questions manually. Record:
- Whether the question is supported by the cited source.
- Whether the correct answer is factually correct.
- Whether the question is clear and unambiguous.
- Whether the selected difficulty is appropriate.

Measure JSON validity, source-ID grounding rate, answer correctness, and whether the adaptive rule changes difficulty as intended. Source-ID grounding alone is not proof of factual grounding.

## Architecture

`app.py` → `document_processor.py` → `vector_store.py` (Chroma) → `llm_service.py` (LLM API) → `database.py` (SQLite) → dashboard and exports.

`prompts.py` contains the generation, grading, and explanation templates.


## Groq API configuration

Copy `.env.example` to `.env`, set `GROQ_API_KEY` using a key from [Groq Console](https://console.groq.com/keys), and run `python -m streamlit run app.py`. Keep `.env` private.
