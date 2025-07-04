from unittest.mock import Mock, patch

import pytest
from sqlalchemy import Result
from musigree.exceptions import NotFoundError
from musigree.runtime.runtime_database.country_repository import CountryRepository
from musigree.runtime.runtime_database.country_table import CountryTable
from musigree.runtime.runtime_domain.country import Country


class TestCountryRepository:
    """Unit tests for CountryRepository class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.repository = CountryRepository()

    def test_schema_class(self):
        """Test that schema_class is correctly set."""
        # GIVEN/WHEN/THEN
        assert self.repository.schema_class == CountryTable

    @pytest.mark.asyncio
    @patch.object(CountryRepository, '_all')
    async def test_all(self, mock_all):
        """Test retrieving all countries."""
        # GIVEN
        mock_instance1 = Mock()
        mock_instance1.id = 1
        mock_instance1.country_name = "United States"
        
        mock_instance2 = Mock()
        mock_instance2.id = 2
        mock_instance2.country_name = "United Kingdom"
        
        # Create an async generator for the mock
        async def async_generator():
            for item in [mock_instance1, mock_instance2]:
                yield item
        
        mock_all.return_value = async_generator()
        
        with patch.object(Country, 'model_validate') as mock_validate:
            mock_validate.side_effect = [
                Country(id=1, country_name="United States"),
                Country(id=2, country_name="United Kingdom")
            ]
            
            # WHEN
            result = []
            async for country in self.repository.all():
                result.append(country)
            
            # THEN
            assert len(result) == 2
            assert isinstance(result[0], Country)
            assert isinstance(result[1], Country)
            assert result[0].country_name == "United States"
            assert result[1].country_name == "United Kingdom"

    @pytest.mark.asyncio
    @patch.object(CountryRepository, 'execute')
    async def test_get_success(self, mock_execute):
        """Test successfully retrieving a country by ID."""
        # GIVEN
        country_id = 1
        mock_instance = Mock()
        mock_instance.id = country_id
        mock_instance.country_name = "United States"
        
        mock_result = Mock(spec=Result)
        mock_scalars = Mock()
        mock_scalars.one_or_none.return_value = mock_instance
        mock_result.scalars.return_value = mock_scalars
        mock_execute.return_value = mock_result
        
        with patch.object(Country, 'model_validate') as mock_validate:
            expected_country = Country(id=country_id, country_name="United States")
            mock_validate.return_value = expected_country
            
            # WHEN
            result = await self.repository.get_by_id(country_id)
            
            # THEN
            assert result == expected_country
            mock_validate.assert_called_once_with(mock_instance)

    @pytest.mark.asyncio
    @patch.object(CountryRepository, 'execute')
    async def test_get_not_found(self, mock_execute):
        """Test retrieving a country by ID when not found."""
        # GIVEN
        country_id = 999
        
        mock_result = Mock(spec=Result)
        mock_scalars = Mock()
        mock_scalars.one_or_none.return_value = None
        mock_result.scalars.return_value = mock_scalars
        mock_execute.return_value = mock_result
        
        # WHEN/THEN
        with pytest.raises(NotFoundError):
            await self.repository.get_by_id(country_id)

    @pytest.mark.asyncio
    @patch.object(CountryRepository, 'execute')
    async def test_get_by_name_success(self, mock_execute):
        """Test successfully retrieving a country by name."""
        # GIVEN
        country_name = "United States"
        mock_instance = Mock()
        mock_instance.id = 1
        mock_instance.country_name = country_name
        
        mock_result = Mock(spec=Result)
        mock_scalars = Mock()
        mock_scalars.one_or_none.return_value = mock_instance
        mock_result.scalars.return_value = mock_scalars
        mock_execute.return_value = mock_result
        
        with patch.object(Country, 'model_validate') as mock_validate:
            expected_country = Country(id=1, country_name=country_name)
            mock_validate.return_value = expected_country
            
            # WHEN
            result = await self.repository.get_by_name(country_name)
            
            # THEN
            assert result == expected_country
            mock_validate.assert_called_once_with(mock_instance)

    @pytest.mark.asyncio
    @patch.object(CountryRepository, 'execute')
    async def test_get_by_name_not_found(self, mock_execute):
        """Test retrieving a country by name when not found."""
        # GIVEN
        country_name = "NonexistentCountry"
        
        mock_result = Mock(spec=Result)
        mock_scalars = Mock()
        mock_scalars.one_or_none.return_value = None
        mock_result.scalars.return_value = mock_scalars
        mock_execute.return_value = mock_result
        
        # WHEN/THEN
        with pytest.raises(NotFoundError):
            await self.repository.get_by_name(country_name)

    @pytest.mark.asyncio
    @patch.object(CountryRepository, '_save')
    async def test_create(self, mock_save):
        """Test creating a new country."""
        # GIVEN
        country = Country(id=1, country_name="United States")
        mock_instance = Mock()
        mock_instance.id = 1
        mock_instance.country_name = "United States"
        mock_save.return_value = mock_instance
        
        with patch.object(Country, 'model_validate') as mock_validate:
            expected_country = Country(id=1, country_name="United States")
            mock_validate.return_value = expected_country
            
            # WHEN
            result = await self.repository.create(country)
            
            # THEN
            assert result == expected_country
            mock_save.assert_called_once_with(country.model_dump())
            mock_validate.assert_called_once_with(mock_instance) 