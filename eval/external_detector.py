"""
Stub for external team detector integration.
When AIBRIDGE signals readiness, implement the actual REST call or HF model load.
"""
from eval.models import BiasDetectionResult, Language


class ExternalTeamDetector:
    """
    Wraps an external team's bias detector and adapts their schema
    to JuaKazi's BiasDetectionResult.

    Usage:
        detector = ExternalTeamDetector(team_name="TeamX", endpoint="https://...")
        result = detector.detect(text, language)
        # result.source == "external:TeamX"
    """

    def __init__(self, team_name: str, endpoint: str = None, hf_model: str = None):
        self.team_name = team_name
        self.endpoint = endpoint
        self.hf_model = hf_model

    def detect(self, text: str, language: Language) -> BiasDetectionResult:
        # TODO: implement when AIBRIDGE signals readiness
        # Return empty result for now — stub only
        return BiasDetectionResult(
            text=text,
            has_bias_detected=False,
            detected_edits=[],
            warn_edits=[],
        )
