"""Tests for inter-annotator agreement metrics.

This module tests Cohen's Kappa and Krippendorff's Alpha calculations,
including verification against sklearn's implementation.
"""

import pytest
import numpy as np

from annotation.models import (
    AnnotationSample,
    ConfidenceLevel,
    BiasCategory,
    DemographicGroup,
    GenderReferent,
)
from annotation.agreement import (
    calculate_cohen_kappa,
    calculate_weighted_kappa,
    calculate_kappa_with_details,
    interpret_kappa,
    calculate_krippendorff_alpha,
    calculate_alpha_with_details,
    interpret_alpha,
)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def perfect_agreement_samples():
    """Create samples where two annotators perfectly agree."""
    samples_annotator1 = [
        AnnotationSample(
            text=f"Text {i}",
            has_bias=(i % 2 == 0),
            bias_category=BiasCategory.OCCUPATION if i % 2 == 0 else None,
            expected_correction=f"Correction {i}" if i % 2 == 0 else None,
            annotator_id="annotator_1",
            confidence=ConfidenceLevel.HIGH,
            demographic_group=DemographicGroup.NEUTRAL_REFERENT,
            gender_referent=GenderReferent.NEUTRAL,
        )
        for i in range(10)
    ]

    samples_annotator2 = [
        AnnotationSample(
            text=f"Text {i}",
            has_bias=(i % 2 == 0),
            bias_category=BiasCategory.OCCUPATION if i % 2 == 0 else None,
            expected_correction=f"Correction {i}" if i % 2 == 0 else None,
            annotator_id="annotator_2",
            confidence=ConfidenceLevel.HIGH,
            demographic_group=DemographicGroup.NEUTRAL_REFERENT,
            gender_referent=GenderReferent.NEUTRAL,
        )
        for i in range(10)
    ]

    return samples_annotator1, samples_annotator2


@pytest.fixture
def partial_agreement_samples():
    """Create samples with partial agreement (70% agreement)."""
    samples_annotator1 = []
    samples_annotator2 = []

    for i in range(10):
        # Agree on 7 out of 10 samples
        has_bias_1 = i % 2 == 0
        has_bias_2 = i % 2 == 0 if i < 7 else not (i % 2 == 0)

        samples_annotator1.append(
            AnnotationSample(
                text=f"Text {i}",
                has_bias=has_bias_1,
                bias_category=BiasCategory.OCCUPATION if has_bias_1 else None,
                expected_correction=f"Correction {i}" if has_bias_1 else None,
                annotator_id="annotator_1",
                confidence=ConfidenceLevel.HIGH,
                demographic_group=DemographicGroup.NEUTRAL_REFERENT,
                gender_referent=GenderReferent.NEUTRAL,
            )
        )

        samples_annotator2.append(
            AnnotationSample(
                text=f"Text {i}",
                has_bias=has_bias_2,
                bias_category=BiasCategory.OCCUPATION if has_bias_2 else None,
                expected_correction=f"Correction {i}" if has_bias_2 else None,
                annotator_id="annotator_2",
                confidence=ConfidenceLevel.HIGH,
                demographic_group=DemographicGroup.NEUTRAL_REFERENT,
                gender_referent=GenderReferent.NEUTRAL,
            )
        )

    return samples_annotator1, samples_annotator2


# ============================================================================
# COHEN'S KAPPA TESTS (10 tests)
# ============================================================================


def test_perfect_agreement_kappa(perfect_agreement_samples):
    """Test Kappa with perfect agreement."""
    samples1, samples2 = perfect_agreement_samples
    kappa = calculate_cohen_kappa(samples1, samples2)
    assert kappa == pytest.approx(1.0, abs=0.001)


def test_partial_agreement_kappa(partial_agreement_samples):
    """Test Kappa with partial agreement."""
    samples1, samples2 = partial_agreement_samples
    kappa = calculate_cohen_kappa(samples1, samples2)
    # With 70% agreement and balanced classes, Kappa should be ~0.4
    assert 0.3 < kappa < 0.5


