"""Study-material workflows built on the existing ChromaDB and Groq services."""
from llm_service import generate_learning_material
from vector_store import get_all_chunks, list_source_files, search_chunks


def create_learning_material(
    mode: str,
    topic: str = "",
    source_file: str | None = None,
    top_k: int = 12,
) -> dict:
    """Retrieve course content and generate a summary plus cited key points.

    mode='topic' searches relevant chunks across uploaded course files.
    mode='document' retrieves all stored chunks for the selected source file.
    """
    if mode == "topic":
        cleaned_topic = topic.strip()
        if not cleaned_topic:
            raise ValueError("Enter the topic you want to study.")
        chunks = search_chunks(cleaned_topic, top_k=top_k)
        title = cleaned_topic
    elif mode == "document":
        if not source_file:
            raise ValueError("Select a course document first.")
        chunks = get_all_chunks(source_file=source_file)
        title = source_file
    else:
        raise ValueError("Choose either topic summary or complete-document summary.")

    if not chunks:
        raise ValueError(
            "No matching course content was found. Check the topic or process the document again."
        )

    result = generate_learning_material(title, chunks)
    result["title"] = title
    result["mode"] = mode
    result["source_files"] = sorted({item["source_file"] for item in chunks})
    result["source_references"] = sorted({
        f"{item['source_file']} — {item['source_location']}" for item in chunks
    })
    result["chunks_used"] = len(chunks)
    return result


def available_course_files() -> list[str]:
    """List the document names currently stored in ChromaDB."""
    return list_source_files()
