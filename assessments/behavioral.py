from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Iterable, Sequence

from .constants import BEHAVIORAL_TRAITS, normalize_behavioral_focus

# Behavioural dataset contains 200 blocks with statements A, B, C.
# Trait alignment repeats every 10 question blocks.
TRAIT_PATTERN = {
    1: ("communication", "adaptability", "problem_solving"),
    2: ("teamwork", "integrity", "adaptability"),
    3: ("communication", "problem_solving", "teamwork"),
    4: ("integrity", "adaptability", "communication"),
    5: ("problem_solving", "teamwork", "integrity"),
    6: ("communication", "problem_solving", "adaptability"),
    7: ("integrity", "teamwork", "problem_solving"),
    8: ("adaptability", "communication", "integrity"),
    9: ("teamwork", "problem_solving", "communication"),
    10: ("integrity", "teamwork", "adaptability"),
}

RED_FLAG_RULES_CONFIG = {
    "integrity_low": {
        "trait": "integrity",
        "levels": {
            "reject": {"max_score": 39},
            "watchlist": {"min_score": 40, "max_score": 49},
        },
        "reason_reject": "Very low integrity indicators. The candidate may struggle with honesty, ethical decisions, or following rules under pressure.",
        "reason_watchlist": "Below-average integrity. The candidate may have difficulty handling ethical dilemmas and should be probed during the interview.",
    },
    "teamwork_low": {
        "trait": "teamwork",
        "levels": {
            "reject": {"max_score": 39},
            "watchlist": {"min_score": 40, "max_score": 49},
        },
        "reason_reject": "Very low teamwork indicators. Candidate may resist collaboration or negatively impact team morale.",
        "reason_watchlist": "Below-average teamwork. The candidate may prefer working alone or struggle with conflict.",
    },
    "adaptability_low": {
        "trait": "adaptability",
        "levels": {
            "reject": {"max_score": 39},
            "watchlist": {"min_score": 40, "max_score": 49},
        },
        "reason_reject": "Very low adaptability indicators. Candidate shows strong resistance to change or struggles when priorities shift.",
        "reason_watchlist": "Below-average adaptability. Candidate may require support in fast-paced environments.",
    },
    "problem_solving_low": {
        "trait": "problem_solving",
        "levels": {
            "reject": {"max_score": 39},
            "watchlist": {"min_score": 40, "max_score": 49},
        },
        "reason_reject": "Very poor analytical or problem-solving indicators.",
        "reason_watchlist": "Below-average reasoning. Candidate may struggle with ambiguous or complex tasks.",
    },
    "communication_low": {
        "trait": "communication",
        "levels": {
            "reject": {"max_score": 39},
            "watchlist": {"min_score": 40, "max_score": 49},
        },
        "reason_reject": "Very low communication indicators. Candidate may struggle with clarity and coherent expression.",
        "reason_watchlist": "Below-average communication. Candidate may need to improve clarity under pressure.",
    },
    "imbalance_risk": {
        "type": "multi_trait",
        "params": {
            "high_threshold": 75,
            "low_threshold": 40,
            "min_gap": 35,
        },
        "reason": "Large imbalance between strengths and weaknesses. Candidate may be excellent in some traits but weak in others, creating role-fit issues.",
    },
    "inconsistency_pattern": {
        "enabled": True,
        "rule": "If the candidate selects contradicting Most-Like and Least-Like patterns across questions for the same trait.",
        "reason": "Answering inconsistently or inattentively. Indicates potential reliability issues.",
    },
    "faking_good_pattern": {
        "enabled": True,
        "rule": "Triggered if all normalized trait scores are >= 85.",
        "reason": "Candidate may be providing overly idealized answers or attempting to 'fake-good'.",
    },
}

