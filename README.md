# AI Quiz Master

A university prototype that creates quizzes from course materials using retrieval-augmented generation (RAG), adapts difficulty, explains incorrect answers, stores history, and exports reports.

## Features

- Upload PDF, DOCX, and PPTX course files.
- Extract text and split it into token chunks (default 500 tokens, 80-token overlap).
- Generate local embeddings and persist them in Chroma.
- Search course chunks by meaning.
- Generate MCQ, true/false, and short-answer quizzes using the Groq API.
- Generate a summary for a selected topic using relevant retrieved course chunks.
- Generate a complete-document summary by processing all stored chunks in batches.
- Extract important key points with page/slide source references.
- Download generated study guides as PDF.
- Validate JSON structure and require a source chunk ID from retrieval.
- Explain incorrect answers with a course source reference.
- Store users, quizzes, attempts, scores, and per-topic adaptive stats in SQLite.
- Dashboard with accuracy over time, accuracy per topic, and weak areas.
- Export quiz CSV, results CSV, and a PDF results report.
- Basic tests and an evaluation checklist.

## Requirements

- Windows 10/11, macOS, or Linux
- Python 3.11 or newer (use a Python version supported by the installed ChromaDB dependencies)
- Internet access for package/model downloads and LLM API calls
- A Groq API key for quiz generation, grading, explanations, and study guides

## Setup on Windows PowerShell

1. Extract the ZIP and open the `AI_Quiz_Master_Updated` folder in VS Code.
2. Check Python:
   ```powershell
   python --version
   ```
3. Create and activate a virtual environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
   If PowerShell blocks activation, use `.venv\Scripts\python.exe` in place of `python`.
4. Install packages:
   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```
5. Copy the environment template:
   ```powershell
   Copy-Item .env.example .env
   ```
6. Open `.env` in VS Code and replace `put_your_api_key_here` with your Groq API key. Keep the key private. Do not share this file or upload it to GitHub.
7. Run:
   ```powershell
   streamlit run app.py
   ```
8. Open the local address Streamlit prints, usually `http://localhost:8501`.

## First use

1. Open **Course material** and upload a text-based PDF, DOCX, or PPTX.
2. Click **Process and store files**. The first run can take longer because the local embedding model may need to download.
3. Try semantic search to check retrieval.
4. Open **Take a quiz**, enter a topic found in your notes, select question type and difficulty, then generate.
5. Submit answers to see explanations and source references.
6. Open **Summary & Key Points** to summarize a topic or an entire uploaded document and download a PDF study guide.
7. Use the Dashboard and Export tabs.

## API key and cost

Document parsing, local Chroma storage, and semantic retrieval do not need an LLM API key. Quiz generation, LLM-based short-answer grading/explanations, and study-guide generation do. API calls may incur provider charges. Review your provider's pricing and usage limits before using it.

The app reads `GROQ_API_KEY` and optional `GROQ_MODEL` from `.env` or Streamlit secrets. It uses the Groq OpenAI-compatible API endpoint. Check your Groq Console for current model access, usage limits, and pricing before use. Creating an API key does not guarantee free API usage.

## Run tests

```powershell
pytest -q
```

## Data locations

- `data/chroma/`: local vector database
- `data/quiz_master.sqlite3`: users, quizzes, attempts, and topic statistics

These are local files and are ignored by `.gitignore`.

## Summary and key-point generation

- **Selected topic:** semantic search retrieves the most relevant course chunks, then Groq generates a summary and key points from those chunks.
- **Entire document:** all stored chunks for the selected document are processed in batches before the study guide is combined.
- Key-point citations are restricted to source references retrieved from the uploaded material. Always compare generated study notes with the original document.
- Large documents may require multiple Groq requests and can take longer or use more API quota.

## Important limitations

- Scanned PDFs and images inside slides are not OCR-processed.
- Slide notes and complex embedded objects are not extracted.
- Retrieval and source-ID validation reduce unsupported questions but cannot guarantee truth. Manually review generated questions.
- Short-answer grading and explanations can make additional API calls.
- The username selector is a demo identity feature, not secure login or multi-user access control.
- This app is intended as an educational prototype, not a production learning platform.
- If you had uploaded multiple versions of the same filename before this update, upload that document again once so the vector store can replace older chunks for that filename. Clear `data/chroma/` only while the app is stopped if you want to reset the entire vector database (this deletes stored vector data).

## Evaluation plan

Review about 50 questions manually. Record:
- Whether the question is supported by the cited source.
- Whether the correct answer is factually correct.
- Whether the question is clear and unambiguous.
- Whether the selected difficulty is appropriate.

Measure JSON validity, source-ID grounding rate, answer correctness, and whether the adaptive rule changes difficulty as intended. Source-ID grounding alone is not proof of factual grounding.

## Architecture

`app.py` → `document_processor.py` → `vector_store.py` (Chroma) → `learning_tools.py` / `llm_service.py` (Groq API) → `database.py` (SQLite) → dashboard and exports.

`prompts.py` contains quiz, grading, explanation, summary, and key-point prompt templates.


## Groq API configuration

Copy `.env.example` to `.env`, set `GROQ_API_KEY` using a key from [Groq Console](https://console.groq.com/keys), and run `python -m streamlit run app.py`. Keep `.env` private.
