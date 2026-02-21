"""Tests for ML training configuration."""
import pytest
from pathlib import Path
from ml.training.config import TrainingConfig, TrainingMetrics, TrainingResult
from eval.models import Language


def test_training_config_defaults():
    """Test TrainingConfig with default values."""
    config = TrainingConfig()

    assert config.model_name == "xlm-roberta-base"
    assert config.batch_size == 16
    assert config.learning_rate == 2e-5
    assert config.num_epochs == 3
    assert config.max_length == 128
    assert config.random_seed == 42
    assert config.use_gpu is True
    assert config.fp16 is False


def test_training_config_custom_values():
    """Test TrainingConfig with custom values."""
    config = TrainingConfig(
        model_name="bert-base-multilingual",
        batch_size=32,
        learning_rate=1e-5,
        num_epochs=5,
        random_seed=123
    )

    assert config.model_name == "bert-base-multilingual"
    assert config.batch_size == 32
    assert config.learning_rate == 1e-5
    assert config.num_epochs == 5
    assert config.random_seed == 123


def test_training_config_validation_batch_size():
    """Test TrainingConfig validates batch_size."""
    with pytest.raises(ValueError, match="batch_size must be >= 1"):
        TrainingConfig(batch_size=0)


def test_training_config_validation_learning_rate():
    """Test TrainingConfig validates learning_rate."""
    with pytest.raises(ValueError, match="learning_rate must be > 0"):
        TrainingConfig(learning_rate=0)


def test_training_config_validation_num_epochs():
    """Test TrainingConfig validates num_epochs."""
    with pytest.raises(ValueError, match="num_epochs must be >= 1"):
        TrainingConfig(num_epochs=0)


def test_training_config_validation_max_length():
    """Test TrainingConfig validates max_length."""
    with pytest.raises(ValueError, match="max_length must be >= 10"):
        TrainingConfig(max_length=5)


def test_training_config_creates_directories(tmp_path):
    """Test TrainingConfig creates output directories."""
    model_dir = tmp_path / "models"
    log_dir = tmp_path / "logs"

    config = TrainingConfig(
        model_output_dir=model_dir,
        log_dir=log_dir
    )

    assert model_dir.exists()
    assert log_dir.exists()


def test_training_config_to_dict():
    """Test TrainingConfig.to_dict()."""
    config = TrainingConfig(
        model_name="test-model",
        batch_size=32,
        learning_rate=1e-5
    )

    config_dict = config.to_dict()

    assert isinstance(config_dict, dict)
    assert config_dict['model_name'] == "test-model"
    assert config_dict['batch_size'] == 32
    assert config_dict['learning_rate'] == 1e-5
    assert 'random_seed' in config_dict


def test_training_config_summary():
    """Test TrainingConfig.summary()."""
    config = TrainingConfig(language=Language.SWAHILI)
    summary = config.summary()

    assert isinstance(summary, str)
    assert "Training Configuration" in summary
    assert "xlm-roberta-base" in summary
    assert "sw" in summary or "Swahili" in summary


def test_training_metrics_creation():
    """Test TrainingMetrics creation."""
    metrics = TrainingMetrics(
        epoch=1,
        train_loss=0.5,
        val_loss=0.6,
        train_f1=0.8,
        val_f1=0.75
    )

    assert metrics.epoch == 1
    assert metrics.train_loss == 0.5
    assert metrics.val_loss == 0.6
    assert metrics.train_f1 == 0.8
    assert metrics.val_f1 == 0.75


def test_training_metrics_to_dict():
    """Test TrainingMetrics.to_dict()."""
    metrics = TrainingMetrics(
        epoch=2,
        train_loss=0.4,
        val_f1=0.85
    )

    metrics_dict = metrics.to_dict()

    assert isinstance(metrics_dict, dict)
    assert metrics_dict['epoch'] == 2
    assert metrics_dict['train_loss'] == 0.4
    assert metrics_dict['val_f1'] == 0.85


def test_training_metrics_summary():
    """Test TrainingMetrics.summary()."""
    metrics = TrainingMetrics(
        epoch=3,
        train_loss=0.3,
        val_loss=0.4,
        val_f1=0.9,
        val_precision=0.92,
        val_recall=0.88
    )

    summary = metrics.summary()

    assert isinstance(summary, str)
    assert "Epoch 3" in summary
    assert "0.3" in summary  # train_loss
    assert "0.4" in summary  # val_loss
    assert "0.9" in summary  # val_f1


def test_training_result_success():
    """Test TrainingResult for successful training."""
    metrics = TrainingMetrics(
        epoch=3,
        train_loss=0.2,
        val_f1=0.95
    )

    result = TrainingResult(
        success=True,
        model_path=Path("models/test.pt"),
        best_metrics=metrics,
        final_metrics=metrics
    )

    assert result.success is True
    assert result.model_path == Path("models/test.pt")
    assert result.best_metrics == metrics
    assert result.error_message is None


def test_training_result_failure():
    """Test TrainingResult for failed training."""
    result = TrainingResult(
        success=False,
        error_message="Training failed due to OOM"
    )

    assert result.success is False
    assert result.error_message == "Training failed due to OOM"
    assert result.model_path is None


def test_training_result_summary_success():
    """Test TrainingResult.summary() for success."""
    metrics = TrainingMetrics(
        epoch=5,
        train_loss=0.1,
        val_loss=0.15,
        val_f1=0.92
    )

    result = TrainingResult(
        success=True,
        model_path=Path("models/final.pt"),
        best_metrics=metrics,
        final_metrics=metrics,
        training_history=[metrics]
    )

    summary = result.summary()

    assert "Training completed successfully" in summary
    assert "models/final.pt" in summary
    assert "0.92" in summary  # val_f1


def test_training_result_summary_failure():
    """Test TrainingResult.summary() for failure."""
    result = TrainingResult(
        success=False,
        error_message="CUDA out of memory"
    )

    summary = result.summary()

    assert "Training failed" in summary
    assert "CUDA out of memory" in summary


def test_training_config_language_settings():
    """Test TrainingConfig language settings."""
    config = TrainingConfig(language=Language.GIKUYU)

    assert config.language == Language.GIKUYU
    assert Language.GIKUYU in config.languages


def test_training_config_early_stopping():
    """Test TrainingConfig early stopping settings."""
    config = TrainingConfig(
        early_stopping_patience=5,
        early_stopping_threshold=0.001
    )

    assert config.early_stopping_patience == 5
    assert config.early_stopping_threshold == 0.001


def test_training_config_class_weights():
    """Test TrainingConfig class weight settings."""
    config = TrainingConfig(
        use_class_weights=True,
        positive_class_weight=3.0
    )

    assert config.use_class_weights is True
    assert config.positive_class_weight == 3.0
