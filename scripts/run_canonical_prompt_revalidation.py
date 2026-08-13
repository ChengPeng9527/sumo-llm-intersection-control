from __future__ import annotations

import sys

from src.experiments.canonical_prompt_revalidation import run_revalidation


def main() -> int:
    run_revalidation()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
