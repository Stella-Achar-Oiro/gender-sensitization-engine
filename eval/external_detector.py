"""
Stub for external team detector integration (AIBRIDGE).
When AIBRIDGE signals readiness, implement the actual REST call or HF model load
and adapt the external schema to BiasDetectionResult.
"""
from typing import Optional

from eval.models import BiasDetectionResult, Language


class ExternalTeamDetector:
    """
    Wraps an external team's bias detector and adapts their schema
    to JuaKazi's BiasDetectionResult.

    Usage:
        detector = ExternalTeamDetector(team_name="TeamX", endpoint="https://...")
        result = detector.detect(text, language)
        # result.detection_source == "external:TeamX"
        # UI can show "Detected by: TeamX · Corrected by: JuaKazi"
    """

    def __init__(
        self,
        team_name: str,
        endpoint: Optional[str] = None,
        hf_model: Optional[str] = None,
    ):
        self.team_name = team_name
        self.endpoint = endpoint
        self.hf_model = hf_model

    def detect(self, text: str, language: Language) -> BiasDetectionResult:
        # TODO: when AIBRIDGE signals readiness:
        # - POST text to self.endpoint or run self.hf_model
        # - Map their response to detected_edits / warn_edits
        # - Return BiasDetectionResult(..., detection_source=f"external:{self.team_name}")
        return BiasDetectionResult(
            text=text,
            has_bias_detected=False,
            detected_edits=[],
            warn_edits=[],
            detection_source=f"external:{self.team_name}",
        )
