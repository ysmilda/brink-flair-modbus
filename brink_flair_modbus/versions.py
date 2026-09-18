"""Decode the version strings stored in a Brink module's identity registers."""

from __future__ import annotations


def _type_version(word: int | None) -> str:
    """Decode a ``Type and major`` word into its two ASCII characters (S1)."""
    if word is None:
        return "unknown"
    return "".join(chr(byte) for byte in (word >> 8, word & 0xFF))


def _hardware_version(word: int | None) -> str:
    """Decode a hardware version word (high byte major, low byte minor)."""
    if word is None:
        return "unknown"
    return f"H{(word >> 8) & 0xFF}.{word & 0xFF}"


def _minor_fix(word: int | None) -> str | None:
    """Decode a minor/fix word (high byte minor, low byte fix) as ``01.03``."""
    if word is None:
        return None
    return f"{(word >> 8) & 0xFF:02d}.{word & 0xFF:02d}"
