from docling_serve.markdown_cleanup import MarkdownCleanupOptions, cleanup_markdown


def test_domain_headings_removed_when_repeated():
    markdown = "\n".join(
        [
            "## OceanofPDF.com",
            "",
            "Some introductory text.",
            "",
            "## OceanofPDF.com",
            "",
            "## 2",
            "## Hope",
            "Body line.",
        ]
    )

    cleaned = cleanup_markdown(markdown, MarkdownCleanupOptions())

    assert "OceanofPDF.com" not in cleaned
    assert "## 2. Hope" in cleaned


def test_reflow_preserves_lists_and_code_blocks():
    markdown = "\n".join(
        [
            "## 1",
            "## Chapter",
            "First",
            "sentence",
            "",
            "- item one",
            "- item two",
            "",
            "```python",
            "print('hello')",
            "```",
        ]
    )

    cleaned = cleanup_markdown(markdown, MarkdownCleanupOptions())

    expected_body = "First sentence"
    assert expected_body in cleaned
    assert "- item one" in cleaned
    assert "```python" in cleaned


def test_custom_patterns_are_removed():
    markdown = "Noise line\nActual content"
    options = MarkdownCleanupOptions(remove_patterns=(r"^Noise line$",))

    cleaned = cleanup_markdown(markdown, options)

    assert "Noise line" not in cleaned
    assert "Actual content" in cleaned
