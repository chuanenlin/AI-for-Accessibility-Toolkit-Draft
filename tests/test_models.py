"""Tests for core data models."""

from ai4a11y.models import AuditResult, Element, Issue, PageContext, Severity


def test_issue_creation():
    issue = Issue(
        rule_id="test-rule",
        description="Test issue",
        severity=Severity.CRITICAL,
    )
    assert issue.rule_id == "test-rule"
    assert issue.severity == Severity.CRITICAL


def test_audit_result_severity_filters():
    issues = [
        Issue(rule_id="a", description="crit", severity=Severity.CRITICAL),
        Issue(rule_id="b", description="serious", severity=Severity.SERIOUS),
        Issue(rule_id="c", description="mod", severity=Severity.MODERATE),
        Issue(rule_id="d", description="minor", severity=Severity.MINOR),
        Issue(rule_id="e", description="crit2", severity=Severity.CRITICAL),
    ]
    result = AuditResult(
        url="https://test.com",
        page=PageContext(url="https://test.com"),
        issues=issues,
    )
    assert len(result.critical) == 2
    assert len(result.serious) == 1
    assert len(result.moderate) == 1
    assert len(result.minor) == 1


def test_page_context():
    page = PageContext(
        url="https://example.com",
        title="Test",
        elements=[Element(tag="img", selector="img.hero")],
    )
    assert len(page.elements) == 1
    assert page.elements[0].tag == "img"
