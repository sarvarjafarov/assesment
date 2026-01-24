"""
Services for Custom Assessments.
Handles CSV parsing, AI question generation, and session management.
"""
from __future__ import annotations

import csv
import io
import json
import random
from typing import TYPE_CHECKING

from django.conf import settings

from .constants import LEVEL_DIFFICULTY_RANGES

if TYPE_CHECKING:
    from .models import CustomAssessment, CustomAssessmentSession


class CSVValidationError(Exception):
    """Raised when CSV validation fails."""

    def __init__(self, errors: list[dict]):
        self.errors = errors
        super().__init__(f"{len(errors)} validation error(s)")


def parse_csv_questions(file_content: str | bytes) -> list[dict]:
    """
    Parse CSV file content and return list of question dictionaries.

    Expected columns:
    - question_text (required)
    - option_a (required)
    - option_b (required)
    - option_c (optional)
    - option_d (optional)
    - correct_answer (required) - A, B, C, or D
    - explanation (optional)
    - difficulty (optional) - 1-5, default 3
    - category (optional)

    Returns:
        list of question dicts ready for model creation

    Raises:
        CSVValidationError: If validation fails
    """
    if isinstance(file_content, bytes):
        file_content = file_content.decode("utf-8-sig")  # Handle BOM

    reader = csv.DictReader(io.StringIO(file_content))

    # Normalize header names (lowercase, strip whitespace)
    if reader.fieldnames:
        reader.fieldnames = [f.lower().strip() for f in reader.fieldnames]

    questions = []
    errors = []

    for row_num, row in enumerate(reader, start=2):  # Start at 2 to account for header
        row_errors = []

        # Required fields
        question_text = row.get("question_text", "").strip()
        if not question_text:
            row_errors.append("Missing question_text")

        option_a = row.get("option_a", "").strip()
        option_b = row.get("option_b", "").strip()
        if not option_a:
            row_errors.append("Missing option_a")
        if not option_b:
            row_errors.append("Missing option_b")

        correct_answer = row.get("correct_answer", "").strip().upper()
        if not correct_answer:
            row_errors.append("Missing correct_answer")
        elif correct_answer not in ("A", "B", "C", "D"):
            row_errors.append(f"Invalid correct_answer: {correct_answer} (must be A, B, C, or D)")

        # Optional fields
        option_c = row.get("option_c", "").strip()
        option_d = row.get("option_d", "").strip()

        # Validate correct answer matches available options
        if correct_answer == "C" and not option_c:
            row_errors.append("correct_answer is C but option_c is empty")
        if correct_answer == "D" and not option_d:
            row_errors.append("correct_answer is D but option_d is empty")

        explanation = row.get("explanation", "").strip()
        category = row.get("category", "").strip()

        # Parse difficulty
        difficulty_str = row.get("difficulty", "3").strip()
        try:
            difficulty = int(difficulty_str) if difficulty_str else 3
            if difficulty < 1 or difficulty > 5:
                row_errors.append(f"Invalid difficulty: {difficulty} (must be 1-5)")
                difficulty = 3
        except ValueError:
            row_errors.append(f"Invalid difficulty: {difficulty_str} (must be a number 1-5)")
            difficulty = 3

        if row_errors:
            errors.append({
                "row": row_num,
                "errors": row_errors,
                "data": dict(row),
            })
        else:
            questions.append({
                "question_text": question_text,
                "option_a": option_a,
                "option_b": option_b,
                "option_c": option_c,
                "option_d": option_d,
                "correct_answer": correct_answer,
                "explanation": explanation,
                "difficulty_level": difficulty,
                "category": category,
            })

    if errors:
        raise CSVValidationError(errors)

    return questions


