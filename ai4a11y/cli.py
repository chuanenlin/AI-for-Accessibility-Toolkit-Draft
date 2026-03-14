"""CLI for the AI for Accessibility Toolkit.

Commands:
    a11y check https://example.com              # check for accessibility issues
    a11y check https://example.com --profile blv # check for a specific ability profile
    a11y adapt https://example.com --profile blv # adapt a page for a specific ability profile
    a11y tools                                   # list installed tools
    a11y profiles                                # list ability profiles
    a11y create my-tool                          # create a new tool
"""

from __future__ import annotations

import json
import sys

import click
from rich.console import Console
from rich.table import Table

from ai4a11y.models import AuditResult, Severity
from ai4a11y.profiles import PROFILES

console = Console()

# ── Severity display config ──────────────────────────────────────────

SEVERITY_COLORS = {
    Severity.CRITICAL: "red",
    Severity.SERIOUS: "yellow",
    Severity.MODERATE: "blue",
    Severity.MINOR: "dim",
}

SEVERITY_LABELS = {
    Severity.CRITICAL: "CRITICAL",
    Severity.SERIOUS: "SERIOUS",
    Severity.MODERATE: "MODERATE",
    Severity.MINOR: "MINOR",
}


# ── CLI entry point ──────────────────────────────────────────────────

@click.group()
@click.version_option(package_name="ai4a11y")
def main():
    """AI for Accessibility Toolkit — adapt any web page to each user's abilities."""
    pass


# ── a11y check ───────────────────────────────────────────────────────

@main.command()
@click.argument("url")
@click.option(
    "--profile", "-p",
    default=None,
    help="Ability profile: " + ", ".join(sorted(PROFILES.keys())),
)
def check(url: str, profile: str | None):
    """Check a web page for accessibility issues.

    Analyzes the page with AI, selects the right tools,
    and reports accessibility issues.

    Examples:

        a11y check https://example.com

        a11y check https://example.com --profile blv
    """
    from ai4a11y.orchestrator import check as run_check

    with console.status("Analyzing and checking..."):
        try:
            result = run_check(url, profile=profile)
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            console.print(
                "\nMake sure Playwright is installed: "
                "[bold]playwright install chromium[/bold]"
            )
            sys.exit(1)

    _print_check_result(result, profile)


def _print_check_result(result: AuditResult, profile: str | None):
    """Pretty-print check results to terminal."""
    console.print()
    console.print("[bold]AI for Accessibility Toolkit — Check Report[/bold]")
    console.print("=" * 50)
    console.print(f"URL: {result.url}")
    if profile:
        console.print(f"Profile: {profile}")
    console.print(f"Tools: {', '.join(result.tools_run)}")
    if result.plan:
        console.print()
        console.print(f"[dim]Plan: {result.plan.get('analysis', '')}[/dim]")
    console.print()

    if not result.issues:
        console.print("[green]No accessibility issues found.[/green]")
        return

    # Summary counts by severity
    counts = {}
    for issue in result.issues:
        counts[issue.severity] = counts.get(issue.severity, 0) + 1

    total = len(result.issues)
    console.print(f"Found [bold]{total}[/bold] issues:")
    for severity in [Severity.CRITICAL, Severity.SERIOUS, Severity.MODERATE, Severity.MINOR]:
        count = counts.get(severity, 0)
        if count:
            color = SEVERITY_COLORS[severity]
            label = SEVERITY_LABELS[severity]
            console.print(f"  [{color}]{label}[/{color}]: {count}")
    console.print()

    # Issues table
    table = Table(show_header=True, header_style="bold")
    table.add_column("Severity", width=10)
    table.add_column("Rule", width=25)
    table.add_column("Description", width=50)
    table.add_column("Element", width=30)

    for issue in result.issues:
        color = SEVERITY_COLORS[issue.severity]
        label = SEVERITY_LABELS[issue.severity]
        selector = issue.selector[:30] if issue.selector else ""
        desc = issue.description[:50] if issue.description else ""
        table.add_row(
            f"[{color}]{label}[/{color}]",
            issue.rule_id,
            desc,
            selector,
        )

    console.print(table)


