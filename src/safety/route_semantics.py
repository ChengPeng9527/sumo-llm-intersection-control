from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from xml.etree import ElementTree as ET

from src.common.config import load_project_config


APPROACHES = ("N", "E", "S", "W")
MOVEMENTS = ("STRAIGHT", "RIGHT", "LEFT")
MOVEMENT_BY_DIR = {
    "s": "STRAIGHT",
    "r": "RIGHT",
    "l": "LEFT",
}
EDGE_NAME_BY_APPROACH = {
    "N": "north",
    "E": "east",
    "S": "south",
    "W": "west",
}


@dataclass(frozen=True)
class RouteSemantics:
    route_id: str
    incoming_edge: str
    outgoing_edge: str
    movement: str


def _project_root() -> Path:
    return Path(load_project_config()["project_root"])


def _net_path() -> Path:
    return _project_root() / "net.net.xml"


def _route_id_from_edges(incoming_edge: str, outgoing_edge: str) -> str:
    outgoing_approach = outgoing_edge.lstrip("-")
    if incoming_edge not in APPROACHES or outgoing_approach not in APPROACHES:
        raise ValueError(f"Unsupported edge pair: {incoming_edge!r} -> {outgoing_edge!r}")
    return f"{incoming_edge}_{outgoing_approach}"


def _route_id_from_approaches(incoming_approach: str, outgoing_approach: str) -> str:
    return _route_id_from_edges(incoming_approach, f"-{outgoing_approach}")


@lru_cache(maxsize=1)
def _movement_lookup() -> dict[tuple[str, str], str]:
    tree = ET.parse(_net_path())
    lookup: dict[tuple[str, str], str] = {}
    for node in tree.iterfind(".//connection"):
        incoming_edge = node.get("from", "")
        outgoing_edge = node.get("to", "")
        movement_dir = node.get("dir", "").strip().lower()
        if incoming_edge not in APPROACHES:
            continue
        if outgoing_edge not in {f"-{approach}" for approach in APPROACHES}:
            continue
        if movement_dir not in MOVEMENT_BY_DIR:
            continue
        lookup[(incoming_edge, outgoing_edge)] = MOVEMENT_BY_DIR[movement_dir]

    expected_pairs = {
        ("N", "-W"),
        ("N", "-S"),
        ("N", "-E"),
        ("E", "-N"),
        ("E", "-W"),
        ("E", "-S"),
        ("S", "-E"),
        ("S", "-N"),
        ("S", "-W"),
        ("W", "-S"),
        ("W", "-E"),
        ("W", "-N"),
    }
    missing = sorted(expected_pairs - set(lookup))
    if missing:
        raise RuntimeError(f"Route semantics are incomplete for the current network: {missing}")
    return lookup


def movement_from_edges(incoming_edge: str, outgoing_edge: str) -> str:
    key = (incoming_edge, outgoing_edge)
    try:
        return _movement_lookup()[key]
    except KeyError as exc:
        raise ValueError(f"Unsupported movement for edge pair: {incoming_edge!r} -> {outgoing_edge!r}") from exc


def edges_from_route_id(route_id: str) -> tuple[str, str]:
    if not isinstance(route_id, str) or "_" not in route_id:
        raise ValueError(f"Invalid route id: {route_id!r}")
    incoming_approach, outgoing_approach = route_id.split("_", 1)
    incoming_edge = incoming_approach.strip().upper()
    outgoing_edge = f"-{outgoing_approach.strip().upper()}"
    if incoming_edge not in APPROACHES or outgoing_edge not in {f"-{approach}" for approach in APPROACHES}:
        raise ValueError(f"Unsupported route id: {route_id!r}")
    return incoming_edge, outgoing_edge


def describe_edge_pair(incoming_edge: str, outgoing_edge: str) -> RouteSemantics:
    incoming_edge = incoming_edge.strip().upper()
    outgoing_edge = outgoing_edge.strip().upper()
    movement = movement_from_edges(incoming_edge, outgoing_edge)
    return RouteSemantics(
        route_id=_route_id_from_edges(incoming_edge, outgoing_edge),
        incoming_edge=incoming_edge,
        outgoing_edge=outgoing_edge,
        movement=movement,
    )


def describe_route_id(route_id: str) -> RouteSemantics:
    incoming_edge, outgoing_edge = edges_from_route_id(route_id)
    return describe_edge_pair(incoming_edge, outgoing_edge)


def supported_route_catalog() -> list[RouteSemantics]:
    catalog: list[RouteSemantics] = []
    for incoming_edge in APPROACHES:
        for movement in MOVEMENTS:
            for outgoing_edge in sorted(
                edge for edge, label in _movement_lookup().items() if edge[0] == incoming_edge and label == movement
            ):
                catalog.append(describe_edge_pair(*outgoing_edge))
    return catalog


def supported_route_ids() -> list[str]:
    return [route.route_id for route in supported_route_catalog()]


def route_edges_for_route_id(route_id: str) -> tuple[str, str]:
    semantics = describe_route_id(route_id)
    return semantics.incoming_edge, semantics.outgoing_edge


def route_direction_from_route_id(route_id: str) -> str:
    semantics = describe_route_id(route_id)
    incoming = EDGE_NAME_BY_APPROACH.get(semantics.incoming_edge, "unknown")
    outgoing = EDGE_NAME_BY_APPROACH.get(semantics.outgoing_edge.lstrip("-"), "unknown")
    return f"{incoming}_{outgoing}"
