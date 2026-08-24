import argparse
import json
import sys
from pathlib import Path

# Ensure local src/ can be imported
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ahoum_assignment.keyword_router import KeywordRouter

def main():
    parser = argparse.ArgumentParser(description="Runtime Keyword Routing CLI")
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", type=str, help="Direct conversation text input")
    group.add_argument("--file", type=str, help="Text file input path")
    
    parser.add_argument("--output", type=str, help="Optional JSON output path")
    
    args = parser.parse_args()
    
    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                text = f.read()
        except FileNotFoundError:
            print(f"Error: Could not read file at {args.file}")
            sys.exit(1)
    else:
        text = args.text
        
    root = Path(__file__).resolve().parents[1]
    catalogue_csv = root / "data" / "processed" / "facet_catalogue.csv"
    rules_toml = root / "config" / "routing_rules.toml"
    
    try:
        router = KeywordRouter(rules_toml, catalogue_csv)
        result = router.retrieve(text)
    except Exception as e:
        print(f"Routing Error: {e}")
        sys.exit(1)
        
    out_data = result.model_dump()
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(out_data, f, indent=2)
        print(f"Results successfully written to {args.output}")
    else:
        print(json.dumps(out_data, indent=2))


if __name__ == "__main__":
    main()