# ── a11y adapt ───────────────────────────────────────────────────────

@main.command()
@click.argument("url")
@click.option(
    "--profile", "-p",
    required=True,
    help="Ability profile to adapt for: " + ", ".join(sorted(PROFILES.keys())),
)
@click.option(
    "--format", "-f", "output_format",
    default="terminal",
    type=click.Choice(["terminal", "json"]),
    help="Output format.",
)
def adapt(url: str, profile: str, output_format: str):
    """Adapt a web page for a specific ability profile.

    The orchestrator analyzes the page, selects the right tools,
    and generates prioritized adaptations for the user.

    Requires --profile to know what adaptations to generate.

    Examples:

        a11y adapt https://example.com --profile blv

        a11y adapt https://example.com --profile cognitive --format json
    """
    from ai4a11y.orchestrator import adapt as run_adapt

    # Support comma-separated profiles: --profile blv,motor
    profiles = [p.strip() for p in profile.split(",")]
    for p in profiles:
        if p not in PROFILES:
            console.print(f"[red]Unknown profile:[/red] {p}")
            console.print(f"Available: {', '.join(sorted(PROFILES.keys()))}")
            sys.exit(1)
    profile_arg: str | list[str] = profiles if len(profiles) > 1 else profiles[0]

    with console.status(f"Analyzing and adapting for {profile}..."):
        try:
            result = run_adapt(url, profile=profile_arg)
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            console.print(
                "\nMake sure Playwright is installed: "
                "[bold]playwright install chromium[/bold]"
            )
            sys.exit(1)

    if output_format == "json":
        _print_adapt_json(result)
    else:
        _print_adapt_result(result, profile)


def _print_adapt_result(result: AuditResult, profile: str):
    """Pretty-print adaptation results to terminal."""
    console.print()
    console.print("[bold]AI for Accessibility Toolkit — Adaptations[/bold]")
    console.print("=" * 50)
    console.print(f"URL: {result.url}")
    console.print(f"Profile: {profile}")
    console.print(f"Tools: {', '.join(result.tools_run)}")
    if result.plan:
        console.print()
        console.print(f"[dim]Plan: {result.plan.get('analysis', '')}[/dim]")
        reasoning = result.plan.get("reasoning", "")
        if reasoning:
            console.print(f"[dim]Reasoning: {reasoning}[/dim]")
    console.print()

    # Show issues found
    if result.issues:
        console.print(f"Found [bold]{len(result.issues)}[/bold] issues")
    else:
        console.print("[green]No issues found.[/green]")

    # Show adaptations
    if result.adaptations:
        console.print(f"Generated [bold]{len(result.adaptations)}[/bold] adaptations:")
        console.print()

        table = Table(show_header=True, header_style="bold")
        table.add_column("Action", width=25)
        table.add_column("Element", width=30)
        table.add_column("Original", width=25)
        table.add_column("Replacement", width=30)

        for adapt in result.adaptations:
            table.add_row(
                adapt.action,
                adapt.element.selector[:30],
                adapt.original[:25] if adapt.original else "",
                adapt.replacement[:30] if adapt.replacement else "",
            )

        console.print(table)
    else:
        console.print()
        console.print("[dim]No adaptations generated. Install tools that support "
                      f"the '{profile}' profile to enable adaptations.[/dim]")


def _print_adapt_json(result: AuditResult):
    """Print adaptation results as JSON."""
    output = {
        "url": result.url,
        "tools_run": result.tools_run,
        "plan": result.plan,
        "issues": len(result.issues),
        "adaptations": [
            {
                "action": a.action,
                "element": a.element.selector,
                "original": a.original,
                "replacement": a.replacement,
                "tool": a.tool_name,
            }
            for a in result.adaptations
        ],
    }
    click.echo(json.dumps(output, indent=2))