def generate_csv_template() -> str:
    """Generate a CSV template with example questions."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "question_text",
        "option_a",
        "option_b",
        "option_c",
        "option_d",
        "correct_answer",
        "explanation",
        "difficulty",
        "category",
    ])

    # Example rows
    writer.writerow([
        "What is the primary purpose of A/B testing?",
        "Increase website traffic",
        "Compare two versions to determine which performs better",
        "Reduce server costs",
        "Improve SEO rankings",
        "B",
        "A/B testing compares two variants to measure performance differences.",
        "3",
        "Analytics",
    ])
    writer.writerow([
        "Which metric best indicates email campaign engagement?",
        "Send rate",
        "Open rate",
        "Unsubscribe rate",
        "Bounce rate",
        "B",
        "Open rate shows how many recipients engaged with the email.",
        "2",
        "Email Marketing",
    ])

    return output.getvalue()


def generate_questions_with_ai(
    role_description: str,
    skills: str,
    difficulty_level: str,
    num_questions: int = 10,
) -> list[dict]:
    """
    Generate assessment questions using Claude API.

    Args:
        role_description: Target role (e.g., "Senior Salesforce Admin")
        skills: Comma-separated skills to test
        difficulty_level: 'junior', 'mid', or 'senior'
        num_questions: Number of questions to generate

    Returns:
        list of question dictionaries

    Raises:
        ValueError: If API key not configured
        Exception: If API call fails
    """
    api_key = getattr(settings, "ANTHROPIC_API_KEY", "")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not configured")

    try:
        import anthropic
    except ImportError:
        raise ImportError("anthropic package not installed. Run: pip install anthropic")

    client = anthropic.Anthropic(api_key=api_key)

    difficulty_guidance = {
        "junior": "foundational concepts, basic terminology, straightforward scenarios. Questions should test fundamental understanding.",
        "mid": "applied knowledge, moderate complexity, real-world scenarios. Questions should test practical application.",
        "senior": "strategic thinking, complex trade-offs, nuanced judgment calls. Questions should test deep expertise and decision-making.",
    }

    prompt = f"""Generate {num_questions} multiple-choice assessment questions for a {role_description} position.

Skills/Knowledge to test: {skills}

Difficulty level: {difficulty_level.title()} - Focus on {difficulty_guidance.get(difficulty_level, difficulty_guidance['mid'])}

Requirements:
1. Each question must have exactly 4 answer options (A, B, C, D)
2. Only one answer should be correct
3. Include a brief explanation for why the correct answer is right
4. Questions should be practical and job-relevant
5. Avoid trick questions or overly academic phrasing
6. Make distractors (wrong answers) plausible but clearly incorrect
7. Vary the correct answer positions (not all B's or C's)

Return ONLY a valid JSON array with this exact structure (no markdown, no extra text):
[
  {{
    "question_text": "The question",
    "option_a": "First option",
    "option_b": "Second option",
    "option_c": "Third option",
    "option_d": "Fourth option",
    "correct_answer": "B",
    "explanation": "Why B is correct",
    "category": "Category name"
  }}
]"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )

    # Parse JSON from response
    response_text = response.content[0].text.strip()

    # Handle potential markdown code blocks
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        response_text = "\n".join(lines[1:-1])

    questions = json.loads(response_text)

    # Add difficulty level and mark as AI generated
    difficulty_map = {"junior": 2, "mid": 3, "senior": 4}
    for q in questions:
        q["difficulty_level"] = difficulty_map.get(difficulty_level, 3)
        q["ai_generated"] = True

    return questions


def create_questions_from_data(assessment: "CustomAssessment", questions_data: list[dict]) -> int:
    """
    Create CustomQuestion objects from question data.

    Args:
        assessment: CustomAssessment to add questions to
        questions_data: List of question dictionaries

    Returns:
        Number of questions created
    """
    from .models import CustomQuestion

    created = 0
    for i, q_data in enumerate(questions_data):
        CustomQuestion.objects.create(
            assessment=assessment,
            order=i + 1,
            question_text=q_data["question_text"],
            option_a=q_data["option_a"],
            option_b=q_data["option_b"],
            option_c=q_data.get("option_c", ""),
            option_d=q_data.get("option_d", ""),
            correct_answer=q_data["correct_answer"],
            explanation=q_data.get("explanation", ""),
            difficulty_level=q_data.get("difficulty_level", 3),
            category=q_data.get("category", ""),
            ai_generated=q_data.get("ai_generated", False),
        )
        created += 1

    return created