SCORING_SYSTEM = {
    "traits": BEHAVIORAL_TRAITS,
    "scoring_rules": {
        "most_like_me": 1,
        "least_like_me": -1,
        "neutral": 0,
    },
    "normalization": {
        "description": "Normalize trait scores to a 0–100 scale.",
        "formula": "((raw_score - min_possible) / (max_possible - min_possible)) * 100",
        "notes": "min_possible = -1 * number_of_statements_for_trait; max_possible = +1 * number_of_statements_for_trait",
    },
    "eligibility": {
        "weights": {
            "default": {
                "communication": 0.20,
                "adaptability": 0.20,
                "problem_solving": 0.25,
                "teamwork": 0.20,
                "integrity": 0.15,
            }
        },
        "calculation": {
            "description": "Weighted average of normalized trait scores.",
            "formula": "eligibility_score = Σ (trait_score_normalized * weight)",
        },
        "thresholds": {
            "invite_to_interview": {"min_score": 75},
            "consider_interview": {"min_score": 60, "max_score": 74},
            "reject": {"max_score": 59},
        },
    },
    "role_specific_weights": {
        "customer_service": {
            "communication": 0.30,
            "adaptability": 0.25,
            "problem_solving": 0.15,
            "teamwork": 0.20,
            "integrity": 0.10,
        },
        "sales": {
            "communication": 0.35,
            "adaptability": 0.20,
            "problem_solving": 0.10,
            "teamwork": 0.15,
            "integrity": 0.20,
        },
        "software_engineer": {
            "communication": 0.15,
            "adaptability": 0.20,
            "problem_solving": 0.40,
            "teamwork": 0.15,
            "integrity": 0.10,
        },
        "product_manager": {
            "communication": 0.25,
            "adaptability": 0.20,
            "problem_solving": 0.30,
            "teamwork": 0.15,
            "integrity": 0.10,
        },
        "operations_manager": {
            "communication": 0.20,
            "adaptability": 0.25,
            "problem_solving": 0.30,
            "teamwork": 0.15,
            "integrity": 0.10,
        },
        "finance": {
            "communication": 0.20,
            "adaptability": 0.15,
            "problem_solving": 0.35,
            "teamwork": 0.10,
            "integrity": 0.20,
        },
        "hr_recruiter": {
            "communication": 0.35,
            "adaptability": 0.20,
            "problem_solving": 0.10,
            "teamwork": 0.20,
            "integrity": 0.15,
        },
        "leadership_role": {
            "communication": 0.30,
            "adaptability": 0.20,
            "problem_solving": 0.25,
            "teamwork": 0.10,
            "integrity": 0.15,
        },
    },
    "role_specific_weighting": {
        "customer_service": {
            "communication": 0.30,
            "adaptability": 0.25,
            "problem_solving": 0.15,
            "teamwork": 0.20,
            "integrity": 0.10,
        },
        "sales": {
            "communication": 0.35,
            "adaptability": 0.20,
            "problem_solving": 0.10,
            "teamwork": 0.15,
            "integrity": 0.20,
        },
        "software_engineer": {
            "communication": 0.15,
            "adaptability": 0.20,
            "problem_solving": 0.40,
            "teamwork": 0.15,
            "integrity": 0.10,
        },
        "product_manager": {
            "communication": 0.25,
            "adaptability": 0.20,
            "problem_solving": 0.30,
            "teamwork": 0.15,
            "integrity": 0.10,
        },
        "operations_manager": {
            "communication": 0.20,
            "adaptability": 0.25,
            "problem_solving": 0.30,
            "teamwork": 0.15,
            "integrity": 0.10,
        },
        "finance": {
            "communication": 0.20,
            "adaptability": 0.15,
            "problem_solving": 0.35,
            "teamwork": 0.10,
            "integrity": 0.20,
        },
        "hr_recruiter": {
            "communication": 0.35,
            "adaptability": 0.20,
            "problem_solving": 0.10,
            "teamwork": 0.20,
            "integrity": 0.15,
        },
        "leadership_role": {
            "communication": 0.30,
            "adaptability": 0.20,
            "problem_solving": 0.25,
            "teamwork": 0.10,
            "integrity": 0.15,
        },
    },
    "red_flag_rules": RED_FLAG_RULES_CONFIG,
    "candidate_summary_text": {
        "intro": "This report summarizes the behavioral strengths and development areas identified through the assessment. These results reflect how the candidate typically communicates, collaborates, solves problems, adapts to change, and maintains ethical standards.",
        "trait_descriptions": {
            "communication": {
                "Outstanding": "The candidate communicates with exceptional clarity and structure. They consistently express ideas in a way that reduces confusion and enables efficient decision-making.",
                "Strong": "The candidate communicates clearly and effectively. They adapt their style to the audience and maintain clarity even during challenges.",
                "Moderate": "The candidate communicates adequately but may need refinement in structuring ideas or ensuring full understanding in complex situations.",
                "Weak": "The candidate shows inconsistent clarity in communication and may struggle with conveying ideas under pressure.",
                "Concerning": "The candidate exhibits serious communication challenges that could impact collaboration and execution.",
            },
            "adaptability": {
                "Outstanding": "The candidate adjusts rapidly to new situations and remains composed during sudden changes. They handle uncertainty with confidence.",
                "Strong": "The candidate adapts well to shifting priorities and unexpected challenges.",
                "Moderate": "The candidate generally adapts but may require extra time or support when change is frequent or sudden.",
                "Weak": "The candidate may struggle to adjust quickly, especially when priorities shift unexpectedly.",
                "Concerning": "The candidate shows resistance to change, which could hinder performance in dynamic or fast-paced roles.",
            },
            "problem_solving": {
                "Outstanding": "The candidate demonstrates exceptional logical reasoning and consistently identifies root causes before acting. They break down complex issues with ease.",
                "Strong": "The candidate is a strong analytical thinker who solves problems efficiently and methodically.",
                "Moderate": "The candidate can solve routine problems but may struggle with ambiguous or complex scenarios.",
                "Weak": "The candidate shows difficulty analyzing issues and may rely on surface-level thinking.",
                "Concerning": "The candidate lacks essential problem-solving capabilities required for independent decision-making.",
            },
            "teamwork": {
                "Outstanding": "The candidate excels at fostering collaboration, resolving conflicts, and maintaining team morale.",
                "Strong": "The candidate actively supports teamwork and collaborates well with others.",
                "Moderate": "The candidate participates in teamwork but may take a passive role during conflicts or high-pressure environments.",
                "Weak": "The candidate may struggle with team dynamics and require support to collaborate effectively.",
                "Concerning": "The candidate demonstrates behaviors that may disrupt team cohesion.",
            },
            "integrity": {
                "Outstanding": "The candidate maintains exceptionally high ethical standards in every situation, even under pressure.",
                "Strong": "The candidate consistently behaves ethically and avoids questionable decisions.",
                "Moderate": "The candidate generally acts with integrity but may face difficulty in high-pressure ethical dilemmas.",
                "Weak": "The candidate may struggle with consistency in ethical decision-making.",
                "Concerning": "The candidate displays concerning patterns related to honesty or moral decision-making.",
            },
        },
        "eligibility_summary": {
            "invite_to_interview": "Based on the combined results, this candidate demonstrates strong behavioral readiness and is recommended for the interview stage.",
            "neutral": "The candidate shows potential but also notable development areas. An interview may be considered depending on the role’s requirements.",
            "reject": "The current behavioral indicators suggest the candidate may not be a suitable fit at this time.",
        },
        "closing": "This assessment provides behavioral insights but should be combined with technical evaluations, interviews, and role-specific requirements for a complete decision.",
    },
    "summary_generation": {
        "labels": {
            "Outstanding": {"min": 81, "max": 100},
            "Strong": {"min": 61, "max": 80},
            "Moderate": {"min": 41, "max": 60},
            "Weak": {"min": 21, "max": 40},
            "Concerning": {"min": 0, "max": 20},
        },
        "profile_messages": {
            "communication": {
                "Outstanding": "Communicates with exceptional clarity and confidence.",
                "Strong": "Communicates well and adapts to audience.",
                "Moderate": "Communication is acceptable but needs refinement.",
                "Weak": "Struggles with clarity and structure.",
                "Concerning": "Major communication challenges.",
            },
            "adaptability": {
                "Outstanding": "Adjusts rapidly to new situations.",
                "Strong": "Handles change well.",
                "Moderate": "Manages change with some effort.",
                "Weak": "Struggles when things shift.",
                "Concerning": "Highly resistant to change.",
            },
            "problem_solving": {
                "Outstanding": "Exceptional analytical and reasoning skills.",
                "Strong": "Consistently logical and structured.",
                "Moderate": "Solves basic issues but struggles with complexity.",
                "Weak": "Poor problem-solving behavior.",
                "Concerning": "Cannot handle ambiguity or analysis.",
            },
            "teamwork": {
                "Outstanding": "Highly collaborative and conflict-resolving.",
                "Strong": "Works well in teams.",
                "Moderate": "Participates but may be passive.",
                "Weak": "Struggles with collaboration.",
                "Concerning": "May disrupt team cohesion.",
            },
            "integrity": {
                "Outstanding": "Exceptionally ethical and trustworthy.",
                "Strong": "Shows consistent integrity.",
                "Moderate": "Generally ethical under normal conditions.",
                "Weak": "May waiver under pressure.",
                "Concerning": "Serious integrity concerns.",
            },
        },
    },
    "red_flag_detector": {
        "rules": RED_FLAG_RULES_CONFIG,
        "algorithm": {
            "description": "Procedure to evaluate red flags based on trait scores.",
            "steps": [
                "1. Initialize an empty list: red_flags = []",
                "2. For each single-trait rule (integrity_low, teamwork_low, adaptability_low, problem_solving_low, communication_low):",
                "   - If normalized score ≤ reject.max_score → add a reject red flag",
                "   - Else if score between watchlist.min_score and watchlist.max_score → add a watchlist red flag",
                "3. For imbalance_risk:",
                "   - Find highest trait score and lowest trait score among all five traits.",
                "   - If highest ≥ high_threshold AND lowest ≤ low_threshold AND (highest - lowest) ≥ min_gap → add an imbalance watchlist flag",
                "4. For inconsistency_pattern (if enabled):",
                "   - Review answer distribution for traits heavily flipping between +1 and -1.",
                "   - If detected → add inconsistency red flag",
                "5. For faking_good_pattern (if enabled):",
                "   - If ALL traits ≥ 85 → add faking-good watchlist flag",
                "6. Determine overall_risk_level:",
                "   - If ANY reject flag exists → overall = 'high_risk'",
                "   - Else if ANY watchlist flag exists → overall = 'moderate_risk'",
                "   - Else → overall = 'low_risk'",
                "7. Return all red flags and final risk level.",
            ],
        },
        "output_schema": {
            "candidate_red_flag_report": {
                "candidate_id": "string",
                "normalized_scores": {
                    "communication": "number (0-100)",
                    "adaptability": "number (0-100)",
                    "problem_solving": "number (0-100)",
                    "teamwork": "number (0-100)",
                    "integrity": "number (0-100)",
                },
                "red_flags_detected": [
                    {
                        "code": "string",
                        "level": "reject or watchlist",
                        "trait": "string or 'multi'",
                        "explanation": "string",
                    }
                ],
                "overall_risk_level": "low_risk | moderate_risk | high_risk",
            }
        },
        "follow_up_questions": {
            "integrity_low": {
                "title": "Low Integrity Risk",
                "questions": [
                    "Tell me about a time you had to choose between doing what was right and doing what was easier. What did you do?",
                    "Describe a situation where you made a mistake that affected others. How did you handle it?",
                    "When have you disagreed with a rule or policy? What did you do?",
                    "Tell me about a time someone trusted you with sensitive information. How did you handle it?",
                ],
                "probing_questions": [
                    "How did you feel about the consequences?",
                    "What feedback did you receive afterward?",
                    "If you could redo it, what would you change?",
                ],
                "red_flag_indicators": [
                    "Blames others or avoids responsibility",
                    "Cannot admit mistakes",
                    "Gives overly perfect or unrealistic answers",
                    "Shows no remorse or self-awareness",
                ],
            },
            "teamwork_low": {
                "title": "Low Teamwork / Conflict Risk",
                "questions": [
                    "Describe a time you worked with someone whose style clashed with yours. What did you do?",
                    "Tell me about a team decision you disagreed with. How did you respond?",
                    "Give an example of when you supported a teammate who was struggling.",
                    "Tell me about your role in the most challenging team you’ve worked with.",
                ],
                "probing_questions": [
                    "What feedback did your teammates give you?",
                    "What specifically did you contribute to resolving the situation?",
                    "What did you learn about yourself?",
                ],
                "red_flag_indicators": [
                    "Prefers working alone",
                    "Focuses only on others’ mistakes",
                    "Avoids conflict but doesn't resolve it",
                    "Shows low accountability in team settings",
                ],
            },
            "adaptability_low": {
                "title": "Low Adaptability / Change Aversion",
                "questions": [
                    "Tell me about a time when everything changed at the last minute. How did you handle it?",
                    "Describe a situation where you had to learn something quickly.",
                    "What’s the biggest change you’ve experienced at work? What was difficult about it?",
                    "Explain a moment when a plan failed. What did you do next?",
                ],
                "probing_questions": [
                    "How did you manage your emotions?",
                    "What steps did you take to adjust?",
                    "Did you ask for help? Why or why not?",
                ],
                "red_flag_indicators": [
                    "Expresses strong resistance to change",
                    "Mentions shutting down during uncertainty",
                    "Shows anxiety or panic instead of adjustment",
                    "No evidence of learning from unexpected events",
                ],
            },
            "problem_solving_low": {
                "title": "Low Problem-Solving / Avoidance Risk",
                "questions": [
                    "Tell me about a time you solved a problem no one else noticed.",
                    "Describe a difficult problem you faced with limited information.",
                    "What is an example of a decision you made that involved risk?",
                    "Walk me through your thinking when you faced a complex challenge.",
                ],
                "probing_questions": [
                    "What other options did you consider?",
                    "How did you evaluate your choices?",
                    "How did you determine what success looked like?",
                ],
                "red_flag_indicators": [
                    "Gives vague or unstructured answers",
                    "No step-by-step thinking",
                    "Avoids taking ownership of solutions",
                    "Does not evaluate consequences or alternatives",
                ],
            },
            "communication_low": {
                "title": "Weak Communication Skills",
                "questions": [
                    "Explain a complex idea to me as if I’m unfamiliar with it.",
                    "Tell me about a time your communication prevented a misunderstanding.",
                    "Describe a situation where miscommunication caused a problem — how did you fix it?",
                    "Give an example of how you adjust communication for different audiences.",
                ],
                "probing_questions": [
                    "How did you ensure the message was understood?",
                    "What feedback did you receive?",
                    "What specifically changed afterward?",
                ],
                "red_flag_indicators": [
                    "Unstructured or confusing explanations",
                    "Over-talking or unclear language",
                    "Does not verify understanding with others",
                    "Defensive when asked for clarification",
                ],
            },
            "imbalance_risk": {
                "title": "Trait Imbalance Risk",
                "questions": [
                    "What type of tasks energize you most? Which ones drain you?",
                    "Tell me about a time your strengths helped you succeed — and a time they created problems.",
                    "Describe a task you often avoid. Why?",
                    "How do you compensate for areas that are not your strengths?",
                ],
                "probing_questions": [
                    "How have others described your strengths and weaknesses?",
                    "What patterns have you noticed in your work behavior?",
                ],
                "red_flag_indicators": [
                    "Lack of self-awareness",
                    "Denies having weaknesses",
                    "Strengths often turn into rigid behaviors",
                    "Mismatch between self-view and actual behavior",
                ],
            },
            "inconsistency_pattern": {
                "title": "Inconsistent or Random Answering Pattern",
                "questions": [
                    "Tell me how you approached the assessment. What was your mindset?",
                    "Which questions were hardest for you and why?",
                    "If you answered instinctively, what does that say about your work style?",
                    "What traits do you believe describe you most accurately?",
                ],
                "probing_questions": [
                    "Which questions felt confusing?",
                    "Did you struggle choosing Most/Least options?",
                ],
                "red_flag_indicators": [
                    "Admits to rushing or guessing answers",
                    "Cannot explain decision patterns",
                    "Contradicts their own score profile",
                    "Shows mismatch between self-perception and test results",
                ],
            },
            "faking_good_pattern": {
                "title": "Faking-Good or Overly Perfect Responses",
                "questions": [
                    "Tell me about a time you failed or handled something poorly.",
                    "When have you received tough feedback? What specifically was said?",
                    "What is a behavior you struggle with that others might notice?",
                    "Describe a weakness that has caused problems for you.",
                ],
                "probing_questions": [
                    "What did you do to improve after that?",
                    "What is something you still struggle with today?",
                ],
                "red_flag_indicators": [
                    "Gives only perfect-sounding answers",
                    "Claims weaknesses that are strengths (e.g., 'I work too hard')",
                    "Shows defensiveness when discussing failure",
                    "Lacks any authentic self-critique",
                ],
            },
        },
    },
    "output_schema": {
        "candidate_result": {
            "candidate_id": "string",
            "answers": "array",
            "raw_scores": {
                "communication": "integer",
                "adaptability": "integer",
                "problem_solving": "integer",
                "teamwork": "integer",
                "integrity": "integer",
            },
            "normalized_scores": {
                "communication": "0-100",
                "adaptability": "0-100",
                "problem_solving": "0-100",
                "teamwork": "0-100",
                "integrity": "0-100",
            },
            "behavior_profile": {
                "communication": "label",
                "adaptability": "label",
                "problem_solving": "label",
                "teamwork": "label",
                "integrity": "label",
            },
            "eligibility": {
                "score": "number",
                "decision": "invite/interview/reject",
            },
            "red_flags_detected": [
                {"code": "string", "level": "reject/watchlist", "reason": "string"}
            ],
        }
    },
}

