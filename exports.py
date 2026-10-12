"""CSV and PDF exports for quiz results."""
import csv
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

def attempts_to_csv(attempts):
    output = io.StringIO()
    fields = ["created_at", "topic", "question", "student_answer", "correct_answer",
              "is_correct", "source_file", "source_location", "explanation"]
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for row in attempts:
        row = dict(row)
        row["is_correct"] = "Correct" if row.get("is_correct") else "Incorrect"
        writer.writerow(row)
    return output.getvalue().encode("utf-8-sig")

def quiz_to_csv(questions):
    output = io.StringIO()
    fields = ["question", "question_type", "options", "correct_answer",
              "explanation", "difficulty", "source_file", "source_location", "source_chunk"]
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for q in questions:
        row = dict(q)
        row["options"] = " | ".join(q.get("options", []))
        writer.writerow(row)
    return output.getvalue().encode("utf-8-sig")

def results_to_pdf(username, attempts, topic_stats):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=0.55*inch,
                            leftMargin=0.55*inch, topMargin=0.6*inch, bottomMargin=0.6*inch)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("AI Quiz Master — Results Report", styles["Title"]),
        Paragraph(f"Student: {username}", styles["Normal"]),
        Paragraph(f"Total answered questions: {len(attempts)}", styles["Normal"]),
        Spacer(1, 12),
    ]
    if attempts:
        correct = sum(int(a["is_correct"]) for a in attempts)
        accuracy = 100 * correct / len(attempts)
        story.append(Paragraph(f"Overall accuracy: {accuracy:.1f}%", styles["Heading2"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Accuracy by topic", styles["Heading2"]))
    table_data = [["Topic", "Attempts", "Correct", "Accuracy", "Current level"]]
    for t in topic_stats:
        total = int(t["total_attempts"])
        correct = int(t["correct_attempts"])
        table_data.append([t["topic"], str(total), str(correct),
                           f"{100*correct/total:.1f}%" if total else "—",
                           t["difficulty"]])
    if len(table_data) == 1:
        table_data.append(["No attempts yet", "0", "0", "—", "medium"])
    table = Table(table_data, repeatRows=1, colWidths=[2.2*inch, .8*inch, .7*inch, .8*inch, 1.0*inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#263238")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), .4, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(table)
    story.append(Spacer(1, 14))
    story.append(Paragraph("Recent answers", styles["Heading2"]))
    for attempt in attempts[-30:]:
        status = "Correct" if attempt["is_correct"] else "Incorrect"
        text = (
            f"<b>{status} — {attempt['topic']}</b><br/>"
            f"{attempt['question']}<br/>"
            f"Your answer: {attempt['student_answer']}<br/>"
            f"Expected answer: {attempt['correct_answer']}<br/>"
            f"Source: {attempt['source_file']} — {attempt['source_location']}"
        )
        story.append(Paragraph(text, styles["BodyText"]))
        story.append(Spacer(1, 7))
    doc.build(story)
    return buffer.getvalue()