def test_no_agreement_kappa():
    """Test Kappa with complete disagreement."""
    samples1 = [
        AnnotationSample(
            text=f"Text {i}",
            has_bias=True,
            bias_category=BiasCategory.OCCUPATION,
            expected_correction=f"Correction {i}",
            annotator_id="annotator_1",
            confidence=ConfidenceLevel.HIGH,
            demographic_group=DemographicGroup.NEUTRAL_REFERENT,
            gender_referent=GenderReferent.NEUTRAL,
        )
        for i in range(10)
    ]

    samples2 = [
        AnnotationSample(
            text=f"Text {i}",
            has_bias=False,
            annotator_id="annotator_2",
            confidence=ConfidenceLevel.HIGH,
            demographic_group=DemographicGroup.NEUTRAL_REFERENT,
            gender_referent=GenderReferent.NEUTRAL,
        )
        for i in range(10)
    ]

    kappa = calculate_cohen_kappa(samples1, samples2)
    # When one annotator always says yes and other always says no,
    # observed agreement is 0%, expected agreement is 0.5, so Kappa = -1.0
    # But with our formula, if they both choose same proportion by chance, Kappa = 0
    assert kappa <= 0.01  # Should be very low (at or below chance)


def test_kappa_vs_sklearn(perfect_agreement_samples):
    """Test Kappa matches sklearn implementation."""
    try:
        from sklearn.metrics import cohen_kappa_score
    except ImportError:
        pytest.skip("sklearn not installed")

    samples1, samples2 = perfect_agreement_samples
    labels1 = [1 if s.has_bias else 0 for s in samples1]
    labels2 = [1 if s.has_bias else 0 for s in samples2]

    our_kappa = calculate_cohen_kappa(samples1, samples2)
    sklearn_kappa = cohen_kappa_score(labels1, labels2)

    assert our_kappa == pytest.approx(sklearn_kappa, abs=0.001)


def test_kappa_mismatched_lengths():
    """Test Kappa raises error with mismatched lengths."""
    samples1 = [
        AnnotationSample(
            text="Text",
            has_bias=True,
            bias_category=BiasCategory.OCCUPATION,
            expected_correction="Correction",
            annotator_id="annotator_1",
            confidence=ConfidenceLevel.HIGH,
            demographic_group=DemographicGroup.NEUTRAL_REFERENT,
            gender_referent=GenderReferent.NEUTRAL,
        )
    ]
    samples2 = []

    with pytest.raises(ValueError, match="don't match"):
        calculate_cohen_kappa(samples1, samples2)


def test_kappa_text_mismatch():
    """Test Kappa raises error when texts don't match."""
    samples1 = [
        AnnotationSample(
            text="Text A",
            has_bias=True,
            bias_category=BiasCategory.OCCUPATION,
            expected_correction="Correction",
            annotator_id="annotator_1",
            confidence=ConfidenceLevel.HIGH,
            demographic_group=DemographicGroup.NEUTRAL_REFERENT,
            gender_referent=GenderReferent.NEUTRAL,
        )
    ]
    samples2 = [
        AnnotationSample(
            text="Text B",
            has_bias=True,
            bias_category=BiasCategory.OCCUPATION,
            expected_correction="Correction",
            annotator_id="annotator_2",
            confidence=ConfidenceLevel.HIGH,
            demographic_group=DemographicGroup.NEUTRAL_REFERENT,
            gender_referent=GenderReferent.NEUTRAL,
        )
    ]

    with pytest.raises(ValueError, match="Text mismatch"):
        calculate_cohen_kappa(samples1, samples2)


def test_weighted_kappa(perfect_agreement_samples):
    """Test weighted Kappa calculation."""
    samples1, samples2 = perfect_agreement_samples
    weighted_kappa = calculate_weighted_kappa(samples1, samples2)
    # Should still be 1.0 for perfect agreement
    assert weighted_kappa == pytest.approx(1.0, abs=0.001)


def test_kappa_with_details(partial_agreement_samples):
    """Test Kappa with detailed statistics."""
    samples1, samples2 = partial_agreement_samples
    details = calculate_kappa_with_details(samples1, samples2)

    assert "kappa" in details
    assert "agreement_rate" in details
    assert "disagreements" in details
    assert "passes_aibridge_bronze" in details
    assert details["total_samples"] == 10
    assert details["agreement_rate"] == 0.7  # 70% agreement