def initialize_session(session: "CustomAssessmentSession", shuffle: bool = True) -> None:
    """
    Initialize a session with question order, filtered by difficulty level.

    Args:
        session: CustomAssessmentSession to initialize
        shuffle: Whether to randomize question order

    Questions are filtered by difficulty based on the session's level:
    - Junior: difficulty 1-2 (foundational)
    - Mid: difficulty 2-4 (applied knowledge)
    - Senior: difficulty 3-5 (strategic/complex)

    If not enough questions match the level, falls back to all questions.
    """
    level = session.level
    min_diff, max_diff = LEVEL_DIFFICULTY_RANGES.get(level, (1, 5))

    # Try to get questions filtered by difficulty
    filtered_questions = session.assessment.questions.filter(
        difficulty_level__gte=min_diff,
        difficulty_level__lte=max_diff
    )

    # Fall back to all questions if not enough at the target level
    if filtered_questions.count() < 3:
        question_ids = list(
            session.assessment.questions.values_list("pk", flat=True)
        )
    else:
        question_ids = list(filtered_questions.values_list("pk", flat=True))

    if shuffle:
        random.shuffle(question_ids)

    session.question_order = question_ids
    session.save(update_fields=["question_order", "updated_at"])


def send_custom_assessment_invitation(
    session: "CustomAssessmentSession",
    assessment_url: str,
) -> tuple[bool, str | None]:
    """
    Send email invitation to candidate for custom assessment.

    Args:
        session: CustomAssessmentSession to invite for
        assessment_url: Full URL to the assessment

    Returns:
        Tuple of (success: bool, error_message: str | None)
    """
    import logging
    from django.core.mail import send_mail
    from django.template.loader import render_to_string

    logger = logging.getLogger(__name__)

    if not session.candidate_email:
        return False, "No candidate email provided"

    if not settings.EMAIL_ENABLED:
        logger.info(
            "EMAIL_ENABLED is False. Assessment link for %s: %s",
            session.candidate_email,
            assessment_url,
        )
        return True, None  # Return success even if email disabled

    context = {
        "candidate_name": session.candidate_id,
        "candidate_email": session.candidate_email,
        "assessment_name": session.assessment.name,
        "assessment_description": session.assessment.description,
        "company_name": session.client.company_name,
        "time_limit": session.assessment.time_limit_minutes,
        "question_count": session.assessment.question_count(),
        "assessment_url": assessment_url,
        "level": session.get_level_display(),
        "deadline_at": session.deadline_at,
    }

    subject = f"You've been invited to take: {session.assessment.name}"

    try:
        text_body = render_to_string(
            "custom_assessments/emails/invitation.txt", context
        )
        html_body = render_to_string(
            "custom_assessments/emails/invitation.html", context
        )
    except Exception:
        # Fallback to simple text if templates don't exist
        text_body = f"""Hi {session.candidate_id},

You've been invited by {session.client.company_name} to complete an assessment.

Assessment: {session.assessment.name}
Time Limit: {session.assessment.time_limit_minutes} minutes
Questions: {session.assessment.question_count()}

Start your assessment here: {assessment_url}

Good luck!

- The {session.client.company_name} Team
"""
        html_body = None

    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None)

    try:
        send_mail(
            subject,
            text_body,
            from_email,
            [session.candidate_email],
            html_message=html_body,
        )
        logger.info(
            "Custom assessment invite sent to %s for %s",
            session.candidate_email,
            session.assessment.name,
        )
        return True, None
    except Exception as exc:
        logger.warning(
            "Failed to send custom assessment invite: %s", exc
        )
        return False, str(exc)
