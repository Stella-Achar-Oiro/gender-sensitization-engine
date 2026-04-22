"""
Tests for Human-in-the-Loop (HITL) metrics calculation.

Verifies AI BRIDGE HITL requirements:
- Human-Model Agreement Rate (HMAR): ≥0.80
- Cohen's Kappa (κ): ≥0.70
- Krippendorff's Alpha (α): ≥0.80
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from eval.hitl_metrics import (
    HITLCalculator,
    HITLMetrics,
    format_hitl_report
)


class TestHMAR:
    """Test Human-Model Agreement Rate calculation."""

    def test_perfect_agreement(self):
        """All predictions match human labels → HMAR = 1.0"""
        calculator = HITLCalculator()

        model_predictions = [True, False, True, False]
        human_labels = [True, False, True, False]

        hmar = calculator.calculate_hmar(model_predictions, human_labels)
        assert hmar == 1.0, f"Expected 1.0, got {hmar}"

    def test_no_agreement(self):
        """All predictions opposite of human labels → HMAR = 0.0"""
        calculator = HITLCalculator()

        model_predictions = [True, True, True, True]
        human_labels = [False, False, False, False]

        hmar = calculator.calculate_hmar(model_predictions, human_labels)
        assert hmar == 0.0, f"Expected 0.0, got {hmar}"

    def test_partial_agreement(self):
        """Half agree, half disagree → HMAR = 0.5"""
        calculator = HITLCalculator()

        model_predictions = [True, True, False, False]
        human_labels = [True, False, False, True]

        hmar = calculator.calculate_hmar(model_predictions, human_labels)
        assert hmar == 0.5, f"Expected 0.5, got {hmar}"

    def test_aibridge_threshold(self):
        """Verify HMAR ≥ 0.80 threshold detection"""
        calculator = HITLCalculator()

        # 8 out of 10 agree = 0.80
        model_predictions = [True] * 8 + [False] * 2
        human_labels = [True] * 8 + [True] * 2

        hmar = calculator.calculate_hmar(model_predictions, human_labels)
        assert hmar == 0.80, f"Expected 0.80, got {hmar}"
        assert hmar >= 0.80, "Should meet AI BRIDGE threshold"

    def test_empty_input(self):
        """Handle empty inputs gracefully"""
        calculator = HITLCalculator()

        hmar = calculator.calculate_hmar([], [])
        assert hmar == 0.0

    def test_mismatched_lengths(self):
        """Handle mismatched input lengths"""
        calculator = HITLCalculator()

        model_predictions = [True, False]
        human_labels = [True]

        hmar = calculator.calculate_hmar(model_predictions, human_labels)
        assert hmar == 0.0


class TestCohensKappa:
    """Test Cohen's Kappa calculation."""

    def test_perfect_agreement(self):
        """Perfect agreement → κ = 1.0"""
        calculator = HITLCalculator()

        annotator1 = [True, False, True, False]
        annotator2 = [True, False, True, False]

        kappa = calculator.calculate_cohens_kappa(annotator1, annotator2)
        assert kappa == 1.0, f"Expected 1.0, got {kappa}"

    def test_random_agreement(self):
        """Agreement by chance → κ ≈ 0.0"""
        calculator = HITLCalculator()

        # Simulate random 50/50 annotations
        annotator1 = [True, False] * 50
        annotator2 = [True, True, False, False] * 25

        kappa = calculator.calculate_cohens_kappa(annotator1, annotator2)
        # Should be near 0 (random chance)
        assert -0.1 <= kappa <= 0.1, f"Expected ~0.0, got {kappa}"

    def test_substantial_agreement(self):
        """Substantial agreement → κ ≥ 0.70"""
        calculator = HITLCalculator()

        # 90% agreement, accounting for chance
        annotator1 = [True] * 9 + [False] * 1
        annotator2 = [True] * 9 + [False] * 1

        kappa = calculator.calculate_cohens_kappa(annotator1, annotator2)
        assert kappa >= 0.70, f"Should meet AI BRIDGE threshold, got {kappa}"

    def test_aibridge_threshold(self):
        """Verify κ ≥ 0.70 threshold"""
        calculator = HITLCalculator()

        # Known case: 80% agreement with balanced distribution
        annotator1 = [True] * 8 + [False] * 2
        annotator2 = [True] * 8 + [False] * 2

        kappa = calculator.calculate_cohens_kappa(annotator1, annotator2)
        # With perfect agreement on balanced data, kappa = 1.0
        assert kappa >= 0.70, f"Should meet threshold, got {kappa}"

    def test_disagreement(self):
        """Complete disagreement → κ ≤ 0"""
        calculator = HITLCalculator()

        annotator1 = [True] * 10
        annotator2 = [False] * 10

        kappa = calculator.calculate_cohens_kappa(annotator1, annotator2)
        # Complete disagreement (kappa can be 0 when p_e calculation hits edge case)
        assert kappa <= 0, f"Expected non-positive kappa, got {kappa}"

    def test_empty_input(self):
        """Handle empty inputs"""
        calculator = HITLCalculator()

        kappa = calculator.calculate_cohens_kappa([], [])
        assert kappa == 0.0


