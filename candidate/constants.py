DEFAULT_HELP_TOPICS = [
    {
        "question": "Can I pause and resume later?",
        "answer": "Yes. Use the Pause button to save progress—you’ll land on a pause page with a resume button, and we also email you the secure link if requested.",
    },
    {
        "question": "What happens if my browser crashes?",
        "answer": "We autosave responses every step. Reopen your invitation link in the same or another device and you’ll restart from the next unanswered question.",
    },
    {
        "question": "Is there a time limit?",
        "answer": "Most assessments display the remaining time near the top. If no countdown appears, you can focus on thoughtful responses without a strict timer.",
    },
    {
        "question": "Need technical help?",
        "answer": "Email support at support@sira.so or reply directly to the invitation message. Attach screenshots if you notice something unexpected.",
    },
]

PRACTICE_QUESTIONS = [
    {
        "id": "metrics",
        "type": "multiple_choice",
        "prompt": "Which metric best captures weekly retention?",
        "options": [
            {"value": "A", "label": "Total sign-ups"},
            {"value": "B", "label": "Number of feature launches"},
            {"value": "C", "label": "Users active in consecutive weeks"},
            {"value": "D", "label": "Revenue per marketing channel"},
        ],
        "answer": "C",
        "rationale": "Retention measures how consistently users return period over period.",
    },
    {
        "id": "text",
        "type": "text",
        "prompt": "Write two sentences explaining how you prioritize roadmap items.",
        "guidance": "Mention both user impact and effort. Keep it concise.",
        "example": "I rank ideas using RICE: reach, impact, confidence, and effort. This keeps the roadmap focused on outcomes rather than stakeholder volume.",
    },
]
