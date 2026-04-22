"""Training configuration for ML bias detection models."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List
from eval.models import Language


@dataclass
class TrainingConfig:
    """Configuration for model training."""

    # Model settings
    model_name: str = "xlm-roberta-base"  # Multilingual transformer
    model_output_dir: Path = Path("models/bias_detector")

    # Training data
    train_data_path: Optional[Path] = None
    val_data_path: Optional[Path] = None
    test_data_path: Optional[Path] = None

    # Language settings
    language: Language = Language.ENGLISH
    languages: List[Language] = field(default_factory=lambda: [
        Language.ENGLISH,
        Language.SWAHILI,
        Language.FRENCH,
        Language.GIKUYU
    ])

    # Training hyperparameters
    batch_size: int = 16
    learning_rate: float = 2e-5
    num_epochs: int = 3
    max_length: int = 128
    warmup_steps: int = 500
    weight_decay: float = 0.01

    # Early stopping
    early_stopping_patience: int = 3
    early_stopping_threshold: float = 0.01

    # Logging
    log_dir: Path = Path("ml/logs")
    save_steps: int = 500
    eval_steps: int = 500
    logging_steps: int = 100

    # Hardware
    use_gpu: bool = True
    fp16: bool = False  # Mixed precision training

    # Data augmentation
    augment_data: bool = False
    augmentation_factor: int = 2

    # Class weights (for imbalanced data)
    use_class_weights: bool = True
    positive_class_weight: float = 2.0

    # Seed for reproducibility
    random_seed: int = 42

    def __post_init__(self):
        """Validate configuration."""
        if self.batch_size < 1:
            raise ValueError("batch_size must be >= 1")

        if self.learning_rate <= 0:
            raise ValueError("learning_rate must be > 0")

        if self.num_epochs < 1:
            raise ValueError("num_epochs must be >= 1")

        if self.max_length < 10:
            raise ValueError("max_length must be >= 10")

        # Create directories
        self.model_output_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def to_dict(self) -> dict:
        """Convert config to dictionary."""
        return {
            'model_name': self.model_name,
            'model_output_dir': str(self.model_output_dir),
            'language': self.language.value if hasattr(self.language, 'value') else str(self.language),
            'batch_size': self.batch_size,
            'learning_rate': self.learning_rate,
            'num_epochs': self.num_epochs,
            'max_length': self.max_length,
            'warmup_steps': self.warmup_steps,
            'weight_decay': self.weight_decay,
            'early_stopping_patience': self.early_stopping_patience,
            'random_seed': self.random_seed,
            'use_gpu': self.use_gpu,
            'fp16': self.fp16,
        }

    def summary(self) -> str:
        """Get human-readable summary."""
        return f"""Training Configuration:
  Model: {self.model_name}
  Language: {self.language.value if hasattr(self.language, 'value') else str(self.language)}
  Batch size: {self.batch_size}
  Learning rate: {self.learning_rate}
  Epochs: {self.num_epochs}
  Max length: {self.max_length}
  Output: {self.model_output_dir}
  GPU: {self.use_gpu}
  FP16: {self.fp16}
"""


@dataclass
class TrainingMetrics:
    """Metrics tracked during training."""

    epoch: int
    train_loss: float
    val_loss: Optional[float] = None
    train_accuracy: Optional[float] = None
    val_accuracy: Optional[float] = None
    train_f1: Optional[float] = None
    val_f1: Optional[float] = None
    train_precision: Optional[float] = None
    val_precision: Optional[float] = None
    train_recall: Optional[float] = None
    val_recall: Optional[float] = None
    learning_rate: Optional[float] = None

    def to_dict(self) -> dict:
        """Convert metrics to dictionary."""
        return {
            'epoch': self.epoch,
            'train_loss': self.train_loss,
            'val_loss': self.val_loss,
            'train_accuracy': self.train_accuracy,
            'val_accuracy': self.val_accuracy,
            'train_f1': self.train_f1,
            'val_f1': self.val_f1,
            'train_precision': self.train_precision,
            'val_precision': self.val_precision,
            'train_recall': self.train_recall,
            'val_recall': self.val_recall,
            'learning_rate': self.learning_rate,
        }

    def summary(self) -> str:
        """Get human-readable summary."""
        lines = [f"Epoch {self.epoch}:"]
        lines.append(f"  Train Loss: {self.train_loss:.4f}")

        if self.val_loss is not None:
            lines.append(f"  Val Loss: {self.val_loss:.4f}")

        if self.train_f1 is not None:
            lines.append(f"  Train F1: {self.train_f1:.4f}")

        if self.val_f1 is not None:
            lines.append(f"  Val F1: {self.val_f1:.4f}")

        if self.val_precision is not None and self.val_recall is not None:
            lines.append(f"  Val Precision: {self.val_precision:.4f}, Recall: {self.val_recall:.4f}")

        return "\n".join(lines)


@dataclass
class TrainingResult:
    """Result from training process."""

    success: bool
    model_path: Optional[Path] = None
    final_metrics: Optional[TrainingMetrics] = None
    best_metrics: Optional[TrainingMetrics] = None
    training_history: List[TrainingMetrics] = field(default_factory=list)
    error_message: Optional[str] = None

    def summary(self) -> str:
        """Get human-readable summary."""
        if not self.success:
            return f"Training failed: {self.error_message}"

        lines = ["Training completed successfully!"]

        if self.model_path:
            lines.append(f"  Model saved to: {self.model_path}")

        if self.best_metrics:
            lines.append(f"  Best Val F1: {self.best_metrics.val_f1:.4f} (Epoch {self.best_metrics.epoch})")

        if self.final_metrics:
            lines.append(f"  Final Train Loss: {self.final_metrics.train_loss:.4f}")
            if self.final_metrics.val_loss:
                lines.append(f"  Final Val Loss: {self.final_metrics.val_loss:.4f}")

        lines.append(f"  Total epochs: {len(self.training_history)}")

        return "\n".join(lines)
