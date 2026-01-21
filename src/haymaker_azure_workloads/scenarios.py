"""Scenario loading and management.

Scenarios are defined as markdown files with embedded bash commands.
This module loads and parses scenario definitions.
"""

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Scenario:
    """A parsed scenario definition."""

    name: str
    description: str
    technology_area: str
    goal: str
    prompt: str  # The full prompt/instructions for the agent
    phases: dict[str, str]  # Phase name -> bash commands


class ScenarioLoader:
    """Loads scenario definitions from markdown files.

    Scenarios are stored in the 'scenarios/' directory relative
    to this package, following the format:
        scenarios/
            compute/
                linux-vm-web-server.md
                app-service-python.md
            databases/
                mysql-wordpress.md
            ...
    """

    def __init__(self, scenarios_dir: Path | None = None) -> None:
        if scenarios_dir:
            self._scenarios_dir = scenarios_dir
        else:
            # Default to package's scenarios directory
            self._scenarios_dir = Path(__file__).parent / "scenarios"

    def load(self, name: str) -> Scenario | None:
        """Load a scenario by name.

        Args:
            name: Scenario name (e.g., "linux-vm-web-server" or "compute/linux-vm")

        Returns:
            Parsed Scenario or None if not found
        """
        # Try direct file path
        file_path = self._find_scenario_file(name)
        if not file_path:
            return None

        return self._parse_scenario_file(file_path)

    def list_scenarios(self) -> list[str]:
        """List all available scenario names."""
        scenarios = []

        if not self._scenarios_dir.exists():
            return scenarios

        for md_file in self._scenarios_dir.rglob("*.md"):
            # Skip template files
            if "template" in md_file.name.lower():
                continue

            # Create relative name
            rel_path = md_file.relative_to(self._scenarios_dir)
            name = str(rel_path.with_suffix(""))
            scenarios.append(name)

        return sorted(scenarios)

    def _find_scenario_file(self, name: str) -> Path | None:
        """Find the scenario markdown file."""
        if not self._scenarios_dir.exists():
            return None

        # Try exact match
        direct = self._scenarios_dir / f"{name}.md"
        if direct.exists():
            return direct

        # Try with category prefix (e.g., "compute/linux-vm")
        with_category = self._scenarios_dir / name
        if with_category.with_suffix(".md").exists():
            return with_category.with_suffix(".md")

        # Search all subdirectories
        for md_file in self._scenarios_dir.rglob("*.md"):
            if name in md_file.stem:
                return md_file

        return None

    def _parse_scenario_file(self, file_path: Path) -> Scenario:
        """Parse a scenario markdown file into a Scenario object."""
        content = file_path.read_text()

        # Extract metadata from markdown
        name = file_path.stem
        description = self._extract_section(content, "Scenario Description") or ""
        technology_area = self._extract_section(content, "Technology Area") or "General"
        goal = self._extract_section(content, "Goal") or description

        # Extract phases (deployment, operations, cleanup)
        phases = {}
        phase_patterns = [
            ("deployment", r"Phase 1.*?Deployment"),
            ("operations", r"Phase 2.*?Operations"),
            ("cleanup", r"Phase 3.*?Cleanup"),
        ]

        for phase_name, pattern in phase_patterns:
            bash_blocks = self._extract_bash_after_pattern(content, pattern)
            if bash_blocks:
                phases[phase_name] = "\n\n".join(bash_blocks)

        return Scenario(
            name=name,
            description=description,
            technology_area=technology_area,
            goal=goal,
            prompt=content,  # Full markdown as prompt
            phases=phases,
        )

    def _extract_section(self, content: str, header: str) -> str | None:
        """Extract content under a markdown header."""
        pattern = rf"##\s*{header}\s*\n(.*?)(?=\n##|\Z)"
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    def _extract_bash_after_pattern(self, content: str, pattern: str) -> list[str]:
        """Extract bash code blocks after a pattern match."""
        # Find the pattern
        match = re.search(pattern, content, re.IGNORECASE)
        if not match:
            return []

        # Get content after the pattern
        after = content[match.end():]

        # Find the next major section (##) to limit scope
        next_section = re.search(r"\n##\s+[A-Z]", after)
        if next_section:
            after = after[:next_section.start()]

        # Extract all bash blocks
        bash_pattern = r"```bash\n(.*?)```"
        matches = re.findall(bash_pattern, after, re.DOTALL)

        return matches
