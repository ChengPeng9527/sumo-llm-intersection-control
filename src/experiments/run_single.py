from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from src.common.config import load_project_config


def run_controller(controller_script: Path) -> int:
    proc = subprocess.run([sys.executable, str(controller_script)])
    return proc.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--controller", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    root = Path(load_project_config()["project_root"])
    controller_script = root / args.controller

    if args.dry_run:
        print(f"DRY_RUN: {controller_script}")
        return 0

    return run_controller(controller_script)


if __name__ == "__main__":
    raise SystemExit(main())
