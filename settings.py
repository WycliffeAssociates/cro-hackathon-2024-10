""" Persist settings between runs. """

from dataclasses import dataclass, asdict
import json
import logging
import os

SETTINGS_FILENAME = "settings.json"


@dataclass
class Settings:
    """Settings to be persisted"""

    user_name: str = ""
    email: str = ""
    wacs_user_id: str = ""
    repo_dir: str = ""


def load_settings() -> Settings:
    """Loads settings file from disk."""
    if not os.path.exists(SETTINGS_FILENAME):
        logging.warning(
            "Settings file not found, using defaults: %s", SETTINGS_FILENAME
        )
        return Settings()
    with open(SETTINGS_FILENAME, "r", encoding="utf=8") as infile:
        data = json.load(infile)
        return Settings(**data)


def save_settings(settings: Settings) -> None:
    """Saves settings to disk"""
    with open(SETTINGS_FILENAME, "w", encoding="utf=8") as outfile:
        json.dump(asdict(settings), outfile, indent=4)
    logging.debug("Wrote settings to: %s", SETTINGS_FILENAME)
