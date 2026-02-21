"""
Integration tests for Week 2 complete pipeline.

Tests the full workflow from data collection through ML training to evaluation.
"""
import pytest
from pathlib import Path
import subprocess
import sys


# Week 2 Day 6-7: Data Collection Tests

def test_ground_truth_collector_all_languages():
    """Test GroundTruthCollector works for all languages."""
    from scripts.data_collection.base_collector import CollectionConfig
    from scripts.data_collection.wikipedia_collector import GroundTruthCollector

    for lang in ["en", "sw", "fr", "ki"]:
        config = CollectionConfig(
            language=lang,
            max_items=5,
            output_file=Path(f"/tmp/test_gt_{lang}.csv")
        )
        collector = GroundTruthCollector(config)
        samples = collector.collect()

        assert len(samples) > 0, f"No samples for {lang}"
        assert all(s.language == lang for s in samples)


def test_data_collection_to_csv_integration(tmp_path):
    """Test complete data collection to CSV workflow."""
    from scripts.data_collection.base_collector import CollectionConfig
    from scripts.data_collection.wikipedia_collector import GroundTruthCollector

    output_file = tmp_path / "collected_data.csv"

    config = CollectionConfig(
        language="en",
        max_items=10,
        output_file=output_file
    )

    collector = GroundTruthCollector(config)
    samples = collector.collect()
    result = collector.save_samples(samples)

    assert result.success
    assert output_file.exists()
    assert result.samples_collected == len(samples)

    # Verify CSV contents
    lines = output_file.read_text().splitlines()
    assert len(lines) == len(samples) + 1  # Header + samples


# Week 2 Day 8: CLI Integration Tests

def test_cli_collect_to_file(tmp_path):
    """Test CLI collection saves to file correctly."""
    output_file = tmp_path / "cli_test.csv"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/data_collection/cli.py",
            "collect", "ground-truth",
            "--language", "en",
            "--max-items", "3",
            "--output", str(output_file),
            "--quiet"
        ],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    assert output_file.exists()

    # Verify file has data
    lines = output_file.read_text().splitlines()
    assert len(lines) == 4  # 1 header + 3 samples


