"""Pipeline script to normalize facets and build the base catalogue."""

import sys
from pathlib import Path

# Ensure the local src/ package can be imported
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ahoum_assignment.preprocessing import process_file


def main():
    root = Path(__file__).resolve().parents[1]
    input_csv = root / "data" / "raw" / "Facets Assignment.csv"
    output_csv = root / "data" / "processed" / "facet_catalogue.csv"
    
    print(f"Running preprocessing pipeline...\nInput:  {input_csv}\nOutput: {output_csv}")
    process_file(input_csv, output_csv)
    print("Success: Generated deterministic facet catalogue.")


if __name__ == "__main__":
    main()
