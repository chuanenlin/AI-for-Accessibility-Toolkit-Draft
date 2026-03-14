"""Tests for ability profiles."""

import pytest

from ai4a11y.profiles import PROFILES, combine_profiles, get_profile


def test_get_known_profile():
    profile = get_profile("blv")
    assert profile.name == "blv"
    assert "screen_reader" in profile.needs


def test_get_unknown_profile():
    with pytest.raises(ValueError, match="Unknown profile"):
        get_profile("nonexistent")


def test_combine_profiles():
    combined = combine_profiles("blv", "motor")
    assert "blv+motor" == combined.name
    assert "screen_reader" in combined.needs
    assert "keyboard_only" in combined.needs


def test_sub_profiles_have_parent():
    for name, profile in PROFILES.items():
        if profile.parent:
            assert profile.parent in PROFILES, \
                f"Profile {name!r} has unknown parent {profile.parent!r}"


def test_all_profiles_have_needs():
    for name, profile in PROFILES.items():
        assert profile.needs, f"Profile {name!r} has no needs"


def test_all_profiles_have_description():
    for name, profile in PROFILES.items():
        assert profile.description, f"Profile {name!r} has no description"
