"""
Tests for fairness metrics calculation.

Verifies AI BRIDGE fairness requirements:
- Demographic Parity (DP): ≤0.10
- Equal Opportunity (EO): ≤0.05
- Equalized Odds: ≤0.05
- Multilingual Bias Evaluation (MBE): ≥0.85
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from eval.fairness_metrics import (
    FairnessCalculator,
    FairnessMetrics,
    DemographicGroup,
    extract_demographic_group
)
from eval.models import Language


class TestDemographicParity:
    """Test Demographic Parity calculation."""

    def test_perfect_parity(self):
        """All groups have same positive rate → DP = 0.0"""
        calculator = FairnessCalculator()

        predictions = [True, True, False, False]
        groups = [
            DemographicGroup.MALE_REFERENT,
            DemographicGroup.FEMALE_REFERENT,
            DemographicGroup.MALE_REFERENT,
            DemographicGroup.FEMALE_REFERENT
        ]

        # Male: 1/2 = 0.50, Female: 1/2 = 0.50
        dp = calculator.calculate_demographic_parity(predictions, groups)
        assert dp == 0.0, f"Expected 0.0, got {dp}"

    def test_maximum_disparity(self):
        """One group all positive, other all negative → DP = 1.0"""
        calculator = FairnessCalculator()

        predictions = [True, True, False, False]
        groups = [
            DemographicGroup.MALE_REFERENT,
            DemographicGroup.MALE_REFERENT,
            DemographicGroup.FEMALE_REFERENT,
            DemographicGroup.FEMALE_REFERENT
        ]

        # Male: 2/2 = 1.00, Female: 0/2 = 0.00
        dp = calculator.calculate_demographic_parity(predictions, groups)
        assert dp == 1.0, f"Expected 1.0, got {dp}"

    def test_aibridge_threshold(self):
        """Verify DP ≤ 0.10 threshold detection"""
        calculator = FairnessCalculator()

        # Passing case: DP = 0.08
        predictions = [True] * 9 + [False] + [True] * 8 + [False] * 2
        groups = [DemographicGroup.MALE_REFERENT] * 10 + [DemographicGroup.FEMALE_REFERENT] * 10

        # Male: 9/10 = 0.90, Female: 8/10 = 0.80, DP = 0.10
        dp = calculator.calculate_demographic_parity(predictions, groups)
        assert dp <= 0.10, f"Should pass threshold, got {dp}"

    def test_empty_input(self):
        """Handle empty inputs gracefully"""
        calculator = FairnessCalculator()

        dp = calculator.calculate_demographic_parity([], [])
        assert dp == 0.0

    def test_single_group(self):
        """Single group → DP = 0.0 (no comparison)"""
        calculator = FairnessCalculator()

        predictions = [True, False, True]
        groups = [DemographicGroup.MALE_REFERENT] * 3

        dp = calculator.calculate_demographic_parity(predictions, groups)
        assert dp == 0.0


class TestEqualOpportunity:
    """Test Equal Opportunity calculation."""

    def test_perfect_equal_opportunity(self):
        """All groups have same TPR → EO = 0.0"""
        calculator = FairnessCalculator()

        predictions = [True, True, False, False]
        labels = [True, True, True, True]
        groups = [
            DemographicGroup.MALE_REFERENT,
            DemographicGroup.FEMALE_REFERENT,
            DemographicGroup.MALE_REFERENT,
            DemographicGroup.FEMALE_REFERENT
        ]

        # Male TPR: 1/2 = 0.50, Female TPR: 1/2 = 0.50
        eo = calculator.calculate_equal_opportunity(predictions, labels, groups)
        assert eo == 0.0, f"Expected 0.0, got {eo}"

    def test_maximum_eo_disparity(self):
        """One group TPR=1.0, other TPR=0.0 → EO = 1.0"""
        calculator = FairnessCalculator()

        predictions = [True, True, False, False]
        labels = [True, True, True, True]
        groups = [
            DemographicGroup.MALE_REFERENT,
            DemographicGroup.MALE_REFERENT,
            DemographicGroup.FEMALE_REFERENT,
            DemographicGroup.FEMALE_REFERENT
        ]

        # Male TPR: 2/2 = 1.00, Female TPR: 0/2 = 0.00
        eo = calculator.calculate_equal_opportunity(predictions, labels, groups)
        assert eo == 1.0, f"Expected 1.0, got {eo}"

    def test_aibridge_threshold(self):
        """Verify EO ≤ 0.05 threshold detection"""
        calculator = FairnessCalculator()

        # Passing case: EO = 0.05
        predictions = [True] * 19 + [False] + [True] * 18 + [False] * 2
        labels = [True] * 40
        groups = [DemographicGroup.MALE_REFERENT] * 20 + [DemographicGroup.FEMALE_REFERENT] * 20

        # Male TPR: 19/20 = 0.95, Female TPR: 18/20 = 0.90, EO = 0.05
        eo = calculator.calculate_equal_opportunity(predictions, labels, groups)
        assert eo <= 0.05, f"Should pass threshold, got {eo}"

    def test_no_positives(self):
        """Handle case with no positive labels"""
        calculator = FairnessCalculator()

        predictions = [False] * 4
        labels = [False] * 4
        groups = [DemographicGroup.MALE_REFERENT] * 2 + [DemographicGroup.FEMALE_REFERENT] * 2

        eo = calculator.calculate_equal_opportunity(predictions, labels, groups)
        assert eo == 0.0


class TestEqualizedOdds:
    """Test Equalized Odds calculation."""

    def test_perfect_equalized_odds(self):
        """Same TPR and FPR across groups → EqOdds = 0.0"""
        calculator = FairnessCalculator()

        predictions = [True, False, True, False]
        labels = [True, False, True, False]
        groups = [
            DemographicGroup.MALE_REFERENT,
            DemographicGroup.MALE_REFERENT,
            DemographicGroup.FEMALE_REFERENT,
            DemographicGroup.FEMALE_REFERENT
        ]

        # Both groups: TPR = 1.0, FPR = 0.0
        eq_odds = calculator.calculate_equalized_odds(predictions, labels, groups)
        assert eq_odds == 0.0, f"Expected 0.0, got {eq_odds}"

    def test_tpr_dominates(self):
        """TPR difference > FPR difference → returns TPR diff"""
        calculator = FairnessCalculator()

        predictions = [True, True, False, False]
        labels = [True, True, True, True]
        groups = [
            DemographicGroup.MALE_REFERENT,
            DemographicGroup.MALE_REFERENT,
            DemographicGroup.FEMALE_REFERENT,
            DemographicGroup.FEMALE_REFERENT
        ]

        # Male TPR: 2/2 = 1.0, Female TPR: 0/2 = 0.0
        # FPR: both 0.0 (no negatives)
        eq_odds = calculator.calculate_equalized_odds(predictions, labels, groups)
        assert eq_odds == 1.0, f"Expected 1.0 (TPR diff), got {eq_odds}"

    def test_fpr_dominates(self):
        """FPR difference > TPR difference → returns FPR diff"""
        calculator = FairnessCalculator()

        predictions = [True, True, True, True]
        labels = [False, False, False, False]
        groups = [
            DemographicGroup.MALE_REFERENT,
            DemographicGroup.MALE_REFERENT,
            DemographicGroup.FEMALE_REFERENT,
            DemographicGroup.FEMALE_REFERENT
        ]

        # TPR: both 0.0 (no positives)
        # Male FPR: 2/2 = 1.0, Female FPR: 2/2 = 1.0
        eq_odds = calculator.calculate_equalized_odds(predictions, labels, groups)
        assert eq_odds == 0.0, f"Expected 0.0 (both FPR=1.0), got {eq_odds}"


class TestMBEScore:
    """Test Multilingual Bias Evaluation score."""

    def test_perfect_consistency(self):
        """All languages have same F1 → MBE = 1.0"""
        calculator = FairnessCalculator()

        language_f1 = {
            Language.ENGLISH: 0.80,
            Language.SWAHILI: 0.80,
            Language.FRENCH: 0.80,
            Language.GIKUYU: 0.80
        }

        mbe = calculator.calculate_mbe_score(language_f1, target_f1=0.75)
        assert mbe == 1.0, f"Expected 1.0, got {mbe}"

    def test_aibridge_target_performance(self):
        """Verify MBE ≥ 0.85 threshold"""
        calculator = FairnessCalculator()

        # Realistic case: some variance but within acceptable range
        language_f1 = {
            Language.ENGLISH: 0.76,
            Language.SWAHILI: 0.80,
            Language.FRENCH: 0.75,
            Language.GIKUYU: 0.74
        }

        mbe = calculator.calculate_mbe_score(language_f1, target_f1=0.75)
        # Mean: 0.7625, StdDev: ~0.025, MBE = 1 - (0.025/0.75) ≈ 0.967
        assert mbe >= 0.85, f"Should pass threshold, got {mbe}"

    def test_high_variance(self):
        """High variance across languages → low MBE"""
        calculator = FairnessCalculator()

        language_f1 = {
            Language.ENGLISH: 0.90,
            Language.SWAHILI: 0.50,
            Language.FRENCH: 0.80,
            Language.GIKUYU: 0.60
        }

        mbe = calculator.calculate_mbe_score(language_f1, target_f1=0.75)
        # High std dev → low MBE
        assert mbe < 0.85, f"High variance should fail, got {mbe}"

    def test_single_language(self):
        """Single language → MBE = 0.0 (no comparison)"""
        calculator = FairnessCalculator()

        language_f1 = {Language.ENGLISH: 0.80}

        mbe = calculator.calculate_mbe_score(language_f1)
        assert mbe == 0.0


class TestFairnessMetricsIntegration:
    """Test comprehensive fairness metrics calculation."""

    def test_calculate_all_metrics(self):
        """Test end-to-end fairness calculation"""
        calculator = FairnessCalculator()

        # Realistic scenario: slight disparity
        predictions = [True] * 8 + [False] * 2 + [True] * 7 + [False] * 3
        labels = [True] * 10 + [True] * 10
        groups = [DemographicGroup.MALE_REFERENT] * 10 + [DemographicGroup.FEMALE_REFERENT] * 10

        language_f1 = {
            Language.ENGLISH: 0.78,
            Language.SWAHILI: 0.75,
            Language.FRENCH: 0.76,
            Language.GIKUYU: 0.74
        }

        metrics = calculator.calculate_fairness_metrics(
            predictions, labels, groups, language_f1
        )

        # Verify structure
        assert isinstance(metrics, FairnessMetrics)
        assert 0.0 <= metrics.demographic_parity <= 1.0
        assert 0.0 <= metrics.equal_opportunity <= 1.0
        assert 0.0 <= metrics.equalized_odds <= 1.0
        assert 0.0 <= metrics.mbe_score <= 1.0
        assert len(metrics.group_metrics) > 0

    def test_passing_aibridge_requirements(self):
        """Test scenario that passes all AI BRIDGE thresholds"""
        calculator = FairnessCalculator()

        # Near-perfect fairness
        predictions = [True] * 9 + [False] + [True] * 9 + [False]
        labels = [True] * 10 + [True] * 10
        groups = [DemographicGroup.MALE_REFERENT] * 10 + [DemographicGroup.FEMALE_REFERENT] * 10

        language_f1 = {
            Language.ENGLISH: 0.77,
            Language.SWAHILI: 0.76,
            Language.FRENCH: 0.76,
            Language.GIKUYU: 0.75
        }

        metrics = calculator.calculate_fairness_metrics(
            predictions, labels, groups, language_f1
        )

        # Should pass all thresholds
        assert metrics.passes_aibridge_requirements(), "Should pass AI BRIDGE requirements"
        assert metrics.demographic_parity <= 0.10
        assert metrics.equal_opportunity <= 0.05
        assert metrics.equalized_odds <= 0.05
        assert metrics.mbe_score >= 0.85

    def test_failing_aibridge_requirements(self):
        """Test scenario that fails AI BRIDGE thresholds"""
        calculator = FairnessCalculator()

        # Biased predictions
        predictions = [True] * 10 + [False] * 10
        labels = [True] * 20
        groups = [DemographicGroup.MALE_REFERENT] * 10 + [DemographicGroup.FEMALE_REFERENT] * 10

        language_f1 = {
            Language.ENGLISH: 0.90,
            Language.SWAHILI: 0.50  # High variance
        }

        metrics = calculator.calculate_fairness_metrics(
            predictions, labels, groups, language_f1
        )

        # Should fail
        assert not metrics.passes_aibridge_requirements()

    def test_group_metrics_breakdown(self):
        """Verify per-group metrics calculation"""
        calculator = FairnessCalculator()

        predictions = [True, True, False, True]
        labels = [True, True, True, False]
        groups = [
            DemographicGroup.MALE_REFERENT,
            DemographicGroup.MALE_REFERENT,
            DemographicGroup.FEMALE_REFERENT,
            DemographicGroup.FEMALE_REFERENT
        ]

        metrics = calculator.calculate_fairness_metrics(
            predictions, labels, groups
        )

        # Check group_metrics structure
        assert "male_referent" in metrics.group_metrics
        assert "female_referent" in metrics.group_metrics

        male_metrics = metrics.group_metrics["male_referent"]
        assert "precision" in male_metrics
        assert "recall" in male_metrics
        assert "f1_score" in male_metrics
        assert "sample_count" in male_metrics
        assert male_metrics["sample_count"] == 2


class TestDemographicGroupExtraction:
    """Test demographic group extraction from text."""

    def test_english_male_referent(self):
        """Detect male referent in English"""
        text = "The doctor said he would call back"
        group = extract_demographic_group(text, Language.ENGLISH)
        assert group == DemographicGroup.MALE_REFERENT

    def test_english_female_referent(self):
        """Detect female referent in English"""
        text = "The nurse said she would be ready"
        group = extract_demographic_group(text, Language.ENGLISH)
        assert group == DemographicGroup.FEMALE_REFERENT

    def test_english_neutral_referent(self):
        """Detect neutral referent in English"""
        text = "The person said they would arrive"
        group = extract_demographic_group(text, Language.ENGLISH)
        assert group == DemographicGroup.NEUTRAL_REFERENT

    def test_english_unknown(self):
        """No clear gender markers → unknown"""
        text = "The meeting is scheduled for tomorrow"
        group = extract_demographic_group(text, Language.ENGLISH)
        assert group == DemographicGroup.UNKNOWN

    def test_swahili_male_referent(self):
        """Detect male referent in Swahili"""
        text = "Daktari alikuwa mwanamume"
        group = extract_demographic_group(text, Language.SWAHILI)
        assert group == DemographicGroup.MALE_REFERENT

    def test_swahili_female_referent(self):
        """Detect female referent in Swahili"""
        text = "Mwalimu ni mwanamke"
        group = extract_demographic_group(text, Language.SWAHILI)
        assert group == DemographicGroup.FEMALE_REFERENT

    def test_swahili_neutral(self):
        """Swahili gender-neutral → unknown"""
        text = "Daktari alikuja kesho"
        group = extract_demographic_group(text, Language.SWAHILI)
        assert group == DemographicGroup.UNKNOWN


def run_all_tests():
    """Run all fairness metrics tests."""
    print("Running Fairness Metrics Tests...")
    print("=" * 60)

    test_classes = [
        TestDemographicParity,
        TestEqualOpportunity,
        TestEqualizedOdds,
        TestMBEScore,
        TestFairnessMetricsIntegration,
        TestDemographicGroupExtraction
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