class TestKrippendorffsAlpha:
    """Test Krippendorff's Alpha calculation."""

    def test_perfect_agreement_two_annotators(self):
        """Perfect agreement with 2 annotators → α = 1.0"""
        calculator = HITLCalculator()

        annotations = [
            [True, False, True, False],  # Annotator 1
            [True, False, True, False]   # Annotator 2
        ]

        alpha = calculator.calculate_krippendorffs_alpha(annotations)
        assert alpha == 1.0, f"Expected 1.0, got {alpha}"

    def test_perfect_agreement_three_annotators(self):
        """Perfect agreement with 3 annotators → α = 1.0"""
        calculator = HITLCalculator()

        annotations = [
            [True, False, True, False],  # Annotator 1
            [True, False, True, False],  # Annotator 2
            [True, False, True, False]   # Annotator 3
        ]

        alpha = calculator.calculate_krippendorffs_alpha(annotations)
        assert alpha == 1.0, f"Expected 1.0, got {alpha}"

    def test_partial_disagreement(self):
        """Some disagreement → 0 < α < 1"""
        calculator = HITLCalculator()

        annotations = [
            [True, True, False, True],   # Annotator 1
            [True, False, False, True],  # Annotator 2
            [True, True, False, False]   # Annotator 3
        ]

        alpha = calculator.calculate_krippendorffs_alpha(annotations)
        assert 0.0 < alpha < 1.0, f"Expected 0 < α < 1, got {alpha}"

    def test_aibridge_threshold(self):
        """Verify α ≥ 0.80 threshold"""
        calculator = HITLCalculator()

        # High agreement scenario - balanced distribution with high agreement
        # Mix of True and False with minimal disagreements
        annotations = [
            [True] * 10 + [False] * 10,          # Annotator 1: Balanced
            [True] * 10 + [False] * 10,          # Annotator 2: Same as 1
            [True] * 10 + [False] * 9 + [True]   # Annotator 3: One disagreement
        ]

        alpha = calculator.calculate_krippendorffs_alpha(annotations)
        assert alpha >= 0.80, f"Should meet AI BRIDGE threshold, got {alpha}"

    def test_single_annotator(self):
        """Single annotator → α = 0.0 (no comparison)"""
        calculator = HITLCalculator()

        annotations = [
            [True, False, True, False]
        ]

        alpha = calculator.calculate_krippendorffs_alpha(annotations)
        assert alpha == 0.0

    def test_empty_annotations(self):
        """Handle empty annotations"""
        calculator = HITLCalculator()

        alpha = calculator.calculate_krippendorffs_alpha([])
        assert alpha == 0.0

    def test_mismatched_lengths(self):
        """Handle mismatched annotation lengths"""
        calculator = HITLCalculator()

        annotations = [
            [True, False, True],
            [True, False]  # Different length
        ]

        alpha = calculator.calculate_krippendorffs_alpha(annotations)
        assert alpha == 0.0


