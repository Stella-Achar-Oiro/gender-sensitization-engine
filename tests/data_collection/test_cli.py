"""Tests for unified data collection CLI."""
import subprocess
import sys
from pathlib import Path
import pytest


CLI_PATH = Path(__file__).parent.parent.parent / "scripts" / "data_collection" / "cli.py"


def run_cli(*args, check=True):
    """Run CLI and return result."""
    cmd = [sys.executable, str(CLI_PATH)] + list(args)
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=30
    )
    if check and result.returncode != 0:
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
    return result


def test_cli_help():
    """Test CLI --help works."""
    result = run_cli("--help")
    assert result.returncode == 0
    assert "JuaKazi Data Collection CLI" in result.stdout
    assert "list-sources" in result.stdout
    assert "show-lineage" in result.stdout
    assert "collect" in result.stdout


def test_cli_no_command():
    """Test CLI with no command shows help."""
    result = run_cli(check=False)
    assert result.returncode == 1
    assert "usage:" in result.stdout or "usage:" in result.stderr


def test_list_sources():
    """Test list-sources command."""
    result = run_cli("list-sources")
    assert result.returncode == 0
    assert "Available Data Sources" in result.stdout
    assert "wikipedia" in result.stdout
    assert "news" in result.stdout
    assert "bible" in result.stdout
    assert "ground-truth" in result.stdout
    assert "Total sources: 4" in result.stdout


def test_list_sources_shows_details():
    """Test list-sources shows collector details."""
    result = run_cli("list-sources")
    assert "WikipediaCollector" in result.stdout
    assert "NewsCollector" in result.stdout
    assert "BibleCollector" in result.stdout
    assert "Languages:" in result.stdout


def test_collect_help():
    """Test collect --help works."""
    result = run_cli("collect", "--help")
    assert result.returncode == 0
    assert "collect" in result.stdout
    assert "--language" in result.stdout
    assert "--max-items" in result.stdout


def test_collect_ground_truth(tmp_path):
    """Test collecting from ground truth."""
    output_file = tmp_path / "test.csv"

    result = run_cli(
        "collect", "ground-truth",
        "--language", "en",
        "--max-items", "5",
        "--output", str(output_file)
    )

    assert result.returncode == 0
    assert "Collection complete" in result.stdout
    assert output_file.exists()

    # Verify CSV has data
    lines = output_file.read_text().splitlines()
    assert len(lines) == 6  # 1 header + 5 samples


def test_collect_ground_truth_all_languages(tmp_path):
    """Test collecting from ground truth for all languages."""
    for lang in ["en", "sw", "fr", "ki"]:
        output_file = tmp_path / f"test_{lang}.csv"

        result = run_cli(
            "collect", "ground-truth",
            "--language", lang,
            "--max-items", "3",
            "--output", str(output_file)
        )

        assert result.returncode == 0, f"Failed for language: {lang}"
        assert output_file.exists()


def test_collect_quiet_mode(tmp_path):
    """Test collect with --quiet flag."""
    output_file = tmp_path / "test_quiet.csv"

    result = run_cli(
        "collect", "ground-truth",
        "--language", "en",
        "--max-items", "5",
        "--output", str(output_file),
        "--quiet"
    )

    assert result.returncode == 0
    # Quiet mode should have minimal output
    assert "Collection complete" not in result.stdout
    assert "samples saved to" in result.stdout
    assert output_file.exists()


def test_collect_verbose_mode(tmp_path):
    """Test collect with --verbose flag."""
    output_file = tmp_path / "test_verbose.csv"

    result = run_cli(
        "collect", "ground-truth",
        "--language", "en",
        "--max-items", "5",
        "--output", str(output_file),
        "--verbose"
    )

    assert result.returncode == 0
    # Verbose mode should show lineage
    assert "Lineage:" in result.stdout
    assert output_file.exists()


def test_collect_invalid_source():
    """Test collect with invalid source."""
    result = run_cli(
        "collect", "invalid_source",
        "--language", "en",
        "--max-items", "5",
        check=False
    )

    assert result.returncode != 0
    assert "invalid choice" in result.stderr.lower() or "invalid choice" in result.stdout.lower()


def test_collect_unsupported_language():
    """Test collect with unsupported language for source."""
    result = run_cli(
        "collect", "news",
        "--language", "en",  # News only supports Swahili
        "--max-items", "5",
        check=False
    )

    assert result.returncode == 1
    assert "not supported" in result.stderr or "not supported" in result.stdout


