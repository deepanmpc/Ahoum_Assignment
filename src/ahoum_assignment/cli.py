"""Unified interactive command-line entry point."""

from __future__ import annotations

import argparse
import subprocess
import sys
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
    print("No model or network call was made. This command will never contact Ollama or cloud providers.")
    return 0


def run_script(script_name: str, args: list[str] = None):
    """Run a script from the scripts directory."""
    if args is None:
        args = []
    root = Path(__file__).resolve().parents[2]
    script_path = root / "scripts" / script_name
    cmd = [sys.executable, str(script_path)] + args
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"\n[!] Command failed with exit code {e.returncode}")
    except KeyboardInterrupt:
        print("\n[!] Operation cancelled by user.")


def interactive_menu():
    """Interactive CLI menu for all Ahoum features."""
    while True:
        print("\n" + "="*55)
        print(" Ahoum Assignment - Interactive CLI")
        print("="*55)
        print(" 1. Run Doctor Check (Validate Config)")
        print(" 2. Preprocess Facets (CSV -> Enriched Catalogue)")
        print(" 3. Build Semantic Index (For Hybrid Retrieval)")
        print(" 4. Retrieve Facets (Hybrid: Semantic + Keywords)")
        print(" 5. Score Conversation (Batched LLM Scoring)")
        print(" 6. Run Full Test Suite")
        print(" 7. Run Full Pipeline Demo (run.sh)")
        print(" 8. Exit")
        print("="*55)
        
        choice = input("Select an option [1-8]: ").strip()
        
        if choice == "1":
            print("\n--- Running Doctor Check ---")
            doctor(Path("config.toml"))
        elif choice == "2":
            print("\n--- Preprocessing Facets ---")
            run_script("preprocess_facets.py")
        elif choice == "3":
            print("\n--- Building Semantic Index ---")
            run_script("build_index.py")
        elif choice == "4":
            text = input("\nEnter conversation text to retrieve facets for:\n> ").strip()
            if text:
                print("\n--- Retrieving Facets ---")
                run_script("retrieve_facets.py", ["--text", text, "--human"])
        elif choice == "5":
            text = input("\nEnter conversation text to score:\n> ").strip()
            if text:
                dry_run = input("Dry run? (Build prompts only, NO LLM call) [y/N]: ").strip().lower()
                args = ["--text", text, "--human"]
                if dry_run == 'y':
                    args.append("--dry-run")
                print("\n--- Scoring Conversation ---")
                run_script("score_conversation.py", args)
        elif choice == "6":
            print("\n--- Running Test Suite ---")
            try:
                subprocess.run([sys.executable, "-m", "pytest", "tests/", "-v"], check=True)
            except subprocess.CalledProcessError:
                pass
        elif choice == "7":
            print("\n--- Running Full Pipeline Demo ---")
            root = Path(__file__).resolve().parents[2]
            try:
                subprocess.run(["bash", str(root / "run.sh")], check=True, cwd=str(root))
            except subprocess.CalledProcessError:
                pass
        elif choice == "8":
            print("Exiting.")
            sys.exit(0)
        else:
            print("Invalid choice. Please select a number from 1 to 8.")
            
        input("\nPress Enter to continue...")


def main() -> int:
    parser = argparse.ArgumentParser(description="Ahoum assignment interactive CLI")
    parser.add_argument("command", nargs="?", help="Direct command (e.g., 'doctor') or omit for interactive mode")
    parser.add_argument("--config", type=Path, default=Path("config.toml"), help="Path to config.toml")
    args, _ = parser.parse_known_args()

    # If the user specifically asks for doctor without interactive
    if args.command == "doctor":
        return doctor(args.config)
    elif args.command is not None:
        parser.error(f"Unsupported command: {args.command}. Run without arguments for the interactive menu.")
        return 2
    
    # Default to interactive mode
    try:
        interactive_menu()
    except KeyboardInterrupt:
        print("\nExiting.")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
