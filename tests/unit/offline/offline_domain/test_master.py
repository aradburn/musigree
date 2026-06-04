"""Unit tests for offline_domain Master model."""

from musigree.offline.offline_domain.master import Master


class TestMaster:
    """Test cases for Master class."""

    def test_master_init(self) -> None:
        """Test Master initialization."""
        master = Master(
            master_id=1,
            title="Test Master",
            year=2020,
            main_release="12345",
            data_quality="high",
        )
        assert master.master_id == 1
        assert master.title == "Test Master"
        assert master.year == 2020
        assert master.main_release == "12345"
        assert master.data_quality == "high"
        assert master.artists is None
        assert master.genres is None
        assert master.styles is None
        assert master.videos is None
        assert master.images is None

    def test_master_init_with_optional_fields(self) -> None:
        """Test Master initialization with optional lists."""
        master = Master(
            master_id=2,
            title="Another Master",
            year=2019,
            main_release="67890",
            data_quality="medium",
            artists=[{"id": 1, "name": "Artist"}],
            genres=["Rock"],
            styles=["Alternative"],
        )
        assert master.artists == [{"id": 1, "name": "Artist"}]
        assert master.genres == ["Rock"]
        assert master.styles == ["Alternative"]

    def test_to_domain_returns_self(self) -> None:
        """Test to_domain returns the instance (domain and db are same)."""
        master = Master(
            master_id=1,
            title="Test",
            year=2020,
            main_release="1",
            data_quality="high",
        )
        result = master.to_domain()
        assert result is master

    def test_to_db_returns_self(self) -> None:
        """Test to_db returns the instance (domain and db are same)."""
        master = Master(
            master_id=1,
            title="Test",
            year=2020,
            main_release="1",
            data_quality="high",
        )
        result = master.to_db()
        assert result is master
