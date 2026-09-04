from typing import TypedDict

from app.schema import SourceSpan


class SectionHeader(TypedDict):
    level: int
    title: str


def make_section(
    header: SectionHeader | None, body: list[str], sequence: int
) -> SourceSpan:
    return {
        "section": header["title"] if header is not None else "",
        "level": header["level"] if header is not None else 0,
        "body": "\n".join(body),
        "sequence": sequence,
    }


def make_source_span(content: str) -> list[SourceSpan]:
    source_spans: list[SourceSpan] = []

    body: list[str] = []
    header: SectionHeader | None = None

    for line in content.splitlines():
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            title = line[level:].strip()

            if header is not None or body:
                source_spans.append(make_section(header, body, len(source_spans) + 1))
            header = {"level": level, "title": title}
            body = []
        else:
            body.append(line)

    if header is not None or body:
        source_spans.append(make_section(header, body, len(source_spans) + 1))

    return source_spans
