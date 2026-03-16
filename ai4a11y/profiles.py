"""Ability profiles for the AI for Accessibility Toolkit.

Ability-based design: adapt to what users can do, not what they can't.
Profiles are combinable — e.g., ["blv", "motor"] for a blind user with
limited mobility.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AbilityProfile:
    """Describes a user's abilities and adaptation needs."""

    name: str
    description: str = ""
    needs: list[str] = field(default_factory=list)
    preferred_modalities: list[str] = field(default_factory=list)
    parent: str | None = None  # sub-profile of a broader category


# Built-in profiles
PROFILES: dict[str, AbilityProfile] = {
    # Vision
    "blv": AbilityProfile(
        name="blv",
        description="Blind or low vision",
        needs=["screen_reader", "audio_first", "high_contrast", "magnification"],
        preferred_modalities=["audio", "haptic"],
    ),
    "blind": AbilityProfile(
        name="blind",
        description="Blind — no functional vision",
        needs=["screen_reader", "audio_first", "no_visual"],
        preferred_modalities=["audio", "haptic"],
        parent="blv",
    ),
    "low_vision": AbilityProfile(
        name="low_vision",
        description="Low vision — some functional vision",
        needs=["magnification", "high_contrast", "large_text"],
        preferred_modalities=["visual", "audio"],
        parent="blv",
    ),
    "color_blind": AbilityProfile(
        name="color_blind",
        description="Color vision deficiency",
        needs=["no_color_only", "patterns", "labels"],
        preferred_modalities=["visual"],
    ),
    # Hearing
    "dhh": AbilityProfile(
        name="dhh",
        description="Deaf or hard of hearing",
        needs=["captions", "visual_emphasis", "sign_language"],
        preferred_modalities=["visual", "haptic"],
    ),
    "deaf": AbilityProfile(
        name="deaf",
        description="Deaf — no functional hearing",
        needs=["captions", "sign_language", "no_audio"],
        preferred_modalities=["visual", "haptic"],
        parent="dhh",
    ),
    "hard_of_hearing": AbilityProfile(
        name="hard_of_hearing",
        description="Hard of hearing — some functional hearing",
        needs=["captions", "audio_boost", "visual_emphasis"],
        preferred_modalities=["visual", "audio"],
        parent="dhh",
    ),
    # Motor
    "motor": AbilityProfile(
        name="motor",
        description="Motor impairment",
        needs=["keyboard_only", "switch_access", "voice_control"],
        preferred_modalities=["visual", "audio"],
    ),
    "limited_mobility": AbilityProfile(
        name="limited_mobility",
        description="Limited fine motor control",
        needs=["large_targets", "keyboard_only", "reduced_motion"],
        preferred_modalities=["visual", "audio"],
        parent="motor",
    ),
    "tremor": AbilityProfile(
        name="tremor",
        description="Hand tremor",
        needs=["large_targets", "click_tolerance", "no_hover"],
        preferred_modalities=["visual", "audio"],
        parent="motor",
    ),
    # Cognitive
    "cognitive": AbilityProfile(
        name="cognitive",
        description="Cognitive disability",
        needs=["plain_language", "simplified_ui", "predictable_navigation"],
        preferred_modalities=["visual", "audio"],
    ),
    "dyslexia": AbilityProfile(
        name="dyslexia",
        description="Dyslexia",
        needs=["dyslexia_font", "line_spacing", "plain_language"],
        preferred_modalities=["visual", "audio"],
        parent="cognitive",
    ),
    "idd": AbilityProfile(
        name="idd",
        description="Intellectual or developmental disability",
        needs=["plain_language", "simplified_ui", "step_by_step"],
        preferred_modalities=["visual", "audio"],
        parent="cognitive",
    ),
    "autism": AbilityProfile(
        name="autism",
        description="Autism spectrum",
        needs=["predictable_navigation", "reduced_motion", "reduced_sensory"],
        preferred_modalities=["visual"],
        parent="cognitive",
    ),
    # Speech
    "speech": AbilityProfile(
        name="speech",
        description="Speech disability",
        needs=["alternative_input", "tuned_speech_recognition"],
        preferred_modalities=["visual", "haptic"],
    ),
    "nonverbal": AbilityProfile(
        name="nonverbal",
        description="Nonverbal — does not use speech",
        needs=["alternative_input", "no_voice_required"],
        preferred_modalities=["visual", "haptic"],
        parent="speech",
    ),
    "atypical_speech": AbilityProfile(
        name="atypical_speech",
        description="Atypical speech patterns",
        needs=["tuned_speech_recognition", "patient_listening"],
        preferred_modalities=["visual", "audio"],
        parent="speech",
    ),
    # Aging
    "aging": AbilityProfile(
        name="aging",
        description="Age-related combined decline",
        needs=[
            "large_text", "high_contrast", "captions",
            "simplified_ui", "large_targets", "memory_aids",
        ],
        preferred_modalities=["visual", "audio"],
    ),
}


def get_profile(name: str) -> AbilityProfile:
    """Get a built-in ability profile by name."""
    if name not in PROFILES:
        available = ", ".join(sorted(PROFILES.keys()))
        raise ValueError(f"Unknown profile: {name!r}. Available: {available}")
    return PROFILES[name]


def combine_profiles(*names: str) -> AbilityProfile:
    """Combine multiple profiles into one (e.g., blv + motor)."""
    if not names:
        raise ValueError("combine_profiles() requires at least one profile name")
    profiles = [get_profile(n) for n in names]
    combined_needs = []
    combined_modalities = []
    for p in profiles:
        for need in p.needs:
            if need not in combined_needs:
                combined_needs.append(need)
        for mod in p.preferred_modalities:
            if mod not in combined_modalities:
                combined_modalities.append(mod)
    return AbilityProfile(
        name="+".join(names),
        description=" + ".join(p.description for p in profiles),
        needs=combined_needs,
        preferred_modalities=combined_modalities,
    )