KNOWN_TRAITS = tuple(SCORING_SYSTEM["traits"])
SCORING_RULES = SCORING_SYSTEM["scoring_rules"]
DEFAULT_WEIGHTS = SCORING_SYSTEM["eligibility"]["weights"]["default"]
ROLE_SPECIFIC_WEIGHTS = SCORING_SYSTEM["role_specific_weights"]
ELIGIBILITY_THRESHOLDS = SCORING_SYSTEM["eligibility"]["thresholds"]
SUMMARY_LABELS = SCORING_SYSTEM["summary_generation"]["labels"]
PROFILE_MESSAGES = SCORING_SYSTEM["summary_generation"]["profile_messages"]
RED_FLAG_RULES = SCORING_SYSTEM["red_flag_rules"]
AVERAGE_SHARE = 100 / len(KNOWN_TRAITS)
CANDIDATE_SUMMARY_TEXT = SCORING_SYSTEM["candidate_summary_text"]
RED_FLAG_DETECTOR_META = SCORING_SYSTEM["red_flag_detector"]
FOLLOW_UP_QUESTIONS = RED_FLAG_DETECTOR_META.get("follow_up_questions", {})

# Optional map that can be hydrated with the verbose statement dataset so we can
# surface the exact prompts a candidate selected.
STATEMENT_LIBRARY: dict[str, dict[str, str]] = {}


