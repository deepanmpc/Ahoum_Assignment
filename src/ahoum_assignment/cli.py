"""Dependency-free command-line entry point for local diagnostics."""

from __future__ import annotations

import argparse
from pathlib import Path

from .config import load_config


def doctor(config_path: Path) -> int:
    """Validate local configuration only; this command makes no model/API calls."""

    config = load_config(config_path)
    required_directories = (config.examples_dir, config.outputs_dir, config.raw_facets_csv.parent)
    missing = [str(directory.relative_to(config.root_dir)) for directory in required_directories if not directory.is_dir()]
    if missing:
        print(f"Configuration invalid: missing directories: {', '.join(missing)}")
        return 1

    print("Configuration is valid.")
    print(f"Model provider: {config.model_provider}")
    print(f"Model name: {config.model_name}")
    print("No model or network call was made.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Ahoum assignment project commands")
    subparsers = parser.add_subparsers(dest="command", required=True)
    doctor_parser = subparsers.add_parser("doctor", help="validate local configuration")
    doctor_parser.add_argument("--config", type=Path, default=Path("config.toml"))
    args = parser.parse_args()

    if args.command == "doctor":
        return doctor(args.config)
    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
