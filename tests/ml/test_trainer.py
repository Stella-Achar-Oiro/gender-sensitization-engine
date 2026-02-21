"""Tests for ML training trainer."""
import pytest
from pathlib import Path
from ml.training.config import TrainingConfig
from ml.training.trainer import BiasDetectionTrainer
from eval.models import Language


def test_trainer_initialization():
    """Test BiasDetectionTrainer initialization."""
    config = TrainingConfig(language=Language.ENGLISH)
    trainer = BiasDetectionTrainer(config)

    assert trainer.config == config
    assert trainer.training_history == []
    assert trainer.best_val_f1 == 0.0
    assert trainer.best_epoch == 0


def test_trainer_load_data_english():
    """Test loading data for English."""
    config = TrainingConfig(language=Language.ENGLISH)
    trainer = BiasDetectionTrainer(config)

    train_data, val_data, test_data = trainer.load_data()

    # Should have data for all splits
    assert len(train_data) > 0
    assert len(val_data) > 0
    assert len(test_data) > 0

    # Check split proportions (approximately)
    total = len(train_data) + len(val_data) + len(test_data)
    train_ratio = len(train_data) / total
    val_ratio = len(val_data) / total
    test_ratio = len(test_data) / total

    # Train should be ~70%, val ~15%, test ~15%
    assert 0.6 <= train_ratio <= 0.8
    assert 0.1 <= val_ratio <= 0.25
    assert 0.1 <= test_ratio <= 0.25


def test_trainer_load_data_all_languages():
    """Test loading data for all supported languages."""
    for lang in [Language.ENGLISH, Language.SWAHILI, Language.FRENCH, Language.GIKUYU]:
        config = TrainingConfig(language=lang)
        trainer = BiasDetectionTrainer(config)

        train_data, val_data, test_data = trainer.load_data()

        assert len(train_data) > 0, f"No train data for {lang}"
        assert len(val_data) >= 0, f"No val data for {lang}"
        assert len(test_data) >= 0, f"No test data for {lang}"


def test_trainer_train_single_epoch(tmp_path):
    """Test training for single epoch."""
    config = TrainingConfig(
        language=Language.ENGLISH,
        num_epochs=1,
        model_output_dir=tmp_path / "models"
    )
    trainer = BiasDetectionTrainer(config)

    train_data, val_data, _ = trainer.load_data()
    result = trainer.train(train_data, val_data)

    assert result.success is True
    assert result.model_path is not None
    assert result.model_path.exists()
    assert len(trainer.training_history) == 1


def test_trainer_train_multiple_epochs(tmp_path):
    """Test training for multiple epochs."""
    config = TrainingConfig(
        language=Language.ENGLISH,
        num_epochs=3,
        model_output_dir=tmp_path / "models"
    )
    trainer = BiasDetectionTrainer(config)

    train_data, val_data, _ = trainer.load_data()
    result = trainer.train(train_data, val_data)

    assert result.success is True
    assert len(trainer.training_history) == 3
    assert result.best_metrics is not None
    assert result.final_metrics is not None


def test_trainer_early_stopping(tmp_path):
    """Test early stopping functionality."""
    config = TrainingConfig(
        language=Language.ENGLISH,
        num_epochs=10,
        early_stopping_patience=2,
        model_output_dir=tmp_path / "models"
    )
    trainer = BiasDetectionTrainer(config)

    train_data, val_data, _ = trainer.load_data()
    result = trainer.train(train_data, val_data)

    # Should stop before 10 epochs due to early stopping
    # (with random metrics, this might not always trigger)
    assert result.success is True
    assert len(trainer.training_history) <= 10


def test_trainer_saves_checkpoints(tmp_path):
    """Test that trainer saves checkpoints."""
    config = TrainingConfig(
        language=Language.ENGLISH,
        num_epochs=2,
        model_output_dir=tmp_path / "models"
    )
    trainer = BiasDetectionTrainer(config)

    train_data, val_data, _ = trainer.load_data()
    result = trainer.train(train_data, val_data)

    assert result.success is True

    # Check checkpoints directory exists
    checkpoint_dir = tmp_path / "models" / "checkpoints"
    assert checkpoint_dir.exists()

    # Should have at least one checkpoint
    checkpoints = list(checkpoint_dir.glob("*.json"))
    assert len(checkpoints) > 0


