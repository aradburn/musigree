import datetime

from musigree.offline.loader.parser_utils import ParserUtils


class TestBootstrapperElementToDatetime:
    def test_1(self) -> None:
        date_string = "1989-06-23"
        date = ParserUtils.parse_release_date(date_string)
        assert date == datetime.datetime(1989, 6, 23)

    def test_2(self) -> None:
        date_string = "2015-06-31"
        date = ParserUtils.parse_release_date(date_string)
        assert date == datetime.datetime(2015, 7, 1)

    def test_3(self) -> None:
        date_string = "2014-06-00"
        date = ParserUtils.parse_release_date(date_string)
        assert date == datetime.datetime(2014, 6, 1)

    def test_4(self) -> None:
        date_string = "2013-00-00"
        date = ParserUtils.parse_release_date(date_string)
        assert date == datetime.datetime(2013, 1, 1)

    def test_5(self) -> None:
        date_string = "2001"
        date = ParserUtils.parse_release_date(date_string)
        assert date == datetime.datetime(2001, 1, 1, 0, 0)

    def test_6(self) -> None:
        date_string = "1971"
        date = ParserUtils.parse_release_date(date_string)
        assert date == datetime.datetime(1971, 1, 1, 0, 0)

    def test_7(self) -> None:
        date_string = "?"
        date = ParserUtils.parse_release_date(date_string)
        assert date is None

    def test_8(self) -> None:
        date_string = "????"
        date = ParserUtils.parse_release_date(date_string)
        assert date is None

    def test_9(self) -> None:
        date_string = "None"
        date = ParserUtils.parse_release_date(date_string)
        assert date is None

    def test_10(self) -> None:
        date_string = ""
        date = ParserUtils.parse_release_date(date_string)
        assert date is None

    def test_11(self) -> None:
        date_string = ""
        date = ParserUtils.parse_release_date(date_string)
        assert date is None
