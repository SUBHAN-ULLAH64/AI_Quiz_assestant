"""AI Quiz Master — complete Streamlit application."""
import json
import pandas as pd
import streamlit as st

from document_processor import process_document
from vector_store import store_chunks, search_chunks, get_database_stats, list_source_files
from database import (
    init_db, get_or_create_user, get_usernames, get_topic_stats,
    save_quiz, save_attempt, get_dashboard_data
)
from llm_service import generate_quiz, grade_short_answer, explain_wrong_answer
from adaptive import weak_topics
from exports import attempts_to_csv, quiz_to_csv, results_to_pdf

st.set_page_config(page_title="AI Quiz Master", page_icon="📚", layout="wide", initial_sidebar_state="expanded")
st.markdown("""<style>
.stApp{background:radial-gradient(ellipse at top left,#172554 0%,#0b1220 40%,#080d18 100%);color:#eef2ff}
[data-testid="stHeader"]{background:rgba(8,13,24,.88)}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#111c31,#0b1220);border-right:1px solid #263550}
.block-container{max-width:1440px;padding-top:1.5rem;padding-bottom:3rem}
h1,h2,h3{color:#f8fafc!important;letter-spacing:-.02em} p,label,.stMarkdown,[data-testid="stCaptionContainer"]{color:#d5deef}
/* Premium dashboard metric cards */
div[data-testid="stMetric"]{background:linear-gradient(145deg,rgba(30,48,76,.98),rgba(15,26,45,.98));border:1px solid #3a5276;border-radius:18px;padding:20px 22px;box-shadow:0 10px 26px rgba(0,0,0,.22);transition:transform .18s ease,border-color .18s ease;min-height:132px}
div[data-testid="stMetric"]:hover{transform:translateY(-2px);border-color:#7897c7}
div[data-testid="stMetricLabel"]{color:#b9c9e2;font-size:.94rem;font-weight:650} div[data-testid="stMetricValue"]{color:#f8fafc;font-size:2.25rem;font-weight:800;letter-spacing:-.035em}
div[data-testid="stMetricDelta"]{font-size:.82rem}
[data-testid="stVerticalBlock"] h2,[data-testid="stVerticalBlock"] h3{font-weight:800;letter-spacing:-.025em}
[data-testid="stPlotlyChart"], [data-testid="stArrowVegaLiteChart"], [data-testid="stVegaLiteChart"]{background:linear-gradient(145deg,rgba(17,29,49,.72),rgba(10,18,31,.72));border:1px solid #2b3f5e;border-radius:16px;padding:12px}
.stDataFrame{border:1px solid #304563;border-radius:14px;overflow:hidden}
.stProgress>div>div{background:linear-gradient(90deg,#3b82f6,#8b5cf6)}
.stTabs [data-baseweb="tab-list"]{gap:8px;padding:8px;background:#101a2d;border:1px solid #283954;border-radius:15px}
.stTabs [data-baseweb="tab"]{min-height:46px;padding:10px 16px;border-radius:10px;color:#c7d2e5;font-weight:650}
.stTabs [aria-selected="true"]{background:#273b60!important;color:#fff!important}
.stButton>button,.stDownloadButton>button,[data-testid="stFormSubmitButton"] button{border-radius:11px;min-height:44px;font-weight:650;border:1px solid #4c6fa8}
.stButton>button[kind="primary"],[data-testid="stFormSubmitButton"] button[kind="primary"]{background:linear-gradient(90deg,#2563eb,#7c3aed);color:#fff;border:0}
input,textarea,[data-baseweb="select"]>div{background-color:#111c30!important;color:#f8fafc!important;border-color:#344765!important;border-radius:10px!important}
[data-testid="stFileUploader"]{background:#101a2d;border:1px dashed #52698d;border-radius:14px;padding:12px}
[data-testid="stExpander"]{background:#101a2d;border:1px solid #2b3c58;border-radius:12px;overflow:hidden}
[data-testid="stAlert"]{border-radius:12px} hr{border-color:#2b3c58}
/* Professional student sidebar */
[data-testid="stSidebar"] h2{color:#f8fafc!important;font-size:1.35rem;font-weight:800}
.student-profile-card{background:linear-gradient(135deg,#1e3a5f,#25234b);border:1px solid #45628d;border-radius:16px;padding:18px 16px;margin:8px 0 16px;box-shadow:0 8px 22px #0003}
.student-profile-card .profile-label{color:#93c5fd;font-size:.75rem;font-weight:800;letter-spacing:1.5px;text-transform:uppercase}
.student-profile-card .profile-name{color:#fff;font-size:1.15rem;font-weight:750;margin-top:8px;overflow-wrap:anywhere}
.student-profile-card .profile-status{color:#bbf7d0;font-size:.82rem;margin-top:7px}
[data-testid="stSidebar"] .stButton>button{width:100%;border-radius:10px;min-height:46px;font-weight:750;transition:all .2s ease}
[data-testid="stSidebar"] .stButton>button:hover{border-color:#93c5fd;transform:translateY(-1px)}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"]{color:#9aabc5;font-size:.78rem;line-height:1.5}
.section-banner{background:linear-gradient(115deg,#1b3558 0%,#202747 55%,#302353 100%);border:1px solid #405a82;border-radius:18px;padding:21px 24px;margin:4px 0 22px;box-shadow:0 12px 28px rgba(0,0,0,.22);position:relative;overflow:hidden}.section-banner:before{content:"";display:block;position:absolute;left:0;top:0;bottom:0;width:4px;background:linear-gradient(180deg,#60a5fa,#a78bfa)}
.section-banner .eyebrow{color:#9bc9ff;font-size:.76rem;font-weight:850;letter-spacing:.15em;text-transform:uppercase;margin-bottom:7px}
.section-banner .heading{color:#fff;font-size:1.55rem;line-height:1.3;font-weight:850;letter-spacing:-.025em;margin-top:2px}.section-banner .subheading{color:#d2dced;font-size:1rem;line-height:1.55;margin-top:8px;max-width:900px}
.hero{background:linear-gradient(120deg,#172554,#1e293b 50%,#312e81);border:1px solid #405580;border-radius:20px;padding:24px 26px;margin-bottom:20px;box-shadow:0 14px 32px #0004}
.hero-title-row{display:flex;align-items:center;justify-content:space-between;gap:18px;flex-wrap:wrap}.hero h1{margin:0;font-size:2.15rem;line-height:1.25}.hero-badge{display:inline-flex;align-items:center;gap:8px;background:linear-gradient(110deg,#2449a8,#49318c);border:1px solid #617ed2;border-radius:12px;padding:10px 16px;color:#eaf2ff;font-size:.78rem;font-weight:800;letter-spacing:.12em;white-space:normal}.hero p{margin:16px 0 0;color:#dbeafe}
@media(max-width:800px){.block-container{padding-left:1rem;padding-right:1rem}.hero h1{font-size:1.65rem}.hero-badge{font-size:.68rem;padding:8px 11px}.hero-title-row{align-items:flex-start}.stTabs [data-baseweb="tab"]{padding:8px}div[data-testid="stMetric"]{padding:16px;min-height:110px}div[data-testid="stMetricValue"]{font-size:1.8rem}.section-banner{padding:18px 19px}.section-banner .heading{font-size:1.35rem}.section-banner .subheading{font-size:.92rem}}
</style><div class="hero"><div class="hero-title-row"><h1>📚 AI Quiz Master</h1><div class="hero-badge">✨ YOUR PERSONAL STUDY ASSISTANT</div></div><p>Turn your course notes into focused quizzes, understand mistakes, and track your learning progress.</p></div>""",unsafe_allow_html=True)
def section_heading(number,title,subtitle):
    st.markdown(f'<div class="section-banner"><div class="eyebrow">STEP {number}</div><div class="heading">{title}</div><div class="subheading">{subtitle}</div></div>',unsafe_allow_html=True)
