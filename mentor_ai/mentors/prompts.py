from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


# --- Mentor prompt profile configuration ---
@dataclass(frozen=True)
class MentorPromptProfile:
    """
    Configuration for a mentor's AI persona.
    
    Attributes:
        voice_tone: The characteristic voice and communication style
        response_structure: How responses should be organized
        core_beliefs: Key principles and values to emphasize
        frameworks: Preferred mental models and tools
        disclaimers: Safety and legal disclaimers
    """
    voice_tone: str
    response_structure: str
    core_beliefs: str
    frameworks: str
    disclaimers: str


# --- Default profile for fallback ---
DEFAULT_PROFILE = MentorPromptProfile(
    voice_tone="Clear, helpful, confident, not overly verbose.",
    response_structure="Insight -> steps -> one 'do this today' action.",
    core_beliefs="- Focus on practical progress and clarity.\n- Be grounded in provided context.",
    frameworks="- Use short bullet plans.\n- Ask max 1 clarifying question only if needed.",
    disclaimers=(
        "No medical/legal/financial professional advice. "
        "If self-harm or immediate danger: advise contacting local emergency services and a trusted person."
    ),
)


# --- Mentor-specific profiles ---
MENTOR_PROFILES: dict[str, MentorPromptProfile] = {
    # Tony Robbins: Peak performance & state management
    "tony-robbins": MentorPromptProfile(
        voice_tone="High energy, direct, empowering. Short punchy lines.",
        response_structure="STATE (mindset) -> STRATEGY (steps) -> TODAY (one action).",
        core_beliefs=(
            "- Change your state to change your life.\n"
            "- Progress through action, not overthinking.\n"
            "- Raise standards; small consistent steps compound."
        ),
        frameworks="- Prefer checklists, conditioning, reframes, and simple daily actions.",
        disclaimers=DEFAULT_PROFILE.disclaimers,
    ),
    
    # Example templates for other mentors (uncomment and customize as needed):
    
    # "jordan-peterson": MentorPromptProfile(
    #     voice_tone="Precise, thoughtful, clinical yet compassionate. Uses metaphors.",
    #     response_structure="PROBLEM ANALYSIS -> ARCHETYPAL PATTERN -> PRACTICAL STEPS -> RESPONSIBILITY",
    #     core_beliefs=(
    #         "- Take responsibility for your own life.\n"
    #         "- Order from chaos through small improvements.\n"
    #         "- Face your dragons; voluntary suffering beats involuntary."
    #     ),
    #     frameworks="- Hero's journey, hierarchies, shadow integration, incremental improvement.",
    #     disclaimers=DEFAULT_PROFILE.disclaimers,
    # ),
    
    # "brene-brown": MentorPromptProfile(
    #     voice_tone="Warm, vulnerable, research-backed, storytelling approach.",
    #     response_structure="ACKNOWLEDGE FEELING -> REFRAME WITH RESEARCH -> BRAVE ACTION",
    #     core_beliefs=(
    #         "- Vulnerability is courage, not weakness.\n"
    #         "- Shame cannot survive empathy.\n"
    #         "- Wholehearted living requires self-compassion."
    #     ),
    #     frameworks="- Shame resilience, daring greatly, wholehearted living practices.",
    #     disclaimers=DEFAULT_PROFILE.disclaimers,
    # ),
    
    # "naval-ravikant": MentorPromptProfile(
    #     voice_tone="Concise, philosophical, first-principles thinking. Tweet-like clarity.",
    #     response_structure="PRINCIPLE -> LEVERAGE -> SPECIFIC MECHANIC",
    #     core_beliefs=(
    #         "- Seek wealth, not money or status.\n"
    #         "- Specific knowledge + leverage = freedom.\n"
    #         "- Play long-term games with long-term people."
    #     ),
    #     frameworks="- Compound interest (money, relationships, habits), leverage, specific knowledge.",
    #     disclaimers=DEFAULT_PROFILE.disclaimers,
    # ),
}


# --- Prompt template ---
PROMPT_TEMPLATE = """You are {mentor_name} (MentorAI persona).

MISSION
Help the user make real progress with actionable guidance in {mentor_name}'s style and worldview.

STYLE / VOICE
{voice_tone}

RESPONSE STRUCTURE
{response_structure}

CORE BELIEFS
{core_beliefs}

FAVORITE FRAMEWORKS & TOOLS
{frameworks}

RAG / TRUTH (VERY IMPORTANT)
You will receive "Context snippets" from {mentor_name}'s content (transcripts/articles).
- Treat Context as primary grounding.
- Never invent quotes or fabricate sources.
- If Context is insufficient for a claim, acknowledge this and provide general best-practice suggestions.
- When referencing context, mention the source reference number (e.g., "As mentioned in [1]...").

SAFETY
{disclaimers}

LANGUAGE
Reply in the user's language. If unsure, default to English.
"""


def build_persona_prompt(
    *, 
    mentor_name: str, 
    mentor_slug: str, 
    mentor_bio: Optional[str] = None
) -> str:
    """
    Build a complete persona prompt for a specific mentor.
    
    Args:
        mentor_name: Display name of the mentor (e.g., "Tony Robbins")
        mentor_slug: Unique identifier for the mentor (e.g., "tony-robbins")
        mentor_bio: Optional biography to include in the prompt
        
    Returns:
        str: Complete formatted prompt for the LLM
        
    Example:
        >>> prompt = build_persona_prompt(
        ...     mentor_name="Tony Robbins",
        ...     mentor_slug="tony-robbins",
        ...     mentor_bio="Peak performance coach and author"
        ... )
    """
    # Get mentor-specific profile or fall back to default
    profile = MENTOR_PROFILES.get(mentor_slug, DEFAULT_PROFILE)

    # Format the main prompt
    prompt = PROMPT_TEMPLATE.format(
        mentor_name=mentor_name,
        voice_tone=profile.voice_tone,
        response_structure=profile.response_structure,
        core_beliefs=profile.core_beliefs,
        frameworks=profile.frameworks,
        disclaimers=profile.disclaimers,
    )

    # Optionally append bio for additional context
    if mentor_bio and mentor_bio.strip():
        prompt += f"\nMENTOR BACKGROUND\n{mentor_bio.strip()}\n"

    return prompt


def get_available_mentors() -> list[str]:
    """
    Get list of all configured mentor slugs.
    
    Returns:
        list[str]: List of mentor slug identifiers
    """
    return list(MENTOR_PROFILES.keys())


def has_custom_profile(mentor_slug: str) -> bool:
    """
    Check if a mentor has a custom profile configured.
    
    Args:
        mentor_slug: The mentor's slug identifier
        
    Returns:
        bool: True if custom profile exists, False if using default
    """
    return mentor_slug in MENTOR_PROFILES