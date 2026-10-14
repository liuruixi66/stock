"""Workspace paths shared by configuration, cache readers and CLI tools."""

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE_DIR / 'cache'