def _load_behavioral_blocks() -> list[dict]:
    data_path = Path(__file__).resolve().parent / "data" / "behavioral_blocks.json"
    if not data_path.exists():
        return []
    with data_path.open() as fh:
        return json.load(fh)


BEHAVIORAL_BLOCKS = _load_behavioral_blocks()
for block in BEHAVIORAL_BLOCKS:
    for statement in block.get("statements", []):
        STATEMENT_LIBRARY[statement["id"]] = {
            "text": statement.get("text", ""),
            "trait": statement.get("trait"),
            "block_id": block.get("id"),
        }


def get_behavioral_blocks(block_ids: list[int] | None = None) -> list[dict]:
    if not block_ids:
        return BEHAVIORAL_BLOCKS
    block_map = {block["id"]: block for block in BEHAVIORAL_BLOCKS}
    return [block_map[_id] for _id in block_ids if _id in block_map]


def parse_behavioral_value(value: str | None, default_response: str = "most_like_me") -> dict | None:
    """Decode a choice value into a behavioural selection payload."""
    if not value:
        return None
    raw = value.strip()
    if not raw:
        return None

    payload: dict | None = None
    if raw.startswith("{") and raw.endswith("}"):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = None
        if isinstance(data, dict):
            payload = data
    if payload is None and "|" in raw:
        parts = raw.split("|", 1)
        payload = {
            "statement_id": parts[0].strip(),
            "response_type": parts[1].strip() if len(parts) > 1 else default_response,
        }
    if payload is None and ":" in raw:
        parts = raw.split(":", 1)
        payload = {
            "statement_id": parts[0].strip(),
            "response_type": parts[1].strip() if len(parts) > 1 else default_response,
        }
    if payload is None:
        payload = {"statement_id": raw}

    statement_id = payload.get("statement_id") or payload.get("id")
    normalized_id = _normalize_statement_id(statement_id) if statement_id else None
    if not normalized_id:
        return None

    response_type = payload.get("response_type") or payload.get("behavior")
    score_override = payload.get("score_override") or payload.get("score")
    if response_type is None and isinstance(score_override, (int, float)):
        response_type = _response_type_from_score(int(score_override))
    if response_type is None:
        response_type = default_response

    result = {
        "statement_id": normalized_id,
        "response_type": str(response_type),
    }
    if isinstance(score_override, (int, float)):
        result["score_override"] = int(score_override)
    return result