def test_interpret_kappa():
    """Test Kappa interpretation."""
    assert "Almost Perfect" in interpret_kappa(0.90)
    assert "Substantial" in interpret_kappa(0.70)
    assert "Moderate" in interpret_kappa(0.50)
    assert "Fair" in interpret_kappa(0.30)
    assert "Slight" in interpret_kappa(0.10)
    assert "Poor" in interpret_kappa(-0.10)


def test_kappa_aibridge_requirements():
    """Test AI BRIDGE tier requirements checking."""
    # Create samples with high agreement for Bronze tier (κ ≥ 0.70)
    samples1 = []
    samples2 = []

    for i in range(20):
        # 90% agreement with balanced classes
        has_bias = i % 2 == 0  # 50% bias
        agrees = i < 18  # 90% agreement

        samples1.append(
            AnnotationSample(
                text=f"Text {i}",
                has_bias=has_bias,
                bias_category=BiasCategory.OCCUPATION if has_bias else None,
                expected_correction=f"Correction {i}" if has_bias else None,
                annotator_id="annotator_1",
                confidence=ConfidenceLevel.HIGH,
                demographic_group=DemographicGroup.NEUTRAL_REFERENT,
                gender_referent=GenderReferent.NEUTRAL,
            )
        )

        samples2.append(
            AnnotationSample(
                text=f"Text {i}",
                has_bias=has_bias if agrees else not has_bias,
                bias_category=BiasCategory.OCCUPATION if (has_bias if agrees else not has_bias) else None,
                expected_correction=f"Correction {i}" if (has_bias if agrees else not has_bias) else None,
                annotator_id="annotator_2",
                confidence=ConfidenceLevel.HIGH,
                demographic_group=DemographicGroup.NEUTRAL_REFERENT,
                gender_referent=GenderReferent.NEUTRAL,
            )
        )

    details = calculate_kappa_with_details(samples1, samples2)
    # With 90% agreement and balanced classes, Kappa should be ~0.80
    assert bool(details["passes_aibridge_bronze"]) is True


# ============================================================================
# KRIPPENDORFF'S ALPHA TESTS (8 tests)
# ============================================================================


def test_alpha_perfect_agreement_two_annotators(perfect_agreement_samples):
    """Test Alpha with perfect agreement (2 annotators)."""
    samples1, samples2 = perfect_agreement_samples
    annotations_by_annotator = {
        "annotator_1": samples1,
        "annotator_2": samples2,
    }
    alpha = calculate_krippendorff_alpha(annotations_by_annotator)
    assert alpha == pytest.approx(1.0, abs=0.001)


def test_alpha_three_annotators():
    """Test Alpha with 3 annotators."""
    # Create 3 annotators with high agreement
    samples_by_annotator = {}

    for annotator_id in ["ann_1", "ann_2", "ann_3"]:
        samples = []
        for i in range(10):
            # All agree on even indices having bias
            # ann_3 disagrees on index 7
            has_bias = i % 2 == 0
            if annotator_id == "ann_3" and i == 7:
                has_bias = not has_bias

            samples.append(
                AnnotationSample(
                    text=f"Text {i}",
                    has_bias=has_bias,
                    bias_category=BiasCategory.OCCUPATION if has_bias else None,
                    expected_correction=f"Correction {i}" if has_bias else None,
                    annotator_id=annotator_id,
                    confidence=ConfidenceLevel.HIGH,
                    demographic_group=DemographicGroup.NEUTRAL_REFERENT,
                    gender_referent=GenderReferent.NEUTRAL,
                )
            )
        samples_by_annotator[annotator_id] = samples

    alpha = calculate_krippendorff_alpha(samples_by_annotator)
    # Should be high but not perfect due to one disagreement
    assert 0.85 < alpha < 0.95


def test_alpha_too_few_annotators():
    """Test Alpha raises error with less than 2 annotators."""
    annotations_by_annotator = {
        "annotator_1": [
            AnnotationSample(
                text="Text",
                has_bias=True,
                bias_category=BiasCategory.OCCUPATION,
                expected_correction="Correction",
                annotator_id="annotator_1",
                confidence=ConfidenceLevel.HIGH,
                demographic_group=DemographicGroup.NEUTRAL_REFERENT,
                gender_referent=GenderReferent.NEUTRAL,
            )
        ]
    }

    with pytest.raises(ValueError, match="at least 2 annotators"):
        calculate_krippendorff_alpha(annotations_by_annotator)


