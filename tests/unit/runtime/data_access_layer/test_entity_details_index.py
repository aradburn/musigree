from unittest.mock import patch, call

from musigree.runtime.data_access_layer.entity_details_index import EntityDetailsIndex


class TestEntityDetailsIndex:
    """Test cases for EntityDetailsIndex class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.index = EntityDetailsIndex()

    def test_init(self):
        """Test that EntityDetailsIndex initializes with empty structures."""
        assert self.index.entity_countries == {}
        assert self.index.countries_list == []
        assert self.index.entity_genres == {}
        assert self.index.genres_list == []
        assert self.index.entity_styles == {}
        assert self.index.styles_list == []

    def test_split_country_simple(self):
        """Test split_country with simple country names."""
        result = EntityDetailsIndex.split_country("USA")
        assert result == ["USA"]

    def test_split_country_with_delimiters(self):
        """Test split_country with various delimiters."""
        result = EntityDetailsIndex.split_country("USA & Canada")
        assert result == ["USA ", " Canada"]

        result = EntityDetailsIndex.split_country("UK/Ireland")
        assert result == ["UK", "Ireland"]

        result = EntityDetailsIndex.split_country("France,Germany")
        assert result == ["France", "Germany"]

    def test_split_country_democratic_republic(self):
        """Test split_country with 'Democratic Republic of the' pattern."""
        result = EntityDetailsIndex.split_country("Congo, Democratic Republic of the")
        assert result == ["Democratic Republic of the Congo"]

    def test_split_country_republic_of_the(self):
        """Test split_country with 'Republic of the' pattern."""
        result = EntityDetailsIndex.split_country("Congo, Republic of the")
        assert result == ["Republic of the Congo"]

    def test_split_country_republic_of(self):
        """Test split_country with 'Republic of' pattern."""
        result = EntityDetailsIndex.split_country("Macedonia, Republic of")
        assert result == ["Republic of Macedonia"]

    def test_split_country_isle_of(self):
        """Test split_country with 'Isle of' pattern."""
        result = EntityDetailsIndex.split_country("Man, Isle of")
        assert result == ["Isle of Man"]

    def test_split_country_the(self):
        """Test split_country with 'The' pattern."""
        result = EntityDetailsIndex.split_country("Bahamas, The")
        assert result == ["The Bahamas"]

    def test_index_country_single(self):
        """Test indexing a single country."""
        self.index.index_country(1, "USA")
        
        assert 1 in self.index.entity_countries
        assert self.index.entity_countries[1] == [0]
        assert self.index.countries_list == ["USA"]

    def test_index_country_multiple_entities(self):
        """Test indexing countries for multiple entities."""
        self.index.index_country(1, "USA")
        self.index.index_country(2, "Canada")
        
        assert self.index.entity_countries[1] == [0]
        assert self.index.entity_countries[2] == [1]
        assert self.index.countries_list == ["USA", "Canada"]

    def test_index_country_same_country_multiple_entities(self):
        """Test indexing same country for multiple entities."""
        self.index.index_country(1, "USA")
        self.index.index_country(2, "USA")
        
        assert self.index.entity_countries[1] == [0]
        assert self.index.entity_countries[2] == [0]
        assert self.index.countries_list == ["USA"]

    def test_index_country_multiple_countries_single_entity(self):
        """Test indexing multiple countries for single entity."""
        self.index.index_country(1, "USA & Canada")
        
        assert self.index.entity_countries[1] == [0, 1]
        assert self.index.countries_list == ["USA", "Canada"]

    def test_index_country_empty_tokens(self):
        """Test indexing country with empty tokens after splitting."""
        self.index.index_country(1, "USA & & Canada")
        
        assert self.index.entity_countries[1] == [0, 1]
        assert self.index.countries_list == ["USA", "Canada"]

    def test_index_country_duplicate_prevention(self):
        """Test that duplicate countries for same entity are prevented."""
        self.index.index_country(1, "USA")
        self.index.index_country(1, "USA")
        
        assert self.index.entity_countries[1] == [0]
        assert self.index.countries_list == ["USA"]

    def test_index_genre_single(self):
        """Test indexing a single genre."""
        self.index.index_genre(1, "Rock")
        
        assert 1 in self.index.entity_genres
        assert self.index.entity_genres[1] == [0]
        assert self.index.genres_list == ["Rock"]

    def test_index_genre_multiple_entities(self):
        """Test indexing genres for multiple entities."""
        self.index.index_genre(1, "Rock")
        self.index.index_genre(2, "Jazz")
        
        assert self.index.entity_genres[1] == [0]
        assert self.index.entity_genres[2] == [1]
        assert self.index.genres_list == ["Rock", "Jazz"]

    def test_index_genre_empty_string(self):
        """Test indexing genre with empty string."""
        self.index.index_genre(1, "")
        
        assert 1 not in self.index.entity_genres
        assert self.index.genres_list == []

    def test_index_genre_empty_token(self):
        """Test indexing genre that results in empty token after splitting."""
        self.index.index_genre(1, "Rock & & Jazz")
        
        assert self.index.entity_genres[1] == [0, 1]
        assert self.index.genres_list == ["Rock", "Jazz"]

    def test_index_style_single(self):
        """Test indexing a single style."""
        self.index.index_style(1, "Alternative")
        
        assert 1 in self.index.entity_styles
        assert self.index.entity_styles[1] == [0]
        assert self.index.styles_list == ["Alternative"]

    def test_index_style_multiple_entities(self):
        """Test indexing styles for multiple entities."""
        self.index.index_style(1, "Alternative")
        self.index.index_style(2, "Punk")
        
        assert self.index.entity_styles[1] == [0]
        assert self.index.entity_styles[2] == [1]
        assert self.index.styles_list == ["Alternative", "Punk"]

    def test_index_style_empty_string(self):
        """Test indexing style with empty string."""
        self.index.index_style(1, "")
        
        assert 1 not in self.index.entity_styles
        assert self.index.styles_list == []

    def test_get_countries_for_id_existing(self):
        """Test getting countries for existing entity ID."""
        self.index.index_country(1, "USA & Canada")
        result = self.index.get_countries_for_id(1)
        assert result == "Canada,USA"

    def test_get_countries_for_id_nonexistent(self):
        """Test getting countries for non-existent entity ID."""
        result = self.index.get_countries_for_id(999)
        assert result is None

    def test_get_countries_for_id_single(self):
        """Test getting single country for entity ID."""
        self.index.index_country(1, "USA")
        result = self.index.get_countries_for_id(1)
        assert result == "USA"

    def test_get_genres_for_id_existing(self):
        """Test getting genres for existing entity ID."""
        self.index.index_genre(1, "Rock & Jazz")
        result = self.index.get_genres_for_id(1)
        assert result == "Jazz,Rock"

    def test_get_genres_for_id_nonexistent(self):
        """Test getting genres for non-existent entity ID."""
        result = self.index.get_genres_for_id(999)
        assert result is None

    def test_get_styles_for_id_existing(self):
        """Test getting styles for existing entity ID."""
        self.index.index_style(1, "Alternative & Punk")
        result = self.index.get_styles_for_id(1)
        assert result == "Alternative,Punk"

    def test_get_styles_for_id_nonexistent(self):
        """Test getting styles for non-existent entity ID."""
        result = self.index.get_styles_for_id(999)
        assert result is None

    @patch('musigree.runtime.data_access_layer.entity_details_index.calculate_size')
    @patch('musigree.runtime.data_access_layer.entity_details_index.log')
    def test_print_sizes(self, mock_log, mock_calculate_size):
        """Test print_sizes method logs correct information."""
        # Setup test data
        self.index.index_country(1, "USA")
        self.index.index_genre(1, "Rock")
        self.index.index_style(1, "Alternative")
        
        # Mock calculate_size to return predictable values
        mock_calculate_size.side_effect = [100, 200, 300]
        
        self.index.print_sizes()
        
        # Verify logging calls
        expected_calls = [
            call.debug("number of entity_countries : 1"),
            call.debug("size of entity_countries   : 100"),
            call.debug("number of countries        : 1"),
            call.debug("number of entity_genres    : 1"),
            call.debug("size of entity_genres      : 200"),
            call.debug("number of genres           : 1"),
            call.debug("number of entity_styles    : 1"),
            call.debug("size of entity_styles      : 300"),
            call.debug("number of styles           : 1"),
        ]
        
        mock_log.debug.assert_has_calls(expected_calls)
        assert mock_calculate_size.call_count == 3

    @patch('musigree.runtime.data_access_layer.entity_details_index.log')
    def test_print_details(self, mock_log):
        """Test print_details method logs correct information."""
        # Setup test data
        self.index.index_country(1, "USA")
        self.index.index_genre(1, "Rock")
        self.index.index_style(1, "Alternative")
        
        self.index.print_details()
        
        # Verify that log.debug was called with expected content
        mock_log.debug.assert_any_call("")
        mock_log.debug.assert_any_call("Countries")
        mock_log.debug.assert_any_call("=========")
        mock_log.debug.assert_any_call("USA")
        mock_log.debug.assert_any_call("")
        mock_log.debug.assert_any_call("Genres")
        mock_log.debug.assert_any_call("Rock")
        mock_log.debug.assert_any_call("")
        mock_log.debug.assert_any_call("Styles")
        mock_log.debug.assert_any_call("Alternative")

    def test_comprehensive_workflow(self):
        """Test a comprehensive workflow with multiple operations."""
        # Index various data
        self.index.index_country(1, "USA & Canada")
        self.index.index_country(2, "Germany")
        self.index.index_genre(1, "Rock & Jazz")
        self.index.index_genre(2, "Classical")
        self.index.index_style(1, "Alternative")
        self.index.index_style(2, "Orchestral & Chamber")
        
        # Verify data structure
        assert len(self.index.entity_countries) == 2
        assert len(self.index.countries_list) == 3  # USA, Canada, Germany
        assert len(self.index.entity_genres) == 2
        assert len(self.index.genres_list) == 3  # Rock, Jazz, Classical
        assert len(self.index.entity_styles) == 2
        assert len(self.index.styles_list) == 3  # Alternative, Orchestral, Chamber
        
        # Test retrieval
        assert self.index.get_countries_for_id(1) == "Canada,USA"
        assert self.index.get_countries_for_id(2) == "Germany"
        assert self.index.get_genres_for_id(1) == "Jazz,Rock"
        assert self.index.get_genres_for_id(2) == "Classical"
        assert self.index.get_styles_for_id(1) == "Alternative"
        assert self.index.get_styles_for_id(2) == "Chamber,Orchestral"

    def test_whitespace_handling(self):
        """Test proper handling of whitespace in tokens."""
        self.index.index_country(1, " USA  &  Canada ")
        self.index.index_genre(1, " Rock  /  Jazz ")
        self.index.index_style(1, " Alternative  ,  Punk ")
        
        assert self.index.countries_list == ["USA", "Canada"]
        assert self.index.genres_list == ["Rock", "Jazz"]
        assert self.index.styles_list == ["Alternative", "Punk"]

    # def test_special_country_cases_with_delimiters(self):
    #     """Test special country cases combined with delimiters."""
    #     self.index.index_country(1, "Congo, Democratic Republic of the & Congo, Republic of the")
    #
    #     assert self.index.countries_list == ["Democratic Republic of the Congo", "Republic of the Congo"]
    #     assert self.index.get_countries_for_id(1) == "Democratic Republic of the Congo,Republic of the Congo"

    def test_edge_case_empty_input(self):
        """Test edge cases with empty or whitespace-only input."""
        self.index.index_country(1, "   ")
        self.index.index_genre(1, "")
        self.index.index_style(1, " , , ")
        
        # Should not create any entries for empty inputs
        assert 1 not in self.index.entity_countries
        assert 1 not in self.index.entity_genres
        assert 1 not in self.index.entity_styles
        assert self.index.countries_list == []
        assert self.index.genres_list == []
        assert self.index.styles_list == [] 