def build_behavioral_profile(
    selections: Iterable[dict | str],
    *,
    weight_profile: str | None = None,
    focus_traits: Sequence[str] | None = None,
) -> dict:
    """
    Aggregate behavioural signals for the statements a candidate selected.

    selections accepts statement identifiers or dict payloads such as:
    {"statement_id": "17B", "response_type": "least_like_me"}.
    """

    normalized_selections = _normalize_selections(selections)
    if not normalized_selections:
        return {}

    focus_traits = normalize_behavioral_focus(focus_traits)

    trait_counts: Counter[str] = Counter()
    raw_scores = {trait: 0 for trait in KNOWN_TRAITS}
    response_distribution = {
        trait: Counter({"most_like_me": 0, "least_like_me": 0, "neutral": 0})
        for trait in KNOWN_TRAITS
    }
    statements_detail = []

    total_responses = 0
    for selection in normalized_selections:
        trait = selection.get("trait")
        if not trait:
            continue
        response_type = selection["response_type"]
        score_value = selection["score_value"]
        statement_id = selection["statement_id"]
        trait_counts[trait] += 1
        raw_scores[trait] += score_value
        response_distribution[trait][response_type] += 1
        statements_detail.append(
            {
                "id": statement_id,
                "trait": trait,
                "response_type": response_type,
                **STATEMENT_LIBRARY.get(statement_id, {}),
            }
        )
        total_responses += 1

    if not total_responses:
        return {}

    counts_dict = {trait: trait_counts.get(trait, 0) for trait in KNOWN_TRAITS}
    percentages = {
        trait: round((counts_dict[trait] / total_responses) * 100, 2)
        for trait in KNOWN_TRAITS
    }
    normalized_scores = _normalize_scores(raw_scores, counts_dict)
    rankings_all = _build_rankings(counts_dict, percentages, raw_scores, normalized_scores)

    focus_counts = {trait: counts_dict.get(trait, 0) for trait in focus_traits}
    focus_percentages = {trait: percentages.get(trait, 0.0) for trait in focus_traits}
    focus_raw_scores = {trait: raw_scores.get(trait, 0) for trait in focus_traits}
    focus_normalized_scores = {
        trait: normalized_scores.get(trait) for trait in focus_traits
    }
    focus_rankings = [entry for entry in rankings_all if entry["trait"] in focus_traits]
    dominant_traits = _dominant_traits(focus_rankings)
    development_traits = _development_traits(focus_rankings)
    coverage_score = round(
        len([trait for trait in focus_traits if focus_counts.get(trait)]) / len(focus_traits),
        2,
    )
    balance_gap = _balance_gap(
        {trait: focus_normalized_scores.get(trait) for trait in focus_traits}
    )
    insights = _build_insights(focus_rankings, coverage_score, development_traits)

    behavior_labels = {
        trait: _label_for_score(focus_normalized_scores[trait]) for trait in focus_traits
    }
    behavior_messages = {
        trait: PROFILE_MESSAGES[trait].get(label)
        if label
        else None
        for trait, label in behavior_labels.items()
    }

    profile_key, weights = _resolve_weight_map(weight_profile)
    filtered_weights = _filter_weights(weights, focus_traits)
    eligibility_score = _weighted_score(focus_normalized_scores, filtered_weights)
    eligibility_band = _eligibility_decision(eligibility_score)
    candidate_summary = _build_candidate_summary(
        focus_normalized_scores, eligibility_band, focus_traits
    )

    focus_distributions = {
        trait: dict(response_distribution[trait]) for trait in focus_traits
    }

    red_flags, risk_level = _evaluate_red_flags(
        focus_normalized_scores,
        balance_gap=balance_gap,
        response_distribution=focus_distributions,
        total_responses=total_responses,
        focus_traits=focus_traits,
    )

    return {
        "total_responses": total_responses,
        "statement_ids": [entry["id"] for entry in statements_detail],
        "statements": statements_detail,
        "focus_traits": focus_traits,
        "trait_counts": focus_counts,
        "trait_percentages": focus_percentages,
        "trait_rankings": focus_rankings,
        "dominant_traits": dominant_traits,
        "development_traits": development_traits,
        "coverage_score": coverage_score,
        "balance_gap": balance_gap,
        "raw_scores": focus_raw_scores,
        "normalized_scores": focus_normalized_scores,
        "behavior_labels": behavior_labels,
        "behavior_messages": behavior_messages,
        "response_distribution": focus_distributions,
        "eligibility": {
            "weight_profile": profile_key,
            "weights": filtered_weights,
            "score": eligibility_score,
            "decision": eligibility_band,
        },
        "red_flags": red_flags,
        "red_flag_report": {
            "normalized_scores": focus_normalized_scores,
            "red_flags": red_flags,
            "overall_risk_level": risk_level,
            "follow_up_questions": _build_follow_up_questions(red_flags),
        },
        "insights": insights,
        "candidate_summary": candidate_summary,
        "scoring_meta": {
            "rules": SCORING_RULES,
            "summary_labels": SUMMARY_LABELS,
            "thresholds": ELIGIBILITY_THRESHOLDS,
            "red_flag_detector": {
                "algorithm": RED_FLAG_DETECTOR_META.get("algorithm", {}),
                "output_schema": RED_FLAG_DETECTOR_META.get("output_schema", {}),
            },
        },
    }


