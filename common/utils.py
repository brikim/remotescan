""" Utility Module """

from typing import Any
import re

ANSI_CODE_START: str = "\33[38;5;"
ANSI_CODE_END: str = "m"

ANSI_CODE_LOG = f"{ANSI_CODE_START}15{ANSI_CODE_END}"
ANSI_CODE_TAG = f"{ANSI_CODE_START}37{ANSI_CODE_END}"
ANSI_CODE_PLEX = f"{ANSI_CODE_START}220{ANSI_CODE_END}"
ANSI_CODE_EMBY = f"{ANSI_CODE_START}77{ANSI_CODE_END}"
ANSI_CODE_JELLYFIN = f"{ANSI_CODE_START}134{ANSI_CODE_END}"


def get_log_ansi_code() -> str:
    """Get assigned log ANSI code."""
    return ANSI_CODE_LOG


def get_tag_ansi_code() -> str:
    """Get assigned tag ANSI code."""
    return ANSI_CODE_TAG


def get_plex_ansi_code() -> str:
    """Get assigned Plex ANSI code."""
    return ANSI_CODE_PLEX


def get_emby_ansi_code() -> str:
    """Get assigned Emby ANSI code."""
    return ANSI_CODE_EMBY


def get_jellyfin_ansi_code() -> str:
    """Get assigned Jellyfin ANSI code."""
    return ANSI_CODE_JELLYFIN


def get_log_header(module_ansi_code: str, module: str) -> str:
    """Get a formatted log header string with ANSI codes."""
    return f"{module_ansi_code}{module}{get_log_ansi_code()}:"


def get_tag(tag_name: str, tag_value: Any) -> str:
    """Get a formatted tag string with ANSI codes."""
    return f"{get_tag_ansi_code()}{tag_name}={get_log_ansi_code()}{tag_value}"


def get_formatted_plex() -> str:
    """Get a formatted Plex string with ANSI codes."""
    return f"{get_plex_ansi_code()}Plex{get_log_ansi_code()}"


def get_formatted_emby() -> str:
    """Get a formatted Emby string with ANSI codes."""
    return f"{get_emby_ansi_code()}Emby{get_log_ansi_code()}"


def get_formatted_jellyfin() -> str:
    """Get a formatted Jellyfin string with ANSI codes."""
    return f"{get_jellyfin_ansi_code()}Jellyfin{get_log_ansi_code()}"


def remove_ansi_code_from_text(text: str) -> str:
    """Removes ANSI escape codes from a string."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


def build_target_string(current_target: str, new_target: str, target_instance: str) -> str:
    """
    Builds a target string by combining current and new targets, optionally with a target instance
    """
    if not current_target:
        return f"{new_target}({target_instance})" if target_instance else new_target
    return f"{current_target},{new_target}:({target_instance})" if target_instance else f"{current_target},{new_target}"
