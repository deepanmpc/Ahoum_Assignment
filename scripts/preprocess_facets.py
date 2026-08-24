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
    audit_md = root / "data" / "processed" / "facet_audit.md"
    
    print(f"Running preprocessing pipeline...\nInput:  {input_csv}\nOutput: {output_csv}")
    stats = process_file(input_csv, output_csv)
    
    with open(audit_md, 'a', encoding='utf-8') as f:
        f.write("\n## Taxonomy & Classification Audit\n\n")
        
        f.write("### Categories\n")
        for k, v in stats['categories'].most_common():
            f.write(f"- {k}: {v}\n")
            
        f.write("\n### Types\n")
        for k, v in stats['types'].most_common():
            f.write(f"- {k}: {v}\n")
            
        f.write("\n### Observability\n")
        for k, v in stats['observability'].most_common():
            f.write(f"- {k}: {v}\n")
            
        f.write("\n### Sensitivity\n")
        for k, v in stats['sensitivity'].most_common():
            f.write(f"- {k}: {v}\n")
            
        f.write("\n### Review Required\n")
        for k, v in stats['review_required'].most_common():
            f.write(f"- {k}: {v}\n")
            
        f.write("\n### Representative Examples\n")
        for cat, examples in stats['examples'].items():
            f.write(f"**{cat}**:\n")
            for ex in examples:
                f.write(f"- {ex}\n")
            f.write("\n")
            
    print("Success: Generated deterministic facet catalogue and updated audit markdown.")


if __name__ == "__main__":
    main()