def test_cli_list_sources_shows_all():
    """Test CLI list-sources shows all collectors."""
    result = subprocess.run(
        [sys.executable, "scripts/data_collection/cli.py", "list-sources"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    assert "wikipedia" in result.stdout
    assert "news" in result.stdout
    assert "bible" in result.stdout
    assert "ground-truth" in result.stdout


def test_cli_show_lineage_integration(tmp_path):
    """Test CLI lineage tracking end-to-end."""
    output_file = tmp_path / "lineage_test.csv"

    # Collect data
    subprocess.run(
        [
            sys.executable,
            "scripts/data_collection/cli.py",
            "collect", "ground-truth",
            "--language", "sw",
            "--max-items", "5",
            "--output", str(output_file),
            "--quiet"
        ],
        check=True
    )

    # Show lineage
    result = subprocess.run(
        [
            sys.executable,
            "scripts/data_collection/cli.py",
            "show-lineage",
            str(output_file)
        ],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    assert "Data Lineage" in result.stdout
    assert "Samples:" in result.stdout


# Week 2 Day 9: ML Training Integration Tests

def test_training_config_validation_integration():
    """Test TrainingConfig validation works correctly."""
    from ml.training.config import TrainingConfig
    from eval.models import Language

    # Valid config
    config = TrainingConfig(language=Language.ENGLISH)
    assert config.language == Language.ENGLISH

    # Invalid batch size
    with pytest.raises(ValueError):
        TrainingConfig(batch_size=0)

    # Invalid learning rate
    with pytest.raises(ValueError):
        TrainingConfig(learning_rate=-0.1)


def test_trainer_complete_workflow(tmp_path):
    """Test complete training workflow: load → train → save → evaluate."""
    from ml.training.config import TrainingConfig
    from ml.training.trainer import BiasDetectionTrainer
    from eval.models import Language

    config = TrainingConfig(
        language=Language.ENGLISH,
        num_epochs=1,
        model_output_dir=tmp_path / "models"
    )

    trainer = BiasDetectionTrainer(config)

    # Load data
    train_data, val_data, test_data = trainer.load_data()
    assert len(train_data) > 0
    assert len(val_data) >= 0
    assert len(test_data) >= 0

    # Train
    result = trainer.train(train_data, val_data)
    assert result.success
    assert result.model_path.exists()

    # Evaluate
    test_metrics = trainer.evaluate(test_data)
    assert 'test_f1' in test_metrics
    assert 0 <= test_metrics['test_f1'] <= 1


def test_training_script_cli_integration(tmp_path):
    """Test train_ml_model.py CLI works end-to-end."""
    result = subprocess.run(
        [
            sys.executable,
            "train_ml_model.py",
            "--language", "en",
            "--epochs", "1",
            "--output-dir", str(tmp_path / "models"),
            "--seed", "42"
        ],
        capture_output=True,
        text=True,
        timeout=60
    )

    assert result.returncode == 0
    assert "Training completed successfully" in result.stdout

    # Check model was saved
    model_file = tmp_path / "models" / "en" / "final_model.json"
    assert model_file.exists()


def test_training_multiple_languages_integration(tmp_path):
    """Test training works for all languages."""
    from ml.training.config import TrainingConfig
    from ml.training.trainer import BiasDetectionTrainer
    from eval.models import Language

    languages = [Language.ENGLISH, Language.SWAHILI, Language.FRENCH, Language.GIKUYU]

    for lang in languages:
        config = TrainingConfig(
            language=lang,
            num_epochs=1,
            model_output_dir=tmp_path / "models" / lang.value
        )

        trainer = BiasDetectionTrainer(config)
        train_data, val_data, _ = trainer.load_data()

        # Just verify we can load data for all languages
        assert len(train_data) > 0, f"No train data for {lang}"


# Week 2 Day 10: Model Comparison Integration Tests

def test_model_comparison_single_language():
    """Test model comparison for single language."""
    from ml.evaluation.model_comparison import ModelComparator
    from eval.models import Language

    comparator = ModelComparator()
    result = comparator.compare_on_language(Language.ENGLISH)

    assert result.language == Language.ENGLISH
    assert result.rules_metrics is not None
    assert result.ml_metrics is not None
    assert result.hybrid_metrics is not None
    assert result.best_model in ["Rules-based", "ML-based", "Hybrid (Rules+ML)"]


def test_model_comparison_all_languages():
    """Test model comparison across all languages."""
    from ml.evaluation.model_comparison import ModelComparator

    comparator = ModelComparator()
    results = comparator.compare_all_languages()

    assert len(results) > 0
    for language, result in results.items():
        assert result.language == language
        assert result.rules_metrics.samples_evaluated > 0


def test_model_comparison_report_generation(tmp_path):
    """Test comparison report generation."""
    from ml.evaluation.model_comparison import ModelComparator
    from eval.models import Language

    comparator = ModelComparator()
    result = comparator.compare_on_language(Language.ENGLISH)

    output_file = tmp_path / "comparison_report.txt"

    # Generate report
    report = comparator.generate_report(
        {Language.ENGLISH: result},
        output_file
    )

    assert output_file.exists()
    assert "Model Comparison Report" in report
    assert "Rules-based" in report
    assert "ML-based" in report
    assert "Hybrid" in report


def test_compare_models_cli_integration():
    """Test compare_models.py CLI works."""
    result = subprocess.run(
        [
            sys.executable,
            "compare_models.py",
            "--language", "en"
        ],
        capture_output=True,
        text=True,
        timeout=30
    )

    assert result.returncode == 0
    assert "Model Comparison" in result.stdout
    assert "Rules-based" in result.stdout
    assert "ML-based" in result.stdout
    assert "Hybrid" in result.stdout
    assert "Best Model:" in result.stdout


# End-to-End Integration Tests

def test_full_pipeline_data_to_training_to_evaluation(tmp_path):
    """Test complete pipeline: collect data → train → evaluate → compare."""
    from scripts.data_collection.base_collector import CollectionConfig
    from scripts.data_collection.wikipedia_collector import GroundTruthCollector
    from ml.training.config import TrainingConfig
    from ml.training.trainer import BiasDetectionTrainer
    from ml.evaluation.model_comparison import ModelComparator
    from eval.models import Language

    language = Language.ENGLISH

    # Step 1: Collect data
    collection_config = CollectionConfig(
        language="en",
        max_items=20,
        output_file=tmp_path / "data.csv"
    )
    collector = GroundTruthCollector(collection_config)
    samples_collected = collector.collect()
    collector.save_samples(samples_collected)

    assert len(samples_collected) > 0

    # Step 2: Train model
    training_config = TrainingConfig(
        language=language,
        num_epochs=1,
        model_output_dir=tmp_path / "models"
    )
    trainer = BiasDetectionTrainer(training_config)
    train_data, val_data, test_data = trainer.load_data()
    training_result = trainer.train(train_data, val_data)

    assert training_result.success
    assert training_result.model_path.exists()

    # Step 3: Evaluate on test set
    test_metrics = trainer.evaluate(test_data)
    assert test_metrics['test_f1'] >= 0

    # Step 4: Compare models
    comparator = ModelComparator()
    comparison = comparator.compare_on_language(language)

    assert comparison.best_model is not None


def test_week2_all_scripts_are_executable():
    """Test all Week 2 scripts can be executed."""
    scripts = [
        "scripts/data_collection/cli.py",
        "train_ml_model.py",
        "compare_models.py"
    ]

    for script in scripts:
        path = Path(script)
        assert path.exists(), f"Script not found: {script}"

        # Test help works
        result = subprocess.run(
            [sys.executable, str(path), "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode == 0, f"Script failed: {script}"
        assert len(result.stdout) > 0, f"No help output: {script}"


def test_week2_data_flows_correctly():
    """Test data flows correctly through Week 2 components."""
    from scripts.data_collection.base_collector import CollectionConfig, CollectedSample
    from ml.training.config import TrainingConfig
    from eval.models import Language

    # Data collection produces CollectedSample
    config = CollectionConfig(language="en", max_items=5, output_file=Path("/tmp/test.csv"))
    from scripts.data_collection.wikipedia_collector import GroundTruthCollector
    collector = GroundTruthCollector(config)
    samples = collector.collect()

    assert all(isinstance(s, CollectedSample) for s in samples)
    assert all(s.language == "en" for s in samples)

    # Training config accepts Language enum
    train_config = TrainingConfig(language=Language.ENGLISH)
    assert train_config.language == Language.ENGLISH


@pytest.mark.slow
def test_week2_full_workflow_all_languages(tmp_path):
    """Test complete Week 2 workflow for all languages."""
    from ml.training.config import TrainingConfig
    from ml.training.trainer import BiasDetectionTrainer
    from ml.evaluation.model_comparison import ModelComparator
    from eval.models import Language

    languages = [Language.ENGLISH, Language.SWAHILI, Language.FRENCH, Language.GIKUYU]

    for language in languages:
        # Train
        config = TrainingConfig(
            language=language,
            num_epochs=1,
            model_output_dir=tmp_path / "models" / language.value
        )
        trainer = BiasDetectionTrainer(config)
        train_data, val_data, test_data = trainer.load_data()

        if len(train_data) == 0:
            continue

        result = trainer.train(train_data, val_data)
        assert result.success, f"Training failed for {language}"

        # Evaluate
        metrics = trainer.evaluate(test_data)
        assert metrics['test_f1'] >= 0

    # Compare all
    comparator = ModelComparator()
    comparisons = comparator.compare_all_languages()

    assert len(comparisons) > 0
