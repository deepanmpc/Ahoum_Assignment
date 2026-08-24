import csv
from pathlib import Path

from ahoum_assignment.preprocessing import (
    normalize_facet,
    is_malformed,
    generate_id,
    process_file,
)


def test_whitespace_normalization():
    assert normalize_facet("  hello   world  ") == "hello world"
    assert normalize_facet("tabs\t\tand\nnewlines") == "tabs and newlines"


def test_trailing_colon_handling():
    assert normalize_facet("Democratic Leadership:") == "democratic leadership"
    assert normalize_facet("  Test:  ") == "test"
    # Should not remove internal colons
    assert normalize_facet("Test: Subtest") == "test: subtest"


def test_numbering_prefix_removal():
    assert normalize_facet("899. Sufi practice") == "sufi practice"
    assert normalize_facet(" 12.   Something ") == "something"
    assert normalize_facet("1) Option") == "option"
    # Don't remove numbers if they don't look like a list prefix
    assert normalize_facet("12345") == "12345"


def test_preservation_of_facet_raw(tmp_path: Path):
    raw_csv = tmp_path / "raw.csv"
    raw_csv.write_text("Facets\n  Weirdly Formatted: \n")
    
    out = tmp_path / "out.csv"
    process_file(raw_csv, out)
    
    with out.open(encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        assert reader[0]["facet_raw"] == "  Weirdly Formatted: "
        assert reader[0]["facet_normalized"] == "weirdly formatted"


def test_malformed_entry_handling():
    # Headers
    malf, _ = is_malformed("Facets", "facets")
    assert malf is True
    malf, _ = is_malformed("Column1", "column1")
    assert malf is True
    
    # Blanks
    malf, _ = is_malformed("   ", "")
    assert malf is True
    
    # Empty after norm
    malf, _ = is_malformed("899.", "")
    assert malf is True
    
    # Mostly punctuation
    malf, _ = is_malformed("+++---", "+++---")
    assert malf is True


def test_stable_ids():
    assert generate_id("test", 1) == generate_id("test", 1)
    assert generate_id("test", 1) != generate_id("test", 2)
    assert generate_id("test", 1) != generate_id("different", 1)


def test_repeated_execution_produces_identical_output(tmp_path: Path):
    raw_csv = tmp_path / "raw.csv"
    raw_csv.write_text("Facets\n1. Hello:\n  Bad   Spacing  \nFacets\n")
    
    out1 = tmp_path / "out1.csv"
    out2 = tmp_path / "out2.csv"
    
    process_file(raw_csv, out1)
    process_file(raw_csv, out2)
    
    assert out1.read_text(encoding="utf-8") == out2.read_text(encoding="utf-8")
