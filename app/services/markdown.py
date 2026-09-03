from app.schema import MarkdownSection, SectionHeader, SourceSpan


def make_source_span(content: str) -> list[SourceSpan]:
    source_spans: list[SourceSpan] = []
    sequence = 1
    chunks = split_markdown_sections(content)

    for chunk in chunks:
        source_spans.append(
            {
                "section": chunk["title"],
                "level": chunk["level"],
                "text": "\n".join(chunk["body"]),
                "sequence": sequence,
            }
        )
        sequence += 1

    return source_spans


def split_markdown_sections(text: str) -> list[MarkdownSection]:
    level_sections: list[MarkdownSection] = []
    body_lines: list[str] = []
    current_chunk: MarkdownSection | SectionHeader | None = None

    for line in text.splitlines():
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            title = line[level:].strip()
            if current_chunk is not None:
                level_sections.append(
                    {
                        "level": current_chunk["level"],
                        "title": current_chunk["title"],
                        "body": body_lines.copy(),
                    }
                )

            current_chunk = {"level": level, "title": title}
            body_lines = []
        else:
            body_lines.append(line)

    if current_chunk is not None:
        level_sections.append(
            {
                "level": current_chunk["level"],
                "title": current_chunk["title"],
                "body": body_lines.copy(),
            }
        )

    return level_sections
