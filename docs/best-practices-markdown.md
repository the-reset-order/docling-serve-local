# Best Practices for Docling Markdown Output

This guide outlines recommended steps for turning Docling conversions of PDF textbooks into clean, well-structured Markdown that is easy for both humans and downstream tooling to consume.

## Clean up and structure the Markdown output

- **Remove noise from the export.** Delete watermark text, repeated headers or footers, and other stray artifacts that Docling may capture during OCR (for example, repeated headings such as `## OceanofPDF.com`).
- **Correct obvious OCR mistakes.** When the source document is scanned, rerun OCR with the right language settings (e.g. `ocr_languages=["en"]`) or manually fix obvious errors such as garbled cover titles.
- **Reflow text into paragraphs.** Merge single-line sentences back into paragraphs separated by blank lines so the Markdown represents coherent blocks of text.
- **Combine multi-line headings.** Join consecutive headings that belong together (e.g. `## 1` and `## Breathing Again` should become `## 1. Breathing Again`) so every section has a single, descriptive heading.
- **Normalize the heading hierarchy.** Promote or demote headings until they reflect the true document structure, using `#` for the book title, `##` for chapters, `###` for subsections, and so on.

## Leverage Docling configuration options

- **Preserve structured elements.** Enable `preserve_tables=True` (or the equivalent table settings in the API) to keep table layouts, and set `include_images=True` with `image_export_mode="placeholder"|"referenced"` to retain images for later substitution.
- **Replace image placeholders.** Docling may emit HTML comments such as `<!-- image -->`; swap these for Markdown image syntax like `![Alt text](images/figure-01.png)` once the extracted files are available.
- **Capture code and formulas.** Turn on enrichment flags such as `do_code_enrichment=True` and `do_formula_enrichment=True` when dealing with source material that contains programming snippets or equations.
- **Tune PDF parsing.** Experiment with alternate PDF backends such as `pdf_backend="dlparse_v2"` (Heron layout model) and ensure `do_table_structure=True` remains enabled when you need accurate table column detection.
- **Record metadata.** Where helpful, add YAML front matter with title, author, and other metadata or keep the DocTags/JSON output alongside Markdown for further processing.

## Improve Markdown formatting for readability

- **Use Markdown emphasis and quotes.** Translate italics, bold, and block quotes from the source into `*italic*`, `**bold**`, and `>` syntax to retain context.
- **Verify lists and enumerations.** Convert bullet and numbered lists into proper Markdown list syntax so they parse cleanly, especially for references, footnotes, or definitions.
- **Prefer standard Markdown features.** Avoid raw HTML whenever possible so that the document remains portable and easy to parse.
- **Mind paragraph spacing.** Keep paragraphs separated by blank lines and optionally wrap lines at natural sentence boundaries for human readability without disrupting machine parsing.

## Optimize for downstream parsing and chunking

- **Choose a chunking strategy.** Decide whether to produce a single Markdown file or split by chapters using Docling's `individual_chunks=True` output mode or manual post-processing.
- **Anchor sections with headings.** Ensure every major section begins with a unique heading (e.g. `## 5. Bouncing Forward`) to make downstream navigation and splitting straightforward.
- **Keep related content together.** Ensure figures stay with captions, multi-page tables remain contiguous, and lists are not inadvertently broken across sections.
- **Plan for token limits.** If the Markdown will feed LLM workflows, aim for sections that roughly align with ~2,000 tokens to simplify later chunking.
- **Test with a Markdown parser.** Run the final document through a Markdown renderer or AST parser to catch structural issues like missing blank lines or malformed lists.

By applying these practices after running Docling, you can produce Markdown that remains faithful to the source textbook while being clean, readable, and ready for downstream knowledge engineering tasks.
