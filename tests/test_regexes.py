import pytest

from trackie.conf import (
    date_pattern,
)


@pytest.mark.parametrize("date_string", [
    '2025-13-01',
    '205-12-01',
    '2025-00-01',
    '2025-1-01',
    '2025-s1-01',
    '2025-01-32',
    '2025-01-00',
])
def test_invalid_date_patterns(date_string):
    # assuming line breaks and trailing spaces are already stripped
    assert not date_pattern.match(date_string)


@pytest.mark.parametrize("date_string", [
    '2025-01-01',
    '2025-12-31',
    '2025-02-31',  # XXX todo: maybe we should catch this
])
def test_valid_date_patterns(date_string):
    # assuming line breaks and trailing spaces are already stripped
    assert date_pattern.match(date_string)