# ── a11y tools ───────────────────────────────────────────────────────

@main.command("tools")
def list_tools():
    """List installed accessibility tools and transforms.

    Shows all tools discovered via entry points (pip-installed)
    and any manually registered tools.

    Examples:

        a11y tools
    """
    from ai4a11y.tools.registry import get_registry

    registry = get_registry()
    registry.discover()

    # Tools table
    tools = registry.tools
    if tools:
        console.print()
        console.print(f"[bold]Tools ({len(tools)})[/bold]")
        table = Table(show_header=True, header_style="bold")
        table.add_column("Name", width=25)
        table.add_column("Description", width=40)
        table.add_column("Profiles", width=25)

        for name, tool in sorted(tools.items()):
            profiles = ", ".join(tool.ability_profiles) if tool.ability_profiles else "all"
            table.add_row(name, tool.description[:40], profiles)

        console.print(table)
    else:
        console.print("[dim]No tools installed.[/dim]")

    # Transforms table
    transforms = registry.transforms
    if transforms:
        console.print()
        console.print(f"[bold]Transforms ({len(transforms)})[/bold]")
        table = Table(show_header=True, header_style="bold")
        table.add_column("Name", width=25)
        table.add_column("Source", width=15)
        table.add_column("Target", width=15)

        for name, transform in sorted(transforms.items()):
            table.add_row(name, transform.source_modality, transform.target_modality)

        console.print(table)

    # Always show the built-in WCAG check
    if not tools and not transforms:
        console.print()
    console.print()
    console.print("[dim]Built-in: wcag-check (always runs with a11y check and a11y adapt)[/dim]")
    console.print("[dim]Install tools with pip to extend the toolkit.[/dim]")


# ── a11y profiles ────────────────────────────────────────────────────

@main.command("profiles")
def list_profiles():
    """List available ability profiles.

    Shows all 18 built-in profiles (6 parent + 12 sub-profiles).
    Profiles can be combined: --profile blv,motor

    Examples:

        a11y profiles
    """
    table = Table(show_header=True, header_style="bold")
    table.add_column("Profile", width=18)
    table.add_column("Description", width=35)
    table.add_column("Needs", width=45)

    # Show parent profiles first, then sub-profiles indented
    parents = [(k, v) for k, v in PROFILES.items() if v.parent is None]
    for name, profile in sorted(parents):
        table.add_row(
            f"[bold]{name}[/bold]",
            profile.description,
            ", ".join(profile.needs[:4]),
        )
        # Sub-profiles nested under parent
        children = [
            (k, v) for k, v in PROFILES.items() if v.parent == name
        ]
        for child_name, child in sorted(children):
            table.add_row(
                f"  {child_name}",
                child.description,
                ", ".join(child.needs[:4]),
            )

    console.print(table)


# ── a11y create ──────────────────────────────────────────────────────

@main.command("create")
@click.argument("name")
@click.option(
    "--type", "-t", "tool_type",
    default="tool",
    type=click.Choice(["tool", "transform"]),
    help="Type of project to create.",
)
def create(name: str, tool_type: str):
    """Create a new accessibility tool project.

    Generates a project directory with tool template, tests,
    and pyproject.toml pre-configured for auto-discovery.

    Examples:

        a11y create sonification

        a11y create chart-to-audio --type transform
    """
    from ai4a11y.scaffold import create_tool_project, create_transform_project

    if tool_type == "tool":
        path = create_tool_project(name)
    else:
        path = create_transform_project(name)

    console.print(f"[green]Created project:[/green] {path}")
    console.print()
    console.print("Next steps:")
    console.print(f"  cd {name}")
    console.print("  pip install -e '.[dev]'")
    console.print("  pytest")
    console.print()
    console.print(f"Edit [bold]{name}/{name.replace('-', '_')}/tool.py[/bold] to implement your tool.")
