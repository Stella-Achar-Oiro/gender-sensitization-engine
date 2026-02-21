"""Integration tests for full pipeline demo."""
import pytest
import subprocess
from pathlib import Path


def test_demo_help():
    """Test that demo --help works."""
    result = subprocess.run(
        ["python3", "demos/demo_full_pipeline.py", "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "JuaKazi" in result.stdout
    assert "--language" in result.stdout
    assert "--samples" in result.stdout


def test_demo_requires_language():
    """Test that demo requires --language argument."""
    result = subprocess.run(
        ["python3", "demos/demo_full_pipeline.py"],
        capture_output=True,
        text=True
    )
    assert result.returncode != 0
    assert "required" in result.stderr.lower() or "required" in result.stdout.lower()


def test_demo_runs_successfully_english():
    """Test demo runs without errors for English."""
    result = subprocess.run(
        ["python3", "demos/demo_full_pipeline.py", "--language", "en", "--samples", "10"],
        capture_output=True,
        text=True,
        timeout=60
    )
    assert result.returncode == 0
    assert "Pipeline Complete" in result.stdout
    assert "F1 Score" in result.stdout
    assert "Precision: 1.000" in result.stdout  # Perfect precision!


def test_demo_quiet_mode():
    """Test demo quiet mode only outputs metrics."""
    result = subprocess.run(
        ["python3", "demos/demo_full_pipeline.py", "-l", "en", "-n", "10", "--quiet"],
        capture_output=True,
        text=True,
        timeout=60
    )
    assert result.returncode == 0
    # Should have F1, Precision, Recall
    assert "F1:" in result.stdout
    assert "Precision:" in result.stdout
    assert "Recall:" in result.stdout
    # Should NOT have verbose output
    assert "Pipeline Complete" not in result.stdout


@pytest.mark.parametrize("lang", ["en", "sw", "fr", "ki"])
def test_demo_all_languages(lang):
    """Test demo works for all supported languages."""
    result = subprocess.run(
        ["python3", "demos/demo_full_pipeline.py", "-l", lang, "-n", "10", "--quiet"],
        capture_output=True,
        text=True,
        timeout=60
    )
    assert result.returncode == 0, f"Demo failed for language: {lang}\n{result.stderr}"
    assert "F1:" in result.stdout
    assert "Precision:" in result.stdout


def test_demo_no_ml_flag():
    """Test demo with ML disabled."""
    result = subprocess.run(
        ["python3", "demos/demo_full_pipeline.py", "-l", "en", "-n", "10", "--no-ml"],
        capture_output=True,
        text=True,
        timeout=60
    )
    assert result.returncode == 0
    assert "method: rules-only" in result.stdout


def test_demo_invalid_sample_size():
    """Test demo rejects invalid sample sizes."""
    result = subprocess.run(
        ["python3", "demos/demo_full_pipeline.py", "-l", "en", "-n", "5"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 1
    assert "sample_size must be >= 10" in result.stderr


@pytest.mark.slow
def test_demo_large_sample():
    """Test demo with larger sample size."""
    result = subprocess.run(
        ["python3", "demos/demo_full_pipeline.py", "-l", "sw", "-n", "50", "--quiet"],
        capture_output=True,
        text=True,
        timeout=120
    )
    assert result.returncode == 0
    # Perfect precision maintained even at larger scale
    assert "Precision: 1.000" in result.stdout


@pytest.mark.slow
def test_demo_preserves_perfect_precision():
    """
    Critical test: Verify perfect precision is maintained.

    This is our key requirement - zero false positives!
    """
    for lang in ["en", "sw", "fr", "ki"]:
        result = subprocess.run(
            ["python3", "demos/demo_full_pipeline.py", "-l", lang, "-n", "20", "--quiet"],
            capture_output=True,
            text=True,
            timeout=120
        )
        assert result.returncode == 0
        # Must have perfect precision
        assert "Precision: 1.000" in result.stdout, \
            f"Precision not perfect for {lang}: {result.stdout}"


def test_demo_creates_output_directory(tmp_path):
    """Test that demo creates specified output directory."""
    output = tmp_path / "test_results"
    assert not output.exists()

    result = subprocess.run(
        ["python3", "demos/demo_full_pipeline.py",
         "-l", "en", "-n", "10", "--output", str(output), "--quiet"],
        capture_output=True,
        text=True,
        timeout=60
    )
    assert result.returncode == 0
    assert output.exists()
    assert output.is_dir()


def test_demo_performance():
    """Test that demo runs in reasonable time (< 10 seconds for 10 samples)."""
    import time
    start = time.time()

    result = subprocess.run(
        ["python3", "demos/demo_full_pipeline.py", "-l", "en", "-n", "10", "--quiet"],
        capture_output=True,
        text=True,
        timeout=60
    )

    elapsed = time.time() - start
    assert result.returncode == 0
    assert elapsed < 10, f"Demo took too long: {elapsed:.1f}s"


@pytest.mark.integration
def test_full_pipeline_end_to_end():
    """
    Complete end-to-end integration test.

    This is what experts will see - the full 2-minute demo!
    """
    result = subprocess.run(
        ["python3", "demos/demo_full_pipeline.py", "-l", "sw", "-n", "30"],
        capture_output=True,
        text=True,
        timeout=120
    )

    assert result.returncode == 0

    # Check all stages completed
    assert "Stage 1: Data Collection" in result.stdout
    assert "Stage 2: Bias Detection" in result.stdout
    assert "Stage 3: Evaluation" in result.stdout
    assert "Pipeline Complete" in result.stdout

    # Check metrics are present
    assert "F1 Score:" in result.stdout
    assert "Precision: 1.000" in result.stdout
    assert "Recall:" in result.stdout

    # Check next steps guidance
    assert "Next steps:" in result.stdout