init_db()

with st.sidebar:
    st.markdown("## 🎓 Student Portal")
    st.caption("Manage your student profile")
    st.divider()

    known_users = get_usernames()
    current_username = (
        st.session_state["user"]["username"]
        if "user" in st.session_state
        else known_users[0] if known_users else "student1"
    )
    username = st.text_input(
        "Student username",
        value=current_username,
        placeholder="Enter your username",
        help="Enter a username to select or create a student profile."
    )

    if st.button("✨  Use / Create Student", type="primary", use_container_width=True):
        try:
            if not username.strip():
                st.error("Please enter a username.")
            else:
                user = get_or_create_user(username.strip())
                st.session_state["user"] = user
                st.success(f"Profile ready, {user['username']}!")
        except Exception as exc:
            st.error(str(exc))

    if "user" not in st.session_state:
        try:
            st.session_state["user"] = get_or_create_user(
                username.strip() or "student1"
            )
        except Exception:
            st.session_state["user"] = get_or_create_user("student1")

    user = st.session_state["user"]
    # Escape user-controlled text before inserting it into HTML.
    from html import escape
    safe_username = escape(str(user["username"]))
    st.markdown(
        f"""
        <div class="student-profile-card">
            <div class="profile-label">ACTIVE STUDENT</div>
            <div class="profile-name">👤 {safe_username}</div>
            <div class="profile-status">● Profile selected</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.caption(
        "Demo mode: this username-based profile is not secure authentication."
    )
    st.divider()
    st.markdown("### 🚀 Learning Workflow")
    st.markdown(
        """
        **01** · Upload course notes

        **02** · Retrieve relevant content

        **03** · Generate and take quizzes

        **04** · Review mistakes

        **05** · Track your progress
        """
    )

user = st.session_state["user"]
tab_upload, tab_quiz, tab_dashboard, tab_export, tab_eval = st.tabs(
    ["📄 Course material", "🧠 Take a quiz", "📊 Dashboard", "⬇️ Export", "🧪 Evaluation"]
)

with tab_upload:
    section_heading("01", "Course material", "Upload notes and build the searchable knowledge base for your quizzes.")
    st.write("Supported: PDF, DOCX and PPTX. Text-based documents work best.")
    uploads = st.file_uploader(
        "Choose course files", type=["pdf", "docx", "pptx"],
        accept_multiple_files=True, key="course_uploads"
    )
    c1, c2 = st.columns(2)
    with c1:
        chunk_size = st.number_input("Chunk size (tokens)", 100, 1000, 500, 50)
    with c2:
        overlap = st.number_input("Overlap (tokens)", 0, 400, 80, 10)
    if st.button("Process and store files", type="primary", disabled=not uploads):
        progress = st.progress(0.0)
        total = 0
        ok = 0
        for i, upload in enumerate(uploads):
            try:
                chunks = process_document(upload.name, upload.getvalue(), int(chunk_size), int(overlap))
                stored = store_chunks(chunks)
                total += stored
                ok += 1
                st.success(f"{upload.name}: processed {len(chunks)} chunks; stored/updated {stored}.")
            except Exception as exc:
                st.error(f"{upload.name}: {exc}")
            progress.progress((i + 1) / len(uploads))
        st.info(f"Completed {ok}/{len(uploads)} file(s). {total} chunk record(s) processed.")
    try:
        stats = get_database_stats()
        a, b = st.columns(2)
        a.metric("Chunks in Chroma", stats["total_chunks"])
        b.metric("Source files", len(list_source_files()))
        st.caption(f"Local vector database: {stats['database_path']}")
    except Exception as exc:
        st.error(f"Could not read vector database: {exc}")

    st.subheader("Test semantic search")
    search_query = st.text_input("Ask about your uploaded notes", placeholder="What is a class in OOP?")
    search_k = st.slider("Results to retrieve", 1, 10, 4, key="search_k")
    if st.button("Search notes"):
        if not search_query.strip():
            st.warning("Enter a search question.")
        else:
            try:
                results = search_chunks(search_query, search_k)
                if not results:
                    st.warning("No chunks found. Upload course material first.")
                for n, result in enumerate(results, 1):
                    with st.expander(f"{n}. {result['source_file']} — {result['source_location']}"):
                        st.write(result["text"])
                        st.caption(f"Chunk ID: {result['id']} | Cosine distance: {result['distance']:.4f}")
            except Exception as exc:
                st.error(f"Search failed: {exc}")

with tab_quiz:
    section_heading("02", "Quiz studio", "Choose your topic and settings, then answer questions based on your uploaded material.")
    if get_database_stats()["total_chunks"] == 0:
        st.warning("Upload and process course material first.")
    else:
        topics = st.text_input("Topic", placeholder="e.g., Object-oriented programming")
        qcol1, qcol2, qcol3 = st.columns(3)
        with qcol1:
            qtype_label = st.selectbox("Question type", ["MCQ", "True / False", "Short answer"])
            qtype = {"MCQ": "mcq", "True / False": "true_false", "Short answer": "short_answer"}[qtype_label]
        with qcol2:
            stats_for_topic = get_topic_stats(user["id"], topics.strip()) if topics.strip() else {"difficulty": "medium"}
            preferred_difficulty = stats_for_topic["difficulty"]
            difficulty = st.selectbox(
                "Difficulty", ["easy", "medium", "hard"],
                index=["easy", "medium", "hard"].index(preferred_difficulty),
                help="Starts at medium. Three correct in a row raises difficulty; two wrong in a row lowers it."
            )
        with qcol3:
            count = st.selectbox("Number of questions", [3, 5, 10], index=1)
        if topics.strip():
            topic_stats = get_topic_stats(user["id"], topics.strip())
            if topic_stats["total_attempts"]:
                accuracy = topic_stats["correct_attempts"] / topic_stats["total_attempts"] * 100
                st.caption(f"Your accuracy for this topic: {accuracy:.1f}% | Current adaptive level: {topic_stats['difficulty']}")
        if st.button("Generate quiz", type="primary"):
            if not topics.strip():
                st.warning("Enter a topic.")
            else:
                try:
                    with st.spinner("Retrieving course context and asking the LLM..."):
                        retrieved = search_chunks(topics.strip(), top_k=8)
                        if not retrieved:
                            raise ValueError("No relevant course chunks found. Upload material first.")
                        questions = generate_quiz(
                            topics.strip(), difficulty, qtype, int(count), retrieved
                        )
                        # Save source details inside each question for explanation/export.
                        by_id = {item["id"]: item for item in retrieved}
                        for question in questions:
                            source = by_id[question["source_chunk"]]
                            question["source_file"] = source["source_file"]
                            question["source_location"] = source["source_location"]
                            question["source_text"] = source["text"]
                        quiz_id = save_quiz(user["id"], topics.strip(), difficulty, qtype, questions)
                        st.session_state["active_quiz"] = {
                            "id": quiz_id, "topic": topics.strip(), "difficulty": difficulty,
                            "question_type": qtype, "questions": questions,
                        }
                        st.session_state.pop("last_result", None)
                    st.success(f"Created {len(questions)} question(s).")
                except Exception as exc:
                    st.error(f"Quiz generation failed: {exc}")
                    st.info("Check your .env API key, internet connection, uploaded material, and model access.")

        quiz = st.session_state.get("active_quiz")
        if quiz:
            st.divider()
            st.subheader(f"Quiz: {quiz['topic']} ({quiz['difficulty']})")
            with st.form(f"quiz_form_{quiz['id']}"):
                answers = []
                for i, question in enumerate(quiz["questions"]):
                    st.markdown(f"**Q{i+1}. {question['question']}**")
                    if question["question_type"] in ("mcq", "true_false"):
                        answer = st.radio(
                            "Choose an answer",
                            options=question["options"],
                            key=f"answer_{quiz['id']}_{i}",
                            index=None,
                        )
                    else:
                        answer = st.text_input(
                            "Your answer",
                            key=f"answer_{quiz['id']}_{i}",
                        )
                    answers.append(answer or "")
                submitted = st.form_submit_button("Submit answers", type="primary")
            if submitted:
                outcomes = []
                with st.spinner("Checking answers and preparing feedback..."):
                    for question, answer in zip(quiz["questions"], answers):
                        try:
                            if question["question_type"] == "short_answer":
                                grading = grade_short_answer(
                                    question["question"], question["correct_answer"],
                                    answer, question["source_text"]
                                )
                                is_correct = grading["is_correct"]
                                grading_feedback = grading["feedback"]
                            else:
                                is_correct = answer.strip().casefold() == question["correct_answer"].strip().casefold()
                                grading_feedback = ""
                        except Exception as exc:
                            st.error(f"Could not grade one answer: {exc}")
                            is_correct = False
                            grading_feedback = "Automatic grading failed; please review manually."

                        reference = f"{question['source_file']} — {question['source_location']}"
                        explanation = question["explanation"]
                        if not is_correct:
                            try:
                                explanation = explain_wrong_answer(
                                    question["question"], question["correct_answer"],
                                    answer, question["source_text"], reference
                                )
                            except Exception:
                                explanation = (
                                    f"Expected answer: {question['correct_answer']}. "
                                    f"Review {reference}. Source excerpt: {question['source_text'][:1200]}"
                                )
                        elif grading_feedback:
                            explanation = grading_feedback + "\n\n" + explanation

                        save_attempt(
                            user["id"], quiz["id"], quiz["topic"], question["question"],
                            question["question_type"], answer, question["correct_answer"],
                            is_correct, explanation, question["source_file"], question["source_location"]
                        )
                        outcomes.append({
                            "question": question["question"], "answer": answer,
                            "correct_answer": question["correct_answer"], "is_correct": is_correct,
                            "explanation": explanation, "source_file": question["source_file"],
                            "source_location": question["source_location"],
                        })
                score = sum(x["is_correct"] for x in outcomes)
                st.session_state["last_result"] = {
                    "topic": quiz["topic"], "score": score, "total": len(outcomes),
                    "outcomes": outcomes,
                }
                st.rerun()

        result = st.session_state.get("last_result")
        if result:
            st.subheader("Your result")
            st.metric("Score", f"{result['score']} / {result['total']}",
                      f"{100*result['score']/result['total']:.1f}% accuracy" if result["total"] else None)
            for i, outcome in enumerate(result["outcomes"], 1):
                label = "✅ Correct" if outcome["is_correct"] else "❌ Incorrect"
                with st.expander(f"Q{i}: {label}"):
                    st.write(outcome["question"])
                    st.write(f"Your answer: {outcome['answer'] or '(blank)'}")
                    st.write(f"Correct answer: {outcome['correct_answer']}")
                    st.write(outcome["explanation"])
                    st.caption(f"Reference: {outcome['source_file']} — {outcome['source_location']}")

with tab_dashboard:
    section_heading("03", "Learning dashboard", "Review your accuracy, practice history, and topics that need more attention.")
    attempts, topic_rows, quizzes = get_dashboard_data(user["id"])
    if not attempts:
        st.info("Take a quiz to start building your dashboard.")
    else:
        df = pd.DataFrame(attempts)
        df["is_correct"] = df["is_correct"].astype(int)
        df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
        overall = df["is_correct"].mean() * 100
        m1, m2, m3 = st.columns(3)
        m1.metric("Questions answered", len(df))
        m2.metric("Overall accuracy", f"{overall:.1f}%")
        m3.metric("Topics practiced", df["topic"].nunique())
        st.subheader("Accuracy over time")
        daily = df.dropna(subset=["created_at"]).set_index("created_at")["is_correct"].resample("D").mean().mul(100).dropna()
        if not daily.empty:
            st.line_chart(daily)
        st.subheader("Accuracy per topic")
        topic_data = []
        for row in topic_rows:
            total = row["total_attempts"]
            topic_data.append({"Topic": row["topic"], "Accuracy (%)": round(100*row["correct_attempts"]/total, 1) if total else 0,
                               "Attempts": total, "Adaptive level": row["difficulty"]})
        topic_df = pd.DataFrame(topic_data)
        if not topic_df.empty:
            st.bar_chart(topic_df.set_index("Topic")["Accuracy (%)"])
            st.dataframe(topic_df, use_container_width=True, hide_index=True)
        st.subheader("Weak areas to revisit")
        weak = weak_topics(topic_rows, min_attempts=3)
        if weak:
            for item in weak:
                st.write(f"- **{item['topic']}** — {item['accuracy']*100:.1f}% accuracy across {item['attempts']} attempts")
        else:
            st.write("Complete at least 3 attempts in a topic to identify weak areas.")
        st.subheader("Recent quizzes")
        if quizzes:
            st.dataframe(pd.DataFrame(quizzes), use_container_width=True, hide_index=True)

with tab_export:
    section_heading("04", "Export center", "Download quiz questions and progress reports for study or submission.")
    attempts, topic_rows, quizzes = get_dashboard_data(user["id"])
    active_quiz = st.session_state.get("active_quiz")
    if active_quiz:
        st.download_button(
            "Download current quiz (CSV)",
            data=quiz_to_csv(active_quiz["questions"]),
            file_name=f"quiz_{active_quiz['topic'].replace(' ', '_')}.csv",
            mime="text/csv",
        )
    else:
        st.info("Generate a quiz first to export its questions.")
    st.download_button(
        "Download results history (CSV)",
        data=attempts_to_csv(attempts),
        file_name="quiz_results.csv",
        mime="text/csv",
        disabled=not attempts,
    )
    st.download_button(
        "Download results report (PDF)",
        data=results_to_pdf(user["username"], attempts, topic_rows),
        file_name="quiz_results_report.pdf",
        mime="application/pdf",
    )

with tab_eval:
    section_heading("05", "Evaluation & quality", "Explore validation checks and the project evaluation approach.")
    st.markdown("""
    Use this page to understand the project's quality checks. These checks support
    evaluation but **do not prove** that a question is factually correct.
    """)
    st.subheader("Automated checks")
    st.write("- JSON parsing and required fields are checked in `llm_service.py`.")
    st.write("- Each question must cite a chunk ID returned by retrieval.")
    st.write("- MCQ answer must match one of its four options.")
    st.write("- True/false answers must be True or False.")
    st.write("- Short answers are checked by the LLM against the source.")
    st.subheader("Manual review plan")
    st.write("Review approximately 50 generated questions. For each, check source support, answer correctness, clarity, and difficulty.")
    st.write("Keep a record of reviewer decisions and calculate the percentage that pass each check.")
    st.subheader("Adaptive difficulty")
    st.write("The level begins at medium per topic. Three consecutive correct answers increase it one level; two consecutive incorrect answers decrease it one level.")
    st.warning("This is a university prototype. LLM grading can be wrong, API use may cost money, and username selection is not secure authentication.")
