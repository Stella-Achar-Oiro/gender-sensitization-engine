"""Token-level semantic preservation metrics for bias correction.

Used by api (rewrite threshold) and eval (correction_evaluator).
"""

import re


class SemanticPreservationMetrics:
    """Calculate token-level semantic preservation metrics."""

    @staticmethod
    def tokenize(text: str) -> list[str]:
        """Simple word tokenization."""
        return re.findall(r"\w+", text.lower())

    @staticmethod
    def calculate_bleu_score(original: str, corrected: str, n: int = 2) -> float:
        """BLEU-style n-gram precision (0-1)."""
        orig_tokens = SemanticPreservationMetrics.tokenize(original)
        corr_tokens = SemanticPreservationMetrics.tokenize(corrected)
        if not orig_tokens or not corr_tokens:
            return 0.0
        scores = []
        for gram_size in range(1, n + 1):
            orig_ngrams = [
                tuple(orig_tokens[i : i + gram_size])
                for i in range(len(orig_tokens) - gram_size + 1)
            ]
            corr_ngrams = [
                tuple(corr_tokens[i : i + gram_size])
                for i in range(len(corr_tokens) - gram_size + 1)
            ]
            if not orig_ngrams or not corr_ngrams:
                continue
            matches = sum(1 for ng in corr_ngrams if ng in orig_ngrams)
            precision = matches / len(corr_ngrams) if corr_ngrams else 0.0
            scores.append(precision)
        return sum(scores) / len(scores) if scores else 0.0

    @staticmethod
    def calculate_rouge_l(original: str, corrected: str) -> float:
        """ROUGE-L F1 (longest common subsequence), 0-1."""
        orig_tokens = SemanticPreservationMetrics.tokenize(original)
        corr_tokens = SemanticPreservationMetrics.tokenize(corrected)
        if not orig_tokens or not corr_tokens:
            return 0.0
        m, n = len(orig_tokens), len(corr_tokens)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if orig_tokens[i - 1] == corr_tokens[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                else:
                    dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
        lcs_length = dp[m][n]
        precision = lcs_length / n if n > 0 else 0.0
        recall = lcs_length / m if m > 0 else 0.0
        if precision + recall > 0:
            return 2 * precision * recall / (precision + recall)
        return 0.0

    @staticmethod
    def calculate_token_overlap(original: str, corrected: str) -> float:
        """Token set overlap ratio (0-1)."""
        orig_tokens = set(SemanticPreservationMetrics.tokenize(original))
        corr_tokens = set(SemanticPreservationMetrics.tokenize(corrected))
        if not orig_tokens:
            return 1.0 if not corr_tokens else 0.0
        return len(orig_tokens & corr_tokens) / len(orig_tokens)

    @staticmethod
    def calculate_edit_distance_ratio(original: str, corrected: str) -> float:
        """1 - normalized Levenshtein at token level (1.0 = identical)."""
        orig_tokens = SemanticPreservationMetrics.tokenize(original)
        corr_tokens = SemanticPreservationMetrics.tokenize(corrected)
        if not orig_tokens and not corr_tokens:
            return 1.0
        if not orig_tokens or not corr_tokens:
            return 0.0
        m, n = len(orig_tokens), len(corr_tokens)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if orig_tokens[i - 1] == corr_tokens[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1]
                else:
                    dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])
        distance = dp[m][n]
        max_len = max(m, n)
        return 1.0 - (distance / max_len) if max_len > 0 else 1.0

    @staticmethod
    def calculate_composite_preservation_score(original: str, corrected: str) -> dict[str, float]:
        """Composite score: 0.3*bleu + 0.3*rouge_l + 0.2*overlap + 0.2*edit_sim."""
        bleu = SemanticPreservationMetrics.calculate_bleu_score(original, corrected)
        rouge_l = SemanticPreservationMetrics.calculate_rouge_l(original, corrected)
        token_overlap = SemanticPreservationMetrics.calculate_token_overlap(original, corrected)
        edit_sim = SemanticPreservationMetrics.calculate_edit_distance_ratio(original, corrected)
        composite = 0.3 * bleu + 0.3 * rouge_l + 0.2 * token_overlap + 0.2 * edit_sim
        return {
            "bleu_score": bleu,
            "rouge_l_score": rouge_l,
            "token_overlap": token_overlap,
            "edit_similarity": edit_sim,
            "composite_score": composite,
        }
