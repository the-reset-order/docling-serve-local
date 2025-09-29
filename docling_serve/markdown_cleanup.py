"""Utilities for cleaning up Docling-produced Markdown.

The Docling pipeline focuses on accurate document understanding, but its raw
Markdown export often mirrors quirks from the source PDF (for example,
watermark headings or aggressively wrapped sentences).  This module provides a
small, easily testable toolbox that applies the "best practices" outlined in
the product documentation so that downstream consumers get tidy Markdown by
default.

The helpers operate on plain strings and can therefore be reused from the API
layer, the Gradio UI, or future batch tooling without pulling in heavyweight
dependencies.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass, field

_HEADING_PATTERN = re.compile(r"^(#{1,6})\s*(.+?)\s*$")
_NUMERIC_HEADING_PATTERN = re.compile(r"^(\d+)([.)])?$")
_DOMAIN_HEADING_PATTERN = re.compile(
    r"^(#{1,6})\s*([A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?(?:\.[A-Za-z0-9-]+)+)\s*$",
    re.IGNORECASE,
)


@dataclass(slots=True)
class MarkdownCleanupOptions:
    """Configuration flags controlling how Markdown is post-processed."""

    remove_patterns: Sequence[str] = field(default_factory=tuple)
    auto_remove_domain_headings: bool = True
    combine_numbered_headings: bool = True
    reflow_paragraphs: bool = True


def cleanup_markdown(markdown: str, options: MarkdownCleanupOptions) -> str:
    """Return Markdown text with common Docling artefacts cleaned up.

    The function performs a couple of light-touch transformations:

    * Remove explicit noise patterns (for instance repeated watermarks).
    * Detect obvious domain-style headings that repeat throughout the
      document and drop them as likely watermarks.
    * Merge headings where Docling emitted the chapter number and title on
      two consecutive heading lines.
    * Reflow text paragraphs so that they become continuous blocks instead of
      one sentence per line.

    Each operation can be toggled individually via ``MarkdownCleanupOptions``.
    """

    if not markdown:
        return markdown

    lines = markdown.splitlines()
    original_trailing_newline = markdown.endswith("\n")

    if options.remove_patterns:
        lines = _remove_pattern_matches(lines, options.remove_patterns)

    if options.auto_remove_domain_headings:
        lines = _remove_repeated_domain_headings(lines)

    if options.combine_numbered_headings:
        lines = _combine_numbered_headings(lines)

    if options.reflow_paragraphs:
        lines = _reflow_paragraphs(lines)

    lines = _ensure_heading_spacing(lines)

    cleaned = "\n".join(_squash_blank_lines(lines))
    if original_trailing_newline and cleaned and not cleaned.endswith("\n"):
        cleaned += "\n"
    return cleaned


def _remove_pattern_matches(lines: Sequence[str], patterns: Sequence[str]) -> list[str]:
    compiled = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    if not compiled:
        return list(lines)

    cleaned: list[str] = []
    for line in lines:
        stripped = line.strip()
        if any(regex.search(stripped) for regex in compiled):
            continue
        cleaned.append(line)
    return cleaned


def _remove_repeated_domain_headings(lines: Sequence[str]) -> list[str]:
    # First identify headings that look like domain names and appear multiple times.
    counts: Counter[str] = Counter()
    for heading_text in _iter_domain_heading_text(lines):
        counts[heading_text] += 1

    repeated = {text for text, count in counts.items() if count > 1}
    if not repeated:
        return list(lines)

    cleaned: list[str] = []
    for line in lines:
        match = _DOMAIN_HEADING_PATTERN.match(line.strip())
        if match and match.group(2).lower() in repeated:
            continue
        cleaned.append(line)
    return cleaned


def _iter_domain_heading_text(lines: Sequence[str]) -> Iterator[str]:
    for line in lines:
        match = _DOMAIN_HEADING_PATTERN.match(line.strip())
        if match:
            yield match.group(2).lower()


def _combine_numbered_headings(lines: Sequence[str]) -> list[str]:
    combined: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        match = _HEADING_PATTERN.match(line.strip())
        if match:
            level, text = match.groups()
            numeric_match = _NUMERIC_HEADING_PATTERN.match(text.strip())
            if numeric_match and i + 1 < len(lines):
                next_line = lines[i + 1]
                next_match = _HEADING_PATTERN.match(next_line.strip())
                if next_match and len(next_match.group(1)) == len(level):
                    next_text = next_match.group(2).strip()
                    # Avoid merging if the "title" looks like another pure number.
                    if not _NUMERIC_HEADING_PATTERN.fullmatch(next_text):
                        separator = numeric_match.group(2) or "."
                        separator = separator.strip()
                        space = (
                            ""
                            if not next_text
                            or next_text.startswith((".", ")", "-", "\u2013"))
                            else " "
                        )
                        merged = f"{level} {numeric_match.group(1)}{separator}{space}{next_text}".rstrip()
                        combined.append(merged)
                        i += 2
                        continue
        combined.append(line)
        i += 1
    return combined


def _reflow_paragraphs(lines: Sequence[str]) -> list[str]:
    reflowed: list[str] = []
    paragraph: list[str] = []
    in_code_block = False

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            reflowed.append(" ".join(paragraph))
            paragraph = []

    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = line.strip()

        if stripped.startswith("```"):
            flush_paragraph()
            reflowed.append(line)
            in_code_block = not in_code_block
            continue

        if in_code_block:
            reflowed.append(line)
            continue

        if _is_structure_line(stripped, raw_line):
            flush_paragraph()
            reflowed.append(line)
            continue

        if not stripped:
            flush_paragraph()
            reflowed.append("")
            continue

        paragraph.append(stripped)

    flush_paragraph()
    return reflowed


def _is_structure_line(stripped: str, raw_line: str) -> bool:
    if not stripped:
        return False

    if stripped.startswith(("#", ">")):
        return True

    if re.match(r"^(?:\*|-|\+|\d+\.)\s+", stripped):
        return True

    if raw_line.startswith(("    ", "\t")):
        return True

    if stripped.startswith("|") and stripped.count("|") >= 2:
        return True

    if stripped.startswith("<!--") and stripped.endswith("-->"):
        return True

    if re.match(r"^={3,}$|^-{3,}$", stripped):
        return True

    return False


def _squash_blank_lines(lines: Iterable[str]) -> Iterator[str]:
    previous_blank = False
    for line in lines:
        is_blank = not line.strip()
        if is_blank and previous_blank:
            continue
        yield line
        previous_blank = is_blank


def _ensure_heading_spacing(lines: Sequence[str]) -> list[str]:
    spaced: list[str] = []
    for i, line in enumerate(lines):
        spaced.append(line)
        stripped = line.strip()
        if not stripped.startswith("#"):
            continue

        next_line = lines[i + 1] if i + 1 < len(lines) else None
        if next_line is None:
            continue

        if not next_line.strip() or next_line.strip().startswith("#"):
            continue

        spaced.append("")
    return spaced
