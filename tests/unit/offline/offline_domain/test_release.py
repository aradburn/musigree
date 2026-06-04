"""Unit tests for offline_domain Release model."""

from datetime import date

from musigree.offline.offline_domain.release import Release


class TestRelease:
    """Test cases for Release class."""

    def test_release_init(self) -> None:
        """Test Release initialization."""
        release = Release(
            release_id=1,
            title="Test Release",
        )
        assert release.release_id == 1
        assert release.title == "Test Release"
        assert release.artists is None
        assert release.country is None
        assert release.release_date is None

    def test_release_init_with_optional_fields(self) -> None:
        """Test Release initialization with optional fields."""
        release = Release(
            release_id=2,
            title="Another Release",
            country="US",
            release_date=date(2020, 1, 15),
            genres=["Jazz"],
        )
        assert release.country == "US"
        assert release.release_date == date(2020, 1, 15)
        assert release.genres == ["Jazz"]

    def test_to_domain_returns_self(self) -> None:
        """Test to_domain returns the instance (domain and db are same)."""
        release = Release(release_id=1, title="Test")
        result = release.to_domain()
        assert result is release

    def test_to_db_returns_self(self) -> None:
        """Test to_db returns the instance (domain and db are same)."""
        release = Release(release_id=1, title="Test")
        result = release.to_db()
        assert result is release
