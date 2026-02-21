#!/usr/bin/env python3
"""
Train ML Model for Bias Detection

Usage:
    python3 train_ml_model.py --language sw --epochs 5
    python3 train_ml_model.py --language en --epochs 3 --batch-size 32
    python3 train_ml_model.py --help
"""
import argparse
import sys
from pathlib import Path

from ml.training.config import TrainingConfig
from ml.training.trainer import BiasDetectionTrainer
from eval.models import Language


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Train ML model for gender bias detection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Train for Swahili
  %(prog)s --language sw --epochs 5

  # Train for English with custom settings
  %(prog)s --language en --epochs 3 --batch-size 32 --learning-rate 1e-5

  # Train all languages
  %(prog)s --all-languages --epochs 3
        """
    )

    parser.add_argument(
        '--language', '-l',
        type=str,
        choices=['en', 'sw', 'fr', 'ki'],
        help='Language to train model for'
    )
    parser.add_argument(
        '--all-languages',
        action='store_true',
        help='Train models for all languages'
    )
    parser.add_argument(
        '--epochs', '-e',
        type=int,
        default=3,
        help='Number of training epochs (default: 3)'
    )
    parser.add_argument(
        '--batch-size', '-b',
        type=int,
        default=16,
        help='Batch size (default: 16)'
    )
    parser.add_argument(
        '--learning-rate', '-lr',
        type=float,
        default=2e-5,
        help='Learning rate (default: 2e-5)'
    )
    parser.add_argument(
        '--model-name', '-m',
        type=str,
        default='xlm-roberta-base',
        help='Base model name (default: xlm-roberta-base)'
    )
    parser.add_argument(
        '--output-dir', '-o',
        type=Path,
        default=Path('models/bias_detector'),
        help='Output directory for models (default: models/bias_detector)'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed (default: 42)'
    )
    parser.add_argument(
        '--no-gpu',
        action='store_true',
        help='Disable GPU training'
    )
    parser.add_argument(
        '--fp16',
        action='store_true',
        help='Enable mixed precision (FP16) training'
    )
    parser.add_argument(
        '--evaluate',
        action='store_true',
        help='Evaluate on test set after training'
    )

    return parser.parse_args()


def train_for_language(language: Language, args) -> bool:
    """
    Train model for specific language.

    Args:
        language: Language to train for
        args: Command line arguments

    Returns:
        True if training succeeded
    """
    print("=" * 70)
    print(f"Training Model for {language.value}".center(70))
    print("=" * 70)
    print()

    # Create configuration
    config = TrainingConfig(
        model_name=args.model_name,
        model_output_dir=args.output_dir / language.value,
        language=language,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        num_epochs=args.epochs,
        random_seed=args.seed,
        use_gpu=not args.no_gpu,
        fp16=args.fp16
    )

    print(config.summary())
    print()

    # Initialize trainer
    trainer = BiasDetectionTrainer(config)

    # Load data
    print("Loading data...")
    try:
        train_data, val_data, test_data = trainer.load_data()
        print(f"✓ Loaded {len(train_data)} train, {len(val_data)} val, {len(test_data)} test samples")
        print()
    except ValueError as e:
        print(f"✗ Error loading data: {e}")
        return False

    # Train
    print("Starting training...")
    print()
    result = trainer.train(train_data, val_data)

    # Print results
    print()
    print("=" * 70)
    print(result.summary())
    print("=" * 70)
    print()

    if not result.success:
        return False

    # Evaluate on test set if requested
    if args.evaluate:
        print("Evaluating on test set...")
        test_metrics = trainer.evaluate(test_data)

        print(f"Test Results:")
        print(f"  Accuracy: {test_metrics['test_accuracy']:.4f}")
        print(f"  F1 Score: {test_metrics['test_f1']:.4f}")
        print(f"  Precision: {test_metrics['test_precision']:.4f}")
        print(f"  Recall: {test_metrics['test_recall']:.4f}")
        print()

    # Print training summary
    print(trainer.get_training_summary())
    print()

    return True


def main():
    """Main entry point."""
    args = parse_args()

    # Validate arguments
    if not args.language and not args.all_languages:
        print("Error: Must specify --language or --all-languages")
        return 1

    if args.language and args.all_languages:
        print("Error: Cannot specify both --language and --all-languages")
        return 1

    # Map language codes to enums
    lang_map = {
        'en': Language.ENGLISH,
        'sw': Language.SWAHILI,
        'fr': Language.FRENCH,
        'ki': Language.GIKUYU
    }

    # Determine languages to train
    if args.all_languages:
        languages = list(lang_map.values())
    else:
        languages = [lang_map[args.language]]

    # Train for each language
    success_count = 0
    for language in languages:
        success = train_for_language(language, args)
        if success:
            success_count += 1

        # Add separator between languages
        if len(languages) > 1 and language != languages[-1]:
            print("\n" + "=" * 70 + "\n")

    # Final summary
    print()
    print("=" * 70)
    print(f"Training Complete: {success_count}/{len(languages)} successful".center(70))
    print("=" * 70)

    return 0 if success_count == len(languages) else 1


if __name__ == "__main__":
    sys.exit(main())
