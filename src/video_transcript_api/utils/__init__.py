"""Utility subpackages for video_transcript_api.

This module exposes only the minimal helpers that remain widely used
across the codebase. Most features now live in dedicated subpackages
under ``video_transcript_api.utils``.
"""

import os
from .logging import setup_logger, load_config, ensure_dir


def create_debug_dir(base_dir: str = "logs") -> str:
    """Ensure the debug log directory exists and return its path."""
    logs_dir = base_dir
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    debug_dir = os.path.join(logs_dir, "debug")
    if not os.path.exists(debug_dir):
        os.makedirs(debug_dir)

    return debug_dir


__all__ = ["setup_logger", "load_config", "ensure_dir", "create_debug_dir"]
