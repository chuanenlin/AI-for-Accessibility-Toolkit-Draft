"""Standard test suite for accessibility tools.

Every tool should pass these tests. Tool authors inherit from
StandardToolTests or StandardTransformTests in their test files:

    from ai4a11y.testing.standard import StandardToolTests
    from my_tool.tool import MyTool

    class TestMyTool(StandardToolTests):
        tool_class = MyTool
"""

from __future__ import annotations

from ai4a11y.models import Issue, PageContext
from ai4a11y.tools.base import BaseTool, BaseTransform
from ai4a11y.profiles import PROFILES

# Minimal test page
FIXTURE_HTML = """<!DOCTYPE html>
<html lang="en">
<head><title>Test Page</title></head>
<body>
    <h1>Test</h1>
    <img src="test.jpg">
    <img src="test2.jpg" alt="A test image">
    <a href="/link">Click here</a>
    <button>Submit</button>
    <input type="text" placeholder="Name">
    <input type="email">
    <div role="navigation"><a href="/">Home</a></div>
    <table><tr><td>Data</td></tr></table>
    <p style="color: #777; background: #fff;">Low contrast text</p>
</body>
</html>"""


class StandardToolTests:
    """Standard tests every BaseTool must pass.

    Set `tool_class` to your tool class in the subclass.
    """

    tool_class: type[BaseTool]

    def _make_tool(self) -> BaseTool:
        return self.tool_class()

    def _make_page(self) -> PageContext:
        return PageContext(url="https://test.example.com", html=FIXTURE_HTML)

    def test_has_name(self):
        tool = self._make_tool()
        assert tool.name, "Tool must have a name"

    def test_has_description(self):
        tool = self._make_tool()
        assert tool.description, "Tool must have a description"

    def test_has_ability_profiles(self):
        tool = self._make_tool()
        assert isinstance(tool.ability_profiles, list), \
            "ability_profiles must be a list"
        for profile in tool.ability_profiles:
            assert profile in PROFILES, \
                f"Unknown profile {profile!r}. Available: {', '.join(sorted(PROFILES.keys()))}"

    def test_analyze_returns_list_of_issues(self):
        tool = self._make_tool()
        page = self._make_page()
        result = tool.analyze(page)
        assert isinstance(result, list), "analyze() must return a list"
        for item in result:
            assert isinstance(item, Issue), \
                f"analyze() must return Issue objects, got {type(item)}"

    def test_issues_have_required_fields(self):
        tool = self._make_tool()
        page = self._make_page()
        issues = tool.analyze(page)
        for issue in issues:
            assert issue.rule_id, "Issue must have a rule_id"
            assert issue.description, "Issue must have a description"
            assert issue.severity, "Issue must have a severity"

    def test_adapt_returns_list(self):
        tool = self._make_tool()
        page = self._make_page()
        profile = PROFILES.get("blv") or list(PROFILES.values())[0]
        result = tool.adapt(page, profile)
        assert isinstance(result, list), "adapt() must return a list"

    def test_setup_teardown(self):
        tool = self._make_tool()
        tool.setup()
        tool.teardown()

    def test_repr(self):
        tool = self._make_tool()
        r = repr(tool)
        assert tool.name in r, "repr should include tool name"


class StandardTransformTests:
    """Standard tests every BaseTransform must pass.

    Set `transform_class` to your transform class in the subclass.
    """

    transform_class: type[BaseTransform]

    def _make_transform(self) -> BaseTransform:
        return self.transform_class()

    def test_has_name(self):
        t = self._make_transform()
        assert t.name, "Transform must have a name"

    def test_has_modalities(self):
        t = self._make_transform()
        assert t.source_modality, "Transform must have a source_modality"
        assert t.target_modality, "Transform must have a target_modality"

    def test_can_transform_returns_bool(self):
        from ai4a11y.models import Element
        t = self._make_transform()
        element = Element(tag="img", selector="img", attributes={"src": "test.jpg"})
        result = t.can_transform(element)
        assert isinstance(result, bool), "can_transform() must return bool"

    def test_repr(self):
        t = self._make_transform()
        r = repr(t)
        assert "→" in r, "repr should show source→target modality"
