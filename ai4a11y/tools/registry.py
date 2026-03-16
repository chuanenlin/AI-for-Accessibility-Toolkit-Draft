"""Tool discovery and registration."""

from __future__ import annotations

import logging

from ai4a11y.tools.base import BaseTool, BaseTransform

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for accessibility tools and transforms."""

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}
        self._transforms: dict[str, BaseTransform] = {}
        self._discovered: bool = False

    def register_tool(self, tool: BaseTool) -> None:
        """Register an accessibility tool."""
        if not tool.name:
            raise ValueError(f"Tool {type(tool).__name__} must have a name")
        self._tools[tool.name] = tool
        tool.setup()

    def register_transform(self, transform: BaseTransform) -> None:
        """Register a modality transform."""
        if not transform.name:
            raise ValueError(f"Transform {type(transform).__name__} must have a name")
        self._transforms[transform.name] = transform

    def get_tool(self, name: str) -> BaseTool:
        if name not in self._tools:
            available = ", ".join(sorted(self._tools.keys()))
            raise KeyError(f"Tool {name!r} not found. Available: {available}")
        return self._tools[name]

    def get_transform(self, name: str) -> BaseTransform:
        if name not in self._transforms:
            available = ", ".join(sorted(self._transforms.keys()))
            raise KeyError(f"Transform {name!r} not found. Available: {available}")
        return self._transforms[name]

    @property
    def tools(self) -> dict[str, BaseTool]:
        return dict(self._tools)

    @property
    def transforms(self) -> dict[str, BaseTransform]:
        return dict(self._transforms)

    def tools_for_profile(self, profile_name: str) -> list[BaseTool]:
        """Get all tools relevant to a given ability profile."""
        return [
            t for t in self._tools.values()
            if profile_name in t.ability_profiles
        ]

    def transforms_for_modality(
        self, source: str, target: str
    ) -> list[BaseTransform]:
        """Get transforms that convert between specific modalities."""
        return [
            t for t in self._transforms.values()
            if t.source_modality == source and t.target_modality == target
        ]

    def discover(self) -> None:
        """Auto-discover tools from installed packages via entry points.

        Packages declare tools in their pyproject.toml:
            [project.entry-points."ai4a11y.tools"]
            my-tool = "my_tool.tool:MyTool"
        """
        if self._discovered:
            return
        self._discovered = True

        from importlib.metadata import entry_points

        for ep in entry_points(group="ai4a11y.tools"):
            try:
                cls = ep.load()
                self.register_tool(cls())
            except Exception as e:
                logger.warning("Failed to load tool %r: %s", ep.name, e)

        for ep in entry_points(group="ai4a11y.transforms"):
            try:
                cls = ep.load()
                self.register_transform(cls())
            except Exception as e:
                logger.warning("Failed to load transform %r: %s", ep.name, e)

    def teardown_all(self) -> None:
        """Teardown all registered tools."""
        for tool in self._tools.values():
            tool.teardown()

    def reset(self) -> None:
        """Reset registry state. Useful for test isolation."""
        self._tools.clear()
        self._transforms.clear()
        self._discovered = False


# Global registry
_registry = ToolRegistry()


def register(tool_or_transform: BaseTool | BaseTransform) -> None:
    """Register a tool or transform with the global registry."""
    if isinstance(tool_or_transform, BaseTool):
        _registry.register_tool(tool_or_transform)
    elif isinstance(tool_or_transform, BaseTransform):
        _registry.register_transform(tool_or_transform)
    else:
        raise TypeError(f"Expected BaseTool or BaseTransform, got {type(tool_or_transform)}")


def get_registry() -> ToolRegistry:
    """Get the global tool registry."""
    return _registry
