#!/usr/bin/env python3
"""
JuaKazi Full Pipeline Demo - End-to-End Demonstration

Demonstrates complete workflow:
1. Data Collection (loads from ground truth)
2. Bias Detection (Rules + ML hybrid)
3. Correction & Evaluation
4. AI BRIDGE Metrics

Usage:
    python3 demos/demo_full_pipeline.py --language sw --samples 100
    python3 demos/demo_full_pipeline.py --language en --samples 50 --no-ml
    python3 demos/demo_full_pipeline.py -l ki -n 20 --verbose
"""
import argparse
import sys
from pathlib import Path
from typing import List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from demos.pipeline_config import PipelineConfig
from demos.stages import DataCollectionStage, BiasDetectionStage, EvaluationStage, StageResult
from eval.models import Language


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="JuaKazi Full Pipeline Demo - End-to-End Gender Bias Detection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --language sw --samples 100
  %(prog)s -l en -n 50 --no-ml
  %(prog)s -l ki -n 20 --output results/
        """
    )
    parser.add_argument(
        "--language", "-l",
        type=str,
        required=True,
        choices=["en", "sw", "fr", "ki"],
        help="Language code (en=English, sw=Swahili, fr=French, ki=Gikuyu)"
    )
    parser.add_argument(
        "--samples", "-n",
        type=int,
        default=100,
        help="Number of samples to process (default: 100, min: 10)"
    )
    parser.add_argument(
        "--no-ml",
        action="store_true",
        help="Disable ML fallback (rules only)"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=Path("demos/output"),
        help="Output directory for results (default: demos/output)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress verbose output"
    )
    return parser.parse_args()


def print_header(title: str, width: int = 60):
    """Print formatted header."""
    print("=" * width)
    print(title.center(width))
    print("=" * width)


def print_stage_result(result: StageResult, stage_num: int):
    """Print formatted stage result."""
    status = "✓" if result.success else "✗"
    print(f"\n{status} Stage {stage_num}: {result.stage_name}")
    print(f"  Samples processed: {result.samples_processed}")
    print(f"  {result.output_summary}")
    if result.metrics and result.success:
        print("  Metrics:")
        for key, value in result.metrics.items():
            if isinstance(value, float):
                print(f"    - {key}: {value:.3f}")
            else:
                print(f"    - {key}: {value}")


def main():
    """Run full pipeline demo."""
    args = parse_args()

    # Map language code to enum
    lang_map = {
        "en": Language.ENGLISH,
        "sw": Language.SWAHILI,
        "fr": Language.FRENCH,
        "ki": Language.GIKUYU
    }
    language = lang_map[args.language]

    # Configure pipeline
    try:
        config = PipelineConfig(
            language=language,
            sample_size=args.samples,
            enable_ml=not args.no_ml,
            output_dir=args.output,
            verbose=not args.quiet
        )
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Print header
    if config.verbose:
        print_header("JuaKazi Gender Sensitization Engine")
        print("Full Pipeline Demo - End-to-End Demonstration")
        print_header("")
        print(f"Language: {language.value}")
        print(f"Samples: {args.samples}")
        print(f"ML Enabled: {config.enable_ml}")
        print(f"Output: {config.output_dir}")
        print("=" * 60)

    # Stage 1: Data Collection
    if config.verbose:
        print("\n[1/3] Data Collection...")
    data_stage = DataCollectionStage()
    result1, samples = data_stage.run(language, config.sample_size)

    if config.verbose:
        print_stage_result(result1, 1)

    if not result1.success:
        print("\n❌ Pipeline failed at Stage 1: Data Collection", file=sys.stderr)
        return 1

    # Stage 2: Bias Detection
    if config.verbose:
        print("\n[2/3] Bias Detection...")
    texts = [s.text for s in samples]
    detection_stage = BiasDetectionStage(enable_ml=config.enable_ml)
    result2, detections = detection_stage.run(texts, language)

    if config.verbose:
        print_stage_result(result2, 2)

    if not result2.success:
        print("\n❌ Pipeline failed at Stage 2: Bias Detection", file=sys.stderr)
        return 1

    # Stage 3: Evaluation
    if config.verbose:
        print("\n[3/3] Evaluation...")
    evaluation_stage = EvaluationStage()
    result3 = evaluation_stage.run(samples, detections)

    if config.verbose:
        print_stage_result(result3, 3)

    if not result3.success:
        print("\n❌ Pipeline failed at Stage 3: Evaluation", file=sys.stderr)
        return 1

    # Success summary
    if config.verbose:
        print("\n" + "=" * 60)
        print("✓ Pipeline Complete".center(60))
        print("=" * 60)
        print(f"Total samples processed: {result1.samples_processed}")
        print(f"Bias detected: {result2.metrics.get('detection_rate', 0):.1%}")
        print(f"F1 Score: {result3.metrics.get('f1', 0):.3f}")
        print(f"Precision: {result3.metrics.get('precision', 0):.3f} (perfect=1.000)")
        print(f"Recall: {result3.metrics.get('recall', 0):.3f}")
        print(f"\nOutput saved to: {config.output_dir}")
        print("\nNext steps:")
        print("  - Review results in output directory")
        print("  - Run evaluation: python3 run_evaluation.py")
        print("  - See REPRODUCIBILITY.md for full workflow")
    else:
        # Quiet mode - just print key metrics
        print(f"F1: {result3.metrics.get('f1', 0):.3f}, "
              f"Precision: {result3.metrics.get('precision', 0):.3f}, "
              f"Recall: {result3.metrics.get('recall', 0):.3f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
