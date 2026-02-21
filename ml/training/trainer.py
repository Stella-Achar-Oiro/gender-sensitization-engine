"""ML model trainer for bias detection."""
import json
import random
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime

from .config import TrainingConfig, TrainingMetrics, TrainingResult
from eval.models import Language, GroundTruthSample
from eval.data_loader import GroundTruthLoader


class BiasDetectionTrainer:
    """
    Trainer for bias detection models.

    This is a simplified implementation that demonstrates the training workflow.
    In production, this would integrate with transformers library (HuggingFace).
    """

    def __init__(self, config: TrainingConfig):
        """
        Initialize trainer.

        Args:
            config: Training configuration
        """
        self.config = config
        self.training_history: List[TrainingMetrics] = []
        self.best_val_f1 = 0.0
        self.best_epoch = 0

        # Set random seed
        random.seed(config.random_seed)

    def load_data(self, language: Optional[Language] = None) -> Tuple[List[GroundTruthSample], List[GroundTruthSample], List[GroundTruthSample]]:
        """
        Load training, validation, and test data.

        Args:
            language: Language to load data for (uses config if not specified)

        Returns:
            Tuple of (train_samples, val_samples, test_samples)
        """
        lang = language or self.config.language
        loader = GroundTruthLoader()

        # Load all samples for language
        all_samples = loader.load_ground_truth(lang)

        if not all_samples:
            raise ValueError(f"No data found for language: {lang}")

        # Shuffle
        random.shuffle(all_samples)

        # Split: 70% train, 15% val, 15% test
        n_total = len(all_samples)
        n_train = int(0.7 * n_total)
        n_val = int(0.15 * n_total)

        train_samples = all_samples[:n_train]
        val_samples = all_samples[n_train:n_train + n_val]
        test_samples = all_samples[n_train + n_val:]

        return train_samples, val_samples, test_samples

    def train(self, train_data: List[GroundTruthSample], val_data: List[GroundTruthSample]) -> TrainingResult:
        """
        Train the model.

        Args:
            train_data: Training samples
            val_data: Validation samples

        Returns:
            TrainingResult with training outcome
        """
        try:
            print(f"Starting training for {self.config.language.value}")
            print(f"Train samples: {len(train_data)}")
            print(f"Val samples: {len(val_data)}")
            print(f"Model: {self.config.model_name}")
            print(f"Epochs: {self.config.num_epochs}")
            print()

            # Training loop
            for epoch in range(1, self.config.num_epochs + 1):
                print(f"Epoch {epoch}/{self.config.num_epochs}")

                # Train epoch
                train_loss, train_accuracy, train_f1 = self._train_epoch(train_data, epoch)

                # Validation
                val_loss, val_accuracy, val_f1, val_precision, val_recall = self._validate(val_data)

                # Record metrics
                metrics = TrainingMetrics(
                    epoch=epoch,
                    train_loss=train_loss,
                    val_loss=val_loss,
                    train_accuracy=train_accuracy,
                    val_accuracy=val_accuracy,
                    train_f1=train_f1,
                    val_f1=val_f1,
                    train_precision=None,  # Not computed for training
                    val_precision=val_precision,
                    train_recall=None,
                    val_recall=val_recall,
                    learning_rate=self.config.learning_rate
                )
                self.training_history.append(metrics)

                print(metrics.summary())
                print()

                # Check for best model
                if val_f1 > self.best_val_f1:
                    self.best_val_f1 = val_f1
                    self.best_epoch = epoch
                    self._save_checkpoint(epoch, val_f1)

                # Early stopping
                if self._should_stop_early(epoch):
                    print(f"Early stopping at epoch {epoch}")
                    break

            # Save final model
            model_path = self._save_model()

            # Get best metrics
            best_metrics = None
            for m in self.training_history:
                if m.epoch == self.best_epoch:
                    best_metrics = m
                    break

            return TrainingResult(
                success=True,
                model_path=model_path,
                final_metrics=self.training_history[-1],
                best_metrics=best_metrics,
                training_history=self.training_history
            )

        except Exception as e:
            return TrainingResult(
                success=False,
                error_message=str(e)
            )

    def _train_epoch(self, train_data: List[GroundTruthSample], epoch: int) -> Tuple[float, float, float]:
        """
        Train for one epoch (simplified simulation).

        In production, this would:
        - Create data batches
        - Forward pass through model
        - Calculate loss
        - Backward pass
        - Update weights

        Args:
            train_data: Training samples
            epoch: Current epoch number

        Returns:
            Tuple of (loss, accuracy, f1)
        """
        # Simulate training progress
        # Loss decreases over epochs, metrics improve
        base_loss = 0.8
        loss_improvement = 0.15 * (epoch / self.config.num_epochs)
        train_loss = max(0.1, base_loss - loss_improvement + random.uniform(-0.05, 0.05))

        # Accuracy improves with training
        base_accuracy = 0.65
        accuracy_improvement = 0.25 * (epoch / self.config.num_epochs)
        train_accuracy = min(0.95, base_accuracy + accuracy_improvement + random.uniform(-0.03, 0.03))

        # F1 improves similarly
        base_f1 = 0.60
        f1_improvement = 0.30 * (epoch / self.config.num_epochs)
        train_f1 = min(0.95, base_f1 + f1_improvement + random.uniform(-0.03, 0.03))

        return train_loss, train_accuracy, train_f1

    def _validate(self, val_data: List[GroundTruthSample]) -> Tuple[float, float, float, float, float]:
        """
        Validate model (simplified simulation).

        Args:
            val_data: Validation samples

        Returns:
            Tuple of (loss, accuracy, f1, precision, recall)
        """
        # Validation metrics typically slightly worse than training
        # Simulate realistic validation performance
        val_loss = random.uniform(0.3, 0.6)
        val_accuracy = random.uniform(0.75, 0.90)

        # Calculate precision and recall
        val_precision = random.uniform(0.80, 0.95)
        val_recall = random.uniform(0.70, 0.85)

        # F1 is harmonic mean of precision and recall
        if val_precision + val_recall > 0:
            val_f1 = 2 * (val_precision * val_recall) / (val_precision + val_recall)
        else:
            val_f1 = 0.0

        return val_loss, val_accuracy, val_f1, val_precision, val_recall

    def _should_stop_early(self, current_epoch: int) -> bool:
        """
        Check if training should stop early.

        Args:
            current_epoch: Current epoch number

        Returns:
            True if should stop early
        """
        if current_epoch < self.config.early_stopping_patience:
            return False

        # Check if no improvement in last N epochs
        epochs_since_best = current_epoch - self.best_epoch

        return epochs_since_best >= self.config.early_stopping_patience

    def _save_checkpoint(self, epoch: int, val_f1: float):
        """
        Save model checkpoint.

        Args:
            epoch: Current epoch
            val_f1: Validation F1 score
        """
        checkpoint_dir = self.config.model_output_dir / "checkpoints"
        checkpoint_dir.mkdir(parents=True, exist_ok=True)

        checkpoint_file = checkpoint_dir / f"epoch_{epoch}_f1_{val_f1:.4f}.json"

        checkpoint_data = {
            'epoch': epoch,
            'val_f1': val_f1,
            'config': self.config.to_dict(),
            'timestamp': datetime.now().isoformat()
        }

        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)

    def _save_model(self) -> Path:
        """
        Save final trained model.

        Returns:
            Path to saved model
        """
        model_file = self.config.model_output_dir / "final_model.json"

        model_data = {
            'model_name': self.config.model_name,
            'language': self.config.language.value,
            'best_epoch': self.best_epoch,
            'best_val_f1': self.best_val_f1,
            'config': self.config.to_dict(),
            'training_history': [m.to_dict() for m in self.training_history],
            'timestamp': datetime.now().isoformat()
        }

        with open(model_file, 'w') as f:
            json.dump(model_data, f, indent=2)

        print(f"Model saved to: {model_file}")
        return model_file

    def evaluate(self, test_data: List[GroundTruthSample]) -> dict:
        """
        Evaluate model on test set.

        Args:
            test_data: Test samples

        Returns:
            Dictionary of evaluation metrics
        """
        # Simulate test evaluation
        test_accuracy = random.uniform(0.80, 0.92)
        test_precision = random.uniform(0.85, 0.98)
        test_recall = random.uniform(0.75, 0.88)

        if test_precision + test_recall > 0:
            test_f1 = 2 * (test_precision * test_recall) / (test_precision + test_recall)
        else:
            test_f1 = 0.0

        return {
            'test_accuracy': test_accuracy,
            'test_f1': test_f1,
            'test_precision': test_precision,
            'test_recall': test_recall,
            'test_samples': len(test_data)
        }

    def get_training_summary(self) -> str:
        """
        Get human-readable training summary.

        Returns:
            Summary string
        """
        if not self.training_history:
            return "No training history available"

        lines = ["Training Summary:"]
        lines.append(f"  Total epochs: {len(self.training_history)}")
        lines.append(f"  Best epoch: {self.best_epoch}")
        lines.append(f"  Best Val F1: {self.best_val_f1:.4f}")

        if self.training_history:
            final = self.training_history[-1]
            lines.append(f"  Final Train Loss: {final.train_loss:.4f}")
            if final.val_loss:
                lines.append(f"  Final Val Loss: {final.val_loss:.4f}")

        return "\n".join(lines)
