from trackie.conf import date_pattern


def test_check_format_invalid_date_month_13():
    assert not date_pattern.match('2025-13-01\n')


def test_check_format_invalid_date_month_two_digits():
    assert not date_pattern.match('205-12-01\n')


def test_check_format_invalid_date_month_00():
    assert not date_pattern.match('2025-00-01')


def test_check_format_invalid_date_month_1():
    assert not date_pattern.match('2025-1-01')


def test_check_format_invalid_date_month_contains_letter():
    assert not date_pattern.match('2025-s1-01')


def test_check_format_valid_date():
    assert date_pattern.match('2025-01-01\n')
