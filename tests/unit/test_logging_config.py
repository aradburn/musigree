from unittest.mock import patch, Mock

import pytest

from musigree.logging_config import (
    LOGGING_CONFIG,
    TEST_LOGGING_CONFIG,
    LOGGING_TRACE,
    setup_logging,
    shutdown_logging,
)


class TestLoggingConfig:
    """Test cases for the logging configuration module."""

    def test_logging_trace_constant(self) -> None:
        """Test that LOGGING_TRACE constant is defined."""
        assert isinstance(LOGGING_TRACE, bool)
        assert LOGGING_TRACE is False

    def test_logging_config_structure(self) -> None:
        """Test that LOGGING_CONFIG has the expected structure."""
        assert isinstance(LOGGING_CONFIG, dict)
        assert "version" in LOGGING_CONFIG
        assert "disable_existing_loggers" in LOGGING_CONFIG
        assert "formatters" in LOGGING_CONFIG
        assert "handlers" in LOGGING_CONFIG
        assert "loggers" in LOGGING_CONFIG

        # Check version
        assert LOGGING_CONFIG["version"] == 1
        assert LOGGING_CONFIG["disable_existing_loggers"] is False

    def test_logging_config_formatters(self) -> None:
        """Test that LOGGING_CONFIG has the expected formatters."""
        formatters = LOGGING_CONFIG["formatters"]
        assert "standard" in formatters
        assert "error" in formatters

        # Check standard formatter
        standard = formatters["standard"]
        assert "format" in standard
        assert "datefmt" in standard
        assert "%(asctime)s" in standard["format"]
        assert "%(levelname)s" in standard["format"]
        assert "%(name)s" in standard["format"]
        assert "%(message)s" in standard["format"]

    def test_logging_config_handlers(self) -> None:
        """Test that LOGGING_CONFIG has the expected handlers."""
        handlers = LOGGING_CONFIG["handlers"]
        assert "default" in handlers
        assert "console_handler" in handlers

        # Check default handler
        default = handlers["default"]
        assert default["level"] == "INFO"
        assert default["formatter"] == "standard"
        assert default["class"] == "logging.StreamHandler"

        # Check console handler
        console = handlers["console_handler"]
        assert console["level"] == "DEBUG"
        assert console["formatter"] == "standard"
        assert console["class"] == "logging.StreamHandler"

    def test_logging_config_loggers(self) -> None:
        """Test that LOGGING_CONFIG has the expected loggers."""
        loggers = LOGGING_CONFIG["loggers"]
        assert "" in loggers  # root logger
        assert "musigree" in loggers
        assert "__main__" in loggers

        # Check musigree logger
        musigree_logger = loggers["musigree"]
        assert "console_handler" in musigree_logger["handlers"]
        assert musigree_logger["level"] == "DEBUG"
        assert musigree_logger["propagate"] is False

    def test_test_logging_config_structure(self) -> None:
        """Test that TEST_LOGGING_CONFIG has the expected structure."""
        assert isinstance(TEST_LOGGING_CONFIG, dict)
        assert "version" in TEST_LOGGING_CONFIG
        assert "disable_existing_loggers" in TEST_LOGGING_CONFIG
        assert "formatters" in TEST_LOGGING_CONFIG
        assert "handlers" in TEST_LOGGING_CONFIG
        assert "loggers" in TEST_LOGGING_CONFIG

        # Check version
        assert TEST_LOGGING_CONFIG["version"] == 1
        assert TEST_LOGGING_CONFIG["disable_existing_loggers"] is False

    def test_test_logging_config_has_tests_logger(self) -> None:
        """Test that TEST_LOGGING_CONFIG includes a tests logger."""
        loggers = TEST_LOGGING_CONFIG["loggers"]
        assert "tests" in loggers

        tests_logger = loggers["tests"]
        assert "console_handler" in tests_logger["handlers"]
        assert tests_logger["level"] == "DEBUG"
        assert tests_logger["propagate"] is False

    @patch("logging.config.dictConfig")
    @patch("logging.getLogger")
    def test_setup_logging_production(self, mock_get_logger: Mock, mock_dict_config: Mock) -> None:
        """Test setup_logging with production config."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        setup_logging(is_testing=False)

        # Verify dictConfig was called with production config
        mock_dict_config.assert_called_once_with(LOGGING_CONFIG)

        # Verify logger info calls
        assert mock_logger.info.call_count == 2

    @patch("logging.config.dictConfig")
    @patch("logging.getLogger")
    def test_setup_logging_testing(self, mock_get_logger: Mock, mock_dict_config: Mock) -> None:
        """Test setup_logging with testing config."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        setup_logging(is_testing=True)

        # Verify dictConfig was called with test config
        mock_dict_config.assert_called_once_with(TEST_LOGGING_CONFIG)

        # Verify logger info calls
        assert mock_logger.info.call_count == 2

    @patch("logging.config.dictConfig")
    @patch("logging.getLogger")
    def test_setup_logging_default_is_production(
        self, mock_get_logger: Mock, mock_dict_config: Mock
    ) -> None:
        """Test that setup_logging defaults to production config."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        # Call without parameters
        setup_logging()

        # Should use production config by default
        mock_dict_config.assert_called_once_with(LOGGING_CONFIG)

    @patch("logging.shutdown")
    @patch("logging.getLogger")
    @patch("logging.root.manager.loggerDict", new={"test": Mock(), "another": Mock()})
    def test_shutdown_logging_with_loggers(
        self, mock_get_logger: Mock, mock_shutdown: Mock
    ) -> None:
        """Test shutdown_logging when loggers exist."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        shutdown_logging()

        # Verify logger info was called
        mock_logger.info.assert_called_once_with("Shutting down logging.")

        # Verify logging.shutdown was called
        mock_shutdown.assert_called_once()

    @patch("logging.shutdown")
    @patch("logging.getLogger")
    @patch("logging.root.manager.loggerDict", new={})
    def test_shutdown_logging_no_loggers(self, mock_get_logger: Mock, mock_shutdown: Mock) -> None:
        """Test shutdown_logging when no loggers exist."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        shutdown_logging()

        # Verify logger info was not called when no loggers
        mock_logger.info.assert_not_called()

        # Verify logging.shutdown was not called
        mock_shutdown.assert_not_called()

    def test_config_formatters_have_required_fields(self) -> None:
        """Test that formatters include required fields."""
        for config_name, config in [
            ("LOGGING_CONFIG", LOGGING_CONFIG),
            ("TEST_LOGGING_CONFIG", TEST_LOGGING_CONFIG),
        ]:
            formatters = config["formatters"]

            for formatter_name, formatter in formatters.items():
                assert "format" in formatter, f"{config_name}.{formatter_name} missing format"
                assert "datefmt" in formatter, f"{config_name}.{formatter_name} missing datefmt"

                # Check that format includes essential fields
                format_str = formatter["format"]
                assert "%(asctime)s" in format_str
                assert "%(levelname)s" in format_str
                assert "%(name)s" in format_str
                assert "%(message)s" in format_str

    def test_config_handlers_have_required_fields(self) -> None:
        """Test that handlers include required fields."""
        for config_name, config in [
            ("LOGGING_CONFIG", LOGGING_CONFIG),
            ("TEST_LOGGING_CONFIG", TEST_LOGGING_CONFIG),
        ]:
            handlers = config["handlers"]

            for handler_name, handler in handlers.items():
                assert "level" in handler, f"{config_name}.{handler_name} missing level"
                assert "formatter" in handler, f"{config_name}.{handler_name} missing formatter"
                assert "class" in handler, f"{config_name}.{handler_name} missing class"

                # Check that the formatter referenced exists
                formatter_name = handler["formatter"]
                assert formatter_name in config["formatters"], (
                    f"{config_name}.{handler_name} references unknown formatter {formatter_name}"
                )

    def test_config_loggers_have_required_fields(self) -> None:
        """Test that loggers include required fields."""
        for config_name, config in [
            ("LOGGING_CONFIG", LOGGING_CONFIG),
            ("TEST_LOGGING_CONFIG", TEST_LOGGING_CONFIG),
        ]:
            loggers = config["loggers"]

            for logger_name, logger_config in loggers.items():
                assert "handlers" in logger_config, f"{config_name}.{logger_name} missing handlers"
                assert "level" in logger_config, f"{config_name}.{logger_name} missing level"
                assert "propagate" in logger_config, (
                    f"{config_name}.{logger_name} missing propagate"
                )

                # Check that all referenced handlers exist
                for handler_name in logger_config["handlers"]:
                    assert handler_name in config["handlers"], (
                        f"{config_name}.{logger_name} references unknown handler {handler_name}"
                    )

    def test_musigree_logger_configuration(self) -> None:
        """Test specific configuration for musigree logger."""
        for config in [LOGGING_CONFIG, TEST_LOGGING_CONFIG]:
            musigree_logger = config["loggers"]["musigree"]
            assert musigree_logger["level"] == "DEBUG"
            assert musigree_logger["propagate"] is False
            assert "console_handler" in musigree_logger["handlers"]

    def test_root_logger_configuration(self) -> None:
        """Test specific configuration for root logger."""
        for config in [LOGGING_CONFIG, TEST_LOGGING_CONFIG]:
            root_logger = config["loggers"][""]
            assert root_logger["level"] == "WARNING"
            assert root_logger["propagate"] is False
            assert "default" in root_logger["handlers"]

    @patch("logging.config.dictConfig")
    def test_setup_logging_exception_handling(self, mock_dict_config: Mock) -> None:
        """Test that setup_logging handles exceptions gracefully."""
        # Make dictConfig raise an exception
        mock_dict_config.side_effect = Exception("Config error")

        # Should raise an exception due to config error
        with pytest.raises(Exception, match="Config error"):
            setup_logging()

    def test_config_consistency_between_prod_and_test(self) -> None:
        """Test that production and test configs are consistent where expected."""
        # Both should have the same formatters
        assert LOGGING_CONFIG["formatters"] == TEST_LOGGING_CONFIG["formatters"]

        # Both should have the same version and disable_existing_loggers
        assert LOGGING_CONFIG["version"] == TEST_LOGGING_CONFIG["version"]
        assert (
            LOGGING_CONFIG["disable_existing_loggers"]
            == TEST_LOGGING_CONFIG["disable_existing_loggers"]
        )

        # Both should have musigree and root loggers with same config
        for logger_name in ["", "musigree", "__main__"]:
            assert logger_name in LOGGING_CONFIG["loggers"]
            assert logger_name in TEST_LOGGING_CONFIG["loggers"]
            # Configuration should be the same for these loggers
            assert (
                LOGGING_CONFIG["loggers"][logger_name]
                == TEST_LOGGING_CONFIG["loggers"][logger_name]
            )
