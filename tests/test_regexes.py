import re

import pytest

from trackie.conf import (
    date_pattern,
    spaces_description_pattern,
    spaces_duration_pattern,
)


# date patterns

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


# description pattern with spaces

@pytest.mark.parametrize("description_line", [
    " " * 4 + "descriptive text",
])
def test_valid_space_description_lines(description_line):
    assert re.compile(
        spaces_description_pattern.format(' ' * 4)).match(description_line)


@pytest.mark.parametrize("description_line", [
    " " * 7 + "descriptive text",
])
def test_invalid_space_description_lines(description_line):
    assert not re.compile(
        spaces_description_pattern.format(' ' * 8)).match(description_line)


# duration pattern with spaces

@pytest.mark.parametrize("duration_line", [
    " " * 8 + "1",
])
def test_valid_space_duration_lines(duration_line):
    assert re.compile(
        spaces_duration_pattern.format(' ' * 8)).match(duration_line)


@pytest.mark.parametrize("duration_line", [
    " " * 9 + "789",
])
def test_invalid_space_duration_lines(duration_line):
    assert not re.compile(
        spaces_duration_pattern.format(' ' * 8)).match(duration_line)
