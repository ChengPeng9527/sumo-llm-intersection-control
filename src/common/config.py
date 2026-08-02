from __future__ import annotations

import os
from pathlib import Path

try:
    import yaml
except Exception as exc:  # pragma: no cover
    yaml = None
    _yaml_import_error = exc


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "config"


def load_yaml_config(name: str) -> dict:
    path = CONFIG_DIR / name
    if yaml is None:  # pragma: no cover
        raise RuntimeError(
            "pyyaml is required to read config files"
        ) from _yaml_import_error

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    return data


def resolve_project_path(value: str | os.PathLike[str]) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (PROJECT_ROOT / path).resolve()


def load_project_config() -> dict:
    config = load_yaml_config("project_config.yaml")
    config["project_root"] = str(PROJECT_ROOT)
    config["project_root_path"] = PROJECT_ROOT
    config["sumo_binary_path"] = resolve_project_path(config["sumo_binary"])
    config["sumo_gui_binary_path"] = resolve_project_path(config["sumo_gui_binary"])
    config["sumo_config_path"] = resolve_project_path(config["sumo_config"])
    config["results_dir_path"] = resolve_project_path(config["results_dir"])
    return config