def trait_for_statement(statement_id: str) -> str | None:
    """Resolve a behavioural trait for a statement identifier."""
    parsed = _pattern_key(statement_id)
    if not parsed:
        return None

    pattern_number, letter = parsed
    traits = TRAIT_PATTERN.get(pattern_number)
    if not traits:
        return None

    index = ord(letter) - ord("A")
    if index < 0 or index >= len(traits):
        return None

    return traits[index]


def _normalize_selections(selections: Iterable[dict | str]) -> list[dict]:
    normalized: list[dict] = []
    for item in selections:
        if not item:
            continue
        if isinstance(item, str):
            selection = {"statement_id": item, "response_type": "most_like_me"}
        elif isinstance(item, dict):
            selection = {
                "statement_id": item.get("statement_id")
                or item.get("id")
                or item.get("statement"),
                "response_type": item.get("response_type") or item.get("behavior"),
            }
            if "score_override" in item:
                selection["score_override"] = item["score_override"]
        else:
            statement_id = getattr(item, "statement_id", None)
            response_type = getattr(item, "response_type", None)
            selection = {"statement_id": statement_id, "response_type": response_type}
            score_override = getattr(item, "score_override", None)
            if score_override is not None:
                selection["score_override"] = score_override

        normalized_id = _normalize_statement_id(selection.get("statement_id"))
        if not normalized_id:
            continue
        response_type = selection.get("response_type") or "most_like_me"
        score_value = selection.get("score_override")
        if score_value is None:
            score_value = SCORING_RULES.get(response_type, 0)
        selection_payload = {
            "statement_id": normalized_id,
            "response_type": response_type,
            "score_value": int(score_value),
            "trait": trait_for_statement(normalized_id),
        }
        normalized.append(selection_payload)
    return normalized


def _normalize_statement_id(statement_id: str | None) -> str | None:
    """Return a canonical id such as 17B."""
    if not statement_id:
        return None
    statement_id = str(statement_id).strip().upper()
    if not statement_id:
        return None

    letter = statement_id[-1]
    if letter not in {"A", "B", "C"}:
        return None

    number_part = "".join(ch for ch in statement_id if ch.isdigit())
    if not number_part:
        return None

    return f"{int(number_part)}{letter}"


def _pattern_key(statement_id: str) -> tuple[int, str] | None:
    """Return (pattern_number, letter) from a statement id such as 17B."""
    normalized = _normalize_statement_id(statement_id)
    if not normalized:
        return None

    letter = normalized[-1]
    number_part = normalized[:-1]
    number = int(number_part)
    pattern_number = (number - 1) % 10 + 1
    return pattern_number, letter


