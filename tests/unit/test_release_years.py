from tests.release_years import release_years


def test_release_years_keeps_ids_and_missing_years() -> None:
    releases = release_years({"12": 1999, "13": None})

    assert releases == {"12": 1999, "13": None}
