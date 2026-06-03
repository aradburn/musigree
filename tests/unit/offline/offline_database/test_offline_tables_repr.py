"""Unit tests for offline_database table __repr__ methods."""

from musigree.library.fields.entity_type import EntityType
from musigree.offline.offline_database.entity_table import EntityTable
from musigree.offline.offline_database.master_table import MasterTable


class TestMasterTableRepr:
    """Test MasterTable.__repr__."""

    def test_repr_returns_normalized_dict_string(self) -> None:
        """Test __repr__ returns a string from normalize_dict(table2dict(self))."""
        row = MasterTable(
            master_id=1,
            title="Test Master",
            year=2020,
            main_release="12345",
            data_quality="high",
            artists=None,
            genres=None,
            styles=None,
            videos=None,
            images=None,
        )
        result = row.__repr__()
        assert isinstance(result, str)
        assert "master_id" in result or "1" in result
        assert "Test Master" in result


class TestEntityTableRepr:
    """Test EntityTable.__repr__."""

    def test_repr_returns_normalized_dict_string(self) -> None:
        """Test __repr__ returns a string from normalize_dict(table2dict(self))."""
        row = EntityTable(
            id=1,
            entity_id=100,
            entity_type=EntityType.ARTIST,
            entity_name="Test Artist",
            relation_counts={},
            entity_metadata={},
            entities={},
            search_content="test content",
        )
        result = row.__repr__()
        assert isinstance(result, str)
        assert "entity_id" in result or "100" in result
        assert "Test Artist" in result