def _response_type_from_score(score: int) -> str:
    for response, value in SCORING_RULES.items():
        if value == score:
            return response
    return "neutral"


def _normalize_scores(raw_scores: dict[str, int], trait_counts: dict[str, int]) -> dict[str, float | None]:
    normalized: dict[str, float | None] = {}
    for trait in KNOWN_TRAITS:
        total = trait_counts.get(trait, 0)
        raw = raw_scores.get(trait, 0)
        if total == 0:
            normalized[trait] = None
            continue
        min_possible = -1 * total
        max_possible = 1 * total
        spread = max_possible - min_possible
        if spread == 0:
            normalized[trait] = 50.0
            continue
        score = ((raw - min_possible) / spread) * 100
        normalized[trait] = round(score, 2)
    return normalized


def _build_rankings(
    counts: dict[str, int],
    percentages: dict[str, float],
    raw_scores: dict[str, int],
    normalized_scores: dict[str, float | None],
) -> list[dict]:
    ranking = []
    for trait in KNOWN_TRAITS:
        ranking.append(
            {
                "trait": trait,
                "count": counts[trait],
                "percentage": percentages[trait],
                "raw_score": raw_scores[trait],
                "normalized_score": normalized_scores[trait],
            }
        )
    ranking.sort(
        key=lambda entry: (
            entry["normalized_score"] if entry["normalized_score"] is not None else -1,
            entry["percentage"],
            entry["trait"],
        ),
        reverse=True,
    )
    return ranking


def _dominant_traits(rankings: Sequence[dict]) -> list[str]:
    if not rankings:
        return []
    top_score = rankings[0]["normalized_score"] or 0
    threshold = max(top_score - 5, 0)
    return [
        entry["trait"]
        for entry in rankings
        if (entry["normalized_score"] or 0) >= threshold and (entry["normalized_score"] or 0) > 0
    ]


def _development_traits(rankings: Sequence[dict]) -> list[str]:
    if not rankings:
        return []
    cutoff = AVERAGE_SHARE * 0.6
    return [
        entry["trait"]
        for entry in rankings
        if (entry["normalized_score"] or 0) <= cutoff
    ]


def _balance_gap(normalized_scores: dict[str, float | None]) -> float:
    scored_values = [score for score in normalized_scores.values() if score is not None]
    if not scored_values:
        return 0.0
    return round(max(scored_values) - min(scored_values), 2)


def _build_insights(
    rankings: list[dict],
    coverage_score: float,
    development_traits: list[str],
) -> list[str]:
    insights: list[str] = []
    if not rankings:
        return insights

    top_trait = rankings[0]["trait"]
    top_label = _label_for_score(rankings[0]["normalized_score"])
    if top_label:
        strength_copy = PROFILE_MESSAGES.get(top_trait, {}).get(top_label)
        if strength_copy:
            insights.append(
                f"{top_trait.replace('_', ' ').title()} strength: {strength_copy}"
            )

    if development_traits:
        focus_trait = development_traits[0]
        low_label = _label_for_score(
            next(
                (entry["normalized_score"] for entry in rankings if entry["trait"] == focus_trait),
                None,
            )
        )
        growth_copy = PROFILE_MESSAGES.get(focus_trait, {}).get(low_label or "Weak")
        if growth_copy:
            insights.append(
                f"Development area ({focus_trait.replace('_', ' ').title()}): {growth_copy}"
            )

    if coverage_score < 0.6:
        insights.append(
            "Limited trait coverage — invite follow-up prompts to uncover missing behaviours."
        )
    elif coverage_score >= 0.8 and len([entry for entry in rankings if entry['count']]) >= 3:
        insights.append(
            "Balanced spread across the behavioural bank, suggesting versatile defaults."
        )

    return insights


def _label_for_score(score: float | None) -> str | None:
    if score is None:
        return None
    for label, bounds in SUMMARY_LABELS.items():
        if bounds["min"] <= score <= bounds["max"]:
            return label
    return None


def _build_candidate_summary(
    normalized_scores: dict[str, float | None],
    decision: str,
    focus_traits: Sequence[str],
) -> dict:
    summary_cfg = CANDIDATE_SUMMARY_TEXT
    trait_cfg = summary_cfg.get("trait_descriptions", {})
    trait_messages: dict[str, dict] = {}

    for trait in focus_traits:
        score = normalized_scores.get(trait)
        label = _label_for_score(score)
        resolved_label = label or "Moderate"
        description = trait_cfg.get(trait, {}).get(resolved_label)
        if not description:
            description = trait_cfg.get(trait, {}).get("Moderate")
        trait_messages[trait] = {
            "label": resolved_label,
            "description": description,
        }

    decision_key = decision or "neutral"
    if decision_key == "consider_interview":
        decision_key = "neutral"
    eligibility_summary = summary_cfg.get("eligibility_summary", {})
    eligibility_message = (
        eligibility_summary.get(decision_key) or eligibility_summary.get("neutral")
    )

    return {
        "intro": summary_cfg.get("intro", ""),
        "traits": trait_messages,
        "eligibility_message": eligibility_message,
        "closing": summary_cfg.get("closing", ""),
    }


def _resolve_weight_map(weight_profile: str | None) -> tuple[str, dict[str, float]]:
    if not weight_profile:
        return "default", DEFAULT_WEIGHTS
    profile_key = str(weight_profile).lower()
    weights = ROLE_SPECIFIC_WEIGHTS.get(profile_key)
    if not weights:
        return "default", DEFAULT_WEIGHTS
    return profile_key, weights


