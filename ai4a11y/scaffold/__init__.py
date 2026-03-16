"""Project scaffolding for new accessibility tools."""

from __future__ import annotations

import os
from pathlib import Path

TOOL_TEMPLATE = '''\
"""{{description}}"""

from ai4a11y.models import Issue, PageContext, Severity
from ai4a11y.tools.base import BaseTool
from ai4a11y.profiles import AbilityProfile


class {{class_name}}(BaseTool):
    """{{description}}

    Implement analyze() to detect issues, and optionally
    adapt() to suggest or apply fixes.
    """

    name = "{{name}}"
    description = "{{description}}"
    ability_profiles = []  # TODO: add profiles this tool helps, e.g. ["blv", "dhh"]
    wcag_criteria = []     # TODO: add WCAG criteria, e.g. ["1.1.1", "1.4.3"]

    def analyze(self, page: PageContext) -> list[Issue]:
        """Find accessibility issues on a page.

        TODO: Implement your analysis logic here.
        """
        issues = []
        # Example:
        # for el in page.elements:
        #     if el.tag == "img" and not el.attributes.get("alt"):
        #         issues.append(Issue(
        #             rule_id="missing-alt-text",
        #             description="Image missing alt text",
        #             severity=Severity.CRITICAL,
        #             wcag_criteria=["1.1.1"],
        #             selector=el.selector,
        #         ))
        return issues
'''

TRANSFORM_TEMPLATE = '''\
"""{{description}}"""

from ai4a11y.models import Element, TransformResult
from ai4a11y.tools.base import BaseTransform
from ai4a11y.profiles import AbilityProfile


class {{class_name}}(BaseTransform):
    """{{description}}"""

    name = "{{name}}"
    source_modality = ""  # TODO: "visual", "audio", "text", "data"
    target_modality = ""  # TODO: "visual", "audio", "text", "haptic"

    def can_transform(self, element: Element) -> bool:
        """Whether this transform applies to the given element.

        TODO: Implement your check here.
        """
        return False

    def transform(self, element: Element, profile: AbilityProfile) -> TransformResult:
        """Transform the element content.

        TODO: Implement your transform here.
        """
        raise NotImplementedError
'''

TEST_TEMPLATE = '''\
"""Tests for {{name}}."""

import pytest

from ai4a11y.testing.standard import StandardToolTests
from {{package_name}}.tool import {{class_name}}


class Test{{class_name}}(StandardToolTests):
    """Standard tool tests + custom tests."""

    tool_class = {{class_name}}

    # Add your custom tests below:
    # def test_my_specific_behavior(self):
    #     tool = self.tool_class()
    #     ...
'''

TRANSFORM_TEST_TEMPLATE = '''\
"""Tests for {{name}}."""

import pytest

from ai4a11y.testing.standard import StandardTransformTests
from {{package_name}}.tool import {{class_name}}


class Test{{class_name}}(StandardTransformTests):
    """Standard transform tests + custom tests."""

    transform_class = {{class_name}}
'''

TOOL_PYPROJECT_TEMPLATE = '''\
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.build_meta"

[project]
name = "{{name}}"
version = "0.1.0"
description = "{{description}}"
requires-python = ">=3.10"
dependencies = [
    "ai4a11y>=0.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
]

[project.entry-points."ai4a11y.tools"]
{{name}} = "{{package_name}}.tool:{{class_name}}"
'''

TRANSFORM_PYPROJECT_TEMPLATE = '''\
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.build_meta"

[project]
name = "{{name}}"
version = "0.1.0"
description = "{{description}}"
requires-python = ">=3.10"
dependencies = [
    "ai4a11y>=0.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
]

[project.entry-points."ai4a11y.transforms"]
{{name}} = "{{package_name}}.tool:{{class_name}}"
'''

README_TEMPLATE = '''\
# {{name}}

{{description}}

## Install

```bash
pip install -e ".[dev]"
```

## Test

```bash
pytest
```

## Usage

```python
from {{package_name}}.tool import {{class_name}}

tool = {{class_name}}()
# ... use with ai4a11y orchestrator
```
'''

INIT_TEMPLATE = '''\
from {{package_name}}.tool import {{class_name}}

__all__ = ["{{class_name}}"]
'''


def _to_class_name(name: str) -> str:
    """Convert kebab-case to PascalCase. e.g., 'my-tool' -> 'MyTool'."""
    return "".join(word.capitalize() for word in name.replace("_", "-").split("-"))


def _to_package_name(name: str) -> str:
    """Convert kebab-case to snake_case. e.g., 'my-tool' -> 'my_tool'."""
    return name.replace("-", "_")


def _render(template: str, **kwargs) -> str:
    """Simple template rendering with {{key}} placeholders."""
    result = template
    for key, value in kwargs.items():
        result = result.replace("{{" + key + "}}", value)
    return result


def _create_project(
    name: str,
    description: str,
    tool_template: str,
    test_template: str,
    pyproject_template: str = "",
) -> str:
    """Create a scaffolded project directory."""
    class_name = _to_class_name(name)
    package_name = _to_package_name(name)

    base = Path(name)
    if base.exists():
        raise FileExistsError(f"Directory '{base}' already exists. Choose a different name or remove it first.")
    pkg = base / package_name
    tests = base / "tests"

    os.makedirs(pkg)
    os.makedirs(tests, exist_ok=True)

    ctx = dict(
        name=name,
        class_name=class_name,
        package_name=package_name,
        description=description,
    )

    (pkg / "__init__.py").write_text(_render(INIT_TEMPLATE, **ctx))
    (pkg / "tool.py").write_text(_render(tool_template, **ctx))
    (tests / "__init__.py").write_text("")
    (tests / f"test_{package_name}.py").write_text(_render(test_template, **ctx))
    (base / "pyproject.toml").write_text(_render(pyproject_template, **ctx))
    (base / "README.md").write_text(_render(README_TEMPLATE, **ctx))

    return str(base)


def create_tool_project(name: str, description: str = "") -> str:
    """Scaffold a new BaseTool project."""
    if not description:
        description = f"Accessibility tool: {name}"
    return _create_project(name, description, TOOL_TEMPLATE, TEST_TEMPLATE, TOOL_PYPROJECT_TEMPLATE)


def create_transform_project(name: str, description: str = "") -> str:
    """Scaffold a new BaseTransform project."""
    if not description:
        description = f"Modality transform: {name}"
    return _create_project(name, description, TRANSFORM_TEMPLATE, TRANSFORM_TEST_TEMPLATE, TRANSFORM_PYPROJECT_TEMPLATE)
