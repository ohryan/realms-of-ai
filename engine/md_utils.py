"""
Utilities for parsing structured .md files used by rooms, enemies, items, and quests.

Each .md file follows this convention:
  # Title              — ignored by the parser
  ## Section Name      — starts a named section
  content...           — belongs to the section above it

  extract_section(md, "Description")  → the text under ## Description
  extract_all_sections(md)            → dict of all section_name -> content
"""


def extract_section(md_content: str, heading: str) -> str:
    """
    Return the text content under a specific ## heading.
    Returns empty string if the heading is not found.
    """
    if not md_content:
        return ""
    lines = md_content.split("\n")
    in_section = False
    result = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            section_name = stripped[3:].strip()
            if section_name == heading:
                in_section = True
                continue
            elif in_section:
                break
        elif in_section:
            result.append(line)

    return "\n".join(result).strip()


def extract_all_sections(md_content: str) -> dict[str, str]:
    """
    Parse all ## sections from a .md file.
    Returns a dict mapping section name -> content string.
    """
    if not md_content:
        return {}

    sections: dict[str, str] = {}
    current_heading: str | None = None
    current_lines: list[str] = []

    for line in md_content.split("\n"):
        stripped = line.strip()
        if stripped.startswith("## "):
            if current_heading is not None:
                sections[current_heading] = "\n".join(current_lines).strip()
            current_heading = stripped[3:].strip()
            current_lines = []
        elif not stripped.startswith("# "):
            if current_heading is not None:
                current_lines.append(line)

    if current_heading is not None:
        sections[current_heading] = "\n".join(current_lines).strip()

    return sections


def load_md(path) -> str:
    """Load a .md file from a Path, returning empty string if not found."""
    try:
        return path.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError):
        return ""