def _filter_weights(weights: dict[str, float], focus_traits: Sequence[str]) -> dict[str, float]:
    filtered = {trait: weights.get(trait, 0.0) for trait in focus_traits if weights.get(trait, 0) > 0}
    if not filtered:
        if not focus_traits:
            return {}
        uniform = round(1 / len(focus_traits), 4)
        return {trait: uniform for trait in focus_traits}
    total = sum(filtered.values())
    if total <= 0:
        uniform = round(1 / len(focus_traits), 4)
        return {trait: uniform for trait in focus_traits}
    return {trait: round(value / total, 4) for trait, value in filtered.items()}


def _weighted_score(normalized_scores: dict[str, float | None], weights: dict[str, float]) -> float:
    score = 0.0
    for trait, weight in weights.items():
        trait_score = normalized_scores.get(trait)
        if trait_score is None:
            trait_score = 50.0
        score += trait_score * weight
    return round(score, 2)


def _eligibility_decision(score: float) -> str:
    invite_rule = ELIGIBILITY_THRESHOLDS["invite_to_interview"]
    if score >= invite_rule["min_score"]:
        return "invite_to_interview"

    consider_rule = ELIGIBILITY_THRESHOLDS["consider_interview"]
    if consider_rule["min_score"] <= score <= consider_rule["max_score"]:
        return "consider_interview"

    return "reject"


def _evaluate_red_flags(
    normalized_scores: dict[str, float | None],
    *,
    balance_gap: float,
    response_distribution: dict[str, Counter],
    total_responses: int,
    focus_traits: Sequence[str],
) -> tuple[list[dict], str]:
    flags: list[dict] = []
    focus_set = set(focus_traits)

    for code, rule in RED_FLAG_RULES.items():
        trait = rule.get("trait")
        if trait:
            if trait not in focus_set:
                continue
            trait_score = normalized_scores.get(trait)
            if trait_score is None:
                continue
            levels = rule.get("levels", {})
            reject_rule = levels.get("reject")
            watch_rule = levels.get("watchlist")
            if reject_rule and trait_score <= reject_rule["max_score"]:
                flags.append(
                    _build_flag(
                        code=code,
                        level="reject",
                        trait=trait,
                        explanation=rule.get("reason_reject"),
                    )
                )
                continue
            if (
                watch_rule
                and trait_score >= watch_rule.get("min_score", 0)
                and trait_score <= watch_rule.get("max_score", 100)
            ):
                flags.append(
                    _build_flag(
                        code=code,
                        level="watchlist",
                        trait=trait,
                        explanation=rule.get("reason_watchlist"),
                    )
                )
            continue

        if code == "imbalance_risk" or rule.get("type") == "multi_trait":
            if len(focus_set) < 2:
                continue
            params = rule.get("params", {})
            high = params.get("high_threshold", 75)
            low = params.get("low_threshold", 40)
            gap = params.get("min_gap", 35)
            scored_values = [score for score in normalized_scores.values() if score is not None]
            if not scored_values:
                continue
            if max(scored_values) >= high and min(scored_values) <= low and balance_gap >= gap:
                flags.append(
                    _build_flag(
                        code=code,
                        level="watchlist",
                        trait="multi",
                        explanation=rule.get("reason"),
                    )
                )
            continue

        if code == "inconsistency_pattern" and rule.get("enabled"):
            if _detect_inconsistency(response_distribution, total_responses):
                flags.append(
                    _build_flag(
                        code=code,
                        level="watchlist",
                        trait="multi",
                        explanation=rule.get("reason"),
                    )
                )
            continue

        if code == "faking_good_pattern" and rule.get("enabled"):
            if _detect_faking_good(normalized_scores):
                flags.append(
                    _build_flag(
                        code=code,
                        level="watchlist",
                        trait="multi",
                        explanation=rule.get("reason"),
                    )
                )

    return flags, _determine_risk_level(flags)


def _detect_inconsistency(
    response_distribution: dict[str, Counter], total_responses: int
) -> bool:
    if total_responses < 8:
        return False
    for trait in KNOWN_TRAITS:
        most = response_distribution[trait]["most_like_me"]
        least = response_distribution[trait]["least_like_me"]
        if most >= 2 and least >= 2 and abs(most - least) <= 1:
            return True
    return False


def _detect_faking_good(normalized_scores: dict[str, float | None]) -> bool:
    if not normalized_scores:
        return False
    scored = [score for score in normalized_scores.values() if score is not None]
    if not scored or len(scored) < len(KNOWN_TRAITS):
        return False
    return all(score >= 85 for score in scored)


def _determine_risk_level(flags: list[dict]) -> str:
    if any(flag["level"] == "reject" for flag in flags):
        return "high_risk"
    if any(flag["level"] == "watchlist" for flag in flags):
        return "moderate_risk"
    return "low_risk"


def _build_flag(code: str, level: str, trait: str, explanation: str | None) -> dict:
    return {
        "code": code,
        "level": level,
        "trait": trait,
        "explanation": explanation,
        "reason": explanation,
    }


def _build_follow_up_questions(flags: list[dict]) -> list[dict]:
    follow_ups: list[dict] = []
    seen_codes: set[str] = set()
    for flag in flags:
        code = flag["code"]
        if code in seen_codes:
            continue
        payload = FOLLOW_UP_QUESTIONS.get(code)
        if not payload:
            continue
        follow_ups.append(
            {
                "code": code,
                "title": payload.get("title"),
                "questions": payload.get("questions", []),
                "probing_questions": payload.get("probing_questions", []),
                "red_flag_indicators": payload.get("red_flag_indicators", []),
            }
        )
        seen_codes.add(code)
    return follow_ups
