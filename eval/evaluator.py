"""
Main evaluation orchestrator for bias detection framework.

This module coordinates the evaluation process and provides the main interface
for running evaluations.
"""
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .models import Language, LanguageEvaluationResult
from .data_loader import GroundTruthLoader, ResultsWriter, DataLoadError
from .bias_detector import BiasDetector, BiasDetectionError
from .metrics_calculator import MetricsCalculator, MetricsFormatter


class EvaluationError(Exception):
    """Custom exception for evaluation errors."""
    pass


class BiasEvaluationOrchestrator:
    """
    Main orchestrator for bias detection evaluation.
    
    Coordinates data loading, bias detection, metrics calculation, and result output.
    Provides a clean interface for running complete evaluations.
    """
    
    def __init__(
        self,
        data_dir: Path = Path("eval"),
        rules_dir: Path = Path("rules"),
        results_dir: Path = Path("eval/results")
    ):
        """
        Initialize the evaluation orchestrator.
        
        Args:
            data_dir: Directory containing ground truth data
            rules_dir: Directory containing bias detection rules
            results_dir: Directory for writing results
        """
        self.ground_truth_loader = GroundTruthLoader(data_dir)
        self.bias_detector = BiasDetector(rules_dir)
        self.metrics_calculator = MetricsCalculator()
        self.metrics_formatter = MetricsFormatter()
        self.results_writer = ResultsWriter(results_dir)
    
    def run_evaluation(
        self, 
        languages: Optional[List[Language]] = None,
        save_results: bool = True
    ) -> List[LanguageEvaluationResult]:
        """
        Run complete bias detection evaluation.
        
        Args:
            languages: List of languages to evaluate (defaults to English and Swahili)
            save_results: Whether to save results to files
            
        Returns:
            List of evaluation results for each language
            
        Raises:
            EvaluationError: If evaluation fails
        """
        if languages is None:
            # JuaKazi languages: EN (production), SW (foundation), FR/KI (pending validation)
            languages = [Language.ENGLISH, Language.SWAHILI, Language.FRENCH, Language.GIKUYU]
        
        results = []
        
        try:
            for language in languages:
                print(f"Evaluating {language.value}...")
                result = self._evaluate_language(language)
                results.append(result)
                
                # Print immediate results
                lang_names = {
                    Language.ENGLISH: "English",
                    Language.SWAHILI: "Swahili",
                    Language.FRENCH: "French",
                    Language.GIKUYU: "Gikuyu"
                }
                lang_name = lang_names.get(language, language.value)
                print(f"{lang_name} Results:")
                print(f"  Overall F1: {result.overall_metrics.f1_score:.3f}")
                print(f"  Precision: {result.overall_metrics.precision:.3f}")
                print(f"  Recall: {result.overall_metrics.recall:.3f}")
                print()
            
            if save_results:
                self._save_results(results)
            
            return results
            
        except Exception as e:
            raise EvaluationError(f"Evaluation failed: {e}") from e
    
    def _evaluate_language(self, language: Language) -> LanguageEvaluationResult:
        """Evaluate bias detection for a single language."""
        try:
            # Load ground truth data
            ground_truth = self.ground_truth_loader.load_ground_truth(language)
            
            # Run bias detection on all samples
            predictions = []
            for sample in ground_truth:
                prediction = self.bias_detector.detect_bias(sample.text, language)
                predictions.append(prediction)
            
            # Calculate metrics
            result = self.metrics_calculator.calculate_language_metrics(
                ground_truth, predictions, language
            )
            
            return result
            
        except (DataLoadError, BiasDetectionError) as e:
            raise EvaluationError(f"Failed to evaluate {language}: {e}") from e
    
    def _save_results(self, results: List[LanguageEvaluationResult]) -> None:
        """Save evaluation results to files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            # Save CSV report
            csv_data = self.metrics_formatter.format_for_csv(results)
            csv_filename = f"f1_report_{timestamp}.csv"
            csv_path = self.results_writer.write_csv_report(csv_data, csv_filename)
            print(f"Report saved to: {csv_path}")
            
        except Exception as e:
            print(f"Warning: Failed to save results: {e}")


def main() -> None:
    """Main entry point for evaluation script."""
    try:
        print("Running bias detection evaluation...")
        
        orchestrator = BiasEvaluationOrchestrator()
        results = orchestrator.run_evaluation()
        
        print("Evaluation completed successfully!")
        
    except EvaluationError as e:
        print(f"Evaluation failed: {e}")
        exit(1)
    except KeyboardInterrupt:
        print("\nEvaluation interrupted by user")
        exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        exit(1)


if __name__ == "__main__":
    main()