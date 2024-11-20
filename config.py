""" Persists config data """

from dataclasses import dataclass, asdict
import json
import os
import logging

CONFIG_FILENAME = "config.json"


@dataclass
class Config:
    """Configuration settings to be persisted"""

    user_name: str = ""
    email: str = ""
    wacs_user_id: str = ""


def load_config() -> Config:
    """Loads config file from disk."""
    if not os.path.exists(CONFIG_FILENAME):
        logging.warning("Config file not found, using defaults: %s", CONFIG_FILENAME)
        return Config()
    with open(CONFIG_FILENAME, "r", encoding="utf=8") as infile:
        data = json.load(infile)
        return Config(**data)


def save_config(config: Config) -> None:
    """Saves config to config.json"""
    with open(CONFIG_FILENAME, "w", encoding="utf=8") as outfile:
        json.dump(asdict(config), outfile, indent=4)
    logging.debug("Wrote config to: %s", CONFIG_FILENAME)
