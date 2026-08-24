"""Run the project configuration check without installing the package."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ahoum_assignment.cli import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
