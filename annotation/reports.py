"""Quality report generation for annotation data.

This module provides utilities to generate human-readable quality reports
for annotation batches and annotators.
"""

from typing import Dict, Any, List
from pathlib import Path

from annotation.models import AnnotationBatch
from annotation.quality import AnnotationQualityChecker


def format_quality_report(report: Dict[str, Any]) -> str:
    """Format quality report as human-readable text.

    Args:
        report: Quality report from AnnotationQualityChecker

    Returns:
        Formatted report string
    """
    lines = [
        "\n" + "=" * 70,
        "Annotation Quality Report",
        "=" * 70,
        f"Batch ID: {report['batch_id']}",
        f"Annotator: {report['annotator_id']}",
        f"Language: {report['language']}",
        f"Total Samples: {report['total_samples']}",
        "",
        f"Quality Score: {report['quality_score']:.0f}/100",
        f"Assessment: {report['assessment']}",
        f"Passes Quality Check: {'✅ YES' if report['passes_quality_check'] else '❌ NO'}",
        "",
    ]

    # Detailed metrics
    lines.append("Detailed Metrics:")
    lines.append("")

    metrics = report["metrics"]

    # Confidence distribution
    if "confidence_distribution" in metrics:
        conf_dist = metrics["confidence_distribution"]
        lines.append("  Confidence Distribution:")
        if "percentages" in conf_dist:
            for level, pct in sorted(conf_dist["percentages"].items()):
                lines.append(f"    {level:12s}: {pct:5.1f}%")
        status = "✅" if conf_dist.get("is_balanced") else "⚠️"
        lines.append(f"    {status} Balanced: {conf_dist.get('is_balanced')}")
        lines.append("")

    # Bias balance
    if "bias_balance" in metrics:
        bias_bal = metrics["bias_balance"]
        lines.append("  Bias Balance:")
        lines.append(f"    Biased:      {bias_bal.get('biased_count', 0)}")
        lines.append(f"    Neutral:     {bias_bal.get('neutral_count', 0)}")
        lines.append(f"    Bias Rate:   {bias_bal.get('bias_rate', 0):.1%}")
        status = "✅" if bias_bal.get("is_balanced") else "⚠️"
        lines.append(f"    {status} Balanced: {bias_bal.get('is_balanced')}")
        lines.append("")

    # Annotator consistency
    if "annotator_consistency" in metrics:
        consistency = metrics["annotator_consistency"]
        if "warning" not in consistency:
            lines.append("  Annotator Consistency:")
            lines.append(f"    Mean Bias Rate: {consistency.get('mean_bias_rate', 0):.1%}")
            lines.append(f"    Std Deviation:  {consistency.get('std_dev', 0):.3f}")
            status = "✅" if consistency.get("is_consistent") else "⚠️"
            lines.append(f"    {status} Consistent: {consistency.get('is_consistent')}")
            lines.append("")

    # Fatigue detection
    if "fatigue_detection" in metrics:
        fatigue = metrics["fatigue_detection"]
        if "warning" not in fatigue:
            lines.append("  Fatigue Detection:")
            if fatigue.get("first_half_rate"):
                lines.append(f"    First Half Rate:  {fatigue['first_half_rate']:.2f} samples/min")
            if fatigue.get("second_half_rate"):
                lines.append(f"    Second Half Rate: {fatigue['second_half_rate']:.2f} samples/min")
            status = "⚠️" if fatigue.get("slowdown_detected") else "✅"
            lines.append(f"    {status} No Fatigue Detected: {not fatigue.get('slowdown_detected')}")
            lines.append("")

    # Schema completeness
    if "schema_completeness" in metrics:
        schema = metrics["schema_completeness"]
        lines.append("  Schema Completeness:")
        if "field_coverage" in schema:
            for field, pct in sorted(schema["field_coverage"].items()):
                status = "✅" if pct == 100.0 else "⚠️"
                lines.append(f"    {status} {field:20s}: {pct:5.1f}%")
        status = "✅" if schema.get("is_complete") else "⚠️"
        lines.append(f"    {status} Complete: {schema.get('is_complete')}")
        lines.append("")

    # Issues
    if report["issues"]:
        lines.append("Issues Detected:")
        for issue in report["issues"]:
            lines.append(f"  ⚠️  {issue['check']}: {issue['issue']}")
        lines.append("")

    lines.append("=" * 70 + "\n")

    return "\n".join(lines)


def generate_multi_batch_report(
    batches: List[AnnotationBatch],
) -> Dict[str, Any]:
    """Generate quality report for multiple batches.

    Args:
        batches: List of annotation batches

    Returns:
        Multi-batch quality report
    """
    checker = AnnotationQualityChecker()

    batch_reports = []
    total_samples = 0
    total_score = 0.0

    for batch in batches:
        report = checker.generate_quality_report(batch)
        batch_reports.append(report)
        total_samples += report["total_samples"]
        total_score += report["quality_score"]

    avg_score = total_score / len(batches) if batches else 0.0

    # Aggregate issues
    all_issues = []
    for report in batch_reports:
        all_issues.extend(report["issues"])

    # Overall assessment
    if avg_score >= 80:
        assessment = "Excellent"
    elif avg_score >= 60:
        assessment = "Good"
    elif avg_score >= 40:
        assessment = "Fair"
    else:
        assessment = "Poor"

    return {
        "num_batches": len(batches),
        "total_samples": total_samples,
        "avg_quality_score": avg_score,
        "assessment": assessment,
        "batch_reports": batch_reports,
        "all_issues": all_issues,
        "passes_quality_check": avg_score >= 60,
    }


def format_multi_batch_report(report: Dict[str, Any]) -> str:
    """Format multi-batch quality report.

    Args:
        report: Multi-batch quality report

    Returns:
        Formatted report string
    """
    lines = [
        "\n" + "=" * 70,
        "Multi-Batch Quality Report",
        "=" * 70,
        f"Number of Batches: {report['num_batches']}",
        f"Total Samples: {report['total_samples']}",
        f"Average Quality Score: {report['avg_quality_score']:.0f}/100",
        f"Overall Assessment: {report['assessment']}",
        f"Passes Quality Check: {'✅ YES' if report['passes_quality_check'] else '❌ NO'}",
        "",
        "Individual Batch Scores:",
    ]

    for batch_report in report["batch_reports"]:
        status = "✅" if batch_report["passes_quality_check"] else "❌"
        lines.append(
            f"  {status} {batch_report['batch_id']:30s}: {batch_report['quality_score']:.0f}/100 ({batch_report['assessment']})"
        )

    if report["all_issues"]:
        lines.append("")
        lines.append("All Issues Detected:")
        # Group by check type
        issues_by_check = {}
        for issue in report["all_issues"]:
            check = issue["check"]
            if check not in issues_by_check:
                issues_by_check[check] = []
            issues_by_check[check].append(issue["issue"])

        for check, issues in sorted(issues_by_check.items()):
            lines.append(f"  {check}:")
            for issue in issues:
                lines.append(f"    - {issue}")

    lines.append("=" * 70 + "\n")

    return "\n".join(lines)


def save_quality_report(
    report: Dict[str, Any],
    output_file: Path,
    format_type: str = "text",
) -> Path:
    """Save quality report to file.

    Args:
        report: Quality report dictionary
        output_file: Output file path
        format_type: Format type ("text" or "json")

    Returns:
        Path to saved file
    """
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    if format_type == "json":
        import json

        with open(output_file, "w") as f:
            json.dump(report, f, indent=2, default=str)
    else:  # text
        formatted = format_quality_report(report)
        with open(output_file, "w") as f:
            f.write(formatted)

    return output_file