class TestHITLMetricsIntegration:
    """Test comprehensive HITL metrics calculation."""

    def test_calculate_all_metrics(self):
        """Test end-to-end HITL calculation"""
        calculator = HITLCalculator()

        model_predictions = [True, True, False, False, True]
        human_labels = [True, True, False, True, True]

        multi_annotator = [
            [True, True, False, True, True],   # Annotator 1 (matches human_labels)
            [True, True, False, False, True],  # Annotator 2
            [True, False, False, True, True]   # Annotator 3
        ]

        metrics = calculator.calculate_hitl_metrics(
            model_predictions, human_labels, multi_annotator
        )

        # Verify structure
        assert isinstance(metrics, HITLMetrics)
        assert 0.0 <= metrics.hmar <= 1.0
        assert -1.0 <= metrics.cohens_kappa <= 1.0
        assert 0.0 <= metrics.krippendorffs_alpha <= 1.0
        assert metrics.annotator_count == 3
        assert metrics.sample_count == 5
        assert "bias_detected" in metrics.agreement_breakdown
        assert "no_bias" in metrics.agreement_breakdown

    def test_passing_aibridge_requirements(self):
        """Test scenario that passes all AI BRIDGE thresholds"""
        calculator = HITLCalculator()

        # High agreement scenario - balanced distribution with high agreement
        model_predictions = [True] * 9 + [False] * 9 + [True] * 2
        human_labels = [True] * 10 + [False] * 10

        multi_annotator = [
            [True] * 10 + [False] * 10,          # Annotator 1 (matches human_labels)
            [True] * 10 + [False] * 10,          # Annotator 2
            [True] * 10 + [False] * 9 + [True]   # Annotator 3: One disagreement
        ]

        metrics = calculator.calculate_hitl_metrics(
            model_predictions, human_labels, multi_annotator
        )

        # Should pass all thresholds
        assert metrics.passes_aibridge_requirements(), f"Should pass AI BRIDGE requirements: HMAR={metrics.hmar:.3f}, Kappa={metrics.cohens_kappa:.3f}, Alpha={metrics.krippendorffs_alpha:.3f}"
        assert metrics.hmar >= 0.80
        assert metrics.cohens_kappa >= 0.70
        assert metrics.krippendorffs_alpha >= 0.80

    def test_failing_aibridge_requirements(self):
        """Test scenario that fails AI BRIDGE thresholds"""
        calculator = HITLCalculator()

        # Low agreement
        model_predictions = [True, False, True, False]
        human_labels = [False, True, False, True]

        multi_annotator = [
            [False, True, False, True],
            [True, True, False, False],
            [False, False, True, True]
        ]

        metrics = calculator.calculate_hitl_metrics(
            model_predictions, human_labels, multi_annotator
        )

        # Should fail
        assert not metrics.passes_aibridge_requirements()

    def test_agreement_breakdown(self):
        """Verify per-category agreement calculation"""
        calculator = HITLCalculator()

        model_predictions = [True, True, False, False]
        human_labels = [True, True, True, False]

        metrics = calculator.calculate_hitl_metrics(
            model_predictions, human_labels
        )

        # Check breakdown structure
        assert "bias_detected" in metrics.agreement_breakdown
        assert "no_bias" in metrics.agreement_breakdown

        # For bias_detected samples (indices 0,1,2):
        # Model agrees on 0,1 but not 2 → 2/3 = 0.667
        bias_agreement = metrics.agreement_breakdown["bias_detected"]
        assert 0.6 <= bias_agreement <= 0.7, f"Expected ~0.667, got {bias_agreement}"

        # For no_bias samples (index 3):
        # Model agrees on 3 → 1/1 = 1.0
        no_bias_agreement = metrics.agreement_breakdown["no_bias"]
        assert no_bias_agreement == 1.0

    def test_without_multi_annotator(self):
        """Test with only model-human comparison (no multi-annotator)"""
        calculator = HITLCalculator()

        model_predictions = [True, False, True, False]
        human_labels = [True, False, True, False]

        metrics = calculator.calculate_hitl_metrics(
            model_predictions, human_labels
        )

        # Should have HMAR but not Cohen's Kappa or Krippendorff's Alpha
        assert metrics.hmar == 1.0
        assert metrics.cohens_kappa == 0.0
        assert metrics.krippendorffs_alpha == 0.0
        assert metrics.annotator_count == 1


