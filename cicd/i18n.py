"""Internationalization support for the CLI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_LANG_DIR = Path(__file__).parent / "lang"
_SUPPORTED = ("en", "pl", "de", "fr", "es", "nl", "cs")
_DEFAULT = "en"

_strings: dict[str, Any] = {}
_current_lang: str = _DEFAULT


def supported_languages() -> tuple[str, ...]:
    """Return tuple of supported language codes."""
    return _SUPPORTED


def current_language() -> str:
    """Return current language code."""
    return _current_lang


def load(lang: str = _DEFAULT) -> None:
    """Load translation strings for the given language."""
    global _strings, _current_lang
    if lang not in _SUPPORTED:
        lang = _DEFAULT
    path = _LANG_DIR / f"{lang}.json"
    if not path.exists():
        path = _LANG_DIR / f"{_DEFAULT}.json"
        lang = _DEFAULT
    with open(path, encoding="utf-8") as f:
        _strings = json.load(f)
    _current_lang = lang


def t(key: str, **kwargs: Any) -> str:
    """Get a translated string by dot-separated key path.
    
    Example: t("init.success", version="16.0") -> "Successfully connected to GitLab 16.0!"
    """
    parts = key.split(".")
    node: Any = _strings
    for part in parts:
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return key  # fallback: return the key itself
    if isinstance(node, str):
        if kwargs:
            try:
                return node.format(**kwargs)
            except (KeyError, IndexError):
                return node
        return node
    return key


def init_from_config(config_loader) -> None:
    """Initialize language from config. Call after config module is available."""
    try:
        cfg = config_loader()
        lang = cfg.get("language", _DEFAULT)
        load(lang)
    except Exception:
        load(_DEFAULT)