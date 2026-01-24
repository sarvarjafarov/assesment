"""
Constants for Custom Assessments.
"""

# Assessment level choices - shared between models and forms
LEVEL_CHOICES = [
    ("junior", "Junior (0-2 years)"),
    ("mid", "Mid-Level (2-5 years)"),
    ("senior", "Senior (5+ years)"),
]

LEVEL_JUNIOR = "junior"
LEVEL_MID = "mid"
LEVEL_SENIOR = "senior"

# Difficulty levels for questions
DIFFICULTY_CHOICES = [
    (1, "1 - Very Easy"),
    (2, "2 - Easy"),
    (3, "3 - Medium"),
    (4, "4 - Hard"),
    (5, "5 - Very Hard"),
]

# Difficulty ranges for each assessment level
LEVEL_DIFFICULTY_RANGES = {
    "junior": (1, 2),  # Easy questions
    "mid": (2, 4),     # Medium questions
    "senior": (3, 5),  # Hard questions
}
