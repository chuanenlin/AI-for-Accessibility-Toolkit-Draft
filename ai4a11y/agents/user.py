"""User Agent — knows who the user is.

Manages ability profiles, preferences, and interaction history.
"""

from __future__ import annotations

from ai4a11y.profiles import AbilityProfile, combine_profiles, get_profile


class UserAgent:
    """Manages the user's ability profile and preferences.

    Args:
        profile: Ability profile name or list of names to combine.
            E.g., "blv" or ["blv", "motor"].
        preferences: Optional dict of user preferences
            (contrast, font_size, input_method, etc.).
    """

    def __init__(
        self,
        profile: str | list[str] | None = None,
        preferences: dict | None = None,
    ):
        if profile is None:
            self.profile = AbilityProfile(name="general", description="No specific profile")
        elif isinstance(profile, list):
            self.profile = combine_profiles(*profile)
        else:
            self.profile = get_profile(profile)

        self.preferences = preferences or {}

    @property
    def needs(self) -> list[str]:
        return self.profile.needs

    @property
    def preferred_modalities(self) -> list[str]:
        return self.profile.preferred_modalities

    def __repr__(self) -> str:
        return f"<UserAgent profile={self.profile.name!r}>"
