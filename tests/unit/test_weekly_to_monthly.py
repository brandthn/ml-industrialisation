from app import week_to_months


def test_week_fully_within_one_month():
    # Week 202002 = Jan 6-12 2020, all in January
    result = week_to_months(202002, 100)
    assert result == [(202001, 100)]


def test_week_spanning_december_january():
    # Dec 30 2019 - Jan 5 2020 ; 2 days in December, 5 days in January
    result = week_to_months(202001, 70)
    assert result == [(201912, 20.0), (202001, 50.0)]


def test_week_spanning_january_february():
    # Jan 27 - Feb 2 2020
    # 5 days in January, 2 days in February
    result = week_to_months(202005, 70)
    assert result == [(202001, 50.0), (202002, 20.0)]


def test_week_spanning_february_march_leap_year():
    # 6 days in February (Feb 24-29), 1 day in March (Mar 1)
    result = week_to_months(202009, 70)
    assert result == [(202002, 60.0), (202003, 10.0)]