def test_alpha_mismatched_sample_counts():
    """Test Alpha raises error with mismatched sample counts."""
    annotations_by_annotator = {
        "annotator_1": [
            AnnotationSample(
                text="Text 1",
                has_bias=True,
                bias_category=BiasCategory.OCCUPATION,
                expected_correction="Correction",
                annotator_id="annotator_1",
                confidence=ConfidenceLevel.HIGH,
                demographic_group=DemographicGroup.NEUTRAL_REFERENT,
                gender_referent=GenderReferent.NEUTRAL,
            ),
            AnnotationSample(
                text="Text 2",
                has_bias=False,
                annotator_id="annotator_1",
                confidence=ConfidenceLevel.HIGH,
                demographic_group=DemographicGroup.NEUTRAL_REFERENT,
                gender_referent=GenderReferent.NEUTRAL,
            ),
        ],
        "annotator_2": [
            AnnotationSample(
                text="Text 1",
                has_bias=True,
                bias_category=BiasCategory.OCCUPATION,
                expected_correction="Correction",
                annotator_id="annotator_2",
                confidence=ConfidenceLevel.HIGH,
                demographic_group=DemographicGroup.NEUTRAL_REFERENT,
                gender_referent=GenderReferent.NEUTRAL,
            )
        ],
    }

    with pytest.raises(ValueError, match="different sample counts"):
        calculate_krippendorff_alpha(annotations_by_annotator)


def test_alpha_with_details(perfect_agreement_samples):
    """Test Alpha with detailed statistics."""
    samples1, samples2 = perfect_agreement_samples
    annotations_by_annotator = {
        "annotator_1": samples1,
        "annotator_2": samples2,
    }

    details = calculate_alpha_with_details(annotations_by_annotator)

    assert "alpha" in details
    assert "n_annotators" in details
    assert "n_samples" in details
    assert "pairwise_agreements" in details
    assert "passes_aibridge_gold" in details
    assert details["n_annotators"] == 2
    assert details["n_samples"] == 10


def test_interpret_alpha():
    """Test Alpha interpretation."""
    assert "High" in interpret_alpha(0.85)
    assert "Moderate" in interpret_alpha(0.75)
    assert "Low" in interpret_alpha(0.50)
    assert "Poor" in interpret_alpha(-0.10)


def test_alpha_aibridge_requirements():
    """Test AI BRIDGE tier requirements for Alpha."""
    # Create perfect agreement samples
    samples1 = [
        AnnotationSample(
            text=f"Text {i}",
            has_bias=(i % 2 == 0),
            bias_category=BiasCategory.OCCUPATION if i % 2 == 0 else None,
            expected_correction=f"Correction {i}" if i % 2 == 0 else None,
            annotator_id="ann_1",
            confidence=ConfidenceLevel.HIGH,
            demographic_group=DemographicGroup.NEUTRAL_REFERENT,
            gender_referent=GenderReferent.NEUTRAL,
        )
        for i in range(10)
    ]

    samples2 = [
        AnnotationSample(
            text=f"Text {i}",
            has_bias=(i % 2 == 0),
            bias_category=BiasCategory.OCCUPATION if i % 2 == 0 else None,
            expected_correction=f"Correction {i}" if i % 2 == 0 else None,
            annotator_id="ann_2",
            confidence=ConfidenceLevel.HIGH,
            demographic_group=DemographicGroup.NEUTRAL_REFERENT,
            gender_referent=GenderReferent.NEUTRAL,
        )
        for i in range(10)
    ]

    annotations_by_annotator = {"ann_1": samples1, "ann_2": samples2}
    details = calculate_alpha_with_details(annotations_by_annotator)

    assert bool(details["passes_aibridge_bronze"]) is True
    assert bool(details["passes_aibridge_silver"]) is True
    assert bool(details["passes_aibridge_gold"]) is True


def test_alpha_equals_kappa_for_two_annotators(perfect_agreement_samples):
    """Test that Alpha approximately equals Kappa for 2 annotators."""
    samples1, samples2 = perfect_agreement_samples

    kappa = calculate_cohen_kappa(samples1, samples2)
    alpha = calculate_krippendorff_alpha({
        "annotator_1": samples1,
        "annotator_2": samples2,
    })

    # Alpha and Kappa should be very close for binary data
    assert alpha == pytest.approx(kappa, abs=0.05)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
