"""
Unit tests for musigree.app.fastapi_permissions_policy module.
"""
from collections.abc import MutableMapping
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
# noinspection PyPackageRequirements
from starlette.types import Send

from musigree.app.fastapi_permissions_policy import PermissionsPolicy, PermissionsPolicyOptions


class TestPermissionsPolicy:
    """Test cases for PermissionsPolicy."""

    def test_init_option_none_raises_syntax_error(self) -> None:
        """Test that Option=None raises SyntaxError."""
        app = MagicMock()
        with pytest.raises(SyntaxError, match="Option cannot be empty"):
            PermissionsPolicy(app, Option=None)

    def test_init_option_empty_dict_raises_syntax_error(self) -> None:
        """Test that empty Option dict raises SyntaxError."""
        app = MagicMock()
        with pytest.raises(SyntaxError, match="Option cannot be empty"):
            options: PermissionsPolicyOptions = {}
            PermissionsPolicy(app, Option=options)

    def test_init_valid_option_builds_policy_string(self) -> None:
        """Test valid Option builds PolicyString (single feature, self)."""
        app = MagicMock()
        with pytest.warns(SyntaxWarning):
            options: PermissionsPolicyOptions = {"camera": ["self"]}
            policy = PermissionsPolicy(app, Option=options)
        assert "camera" in policy.PolicyString

    def test_init_valid_option_star(self) -> None:
        """Test valid Option with wildcard *."""
        app = MagicMock()
        with pytest.warns(SyntaxWarning):
            options: PermissionsPolicyOptions = {"camera": ["*"]}
            policy = PermissionsPolicy(app, Option=options)
        assert policy.PolicyString == "camera=*, "

    def test_init_invalid_policy_key_raises_syntax_error(self) -> None:
        """Test that unknown policy key raises SyntaxError."""
        app = MagicMock()
        with pytest.warns(SyntaxWarning):
            with pytest.raises(SyntaxError, match="does not exist"):
                # noinspection Mypy
                options: PermissionsPolicyOptions = {"invalid-feature": ["self"]}  # type: ignore[typeddict-unknown-key]
                PermissionsPolicy(app, Option=options)

    def test_init_wildcard_with_others_raises_syntax_error(self) -> None:
        """Test that * with other values raises SyntaxError."""
        app = MagicMock()
        with pytest.warns(SyntaxWarning):
            with pytest.raises(SyntaxError, match="Cannot use wildcard"):
                options: PermissionsPolicyOptions = {"camera": ["*", "self"]}
                PermissionsPolicy(app, Option=options)

    def test_init_quoted_url_value(self) -> None:
        """Test Option with quoted URL allowlist."""
        app = MagicMock()
        with pytest.warns(SyntaxWarning):
            options: PermissionsPolicyOptions = {"camera": ['"https://example.com"']}
            policy = PermissionsPolicy(app, Option=options)
        assert "camera" in policy.PolicyString
        assert "https://example.com" in policy.PolicyString

    def test_init_invalid_allowlist_item_raises_syntax_error(self) -> None:
        """Test unquoted URL raises SyntaxError."""
        app = MagicMock()
        with pytest.warns(SyntaxWarning):
            with pytest.raises(SyntaxError, match="Invalid allowlist item"):
                options: PermissionsPolicyOptions = {"camera": ["https://example.com"]}
                PermissionsPolicy(app, Option=options)

    @pytest.mark.asyncio
    async def test_call_http_scope_sets_permissions_policy_header(self) -> None:
        """Test __call__ with http scope adds Permissions-Policy header to response."""
        app = MagicMock()
        with pytest.warns(SyntaxWarning):
            options: PermissionsPolicyOptions = {"camera": ["self"]}
            policy = PermissionsPolicy(app, Option=options)
        scope = {"type": "http"}
        receive = AsyncMock()
        sent_messages: list[MutableMapping[str, Any]] = []

        async def capture_send(message: MutableMapping[str, Any]) -> None:
            sent_messages.append(message)
            if message.get("type") == "http.response.start":
                _headers = message.get("headers", [])
                header_keys = [k.decode().lower() if isinstance(k, bytes) else k.lower() for k, _ in _headers]
                assert "permissions-policy" in header_keys

        send: Send = capture_send

        async def app_side_effect(_scope: dict[str, Any], _rec: object, _send: Send) -> None:
            await _send({"type": "http.response.start", "status": 200, "headers": []})
            await _send({"type": "http.response.body", "body": b"ok"})

        app.side_effect = app_side_effect

        await policy(scope, receive, send)

        app.assert_called_once()
        assert len(sent_messages) >= 2
        start_msg = next((m for m in sent_messages if m.get("type") == "http.response.start"), None)
        assert start_msg is not None
        headers = start_msg.get("headers", [])
        assert any(
            (k.decode().lower() if isinstance(k, bytes) else k.lower()) == "permissions-policy"
            for k, _ in headers
        )

    @pytest.mark.asyncio
    async def test_call_non_http_scope_passes_through(self) -> None:
        """Test __call__ with non-http scope passes to app without wrapping send."""
        app = AsyncMock()
        with pytest.warns(SyntaxWarning):
            options: PermissionsPolicyOptions = {"camera": ["self"]}
            policy = PermissionsPolicy(app, Option=options)
        scope = {"type": "websocket"}
        receive = MagicMock()
        send = MagicMock()

        await policy(scope, receive, send)

        app.assert_called_once_with(scope, receive, send)