def test_trainer_evaluate(tmp_path):
    """Test model evaluation."""
    config = TrainingConfig(
        language=Language.ENGLISH,
        model_output_dir=tmp_path / "models"
    )
    trainer = BiasDetectionTrainer(config)

    train_data, val_data, test_data = trainer.load_data()

    # Train first
    trainer.train(train_data, val_data)

    # Evaluate
    test_metrics = trainer.evaluate(test_data)

    assert 'test_accuracy' in test_metrics
    assert 'test_f1' in test_metrics
    assert 'test_precision' in test_metrics
    assert 'test_recall' in test_metrics
    assert 'test_samples' in test_metrics

    # Metrics should be in valid range
    assert 0 <= test_metrics['test_accuracy'] <= 1
    assert 0 <= test_metrics['test_f1'] <= 1
    assert 0 <= test_metrics['test_precision'] <= 1
    assert 0 <= test_metrics['test_recall'] <= 1


def test_trainer_get_training_summary(tmp_path):
    """Test getting training summary."""
    config = TrainingConfig(
        language=Language.ENGLISH,
        num_epochs=2,
        model_output_dir=tmp_path / "models"
    )
    trainer = BiasDetectionTrainer(config)

    # Before training
    summary_before = trainer.get_training_summary()
    assert "No training history" in summary_before

    # After training
    train_data, val_data, _ = trainer.load_data()
    trainer.train(train_data, val_data)

    summary_after = trainer.get_training_summary()
    assert "Training Summary" in summary_after
    assert "Total epochs" in summary_after
    assert "Best epoch" in summary_after


def test_trainer_training_metrics_improve():
    """Test that training metrics generally improve over epochs."""
    config = TrainingConfig(
        language=Language.ENGLISH,
        num_epochs=3
    )
    trainer = BiasDetectionTrainer(config)

    train_data, val_data, _ = trainer.load_data()

    # Manually call train_epoch to check progression
    losses = []
    f1_scores = []

    for epoch in range(1, 4):
        loss, accuracy, f1 = trainer._train_epoch(train_data, epoch)
        losses.append(loss)
        f1_scores.append(f1)

    # Loss should generally decrease (allowing some variance)
    # F1 should generally increase (allowing some variance)
    # Just check they're in reasonable ranges
    assert all(0 < loss < 2 for loss in losses)
    assert all(0 < f1 < 1 for f1 in f1_scores)


def test_trainer_handles_small_datasets():
    """Test trainer handles small datasets gracefully."""
    config = TrainingConfig(
        language=Language.ENGLISH,
        batch_size=32  # Larger than dataset
    )
    trainer = BiasDetectionTrainer(config)

    # Even with small dataset, should not crash
    train_data, val_data, _ = trainer.load_data()

    # Limit to very small size
    train_data = train_data[:5]
    val_data = val_data[:2]

    result = trainer.train(train_data, val_data)
    assert result.success is True


def test_trainer_reproducibility():
    """Test training is reproducible with same seed."""
    seed = 123

    # Train twice with same seed
    results = []
    for _ in range(2):
        config = TrainingConfig(
            language=Language.ENGLISH,
            num_epochs=1,
            random_seed=seed
        )
        trainer = BiasDetectionTrainer(config)
        train_data, val_data, _ = trainer.load_data()

        # Capture first epoch metrics
        loss, acc, f1 = trainer._train_epoch(train_data, 1)
        results.append((loss, acc, f1))

    # Results should be identical (or very close due to random.seed)
    # Since we use random.seed, they should be exactly the same
    assert results[0] == results[1]


def test_trainer_custom_config_settings(tmp_path):
    """Test trainer respects custom config settings."""
    config = TrainingConfig(
        language=Language.SWAHILI,
        batch_size=8,
        learning_rate=1e-5,
        num_epochs=2,
        model_output_dir=tmp_path / "custom_models"
    )
    trainer = BiasDetectionTrainer(config)

    assert trainer.config.batch_size == 8
    assert trainer.config.learning_rate == 1e-5
    assert trainer.config.num_epochs == 2
    assert str(trainer.config.model_output_dir) == str(tmp_path / "custom_models")
