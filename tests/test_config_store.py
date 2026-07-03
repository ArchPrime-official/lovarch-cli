"""Unit tests for the user config store + `lovarch config` command."""
from __future__ import annotations

import os
import stat

import pytest

from lovarch_cli import config_store


def test_set_get_roundtrip(tmp_path):
    config_store.set_value("language", "pt", home=tmp_path)
    assert config_store.get_value("language", home=tmp_path) == "pt"


def test_unknown_key_rejected(tmp_path):
    with pytest.raises(config_store.ConfigError):
        config_store.set_value("nope", "x", home=tmp_path)


def test_invalid_language_rejected(tmp_path):
    with pytest.raises(config_store.ConfigError):
        config_store.set_value("language", "de", home=tmp_path)


def test_empty_value_rejected(tmp_path):
    with pytest.raises(config_store.ConfigError):
        config_store.set_value("storage_path", "", home=tmp_path)


def test_unset(tmp_path):
    config_store.set_value("mapbox_token", "tok123456", home=tmp_path)
    assert config_store.unset_value("mapbox_token", home=tmp_path) is True
    assert config_store.get_value("mapbox_token", home=tmp_path) is None
    # unset on a missing key returns False (no error)
    assert config_store.unset_value("mapbox_token", home=tmp_path) is False


def test_secret_masked(tmp_path):
    config_store.set_value("openai_key", "sk-abcdefgh1234", home=tmp_path)
    masked = config_store.mask("openai_key", config_store.get_value("openai_key", home=tmp_path))
    assert masked.endswith("1234")
    assert "sk-abcd" not in masked
    assert masked.startswith("•")


def test_non_secret_not_masked(tmp_path):
    assert config_store.mask("language", "it") == "it"


def test_config_file_is_private(tmp_path):
    config_store.set_value("openai_key", "sk-secret-value", home=tmp_path)
    path = config_store.config_path(home=tmp_path)
    mode = stat.S_IMODE(os.stat(path).st_mode)
    # owner-only rw (0600) — no group/other bits
    assert mode & (stat.S_IRWXG | stat.S_IRWXO) == 0


def test_display_items_covers_all_keys(tmp_path):
    items = config_store.display_items(home=tmp_path)
    keys = {k for k, _, _ in items}
    assert keys == set(config_store.CONFIG_KEYS)


def test_corrupt_config_returns_empty(tmp_path):
    path = config_store.config_path(home=tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{ not json")
    assert config_store.load_config(home=tmp_path) == {}
