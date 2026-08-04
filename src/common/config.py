from __future__ import annotations

import os
import re
import warnings
from pathlib import Path

try:
    import yaml
except Exception as exc:  # pragma: no cover
    yaml = None
    _yaml_import_error = exc


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "config"
_YAML_FALLBACK_WARNED = False


def _coerce_yaml_scalar(value: str):
    value = value.strip()
    if not value:
        return ""
    if value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "none", "~"}:
        return None
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_coerce_yaml_scalar(part.strip()) for part in inner.split(",")]
    if re.fullmatch(r"[-+]?\d+", value):
        return int(value)
    if re.fullmatch(r"[-+]?\d*\.\d+", value):
        return float(value)
    return value


def _preprocess_yaml(text: str) -> list[tuple[int, str]]:
    lines: list[tuple[int, str]] = []
    for raw_line in text.splitlines():
        if not raw_line.strip():
            continue
        stripped = raw_line.lstrip(" ")
        if stripped.startswith("#"):
            continue
        indent = len(raw_line) - len(stripped)
        content = stripped.split("#", 1)[0].rstrip()
        if content:
            lines.append((indent, content))
    return lines


def _parse_yaml_block(lines: list[tuple[int, str]], start: int, indent: int):
    if start >= len(lines):
        return {}, start

    kind = "list" if lines[start][1].startswith("- ") else "dict"
    if kind == "list":
        items = []
        index = start
        while index < len(lines):
            current_indent, content = lines[index]
            if current_indent < indent:
                break
            if current_indent > indent:
                break
            if not content.startswith("- "):
                break
            item_text = content[2:].strip()
            index += 1
            if item_text:
                items.append(_coerce_yaml_scalar(item_text))
                continue
            if index < len(lines) and lines[index][0] > indent:
                nested, index = _parse_yaml_block(lines, index, lines[index][0])
                items.append(nested)
            else:
                items.append("")
        return items, index

    mapping: dict[str, object] = {}
    index = start
    while index < len(lines):
        current_indent, content = lines[index]
        if current_indent < indent:
            break
        if current_indent > indent:
            break
        if content.startswith("- "):
            break
        key, sep, remainder = content.partition(":")
        if not sep:
            raise ValueError(f"Invalid YAML line: {content!r}")
        key = key.strip()
        remainder = remainder.strip()
        index += 1
        if remainder:
            mapping[key] = _coerce_yaml_scalar(remainder)
            continue
        if index < len(lines) and lines[index][0] > indent:
            nested, index = _parse_yaml_block(lines, index, lines[index][0])
            mapping[key] = nested
        else:
            mapping[key] = {}
    return mapping, index


def _load_yaml_fallback(text: str) -> dict:
    lines = _preprocess_yaml(text)
    if not lines:
        return {}
    parsed, _ = _parse_yaml_block(lines, 0, lines[0][0])
    return parsed if isinstance(parsed, dict) else {}


def load_yaml_config(name: str) -> dict:
    path = CONFIG_DIR / name
    if yaml is not None:
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    with path.open("r", encoding="utf-8") as f:
        text = f.read()
    try:
        global _YAML_FALLBACK_WARNED
        if not _YAML_FALLBACK_WARNED:
            warnings.warn(
                "PyYAML is unavailable; using the built-in fallback YAML parser for project config files.",
                RuntimeWarning,
                stacklevel=2,
            )
            _YAML_FALLBACK_WARNED = True
        return _load_yaml_fallback(text)
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("pyyaml is required to read config files") from _yaml_import_error


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
