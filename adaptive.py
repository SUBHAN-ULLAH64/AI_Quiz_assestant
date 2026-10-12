"""Small, transparent adaptive-difficulty helpers."""
def next_difficulty(current: str, correct_streak: int, wrong_streak: int):
    levels = ["easy", "medium", "hard"]
    if current not in levels:
        current = "medium"
    index = levels.index(current)
    if correct_streak >= 3:
        index = min(index + 1, len(levels) - 1)
        correct_streak = 0
    if wrong_streak >= 2:
        index = max(index - 1, 0)
        wrong_streak = 0
    return levels[index], correct_streak, wrong_streak

def weak_topics(topic_rows: list[dict], min_attempts: int = 3):
    """Return topics with enough attempts and the lowest accuracy first."""
    results = []
    for row in topic_rows:
        total = int(row.get("total_attempts", 0))
        correct = int(row.get("correct_attempts", 0))
        if total >= min_attempts:
            results.append({
                "topic": row["topic"],
                "attempts": total,
                "accuracy": correct / total,
                "difficulty": row.get("difficulty", "medium"),
            })
    return sorted(results, key=lambda item: item["accuracy"])
