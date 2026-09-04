from app.services.markdown import make_source_span


def test_make_source_span_no_first_header():
    spans = make_source_span("Jack\n# Experience\nfoo")

    assert spans == [
        {"section": "", "level": 0, "text": "Jack", "sequence": 1},
        {"section": "Experience", "level": 1, "text": "foo", "sequence": 2},
    ]


def test_make_source_span_no_title():
    spans = make_source_span("Jack\nfoo")

    assert spans == [
        {"section": "", "level": 0, "text": "Jack\nfoo", "sequence": 1},
    ]
