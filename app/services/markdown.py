from app.schema import MarkdownSection, SectionHeader, SourceSpan


def make_source_span(content: str) -> list[SourceSpan]:
    source_spans: list[SourceSpan] = []
    sequence = 1
    spans = split_markdown_sections(content)

    for span in spans:
        source_spans.append(
            {
                "section": span["title"],
                "level": span["level"],
                "text": "\n".join(span["body"]),
                "sequence": sequence,
            }
        )
        sequence += 1

    return source_spans


def split_markdown_sections(text: str) -> list[MarkdownSection]:
    spans: list[MarkdownSection] = []
    body: list[str] = []
    header: SectionHeader | None = None

    for line in text.splitlines():
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            title = line[level:].strip()

            if header is not None or body:
                spans.append(
                    {
                        "level": header["level"] if header is not None else 0,
                        "title": header["title"] if header is not None else "",
                        "body": body.copy(),
                    }
                )
            # # Experience -> {level:1, title:"Experience"}
            header = {"level": level, "title": title}
            body = []
        else:
            body.append(line)

    if header is not None or body:
        spans.append(
            {
                "level": header["level"] if header is not None else 0,
                "title": header["title"] if header is not None else "",
                "body": body.copy(),
            }
        )

    return spans
