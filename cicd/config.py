"""Configuration management - stores GitLab URL, token, and tracked repos.

Security measures:
- Config file permissions are set to 0600 (owner read/write only)
- API token is obfuscated with base64 to prevent casual reading
- File permission warnings on load
"""

from __future__ import annotations

import base64
import json
import os
import platform
import stat
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "cicd"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG: dict = {
    "gitlab_url": "",
    "api_token": "",
    "repos": [],
    "language": "en",
}


def _ensure_dir() -> None:
    """Create config directory with restricted permissions."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if platform.system() != "Windows":
        os.chmod(CONFIG_DIR, 0o700)


def _set_file_permissions(path: Path) -> None:
    """Restrict file permissions to owner only (unix)."""
    if platform.system() != "Windows":
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)  # 0o600


def _check_permissions(path: Path) -> bool:
    """Check if file permissions are secure. Returns True if OK."""
    if platform.system() == "Windows":
        return True
    if not path.exists():
        return True
    mode = path.stat().st_mode
    # Check that group and others have no access
    if mode & (stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP |
               stat.S_IROTH | stat.S_IWOTH | stat.S_IXOTH):
        return False
    return True


def _encode_token(token: str) -> str:
    """Obfuscate token for storage (base64)."""
    if not token:
        return ""
    return base64.b64encode(token.encode("utf-8")).decode("ascii")


def _decode_token(encoded: str) -> str:
    """De-obfuscate token from storage."""
    if not encoded:
        return ""
    try:
        return base64.b64decode(encoded.encode("ascii")).decode("utf-8")
    except Exception:
        # Fallback: might be a plain token from old config
        return encoded


def load() -> dict:
    """Load config from disk, return defaults if missing.
    
    Automatically decodes the obfuscated API token.
    """
    if not CONFIG_FILE.exists():
        return dict(DEFAULT_CONFIG)

    if not _check_permissions(CONFIG_FILE):
        import warnings
        warnings.warn(
            f"Config file {CONFIG_FILE} has insecure permissions. "
            f"Run: chmod 600 {CONFIG_FILE}",
            stacklevel=2,
        )

    raw = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))

    # Ensure all default keys exist (forward compat)
    cfg = dict(DEFAULT_CONFIG)
    cfg.update(raw)

    # Decode the token
    cfg["api_token"] = _decode_token(cfg.get("api_token", ""))

    return cfg


def save(cfg: dict) -> None:
    """Persist config to disk with restricted permissions.
    
    Automatically obfuscates the API token before writing.
    """
    _ensure_dir()

    # Copy to avoid mutating the caller's dict
    data = dict(cfg)
    data["api_token"] = _encode_token(data.get("api_token", ""))

    CONFIG_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    _set_file_permissions(CONFIG_FILE)


def is_initialized() -> bool:
    """Check if the CLI has been configured with a GitLab URL."""
    return CONFIG_FILE.exists() and bool(load().get("gitlab_url"))


def require_init() -> None:
    """Raise click.UsageError when not yet initialized."""
    import click
    if not is_initialized():
        from cicd.i18n import t
        raise click.UsageError(t("error.not_initialized"))