@pytest.mark.skip("Requires complex working directory setup")
def test_collect_default_output(tmp_path, monkeypatch):
    """Test collect uses default output path."""
    # TODO: This test requires setting up proper working directory structure
    # Skipping for now as it's not critical
    pass


def test_show_lineage_existing_file(tmp_path):
    """Test show-lineage with existing file."""
    # First collect some data
    output_file = tmp_path / "wikipedia_en.csv"
    run_cli(
        "collect", "ground-truth",
        "--language", "en",
        "--max-items", "5",
        "--output", str(output_file)
    )

    # Now show lineage
    result = run_cli("show-lineage", str(output_file))

    assert result.returncode == 0
    assert "Data Lineage" in result.stdout
    assert "Samples:" in result.stdout
    assert "Size:" in result.stdout


def test_show_lineage_nonexistent_file():
    """Test show-lineage with non-existent file."""
    result = run_cli("show-lineage", "/nonexistent/file.csv", check=False)

    assert result.returncode == 1
    assert "ERROR" in result.stderr or "not found" in result.stderr


def test_show_lineage_infers_metadata(tmp_path):
    """Test show-lineage infers metadata from filename."""
    # Create file with pattern: source_lang_version.csv
    output_file = tmp_path / "wikipedia_en_v1.csv"
    run_cli(
        "collect", "ground-truth",
        "--language", "en",
        "--max-items", "5",
        "--output", str(output_file)
    )

    result = run_cli("show-lineage", str(output_file))

    assert result.returncode == 0
    assert "Inferred metadata" in result.stdout
    assert "Source: wikipedia" in result.stdout
    assert "Language: en" in result.stdout


@pytest.mark.slow
def test_collect_wikipedia_integration(tmp_path):
    """Integration test: collect from Wikipedia."""
    output_file = tmp_path / "wiki_test.csv"

    result = run_cli(
        "collect", "wikipedia",
        "--language", "en",
        "--max-items", "3",
        "--output", str(output_file)
    )

    # May fail if network issues, but shouldn't crash
    if result.returncode == 0:
        assert output_file.exists()
        # Verify file has data
        content = output_file.read_text()
        assert "text," in content  # Has header


def test_cli_mutually_exclusive_flags(tmp_path):
    """Test --verbose and --quiet are mutually exclusive."""
    output_file = tmp_path / "test.csv"

    result = run_cli(
        "collect", "ground-truth",
        "--language", "en",
        "--max-items", "5",
        "--output", str(output_file),
        "--verbose",
        "--quiet",
        check=False
    )

    assert result.returncode != 0
    assert "mutually exclusive" in result.stderr.lower() or "mutually exclusive" in result.stdout.lower()


def test_collect_respects_max_items(tmp_path):
    """Test collect respects --max-items limit."""
    for max_items in [3, 5, 10]:
        output_file = tmp_path / f"test_{max_items}.csv"

        run_cli(
            "collect", "ground-truth",
            "--language", "en",
            "--max-items", str(max_items),
            "--output", str(output_file)
        )

        lines = output_file.read_text().splitlines()
        # Should have header + max_items samples
        assert len(lines) == max_items + 1


def test_collect_creates_parent_directories(tmp_path):
    """Test collect creates parent directories if needed."""
    output_file = tmp_path / "nested" / "path" / "test.csv"

    result = run_cli(
        "collect", "ground-truth",
        "--language", "en",
        "--max-items", "3",
        "--output", str(output_file)
    )

    assert result.returncode == 0
    assert output_file.exists()
    assert output_file.parent.exists()


def test_cli_summary_shows_file_size(tmp_path):
    """Test CLI summary shows file size."""
    output_file = tmp_path / "test.csv"

    result = run_cli(
        "collect", "ground-truth",
        "--language", "en",
        "--max-items", "5",
        "--output", str(output_file)
    )

    assert result.returncode == 0
    assert "File size:" in result.stdout
    assert "KB" in result.stdout


def test_cli_handles_collection_errors_gracefully(tmp_path):
    """Test CLI handles collection errors gracefully."""
    # Try to collect Bible without Bible directory
    output_file = tmp_path / "test.csv"

    result = run_cli(
        "collect", "bible",
        "--language", "ki",
        "--max-items", "5",
        "--output", str(output_file),
        "--bible-dir", "/nonexistent/path",
        check=False
    )

    # Should fail gracefully, not crash
    assert result.returncode == 1
    # Should print error message
    assert "ERROR" in result.stderr or "No samples" in result.stderr or "No samples" in result.stdout