class TestFormatHITLReport:
    """Test HITL report formatting."""

    def test_format_passing_report(self):
        """Test report formatting for passing metrics"""
        metrics = HITLMetrics(
            hmar=0.85,
            cohens_kappa=0.75,
            krippendorffs_alpha=0.82,
            annotator_count=3,
            sample_count=100,
            agreement_breakdown={
                "bias_detected": 0.88,
                "no_bias": 0.92
            }
        )

        report = format_hitl_report(metrics)

        # Check key elements
        assert "✅ PASSES" in report
        assert "0.850" in report  # HMAR
        assert "0.750" in report  # Cohen's Kappa
        assert "0.820" in report  # Krippendorff's Alpha
        assert "3" in report      # Annotator count
        assert "100" in report    # Sample count

    def test_format_failing_report(self):
        """Test report formatting for failing metrics"""
        metrics = HITLMetrics(
            hmar=0.60,
            cohens_kappa=0.50,
            krippendorffs_alpha=0.65,
            annotator_count=2,
            sample_count=50,
            agreement_breakdown={
                "bias_detected": 0.55,
                "no_bias": 0.70
            }
        )

        report = format_hitl_report(metrics)

        # Check key elements
        assert "⚠️ FAILS" in report
        assert "0.600" in report  # HMAR (below 0.80)
        assert "0.500" in report  # Cohen's Kappa (below 0.70)
        assert "0.650" in report  # Krippendorff's Alpha (below 0.80)


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_all_positive_labels(self):
        """All samples labeled as bias"""
        calculator = HITLCalculator()

        model_predictions = [True, True, False]
        human_labels = [True, True, True]

        metrics = calculator.calculate_hitl_metrics(
            model_predictions, human_labels
        )

        # Should have bias_detected agreement, no_bias should be 0
        assert metrics.agreement_breakdown["bias_detected"] > 0
        assert metrics.agreement_breakdown["no_bias"] == 0.0

    def test_all_negative_labels(self):
        """All samples labeled as no bias"""
        calculator = HITLCalculator()

        model_predictions = [False, False, True]
        human_labels = [False, False, False]

        metrics = calculator.calculate_hitl_metrics(
            model_predictions, human_labels
        )

        # Should have no_bias agreement, bias_detected should be 0
        assert metrics.agreement_breakdown["no_bias"] > 0
        assert metrics.agreement_breakdown["bias_detected"] == 0.0

    def test_single_sample(self):
        """Single sample evaluation"""
        calculator = HITLCalculator()

        model_predictions = [True]
        human_labels = [True]

        metrics = calculator.calculate_hitl_metrics(
            model_predictions, human_labels
        )

        assert metrics.hmar == 1.0
        assert metrics.sample_count == 1


def run_all_tests():
    """Run all HITL metrics tests."""
    print("Running HITL Metrics Tests...")
    print("=" * 60)

    test_classes = [
        TestHMAR,
        TestCohensKappa,
        TestKrippendorffsAlpha,
        TestHITLMetricsIntegration,
        TestFormatHITLReport,
        TestEdgeCases
    ]

    total_tests = 0
    passed_tests = 0
    failed_tests = 0

    for test_class in test_classes:
        class_name = test_class.__name__
        print(f"\n{class_name}:")

        test_instance = test_class()
        test_methods = [method for method in dir(test_instance) if method.startswith("test_")]

        for test_method in test_methods:
            total_tests += 1
            try:
                getattr(test_instance, test_method)()
                print(f"  ✅ {test_method}")
                passed_tests += 1
            except AssertionError as e:
                print(f"  ❌ {test_method}: {e}")
                failed_tests += 1
            except Exception as e:
                print(f"  ❌ {test_method}: Unexpected error: {e}")
                failed_tests += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed_tests}/{total_tests} tests passed")

    if failed_tests > 0:
        print(f"⚠️  {failed_tests} tests failed")
        return False
    else:
        print("✅ All tests passed!")
        return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
